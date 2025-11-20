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
import asyncio
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
        self.sources = config.get("sources", ["arxiv", "semantic_scholar"])
        self.priority_impact = config.get("priority_impact", True)
        self.impact_min_citations = config.get("impact_min_citations", 10)  # Will be increased to 100
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

    async def _score_papers_with_llm(
        self,
        papers: List[Dict[str, Any]],
        context_text: str,
        batch_size: int = 8,
    ) -> None:
        """
        Use the language model to score relevance for a batch of papers.
        """
        if not papers:
            return

        normalized_context = context_text or "the given research topic"
        schema = {
            "type": "object",
            "patternProperties": {
                "^[0-9]+$": {"type": "number", "minimum": 1, "maximum": 10}
            },
            "additionalProperties": False,
        }

        def _truncate(text: str, limit: int = 1500) -> str:
            if not text:
                return ""
            return text if len(text) <= limit else text[: limit - 3] + "..."

        for start in range(0, len(papers), batch_size):
            batch = papers[start : start + batch_size]
            paper_descriptions = []
            for idx, paper in enumerate(batch):
                title = paper.get("title") or "Untitled"
                abstract = paper.get("abstract") or ""
                venue = paper.get("venue") or paper.get("journal") or ""
                keyword = paper.get("matched_keyword", "")
                year = paper.get("year") or ""
                description = (
                    f"[{idx}] Keyword: {keyword or 'unknown'} | Year: {year}\n"
                    f"Title: {title}\n"
                    f"Venue: {venue}\n"
                    f"Abstract: {_truncate(abstract)}\n"
                )
                paper_descriptions.append(description)

            prompt = (
                "You are an expert research assistant. Score each paper's relevance to "
                f"the topic:\n\"{normalized_context}\"\n\n"
                "Scoring rules:\n"
                "- 10 = directly tackles the exact problem with strong evidence\n"
                "- 5 = partially related or only addresses a sub-problem\n"
                "- 1 = irrelevant or off-topic\n"
                "- Prioritize methodological alignment over venue prestige\n"
                "- Return ONLY JSON mapping index to score between 1-10\n\n"
                "Papers to score:\n"
                f"{''.join(paper_descriptions)}"
            )

            try:
                response = await self._call_model(prompt=prompt, schema=schema)
            except Exception as exc:
                logger.error(f"Failed to score relevance batch: {exc}")
                # Fallback to default score
                for paper in batch:
                    paper.setdefault("relevance_score", 5.0)
                continue

            for idx, paper in enumerate(batch):
                score_value = response.get(str(idx))
                if isinstance(score_value, (int, float)):
                    paper["relevance_score"] = max(1.0, min(10.0, float(score_value)))
                else:
                    paper.setdefault("relevance_score", 5.0)

    def _compute_scores_for_papers(
        self,
        papers: List[Dict[str, Any]],
        task_difficulty: int,
        target_year: int,
    ) -> None:
        """
        Compute normalized citation/relevance and comprehensive score for papers.
        """
        for paper in papers:
            citations = (
                paper.get("citationCount")
                or paper.get("citations")
                or paper.get("citation_score")
                or 0
            )
            if citations > 0:
                norm_citations = min(10.0, 1.0 + (citations / 100.0) ** 0.5)
            else:
                norm_citations = 0.5

            relevance_score = (
                paper.get("relevance_score")
                or paper.get("score")
                or 5.0
            )
            norm_relevance = min(10.0, max(0.0, float(relevance_score)))

            year_weight, year_bonus = self._get_year_weight_and_bonus(
                task_difficulty, target_year
            )

            comprehensive_score = (
                norm_relevance * 0.5
                + norm_citations * 0.25 * year_weight
                + year_bonus
            )

            paper["citation_score"] = citations
            paper["norm_citations"] = norm_citations
            paper["norm_relevance"] = norm_relevance
            paper["year_weight"] = year_weight
            paper["year_bonus"] = year_bonus
            paper["comprehensive_score"] = comprehensive_score

    def _get_year_weight_and_bonus(
        self, task_difficulty: int, target_year: int
    ) -> Tuple[float, float]:
        """
        Determine the year weight and bonus based on difficulty and year.
        """
        try:
            year_value = int(str(target_year)[:4])
        except (TypeError, ValueError):
            year_value = 0

        if task_difficulty <= 2:
            return 1.0, 0.0

        if task_difficulty == 3:
            return (1.2, 0.0) if year_value >= 2022 else (1.0, 0.0)

        # Difficulty 4-5
        if year_value >= 2024:
            return 3.0, 3.5
        if year_value == 2023:
            return 1.8, 2.0
        if year_value == 2022:
            return 1.3, 1.5
        if year_value >= 2020:
            return 0.6, 0.0
        return 0.5, 0.0

    def _select_top_papers_for_year(
        self,
        papers: List[Dict[str, Any]],
        task_difficulty: int,
        target_year: int,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Select top papers for a given year based on task difficulty.
        Returns (selected_papers, strategy_description)
        """
        if not papers:
            return [], "No papers found"

        sorted_year_papers = sorted(
            papers,
            key=lambda x: (
                x.get("comprehensive_score", 0.0),
                x.get("citation_score", 0.0),
                x.get("relevance_score", 0.0),
            ),
            reverse=True,
        )

        if task_difficulty <= 2:
            top_limit = len(sorted_year_papers)
            strategy = "Top papers per keyword (simple task)"
        elif task_difficulty == 3:
            top_limit = 10
            strategy = "Top 10 by comprehensive score (moderate task)"
        else:
            year_value = int(str(target_year)[:4]) if target_year else 0
            if year_value >= 2024:
                top_limit = 12
                strategy = "Top 12 prioritizing 2024-2025 (complex task)"
            elif year_value >= 2022:
                top_limit = 10
                strategy = "Top 10 prioritizing 2022-2023 (complex task)"
            else:
                top_limit = 6
                strategy = "Top 6 for older years (complex task)"

        return sorted_year_papers[:top_limit], strategy
    
    async def _process_single_year(
        self,
        target_year: int,
        round_num: int,
        controlled_keywords: List[str],
        query_kwargs: Dict[str, Any],
        search_sources: List[str],
        task_difficulty: int,
        relevance_context: str,
        integrate_results,
        search_queries: List[str],
        paper_bank: Dict[str, Any],
        seen_titles: set,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process a single year: retrieve, score, and select papers.
        Returns (round_result, selected_papers)
        """
        logger.info(f"Processing Year {target_year} (Round {round_num})")
        
        # Build year-specific query with keywords
        year_queries = []
        for keyword in controlled_keywords:
            year_query = f'KeywordQuery("{keyword}")'
            year_queries.append(year_query)
        
        # Search papers for this year with all keywords
        keyword_year_map: Dict[str, List[Dict[str, Any]]] = {
            kw: [] for kw in controlled_keywords
        }
        
        for current_query in year_queries:
            if current_query not in search_queries:
                search_queries.append(current_query)
            
            # Search with year filter
            year_query_kwargs = query_kwargs.copy()
            year_query_kwargs["min_year"] = target_year
            year_query_kwargs["max_year"] = target_year
            year_query_kwargs["sources"] = search_sources
            
            try:
                logger.info(f"Searching {target_year} with query: {current_query}")
                papers_per_keyword = 15
                paper_results = self.paper_survey.query_route(current_query, papers_per_keyword, **year_query_kwargs)
            except Exception as e:
                logger.error(f"Search error for year {target_year}: {e}")
                continue
            
            # Process results and get filtered papers
            added_count, round_papers = integrate_results(paper_results, round_num)
            keyword_key = current_query.replace('KeywordQuery("', '').replace('")', '')
            keyword_year_map.setdefault(keyword_key, [])
            for paper in round_papers:
                paper['matched_keyword'] = keyword_key
                paper['year'] = paper.get('year') or target_year
            keyword_year_map[keyword_key].extend(round_papers)

        year_selected: List[Dict[str, Any]] = []
        papers_found_count = 0
        selection_strategy = "No papers found"
        
        if task_difficulty <= 2:
            # Simple tasks: process per keyword, max 10 per keyword per year
            for keyword, keyword_papers in keyword_year_map.items():
                keyword_year_filtered = [
                    p for p in keyword_papers
                    if p.get('year') == target_year or str(p.get('year', '')).startswith(str(target_year))
                ]
                papers_found_count += len(keyword_year_filtered)
                if not keyword_year_filtered:
                    continue
                
                # Score papers with LLM (already done in year processing)
                await self._score_papers_with_llm(keyword_year_filtered, relevance_context)
                self._compute_scores_for_papers(keyword_year_filtered, task_difficulty, target_year)
                
                keyword_sorted = sorted(
                    keyword_year_filtered,
                    key=lambda x: (
                        x.get('comprehensive_score', 0.0),
                        x.get('citation_score', 0.0),
                        x.get('relevance_score', 0.0),
                    ),
                    reverse=True,
                )
                top_keyword = keyword_sorted[:10]
                if top_keyword:
                    year_selected.extend(top_keyword)
                    logger.info(
                        f"Year {target_year}, keyword '{keyword}': "
                        f"found {len(keyword_year_filtered)} papers, selected {len(top_keyword)}"
                    )
            if not year_selected:
                logger.warning(f"No papers found for year {target_year}")
                return None, []
            selection_strategy = "Per-keyword top 10 (simple task, arXiv only)"
        else:
            # Moderate/Complex tasks: aggregate all keywords for the year
            aggregated_year = []
            for keyword, keyword_papers in keyword_year_map.items():
                keyword_year_filtered = [
                    p for p in keyword_papers
                    if p.get('year') == target_year or str(p.get('year', '')).startswith(str(target_year))
                ]
                papers_found_count += len(keyword_year_filtered)
                aggregated_year.extend(keyword_year_filtered)
            
            if not aggregated_year:
                logger.warning(f"No papers found for year {target_year}")
                return None, []
            
            # Score papers with LLM (already done in year processing)
            await self._score_papers_with_llm(aggregated_year, relevance_context)
            self._compute_scores_for_papers(aggregated_year, task_difficulty, target_year)
            year_selected, selection_strategy = self._select_top_papers_for_year(
                aggregated_year, task_difficulty, target_year
            )
            if not year_selected:
                logger.warning(f"No papers selected for year {target_year}")
                return None, []
        
        logger.info(
            f"Year {target_year}: Found {papers_found_count} papers, "
            f"selected {len(year_selected)} using {selection_strategy}"
        )
        
        # Record round results
        round_result = {
            "round": round_num,
            "year": target_year,
            "queries": year_queries,
            "papers_found": papers_found_count,
            "papers_selected": len(year_selected),
            "selected_papers": year_selected,
            "top_citation_count": year_selected[0].get('citation_score', 0) if year_selected else 0
        }
        
        return round_result, year_selected
    
    async def _deep_read_single_paper(
        self,
        paper: Dict[str, Any],
        output_schema_paper_details: Dict[str, Any]
    ) -> None:
        """
        Deep read a single paper: download PDF, extract text, and analyze.
        """
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

            try:
                if paper['source'] in ["semantic_scholar", "arXiv"]:
                    pdf_path = download_pdf(url, save_folder=pdf_dir)
                elif paper['source'] == "pubmed":
                    pdf_path = download_pdf_by_doi(doi=url, download_dir=pdf_dir)
                else:
                    pdf_path = None
                
                if pdf_path:
                    text = extract_text_from_pdf(pdf_path)
                    if text:
                        get_detail_prompt = (
                            f"Analyze the following paper text and extract structured information: {text}\n"
                            "Extract: Background, Contributions, Methods, Challenges. Return JSON format."
                        )
                        try:
                            response = await self._call_model(
                                prompt=get_detail_prompt,
                                schema=output_schema_paper_details
                            )
                            details = response
                        except Exception as e:
                            logger.error(f"Failed to get paper details for {paper_id}: {e}")
                            details = None
                        
                        if details:
                            paper["background"] = details.get("background", "")
                            paper["contributions"] = details.get("contributions", "")
                            paper["methods"] = details.get("methods", "")
                            paper["challenges"] = details.get("challenges", "")
            except Exception as e:
                logger.error(f"Failed to deep read paper {paper_id}: {e}")
        
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
        
        # Get task difficulty for dynamic paper selection
        task_difficulty = task_decomp.get("task_difficulty", 3)  # Default to moderate (3)
        if not isinstance(task_difficulty, (int, float)):
            try:
                task_difficulty = int(task_difficulty)
            except (ValueError, TypeError):
                task_difficulty = 3
        task_difficulty = max(1, min(5, task_difficulty))  # Clamp to 1-5
        logger.info(f"Task difficulty detected: {task_difficulty}/5")
        
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
            query_kwargs["min_citation_count"] = max(self.impact_min_citations, 10)
            if self.impact_min_year:
                query_kwargs["min_year"] = self.impact_min_year
        
        relevance_context = (
            task_decomp.get("problem_overview")
            or goal_description
            or domain
            or "该研究任务"
        )
        
        # Year-based retrieval strategy: dynamically adjusted by task difficulty
        # Simple tasks: 2015-2020 (prioritize foundational papers, arXiv only)
        # Moderate/Complex tasks: 2020-2025 (focus on modern methods, configured sources)
        if task_difficulty <= 2:
            target_years = [2015, 2016, 2017, 2018, 2019, 2020]
            search_sources = ["arxiv"]
        else:
            target_years = [2020, 2021, 2022, 2023, 2024, 2025]
            search_sources = self.sources
        
        # Calculate year weights based on task difficulty
        # Higher difficulty tasks favor recent years (2022-2025)
        # Lower difficulty tasks favor earlier years for foundational papers (2015-2020)
        def calculate_year_weights(years, difficulty):
            """Calculate weights for each year based on task difficulty."""
            weights = {}
            if difficulty <= 2:  # Simple tasks: favor earlier years for foundational papers
                # Strongly favor 2015-2020 for foundational papers
                for year in years:
                    if 2015 <= year <= 2020:
                        weights[year] = 1.0  # Uniform weight for foundational years 2015-2020
            elif difficulty == 3:  # Moderate tasks: uniform distribution
                for year in years:
                    weights[year] = 1.0
            else:  # Difficulty 4-5: Complex tasks favor recent years
                # Strongly favor 2022-2025 for cutting-edge methods
                for year in years:
                    if year >= 2022:
                        weights[year] = 1.5  # Higher weight for recent years
                    elif year == 2021:
                        weights[year] = 0.8
                    else:  # 2020
                        weights[year] = 0.5  # Lower weight for older years
            
            # Normalize weights to sum to number of years
            total_weight = sum(weights.values())
            for year in weights:
                weights[year] = (weights[year] / total_weight) * len(years)
            
            return weights
        
        year_weights = calculate_year_weights(target_years, task_difficulty)
        
        # Estimate max papers (flexible, quality-based selection will determine actual count)
        if task_difficulty <= 2:
            estimated_max_papers = len(target_years) * 10  # Simple: up to 10 per year (2015-2020)
        elif task_difficulty == 3:
            estimated_max_papers = len(target_years) * 10  # Moderate: up to 10 per year
        else:
            # Complex: prioritize 2024-2025 (up to 12 each), 2022-2023 (up to 10 each), older (up to 6 each)
            recent_count = sum(1 for y in target_years if y >= 2024) * 12  # 2024-2025: 12 each
            mid_count = sum(1 for y in target_years if 2022 <= y <= 2023) * 10  # 2022-2023: 10 each
            older_count = sum(1 for y in target_years if y < 2022) * 6  # 2020-2021: 6 each
            estimated_max_papers = recent_count + mid_count + older_count
        
        # Override target_max_papers if not explicitly set
        if target_max_papers == 30:  # Default value
            target_max_papers = estimated_max_papers
        
        logger.info(f"Year-based retrieval (difficulty {task_difficulty}/5): {target_years}")
        logger.info(f"Selection strategy: Quality-based dynamic selection (not fixed per year)")
        logger.info(f"Estimated max papers: {estimated_max_papers} (actual count depends on paper quality)")
        logger.info("🚀 Using parallel processing for years to speed up retrieval")
        
        # Parallel processing: process all years concurrently
        async def process_year_wrapper(target_year, round_num):
            try:
                return await self._process_single_year(
                    target_year=target_year,
                    round_num=round_num,
                    controlled_keywords=controlled_keywords,
                    query_kwargs=query_kwargs,
                    search_sources=search_sources,
                    task_difficulty=task_difficulty,
                    relevance_context=relevance_context,
                    integrate_results=integrate_results,
                    search_queries=search_queries,
                    paper_bank=paper_bank,
                    seen_titles=seen_titles,
                )
            except Exception as e:
                logger.error(f"Error processing year {target_year}: {e}", exc_info=True)
                return None, []
        
        # Create tasks for all years
        year_tasks = [
            process_year_wrapper(target_year, round_num + 1)
            for round_num, target_year in enumerate(target_years)
        ]
        
        # Execute all years in parallel (with concurrency limit to avoid overwhelming APIs)
        logger.info(f"Processing {len(year_tasks)} years in parallel...")
        year_results = await asyncio.gather(*year_tasks, return_exceptions=True)
        
        # Process results and collect papers
        for idx, result in enumerate(year_results):
            if isinstance(result, Exception):
                logger.error(f"Year {target_years[idx]} failed with exception: {result}")
                continue
            
            round_result, year_selected = result
            if round_result is None or not year_selected:
                continue
            
            # Add to all selected papers
            all_selected_papers.extend(year_selected)
            round_results.append(round_result)
            
            # Check if we've reached the target
            if len(all_selected_papers) >= target_max_papers:
                logger.info(f"Reached target of {target_max_papers} papers")
                # Sort round_results by year for consistent ordering
                round_results.sort(key=lambda x: x.get("year", 0))
                break
        
        logger.info(f"Completed {len(round_results)} rounds, collected {len(all_selected_papers)} papers total")
        
        # Skip duplicate scoring - papers are already scored during year processing
        # Use relevance_score from year processing instead of re-scoring
        paper_bank_list = all_selected_papers[:]
        logger.info("✅ Using relevance scores from year processing (skipping duplicate scoring)")
        
        # Ensure all papers have relevance_score (use from comprehensive_score calculation)
        for paper in paper_bank_list:
            if 'relevance_score' not in paper:
                # Fallback: use score if available, otherwise use comprehensive_score component
                paper['relevance_score'] = paper.get('score', 5.0)
        
        # Select top papers for deep reading (use relevance_score from year processing)
        # For papers with same relevance, use comprehensive_score as tie-breaker
        final_selected = sorted(
            paper_bank_list,
            key=lambda x: (
                x.get('relevance_score', 0.0),
                x.get('comprehensive_score', 0.0),
                x.get('citation_score', 0.0),
            ),
            reverse=True
        )[:self.top_per_round]
        logger.info(f"Selected top {len(final_selected)} papers for deep reading (using relevance_score from year processing)")
        
        # Deep reading for selected papers - PARALLEL PROCESSING
        logger.info("🚀 Processing deep reading in parallel...")
        deep_read_tasks = [
            self._deep_read_single_paper(paper, output_schema_paper_details)
            for paper in final_selected
        ]
        
        # Execute deep reading in parallel
        await asyncio.gather(*deep_read_tasks, return_exceptions=True)
        logger.info(f"✅ Completed deep reading for {len(final_selected)} papers")
        
        # Mark deep-read papers
        final_selected_ids = {p['id'] for p in final_selected}
        for paper in paper_bank_list:
            paper['is_deep_read'] = paper['id'] in final_selected_ids
        
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
                "grounding_rounds": len(round_results) - len(controlled_keywords) if len(round_results) > len(controlled_keywords) else 0
            },
            "task_decomposition_context": {
                "problem_overview": goal_description,
                "scientific_keywords": tech_kw,
                "main_objectives": main_objectives,
                "key_steps": key_steps
            }
        }