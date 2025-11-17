"""
Adapter layer for the literature_agent repository.

This module exposes a synchronous entry point so the existing Flask API
can trigger the InternAgent survey + summary pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Path to the downloaded literature_agent repository
LITERATURE_AGENT_ROOT = (
    Path(__file__).resolve().parent / "literature_agent" / "literature_agent-123"
)

if LITERATURE_AGENT_ROOT.exists():
    sys.path.insert(0, str(LITERATURE_AGENT_ROOT))
else:
    logging.warning(
        "literature_agent-123 directory is missing. Please unzip the repo into the workspace."
    )

from internagent.mas.agents.agent_factory import AgentFactory
from internagent.mas.models.model_factory import ModelFactory


class LiteratureAgentError(RuntimeError):
    """Shared exception type for the wrapper."""


class LiteratureAgentService:
    """Orchestrates SurveyAgent and LiteratureSummaryAgent execution."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        work_dir: Optional[Path] = None,
    ) -> None:
        if not LITERATURE_AGENT_ROOT.exists():
            raise LiteratureAgentError(
                "literature_agent directory not found. Download and unzip the repo first."
            )

        self.root_dir = LITERATURE_AGENT_ROOT
        self.config_path = (
            Path(config_path)
            if config_path
            else self.root_dir / "config" / "default_config.yaml"
        )
        self.work_dir = Path(work_dir) if work_dir else self.root_dir / "runtime_cache"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self._config = self._load_config()
        self._model_factory = ModelFactory()
        self._task_agent = self._create_agent("task_decomposition")
        self._survey_agent = self._create_agent("survey")
        self._summary_agent = self._create_agent("literature_summary")

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise LiteratureAgentError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as fh:
            config: Dict[str, Any] = yaml.safe_load(fh) or {}

        config["config_path"] = str(self.config_path)
        config["work_dir"] = str(self.work_dir)
        config["task_name"] = "literature_agent_web"
        config.setdefault("tools", {})
        config["tools"].setdefault("paper_survey", {})

        return config

    def _create_agent(self, agent_type: str):
        agent_settings = self._config.get("agents", {}).get(agent_type)
        if not agent_settings:
            raise LiteratureAgentError(f"Missing agent config: {agent_type}")

        merged = agent_settings.copy()
        merged["_global_config"] = self._config
        return AgentFactory.create_agent(
            agent_type=agent_type,
            config=merged,
            model_factory=self._model_factory,
        )

    @staticmethod
    def _validate_environment() -> None:
        required_vars = {
            "DEEPSEEK_API_KEY": "required for DeepSeek chat completions",
            "S2_API_KEY": "required for Semantic Scholar paper search",
        }
        missing: List[str] = []
        for var, desc in required_vars.items():
            if not os.environ.get(var):
                missing.append(f"{var} ({desc})")
        if missing:
            raise LiteratureAgentError(
                "Missing required environment variables: " + ", ".join(missing)
            )

    async def _run_async(
        self,
        question: str,
        domain: Optional[str],
        background: str,
        max_papers: int,
        guidance: Optional[List[str]],
    ) -> Dict[str, Any]:
        self._validate_environment()

        sanitized_guidance = [g for g in (guidance or []) if g]
        effective_domain = domain or "General scientific research"
        max_papers = max(5, min(max_papers, 30))

        plan = None
        plan_guidance: List[str] = []
        try:
            planning_context = {
                "images": [],
                "text_input": question,
                "description": question,
                "domain": effective_domain,
                "manual_guidance": sanitized_guidance,
                "background": background or "",
                "constraints": [],
            }
            plan = await self._task_agent.execute(planning_context, {})

            if plan.get("main_objectives"):
                plan_guidance.append(
                    "Main Objectives:\n"
                    + "\n".join(f"- {obj}" for obj in plan["main_objectives"])
                )
            if plan.get("key_steps"):
                plan_guidance.append(
                    "Key Research Steps:\n"
                    + "\n".join(
                        f"- {step.get('step_name', '')}: {step.get('description', '')}"
                        for step in plan["key_steps"][:5]
                    )
                )
        except Exception as exc:
            logging.warning("Task decomposition failed, falling back to direct survey: %s", exc)
            plan = None

        if plan:
            survey_context = {
                "description": plan.get("problem_overview") or question,
                "domain": effective_domain,
                "task_decomposition": {
                    "problem_overview": plan.get("problem_overview", ""),
                    "domain": effective_domain,
                    "scientific_keywords": plan.get("scientific_keywords", []),
                    "main_objectives": plan.get("main_objectives", []),
                    "key_steps": plan.get("key_steps", []),
                },
                "manual_guidance": sanitized_guidance + plan_guidance,
                "max_papers": max_papers,
                "force_iteration": bool(sanitized_guidance or plan_guidance),
            }
        else:
            survey_context = {
                "description": question,
                "domain": effective_domain,
                "background": background or "",
                "manual_guidance": sanitized_guidance,
                "manual_queries": [question],
                "max_papers": max_papers,
                "force_iteration": bool(sanitized_guidance),
            }

        survey_result = await self._survey_agent.execute(survey_context, {})

        summary_context = {
            "description": plan.get("problem_overview") if plan else question,
            "domain": effective_domain,
            "papers": survey_result.get("papers", []),
            "search_queries": survey_result.get("search_queries", []),
            "manual_guidance": sanitized_guidance + plan_guidance,
            "max_papers": max_papers,
            "task_decomposition": plan or {},
            "round_results": survey_result.get("round_results", []),
            "all_selected_papers": survey_result.get("all_selected_papers", []),
            "final_selected_papers": survey_result.get("final_selected_papers", []),
        }

        summary_result = await self._summary_agent.execute(summary_context, {})

        answer = summary_result.get("full_report") or summary_result.get(
            "problem_formulation", ""
        )

        return {
            "answer": answer,
            "summary": summary_result,
            "survey": survey_result,
        }

    def run(
        self,
        question: str,
        domain: Optional[str] = None,
        background: str = "",
        max_papers: int = 12,
        guidance: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not question or not question.strip():
            raise LiteratureAgentError("Question must not be empty.")

        try:
            return asyncio.run(
                self._run_async(
                    question=question.strip(),
                    domain=domain,
                    background=background,
                    max_papers=max_papers,
                    guidance=guidance,
                )
            )
        except LiteratureAgentError:
            raise
        except Exception as exc:
            raise LiteratureAgentError(f"Literature agent execution failed: {exc}") from exc


_SERVICE_INSTANCE: Optional[LiteratureAgentService] = None


def get_literature_service() -> LiteratureAgentService:
    global _SERVICE_INSTANCE
    if _SERVICE_INSTANCE is None:
        _SERVICE_INSTANCE = LiteratureAgentService()
    return _SERVICE_INSTANCE


def run_literature_query(
    question: str,
    domain: Optional[str] = None,
    background: str = "",
    max_papers: int = 12,
    guidance: Optional[List[str]] = None,
) -> Dict[str, Any]:
    service = get_literature_service()
    return service.run(
        question=question,
        domain=domain,
        background=background,
        max_papers=max_papers,
        guidance=guidance,
    )

