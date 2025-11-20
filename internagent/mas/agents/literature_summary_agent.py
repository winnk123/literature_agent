"""
Literature Summary Agent for InternAgent

Generates structured survey reports from collected paper metadata and search history.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class LiteratureSummaryAgent(BaseAgent):
    """
    Produces structured summaries of literature search results.
    """

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a literature survey report given collected papers and search queries.

        Args:
            context: Expected keys include:
                - description: research goal description
                - domain: scientific domain
                - papers: list[dict] or dict of papers with scores and deep-read annotations
                - search_queries: list[str] of executed queries
                - manual_guidance: optional guidance history for additional context
            params: reserved for future use

        Returns:
            Dict containing structured report fields.
        """
        try:
            # Call the internal method to generate the report
            report = await self._generate_report(context)
        except Exception as exc:
            # Log and raise an error if report generation fails
            logger.error(f"Literature summary generation failed: {exc}")
            raise AgentExecutionError("Literature summary generation failed") from exc

        return report

    async def _generate_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
      goal_description = context.get("description", "")
      domain = context.get("domain", "")
      manual_guidance = context.get("manual_guidance", [])
      if isinstance(manual_guidance, str):
        manual_guidance = [manual_guidance]

      papers_raw = context.get("papers") or []
      if isinstance(papers_raw, dict):
        papers = list(papers_raw.values())
      else:
         papers = papers_raw

      search_queries = context.get("search_queries", [])

      if not papers:
        empty_report = {
            "problem_formulation": "No relevant literature was retrieved; please adjust the search queries or provide manual leads.",
            "current_landscape": "",
            "approach_taxonomy": "",
            "critical_gaps": "",
            "forward_path": "",
            "action_items": ["Provide additional search hints or narrow the research scope."],
            "needs_additional_search": True,
            "notes": "no_papers_found",
            "full_report": "No relevant literature was retrieved. Please adjust search queries or provide manual guidance.",
            "references": []
        }
        return empty_report

      max_papers = context.get("max_papers")
      if not isinstance(max_papers, int) or max_papers <= 0:
        max_papers = self.config.get("max_papers", 30)

      sorted_papers = sorted(papers, key=lambda x: x.get("score", 0), reverse=True)
      top_papers = sorted_papers[: min(len(sorted_papers), max_papers)]

      paper_digest: List[Dict[str, Any]] = []
      references_list: List[Dict[str, Any]] = []
    
      for idx, paper in enumerate(top_papers, 1):
        digest_entry = {
            "id": paper.get("id"),
            "title": paper.get("title"),
            "year": paper.get("year"),
            "venue": paper.get("venue",""),
            "score": paper.get("score"),
            "abstract": (paper.get("abstract") or "")[:1200],
            "background": paper.get("background", ""),
            "contributions": paper.get("contributions", ""),
            "methods": paper.get("methods", ""),
            "challenges": paper.get("challenges", ""),
            "is_deep_read": paper.get("is_deep_read", False),
        }
        paper_digest.append(digest_entry)
        
        # Build reference entry
        authors = paper.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]
        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown"
        
        ref_entry = {
            "id": idx,
            "title": paper.get("title", "Untitled"),
            "authors": author_str,
            "year": paper.get("year"),
            "journal": paper.get("journal") or paper.get("venue", ""),
            "doi": paper.get("doi", ""),
            "url": paper.get("url", ""),
            "citation_count": paper.get("citations", 0),
            "score": paper.get("score", 0)
        }
        references_list.append(ref_entry)

      trimmed_queries = search_queries[-5:] if search_queries else []

      report_schema = {
        "type": "object",
        "properties": {
            "problem_formulation": {"type": "string"},
            "current_landscape": {"type": "string"},
            "approach_taxonomy": {"type": "string"},
            "critical_gaps": {"type": "string"},
            "forward_path": {"type": "string"},
            "action_items": {
                "type": "array",
                "items": {"type": "string"},
            },
            "needs_additional_search": {"type": "boolean"},
            "notes": {"type": "string"},
        },
        "required": [
            "problem_formulation",
            "current_landscape",
            "approach_taxonomy",
            "critical_gaps",
            "forward_path",
            "action_items",
            "needs_additional_search",
        ],
        }

      guidance_block = ""
      if manual_guidance:
        guidance_lines = "\n".join(f"- {g}" for g in manual_guidance)
        guidance_block = f"Recent human guidance for this survey:\n{guidance_lines}\n\n"

      paper_digest_str = json.dumps(paper_digest, ensure_ascii=False)
      recent_queries_str = json.dumps(trimmed_queries, ensure_ascii=False)

      # 获取 task_decomposition 的 key_steps（如果存在）
      task_decomposition = context.get("task_decomposition") or {}
      key_steps = task_decomposition.get("key_steps", [])
      
      key_steps_guidance = ""
      if key_steps:
        key_steps_text = "\n".join([
          f"- {step.get('step_name', '')}: {step.get('description', '')}" 
          for step in key_steps
        ])
        key_steps_guidance = (
          "\n\n**IMPORTANT: Action Items Alignment Requirement**\n"
          "The task decomposition phase has already identified the following key steps:\n"
          f"{key_steps_text}\n\n"
          "You MUST generate action_items that are **aligned with and consistent with** these key steps. "
          "Each action_item should correspond to one or more of these key steps. "
          "You can refine, merge, or split them based on literature findings, but the overall structure and sequence should remain consistent. "
          "The action_items should reflect the same logical flow as the key steps from task decomposition.\n"
        )
      
      report_prompt = (
        "You are an expert scientific literature analyst. Your task is to synthesize the findings from "
        "recent papers related to the following research goal. Your output may be in Simplified Chinese "
        "or English, but it must preserve scientific rigor.\n\n"
        f"Research goal: {goal_description}\n"
        f"Domain: {domain}\n\n"
        f"{guidance_block}"
        "You have the following high-priority papers (with model-assigned scores and extracted highlights):\n"
        f"{paper_digest_str}\n\n"
        "Recent search queries that produced these papers:\n"
        f"{recent_queries_str}\n\n"
        f"{key_steps_guidance}"
        "Produce a concise, structured report that explicitly covers the sections below. "
        "Frame each section around scientifically meaningful questions or hypotheses.\n"
        "1. Problem Formulation (problem_formulation): Clearly articulate the scientific core question, "
        "    explain its theoretical and practical importance, and break it into key scientific sub-challenges.\n"
        "2. Current Landscape (current_landscape): Summarize the most influential, high-quality works addressing "
        "    each aspect of the problem. Mention venues/citation impact when notable.\n"
        "3. Approach Taxonomy (approach_taxonomy): Cluster existing solutions by methodological strategy, "
        "    describe their evolution, and map each strategy to the scientific sub-challenges.\n"
        "4. Critical Gaps (critical_gaps): Analyze unresolved issues across technical, deployment/contextual, "
        "    and evaluation dimensions. Tie the critique back to the original scientific question.\n"
        "5. Synthesis & Forward Path (forward_path): Propose concrete, differentiated research directions or "
        "    methodological combinations that could close the gaps.\n"
       "6. Recommended Actions (action_items): Propose a clear, **step-by-step execution plan** (typically 4-6 steps) that forms a coherent and implementable pipeline from initial preparation to a concrete experiment or prototype. "
        "Each step should include:"
        " **Objective**: What this step aims to achieve."
        "**Method**: Describe the workflow or approach for this step (brief and implementable, **do not write code**)."
        "**Expected Output**: What this step will produce or validate."

        "Ensure that the steps are **logically connected**, i.e., the sequence of steps should together form a **continuous workflow** that a research engineer could follow from start to finish:"
        "1. Each step's output or results should naturally inform, guide, or enable the next step."
        "2. Steps should not be isolated; instead, they should build upon one another to form a pipeline that moves from preparation → model selection → model training → evaluation / deployment."
        "3. If some steps do not directly pass data to the next, they should still contribute to the overall progress toward the final experiment or prototype, so that the reader can see a clear path from start to finish."

        "Focus on **logical, implementable actions** that can later be translated into Jupyter notebook cells or scripts. Do **not write code** in this section; just describe a stepwise, end-to-end experimental or prototyping workflow.\n"
        "7. Whether additional searching is needed (needs_additional_search, true/false).\n"
        "8. Additional notes (notes, optional).\n"
        "Keep the language precise and information-dense."
      )

      response = await self._call_model(
        prompt=report_prompt,
        schema=report_schema,
      )

      action_items = response.get("action_items", [])
      if not isinstance(action_items, list):
        action_items = [str(action_items)]
        response["action_items"] = action_items
 
      # Generate full report text
      full_report = await self._generate_full_report_text(
        structured_data=response,
        goal_description=goal_description,
        domain=domain,
        references=references_list
      )

    # Add full report and references to response
      response["full_report"] = full_report
      # References for citation list: prefer all_selected_papers (full set), fallback to sorted list
      all_papers_for_refs = context.get("all_selected_papers") or sorted_papers
      # Build references from the full set (capped by max_papers if provided)
      full_refs: List[Dict[str, Any]] = []
      for idx, paper in enumerate(all_papers_for_refs[:max_papers], 1):
        authors = paper.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]
        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "") if authors else "Unknown"
        full_refs.append({
            "id": idx,
            "title": paper.get("title", "Untitled"),
            "authors": author_str,
            "year": paper.get("year"),
            "journal": paper.get("journal") or paper.get("venue", ""),
            "doi": paper.get("doi", ""),
            "url": paper.get("url", ""),
            "citation_count": paper.get("citations", 0),
            "score": paper.get("score", 0),
        })
      response["references"] = full_refs
      # Replace author-year citations in full_report with numeric [n] based on full_refs order
      try:
        mapping = self._build_author_year_index(full_refs)
        response["full_report"] = self._replace_author_year_with_numeric(response.get("full_report", ""), mapping)
      except Exception as _exc:
        logger.warning(f"Failed to normalize citations in literature report: {_exc}")

      # Write standalone literature summary report (Markdown) with required sections and all references
      try:
        report_md = self._compose_literature_summary_markdown(
          context=context,
          structured=response,
          references=full_refs
        )
        if report_md and report_md.strip():
          work_dir = (self.config.get("_global_config", {}) or {}).get("work_dir") or self.config.get("work_dir")
          if work_dir:
            out_dir = Path(work_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "LITERATURE_SUMMARY.md"
            # Apply numeric citation mapping for the standalone report as well
            try:
              mapping2 = self._build_author_year_index(full_refs)
              report_md = self._replace_author_year_with_numeric(report_md, mapping2)
            except Exception:
              pass
            out_path.write_text(report_md, encoding="utf-8")
            logger.info(f"Literature summary saved to: {out_path}")
      except Exception as exc:
        logger.warning(f"Failed to write LITERATURE_SUMMARY.md: {exc}")

      return response

    async def _generate_full_report_text(
      self,
      structured_data: Dict[str, Any],
      goal_description: str,
      domain: str,
      references: List[Dict[str, Any]]
    ) -> str:
    
    
    # Format references section
      ref_section = "\n## References\n\n"
      for ref in references:
        ref_line = f"[{ref['id']}] {ref['authors']} ({ref['year']}). {ref['title']}"
        if ref.get('journal'):
            ref_line += f". {ref['journal']}"
        if ref.get('doi'):
            ref_line += f". DOI: {ref['doi']}"
        if ref.get('citation_count', 0) > 0:
            ref_line += f" (Citations: {ref['citation_count']})"
        ref_section += ref_line + "\n\n"
    
    # Build full report prompt
      full_report_prompt = (
        "You are writing a comprehensive literature survey report. Based on the structured analysis below, "
        "generate a coherent, well-formatted report in Markdown format. The report should flow naturally "
        "as a single document, with proper section headers and transitions.\n\n"
        f"Research Goal: {goal_description}\n"
        f"Domain: {domain}\n\n"
        "Structured Analysis:\n"
        f"- Problem Formulation: {structured_data.get('problem_formulation', '')}\n"
        f"- Current Landscape: {structured_data.get('current_landscape', '')}\n"
        f"- Approach Taxonomy: {structured_data.get('approach_taxonomy', '')}\n"
        f"- Critical Gaps: {structured_data.get('critical_gaps', '')}\n"
        f"- Forward Path: {structured_data.get('forward_path', '')}\n"
        f"- Action Items: {', '.join(structured_data.get('action_items', []))}\n\n"
        "Generate a complete report with the following structure:\n"
        "1. Title and Introduction (briefly state the research goal)\n"
        "2. Problem Formulation\n"
        "3. Current Landscape\n"
        "4. Approach Taxonomy\n"
        "5. Critical Gaps\n"
        "6. Future Directions\n"
        "7. Conclusion and Recommendations\n"
        "8. References (list all cited papers with proper citations)\n\n"
        "Use Markdown formatting. When mentioning specific papers, cite them as [1], [2], etc. "
        "corresponding to the reference list. Make the report cohesive and professional."
       )
    
      try:
        full_report_text = await self._call_model(
            prompt=full_report_prompt,
            schema=None  # Free-form text output
        )
        
        # Append formatted references
        full_report_text += ref_section
        
        return full_report_text
      except Exception as exc:
        logger.warning(f"Failed to generate full report text, falling back to structured format: {exc}")
        # Fallback: assemble from structured data
        return self._assemble_report_from_structured(structured_data, references)

    def _assemble_report_from_structured(
    self,
    structured_data: Dict[str, Any],
    references: List[Dict[str, Any]]
) -> str:

        report_lines = [
        "# Literature Survey Report\n",
        "## 1. Problem Formulation\n",
        structured_data.get("problem_formulation", ""),
        "\n\n## 2. Current Landscape\n",
        structured_data.get("current_landscape", ""),
        "\n\n## 3. Approach Taxonomy\n",
        structured_data.get("approach_taxonomy", ""),
        "\n\n## 4. Critical Gaps\n",
        structured_data.get("critical_gaps", ""),
        "\n\n## 5. Future Directions\n",
        structured_data.get("forward_path", ""),
        "\n\n## 6. Recommended Actions\n",
    ]
    
        for item in structured_data.get("action_items", []):
          report_lines.append(f"- {item}\n")
    
        report_lines.append("\n## References\n\n")
        for ref in references:
          ref_line = f"[{ref['id']}] {ref['authors']} ({ref['year']}). {ref['title']}"
          if ref.get('journal'):
            ref_line += f". {ref['journal']}"
          if ref.get('doi'):
              ref_line += f". DOI: {ref['doi']}"
          report_lines.append(ref_line + "\n\n")
    
        return "".join(report_lines)

    def _derive_title_from_text_plain(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return "文献调研"
        base = text.strip().rstrip("？?。.")
        for prefix in ["如何", "怎样", "怎么", "请问", "基于", "面向"]:
            if base.startswith(prefix):
                base = base[len(prefix):].strip()
                break
        if len(base) > 14:
            base = base[:14].strip()
        return base or "文献调研"

    def _compose_literature_summary_markdown(
        self,
        context: Dict[str, Any],
        structured: Dict[str, Any],
        references: List[Dict[str, Any]]
    ) -> str:
        # Title from problem formulation/description
        problem_text = (
            structured.get("problem_formulation")
            or context.get("description")
            or ""
        )
        title = self._derive_title_from_text_plain(problem_text)
        lines: List[str] = []
        lines.append(f"# {title}\n\n")
        
        # Use full_report if available (complete generated text), otherwise fallback to structured fields
        full_report = structured.get("full_report", "")
        if full_report and full_report.strip():
            # Extract main content from full_report (remove references section if present)
            import re
            # Remove references section if it exists
            report_content = re.sub(r'\n## References.*$', '', full_report, flags=re.DOTALL)
            report_content = re.sub(r'\n## 参考文献.*$', '', report_content, flags=re.DOTALL)
            # Reorganize to match required format with level-2 headings
            # Try to extract sections from full_report, or use structured fields as fallback
            # For now, use structured fields to ensure proper format, but we could parse full_report
            # Since full_report format may vary, we'll use structured fields but ensure they're complete
            lines.append("## 问题定义\n\n")
            lines.append(f"{structured.get('problem_formulation','')}\n\n")
            lines.append("## 研究现状\n\n")
            lines.append(f"{structured.get('current_landscape','')}\n\n")
            lines.append("## 方法分类\n\n")
            lines.append(f"{structured.get('approach_taxonomy','')}\n\n")
            lines.append("## 研究缺口\n\n")
            lines.append(f"{structured.get('critical_gaps','')}\n\n")
            lines.append("## 未来方向\n\n")
            lines.append(f"{structured.get('forward_path','')}\n\n")
        else:
            # Fallback: use structured fields directly
            lines.append("## 问题定义\n\n")
            lines.append(f"{structured.get('problem_formulation','')}\n\n")
            lines.append("## 研究现状\n\n")
            lines.append(f"{structured.get('current_landscape','')}\n\n")
            lines.append("## 方法分类\n\n")
            lines.append(f"{structured.get('approach_taxonomy','')}\n\n")
            lines.append("## 研究缺口\n\n")
            lines.append(f"{structured.get('critical_gaps','')}\n\n")
            lines.append("## 未来方向\n\n")
            lines.append(f"{structured.get('forward_path','')}\n\n")
        
        # References (list all, include URLs/DOIs)
        if references:
            lines.append("## 参考文献\n\n")
            for idx, ref in enumerate(references, 1):
                line = f"- [{idx}] {ref.get('authors','Unknown')} ({ref.get('year','n.d.')}). *{ref.get('title','Untitled')}*"
                journal = ref.get("journal")
                if journal:
                    line += f". {journal}"
                doi = ref.get("doi")
                url = ref.get("url")
                if doi:
                    line += f". DOI: {doi}"
                if url:
                    line += f". {url}"
                lines.append(line + "\n")
        return "".join(lines)

    def _make_author_year_key(self, authors: str, year: Any) -> str:
        # authors like "Jonathan Ho, Ajay Jain, P. Abbeel" → use first surname token letters only
        import re
        if not isinstance(authors, str):
            authors = str(authors or "")
        year_str = str(year or "").strip()
        first = authors.split(",")[0] if authors else ""
        surname = re.sub(r"[^A-Za-z\-]", "", first).lower()
        return f"{surname}:{year_str}"

    def _build_author_year_index(self, references: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Build mapping from author-year key to numeric index based on provided references order.
        """
        mapping: Dict[str, int] = {}
        for idx, ref in enumerate(references, 1):
            key = self._make_author_year_key(ref.get("authors", ""), ref.get("year", ""))
            if key and key not in mapping:
                mapping[key] = idx
        return mapping

    def _replace_author_year_with_numeric(self, text: str, author_year_to_num: Dict[str, int]) -> str:
        """
        Replace occurrences like [Surname, 2020] or [Surname 2020] with numeric [n] using mapping.
        """
        import re
        if not text:
            return text
        pattern = re.compile(r"\[([A-Za-z\-\.\s]+),?\s*(\d{4})\]")
        def repl(m):
            surname_raw = m.group(1)
            year = m.group(2)
            surname = re.sub(r"[^A-Za-z\-]", "", surname_raw).lower()
            key = f"{surname}:{year}"
            n = author_year_to_num.get(key)
            return f"[{n}]" if n is not None else m.group(0)
        return pattern.sub(repl, text)