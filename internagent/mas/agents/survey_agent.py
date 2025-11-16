"""
Corrected Survey Agent - Per Round Top 10 by Citations

This module implements the corrected Survey Agent logic:
- Each round searches 20 papers
- Selects top 10 papers by citation count from each round
- Collects all selected papers across rounds
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import os
from .base_agent import BaseAgent, AgentExecutionError
from ..tools.paper_survey import PaperSurvey
from ..tools.utils import PaperMetadata, parse_io_description, format_papers_for_printing_next_query,\
    download_pdf, extract_text_from_pdf, download_pdf_by_doi, select_papers

logger = logging.getLogger(__name__)


class SurveyAgent(BaseAgent):
    """
    Corrected Survey Agent with per-round citation-based selection.

    Logic: Each round searches 20 papers → selects top 10 by citations → continue to next round
    """
    
    def __init__(self, model, config: Dict[str, Any]):
        """
        Initialize the survey agent.
        
        Args:
            model: Language model to use
            config: Configuration dictionary
        """
        super().__init__(model, config)
        
        # Load agent-specific configuration
        self.max_papers = config.get("max_papers", 30)  # Target total papers (3 rounds × 10)
        self.search_depth = config.get("search_depth", "moderate")
        self.sources = config.get("sources", ["pubmed", "arxiv", "semantic_scholar"])
        self.priority_impact = config.get("priority_impact", True)
        self.impact_min_citations = config.get("impact_min_citations", 20)  # Will be increased to 100
        self.impact_min_year = config.get("impact_min_year")
        
        # Papers per search round
        self.papers_per_round = config.get("papers_per_round", 20)
        
        # Top papers to select from each round
        self.top_per_round = config.get("top_per_round", 10)
        
        # Initialize tools
        tools_config = config.get("_global_config", {}).get("tools", {})
        self.paper_survey = None
        self._init_paper_survey(tools_config.get("paper_survey", {}))
        
    def _init_paper_survey(self, config: Dict[str, Any]) -> None:
        """
        Initialize the literature search tool.
        """
        max_results = config.get("max_results", self.papers_per_round)
        sort = config.get("sort", "relevance")
        try:
            self.paper_survey = PaperSurvey(max_results, sort)
            logger.info("Paper survey tool initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize literature search: {str(e)}")
        
    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the survey workflow and return structured literature outputs.
        """
        survey_outputs = await self.advanced_query_paper(context=context)
        
        return survey_outputs

    async def advanced_query_paper(self, context) -> Dict[str, Any]:
        
        def _normalize_query(raw_query: str) -> Optional[str]:
            if not raw_query:
                return None
            query = raw_query.strip()
            if not query:
                return None
            if query.startswith(("KeywordQuery", "PaperQuery", "GetReferences")):
                return query
            escaped = query.replace('"', '\\"')
            return f'KeywordQuery("{escaped}")'
        
        # Extract context from task decomposition
        task_decomp = context.get("task_decomposition", {}) or context.get("subtask", {})
        goal_description = context.get("description", "") or task_decomp.get("problem_overview", "")
        domain = context.get("domain", "") or task_decomp.get("domain", "")
        tech_kw = task_decomp.get("scientific_keywords", []) or context.get("subtask", {}).get("technical_keywords", [])
        if isinstance(tech_kw, str):
            tech_kw = [tech_kw]
        tech_kw = [kw for kw in tech_kw if kw]
        
        main_objectives = task_decomp.get("main_objectives", [])
        key_steps = task_decomp.get("key_steps", [])
        
        manual_guidance = context.get("manual_guidance", [])
        if isinstance(manual_guidance, str):
            manual_guidance = [manual_guidance]
        manual_guidance = [g for g in manual_guidance if g]
        
        manual_queries = context.get("manual_queries", [])
        if isinstance(manual_queries, str):
            manual_queries = [manual_queries]
        manual_queries = [q for q in manual_queries if q]
        
        existing_papers = context.get("paper_bank") or context.get("existing_papers") or []
        existing_queries = context.get("search_queries") or []
        
        target_max_papers = context.get("max_papers") or self.max_papers
        force_iteration = context.get("force_iteration")
        if force_iteration is None:
            force_iteration = bool(manual_guidance or manual_queries)
        
        # Enhanced guidance block
        guidance_block = ""
        if manual_guidance:
            guidance_lines = "\n".join(f"- {g}" for g in manual_guidance)
            guidance_block += f"Human guidance for this survey:\n{guidance_lines}\n\n"
        
        if task_decomp:
            if goal_description:
                guidance_block += f"Problem Overview: {goal_description}\n\n"
            if main_objectives:
                objectives_text = "\n".join(f"- {obj}" for obj in main_objectives)
                guidance_block += f"Main Objectives:\n{objectives_text}\n\n"
            if key_steps:
                steps_text = "\n".join(f"- {step.get('step_name', '')}: {step.get('description', '')}" 
                                     for step in key_steps[:3])
                guidance_block += f"Key Research Steps:\n{steps_text}\n\n"
        
        search_queries = list(existing_queries)
        
        # Track papers by round
        round_results = []
        all_selected_papers = []
        seen_titles = set()
        
        # Initialize paper bank
        paper_bank = {}
        
        output_schema_paper_score={
            "type": "object",
            "Properties": {
                "^[a-zA-Z0-9_]+$": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "description": "A dictionary where each key is a paperID and each value is a score between 1 and 10."
        }
        output_schema_paper_details={
            "type": "object",
            "properties": {
                "background": {"type": "string", "description": "Core problem context and motivation"},
                "contributions": {"type": "string", "description": "Novel contributions to the field"},
                "methods": {"type": "string", "description": "Key technical approaches/methods used"},
                "challenges": {"type": "string", "description": "Limitations or challenges mentioned"}
            },
            "required": ["background", "contributions", "methods", "challenges"]
        }
        
        def integrate_results(result_dict: Optional[Dict[str, Any]], round_num: int) -> Tuple[int, List[Dict]]:
            """
            Integrate results from one round and return (added_count, filtered_papers)
            """
            if not result_dict:
                return 0, []
            
            flattened_papers: List[Dict[str, Any]] = []
            for source, papers in result_dict.items():
                if isinstance(papers, list):
                    for paper in papers:
                        if isinstance(paper, dict):
                            entry = paper.copy()
                            if source:
                                entry.setdefault("source", source)
                            flattened_papers.append(entry)
                elif isinstance(papers, dict) and "data" in papers:
                    for paper in papers["data"]:
                        if isinstance(paper, dict):
                            entry = paper.copy()
                            if source:
                                entry.setdefault("source", source)
                            flattened_papers.append(entry)
            
            # Filter and process papers for this round
            round_papers = []
            for entry in flattened_papers:
                title = entry.get("title")
                citations = entry.get("citationCount") or entry.get("citations") or 0
                year = entry.get("year")
                
                # Quality filtering
                if self.priority_impact:
                    min_citations = max(self.impact_min_citations, 20)  # At least 20 citations
                    if citations < min_citations:
                        continue
                    if self.impact_min_year and year:
                        try:
                            if int(year) < int(self.impact_min_year):
                                continue
                        except Exception:
                            pass
                
                # Top-tier venue detection
                venue_info = entry.get("venue", "") or entry.get("journal", "") or ""
                top_tier_indicators = [
                    "neurips", "icml", "iclr", "aaai", "ijcai",
                    "cvpr", "iccv", "eccv",
                    "acl", "emnlp", "naacl",
                    "nature", "science", "cell",
                    "ieee", "acm", "springer"
                ]
                venue_quality_bonus = any(indicator in venue_info.lower() for indicator in top_tier_indicators)
                
                if title and title in seen_titles:
                    continue
                
                # Assign ID and score
                idx = str(len(paper_bank))
                entry["id"] = str(idx)
                entry["round"] = round_num
                
                # Base scoring
                base_score = 5.0
                if venue_quality_bonus:
                    base_score += 2.0
                if citations > 1000:
                    base_score += 1.0
                entry["score"] = entry.get("score", base_score)
                entry["venue_quality"] = venue_quality_bonus
                
                paper_bank[str(idx)] = entry
                round_papers.append(entry)
                
                if title:
                    seen_titles.add(title)
            
            return len(round_papers), round_papers
        
        # Limited keyword strategy: use only top 3 most important keywords
        # This prevents the AI from combining keywords and keeps search precision
        max_keywords_to_use = min(3, len(tech_kw))  # Use max 3 keywords to avoid sprawl
        controlled_keywords = tech_kw[:max_keywords_to_use]
        
        logger.info(f"Using controlled keyword strategy: {controlled_keywords}")
        
        # Initialize query tracking
        used_keyword_indices = set()
        
        # Task attribute definition (optional for grounding)
        if goal_description:
            define_task_attribute_prompt = f"You are a researcher doing research on: {goal_description}."
        else:
            define_task_attribute_prompt = f"You are a researcher doing research on the topic of {domain}."
        
        define_task_attribute_prompt += "You should define the task attribute such as the model input and output of the topic for better searching relevant papers. Formulate the input and output as: Attribute(\"attribute\"). For example, Input(\"input\"), Output(\"output\")."
        
        if guidance_block:
            define_task_attribute_prompt += f"\n{guidance_block}"
        define_task_attribute_prompt += "The attribute: (just return the task attribute itself with no additional text):"
        
        try:
            response = await self._call_model(prompt=define_task_attribute_prompt)
            io_description = parse_io_description(response)
        except Exception as e:
            logger.error(f"Error defining task attribute: {str(e)}")
            io_description = None
        
        query_kwargs = {}
        if self.priority_impact:
            query_kwargs["sort"] = "citations"
            query_kwargs["min_citation_count"] = max(self.impact_min_citations, 100)
            if self.impact_min_year:
                query_kwargs["min_year"] = self.impact_min_year
        
        # Start rounds loop - each round searches 20 papers and selects top 10
        round_num = 0
        max_rounds = 5  # Maximum rounds to prevent infinite loop
        
        while len(all_selected_papers) < target_max_papers and round_num < max_rounds:
            round_num += 1
            logger.info(f"Starting Round {round_num}")
            
            # Generate query for this round - STRATEGY: one keyword per round
            current_query = None
            
            if round_num <= len(controlled_keywords):
                # Use single scientific keyword for precise search
                keyword_index = round_num - 1
                if keyword_index < len(controlled_keywords):
                    current_keyword = controlled_keywords[keyword_index]
                    current_query = f'KeywordQuery("{current_keyword}")'
                    used_keyword_indices.add(keyword_index)
                    logger.info(f"Round {round_num}: Using single keyword: {current_keyword}")
            else:
                # All keywords used, now use grounding from previous rounds
                if all_selected_papers:
                    grounding_papers = all_selected_papers[-20:] if len(all_selected_papers) >= 20 else all_selected_papers
                    grounding_papers_str = format_papers_for_printing_next_query(grounding_papers)
                    
                    if io_description is not None:
                        new_query_prompt = (
                            f"You are a researcher doing literature review on the topic of {domain if goal_description else goal_description}.\n"
                            f"{guidance_block}"
                            f"The input and output of the queries should be same with: input: {io_description[0]}, output: {io_description[1]}\n"
                            "Always prioritize highly cited papers published in top-tier conferences or journals.\n"
                            "**CRITICAL**: Focus on papers with high citation counts and from prestigious venues.\n"
                            f"Right now you have already collected the following relevant papers: \n{grounding_papers_str}\n"
                            f"You can formulate new search queries based on these papers. And you have already asked the following queries:\n{search_queries}\n"
                            "Please formulate a new query to expand our paper collection with more diverse and relevant papers. Directly give me your new query without any explanation or additional text, just the query itself:"
                        )
                    else:
                        new_query_prompt = (
                            f"You are a researcher doing literature review on the topic of {domain if goal_description else goal_description}.\n"
                            f"{guidance_block}"
                            "Always prioritize highly cited papers published in top-tier conferences or journals.\n"
                            f"Right now you have already collected the following relevant papers: \n{grounding_papers_str}\n"
                            f"You have already asked the following queries:\n{search_queries}\n"
                            "Please formulate a new query to expand our paper collection with more diverse and relevant papers. Directly give me your new query without any explanation or additional text, just the query itself:"
                        )
                    
                    try:
                        response = await self._call_model(prompt=new_query_prompt)
                        current_query = response
                        logger.info(f"Round {round_num}: Using grounding-based query after all keywords exhausted")
                    except Exception as e:
                        logger.error(f"Error generating new query for round {round_num}: {str(e)}")
                        break
                else:
                    # Should not happen, but fallback
                    logger.warning(f"No papers available for grounding in round {round_num}")
                    break
            
            if not current_query:
                logger.warning(f"No query generated for round {round_num}")
                break
            
            # Add to search queries
            if current_query not in search_queries:
                search_queries.append(current_query)
            
            # Search 20 papers for this round
            try:
                logger.info(f"Searching with query: {current_query}")
                paper_results = self.paper_survey.query_route(current_query, self.papers_per_round, **query_kwargs)
            except Exception as e:
                logger.error(f"Search error in round {round_num}: {e}")
                break
            
            # Process results and get filtered papers
            added_count, round_papers = integrate_results(paper_results, round_num)
            
            if added_count == 0:
                logger.warning(f"No papers found in round {round_num}")
                continue
            
            # **CRITICAL**: Select top 10 papers by citation count from this round
            sorted_by_citations = sorted(round_papers, 
                                        key=lambda x: x.get('citationCount', 0) or x.get('citations', 0) or 0, 
                                        reverse=True)
            
            # Select top 10 from this round
            top_10_this_round = sorted_by_citations[:self.top_per_round]
            
            logger.info(f"Round {round_num}: Found {added_count} papers, selected top {len(top_10_this_round)} by citations")
            
            # Add to all selected papers
            all_selected_papers.extend(top_10_this_round)
            
            # Record round results
            round_result = {
                "round": round_num,
                "query": current_query,
                "papers_found": added_count,
                "papers_selected": len(top_10_this_round),
                "selected_papers": top_10_this_round,
                "top_citation_count": top_10_this_round[0].get('citationCount', 0) if top_10_this_round else 0
            }
            round_results.append(round_result)
            
            # If we've reached the target, stop
            if len(all_selected_papers) >= target_max_papers:
                logger.info(f"Reached target of {target_max_papers} papers")
                break
        
        logger.info(f"Completed {len(round_results)} rounds, collected {len(all_selected_papers)} papers total")
        
        # Score all selected papers for relevance
        paper_bank_list = all_selected_papers[:]
        for batch_index in range(0, len(paper_bank_list), 10):
            batch = paper_bank_list[batch_index:batch_index + 10]
            abs_batch = [{'id': paper['id'], 'title': paper['title'], 'abstract': paper['abstract']} for paper in batch]
            
            scoring_context = f"research problem: {goal_description}" if goal_description else f"topic: {domain}"
            paper_score_prompt = f"""You are a helpful literature review assistant. Score each paper from 1 to 10 based on:
            (1) Direct relevance to {scoring_context}
            (2) **CRITICAL**: Prefer work from top-tier venues (NeurIPS, ICML, ICLR, CVPR, ICCV, ACL, Nature, Science) with high citation impact
            (3) Empirical papers that propose novel methods with experimental validation
            (4) **CITATION IMPORTANCE**: Higher citation counts should receive higher scores

            The papers to score are:
            {abs_batch}

            Please score each paper from 1 to 10. Write response as JSON with paper index as key:
            {{
            "0": 8,
            "1": 6, 
            "2": 9,
            "3": 7
            }}
            """
            
            try:
                response = await self._call_model(
                    prompt=paper_score_prompt,
                    schema=output_schema_paper_score
                )
            except Exception as e:
                logger.error(f"Failed to score papers: {e}")
                continue
            
            for key, score in response.items():
                batch_index_in_current_batch = int(key)
                if 0 <= batch_index_in_current_batch < len(batch):
                    # Apply score to the correct paper in the current batch
                    batch[batch_index_in_current_batch]['score'] = score
        
        # Select top papers for deep reading (top 10 by final score)
        final_selected = sorted(paper_bank_list, key=lambda x: x.get('score', 0), reverse=True)[:self.top_per_round]
        logger.info(f"Selected top {len(final_selected)} papers for deep reading")
        
        # Deep reading for selected papers
        for paper in final_selected:
            paper_id = paper["id"]
            url = None
            if paper['source'] in ['arXiv', 'pubmed']:
                url = paper.get('url') or paper.get('doi')
            elif paper['source'] == 'semantic_scholar':
                if paper.get('isOpenAccess', False):
                    url = paper['openAccessPdf']['url']
            
            if url:
                base_dir = 'tmp'
                pdf_dir = os.path.join(base_dir, "pdf")
                if not os.path.exists(pdf_dir):
                    os.makedirs(pdf_dir)

                if paper['source'] in ["semantic_scholar", "arXiv"]:
                    pdf_path = download_pdf(url, save_folder=pdf_dir)
                elif paper['source'] == "pubmed":
                    pdf_path = download_pdf_by_doi(doi=url, download_dir=pdf_dir)
                
                if pdf_path:
                    text = extract_text_from_pdf(pdf_path)
                    if text:
                        get_detail_prompt = f"Analyze the following paper text and extract structured information: {text}\nExtract: Background, Contributions, Methods, Challenges. Return JSON format."
                        try:
                            response = await self._call_model(
                                prompt=get_detail_prompt,
                                schema=output_schema_paper_details
                            )
                            details = response
                        except Exception as e:
                            logger.error(f"Failed to get paper details: {e}")
                            details = None
                        
                        if details:
                            paper["background"] = details.get("background", "")
                            paper["contributions"] = details.get("contributions", "")
                            paper["methods"] = details.get("methods", "")
                            paper["challenges"] = details.get("challenges", "")
        
        # Mark deep-read papers
        for paper in paper_bank_list:
            paper['is_deep_read'] = paper['id'] in [p['id'] for p in final_selected]
        
        # 输出结果
        return {
            "papers": paper_bank_list,  # All papers
            "search_queries": search_queries,
            "round_results": round_results,  # Per round breakdown
            "all_selected_papers": all_selected_papers,  # All papers selected across rounds
            "final_selected_papers": final_selected,  # Top papers for deep reading
            "selection_method": "per_round_citation_priority",
            "papers_per_round": self.papers_per_round,
            "top_per_round": self.top_per_round,
            "total_rounds": len(round_results),
            "keyword_strategy": {
                "controlled_keywords": controlled_keywords,
                "max_keywords_used": max_keywords_to_use,
                "keywords_exhausted": len(used_keyword_indices) >= len(controlled_keywords),
                "grounding_rounds": round_num - len(controlled_keywords) if round_num > len(controlled_keywords) else 0
            },
            "task_decomposition_context": {
                "problem_overview": goal_description,
                "scientific_keywords": tech_kw,
                "main_objectives": main_objectives,
                "key_steps": key_steps
            }
        }