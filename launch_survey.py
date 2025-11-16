"""
Launch a survey-only literature review workflow.

This script runs the SurveyAgent in iterative mode, allowing human guidance
between rounds. It retrieves high-impact papers, generates structured reports,
and supports manual corrections when the search drifts or returns sparse results.
"""

import argparse
import asyncio
import json
import logging
import os
import os.path as osp
import sys
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from internagent.mas.agents.agent_factory import AgentFactory
from internagent.mas.models.model_factory import ModelFactory

load_dotenv()

ROOT_DIR = osp.dirname(osp.abspath(__file__))


def setup_logging(verbose: bool) -> logging.Logger:
    """Configure root logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger("SurveyPipeline")


def load_config(config_path: Optional[str]) -> Tuple[Dict[str, Any], str]:
    """Load YAML or JSON configuration."""
    candidates: List[str] = []
    if config_path:
        candidates.append(config_path)
    default_path = osp.join(ROOT_DIR, "config", "default_config.yaml")
    candidates.append(default_path)

    for path in candidates:
        if path and osp.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                if path.endswith((".yaml", ".yml")):
                    try:
                        import yaml  # type: ignore
                    except ImportError as exc:  # pragma: no cover - runtime safeguard
                        raise RuntimeError(
                            "PyYAML is required to load YAML configuration files."
                        ) from exc
                    config_data = yaml.safe_load(f) or {}
                else:
                    config_data = json.load(f)
            return config_data, path

    raise FileNotFoundError(
        f"Unable to locate configuration. Paths tried: {', '.join(candidates)}"
    )


def slugify(value: str) -> str:
    """Create a filesystem-friendly slug."""
    import re

    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value or "survey"


def load_task_definition(task_arg: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Load task information from prompt.json if a task directory/name is provided."""
    if not task_arg:
        return None, None, None

    if "/" in task_arg or "\\" in task_arg or osp.isdir(task_arg):
        task_dir = task_arg
        task_name = osp.basename(task_dir.rstrip("/\\"))
    else:
        task_dir = osp.join(ROOT_DIR, "tasks", task_arg)
        task_name = task_arg

    prompt_path = osp.join(task_dir, "prompt.json")
    if not osp.exists(prompt_path):
        raise FileNotFoundError(f"Task prompt not found at {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_data = json.load(f)

    return prompt_data, task_dir, task_name


def wrap_text(text: str, width: int = 90) -> str:
    """Wrap text for nicer console output."""
    return textwrap.fill(text, width=width) if text else ""


def summarize_iteration(index: int, result: Dict[str, Any], logger: logging.Logger) -> None:
    """Print a concise summary of iteration results."""
    papers: List[Dict[str, Any]] = result.get("papers", [])
    report: Dict[str, Any] = result.get("report", {})

    logger.info("=" * 80)
    logger.info("Survey Iteration %d Summary", index)
    logger.info("Collected papers: %d", len(papers))
    logger.info("Executed queries: %d", len(result.get("search_queries", [])))

    top_papers = sorted(papers, key=lambda x: x.get("score", 0), reverse=True)[:5]
    if top_papers:
        logger.info("\nTop Papers:")
        for paper in top_papers:
            title = paper.get("title", "Untitled")
            year = paper.get("year", "Unknown")
            score = paper.get("score", 0)
            source = paper.get("source", "unknown")
            logger.info("  - [%.2f] %s (%s, %s)", score, title, year, source)

    if report:
        logger.info("\nReport Overview:\n%s", wrap_text(report.get("overview", "")))
        logger.info("\nKey Limitations:\n%s", wrap_text(report.get("limitations", "")))
        logger.info("\nOpportunities:\n%s", wrap_text(report.get("opportunities", "")))
        logger.info("\nRecommended Directions:\n%s", wrap_text(report.get("recommended_directions", "")))
    logger.info("=" * 80)


def build_output_directory(base_dir: Optional[str], task_name: Optional[str]) -> str:
    """Determine and create output directory."""
    if base_dir:
        output_dir = osp.abspath(base_dir)
    elif task_name:
        output_dir = osp.join(ROOT_DIR, "results", task_name, "survey")
    else:
        output_dir = osp.join(ROOT_DIR, "results", f"survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(osp.join(output_dir, "iterations"), exist_ok=True)
    return output_dir


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the survey agent to generate iterative literature reports."
    )
    parser.add_argument("--task", type=str, help="Task name or path containing prompt.json")
    parser.add_argument("--description", type=str, help="Research goal description (overrides task prompt)")
    parser.add_argument("--domain", type=str, help="Scientific domain (overrides task prompt)")
    parser.add_argument("--background", type=str, help="Additional background information")
    parser.add_argument("--constraint", action="append", dest="constraints", default=[], help="Add a constraint (repeatable)")
    parser.add_argument("--config", type=str, default=None, help="Path to configuration file")
    parser.add_argument("--output_dir", type=str, default=None, help="Directory to store survey outputs")
    parser.add_argument("--max_rounds", type=int, default=3, help="Maximum survey iterations to run")
    parser.add_argument("--max_papers", type=int, default=None, help="Target number of high-value papers to retain")
    parser.add_argument("--search_depth", type=str, choices=["shallow", "moderate", "deep"], help="Override survey search depth")
    parser.add_argument("--guidance", action="append", default=[], help="Initial human guidance instruction (repeatable)")
    parser.add_argument("--manual_query", action="append", default=[], help="Initial manual query (plain text or KeywordQuery format)")
    parser.add_argument("--non_interactive", action="store_true", help="Disable interactive guidance between rounds")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


async def run_survey(args: argparse.Namespace, logger: logging.Logger) -> None:
    """Main asynchronous survey loop."""
    prompt_data, task_dir, task_name = load_task_definition(args.task)

    goal_description = args.description or (prompt_data or {}).get("task_description") or ""
    domain = args.domain or (prompt_data or {}).get("domain") or ""
    background = args.background or (prompt_data or {}).get("background") or ""
    constraints = args.constraints or (prompt_data or {}).get("constraints", [])

    if not goal_description or not domain:
        raise ValueError("Both --description and --domain must be provided when no task prompt is available.")

    if not task_name:
        task_name = slugify(domain or goal_description[:50])

    output_dir = build_output_directory(args.output_dir, task_name)
    logger.info("Survey outputs will be stored in %s", output_dir)

    config, loaded_config_path = load_config(args.config)
    logger.info("Loaded configuration from %s", loaded_config_path)

    config["config_path"] = loaded_config_path
    config["work_dir"] = output_dir
    config["task_name"] = task_name

    agent_settings = config.get("agents", {})

    survey_config = agent_settings.get("survey", {}).copy()
    if args.max_papers:
        survey_config["max_papers"] = args.max_papers
    if args.search_depth:
        survey_config["search_depth"] = args.search_depth
    survey_config["_global_config"] = config

    model_factory = ModelFactory()
    survey_agent = AgentFactory.create_agent("survey", survey_config, model_factory)
    if args.max_papers:
        survey_agent.max_papers = args.max_papers
    if args.search_depth:
        survey_agent.search_depth = args.search_depth

    summary_agent = None
    summary_config = agent_settings.get("literature_summary")
    if summary_config is not None:
        summary_config = summary_config.copy()
        summary_config["_global_config"] = config
        summary_agent = AgentFactory.create_agent("literature_summary", summary_config, model_factory)

    guidance_history: List[str] = []
    pending_guidance: List[str] = [g for g in args.guidance if g]
    pending_queries: List[str] = [q for q in args.manual_query if q]
    accumulated_papers: List[Dict[str, Any]] = []
    accumulated_queries: List[str] = []
    iteration_records: List[Dict[str, Any]] = []
    last_result: Dict[str, Any] = {}
    last_literature_report: Dict[str, Any] = {}

    interactive = not args.non_interactive
    stop_requested = False

    for iteration in range(1, args.max_rounds + 1):
        if stop_requested:
            break

        combined_guidance = guidance_history + pending_guidance
        context: Dict[str, Any] = {
            "description": goal_description,
            "domain": domain,
            "background": background,
            "constraints": constraints,
        }

        if combined_guidance:
            context["manual_guidance"] = combined_guidance
        if pending_queries:
            context["manual_queries"] = pending_queries
        if accumulated_papers:
            context["paper_bank"] = accumulated_papers
        if accumulated_queries:
            context["search_queries"] = accumulated_queries
        if args.max_papers:
            context["max_papers"] = args.max_papers
        if pending_guidance or pending_queries:
            context["force_iteration"] = True

        logger.info("Starting survey iteration %d ...", iteration)
        result = await survey_agent.execute(context, {})
        last_result = result

        # Update state for next loop
        accumulated_papers = result.get("papers", [])
        accumulated_queries = result.get("search_queries", [])

        literature_report = {}
        if summary_agent:
            summary_context = {
                "description": goal_description,
                "domain": domain,
                "papers": accumulated_papers,
                "search_queries": accumulated_queries,
                "manual_guidance": combined_guidance,
                "max_papers": args.max_papers,
            }
            try:
                literature_report = await summary_agent.execute(summary_context, {})
            except Exception as exc:
                logger.error(f"Literature summary agent failed: {exc}")
                literature_report = {}
        last_literature_report = literature_report

        iteration_payload = {
            "iteration": iteration,
            "timestamp": record_timestamp,
            "manual_guidance": combined_guidance,
            "manual_queries": list(pending_queries),
            "papers": accumulated_papers,
            "search_queries": accumulated_queries,
            "report": literature_report,
        }

        iteration_path = osp.join(output_dir, "iterations", f"iteration_{iteration:02d}.json")
        with open(iteration_path, "w", encoding="utf-8") as f:
            json.dump(iteration_payload, f, ensure_ascii=False, indent=2)

        summarize_iteration(iteration, {
            "papers": accumulated_papers,
            "report": literature_report,
            "search_queries": accumulated_queries,
        }, logger)

        iteration_records.append(
            {
                "iteration": iteration,
                "timestamp": record_timestamp,
                "guidance_applied": list(pending_guidance),
                "manual_queries_applied": list(pending_queries),
                "papers_collected": len(accumulated_papers),
                "result_file": osp.relpath(iteration_path, output_dir),
            }
        )

        # Move current instructions into history
        if pending_guidance:
            guidance_history.extend(pending_guidance)
        pending_guidance = []
        pending_queries = []

        if not interactive or iteration == args.max_rounds:
            continue

        logger.info(
            "\n提供人工指导以调整下一轮文献调研：\n"
            "  - 直接输入文字：作为新的检索指导\n"
            "  - 输入 `query:关键词1 关键词2`：手工追加检索语句\n"
            "  - 输入 `stop` 结束调研\n"
            "连续输入多条指令，每条指令回车确认；直接回车进入下一轮。\n"
        )

        while True:
            try:
                user_input = input("指令 > ").strip()
            except EOFError:
                user_input = "stop"

            if not user_input:
                break

            lowered = user_input.lower()
            if lowered in {"stop", "exit", "quit"}:
                stop_requested = True
                break

            if lowered.startswith("query:") or lowered.startswith("q:"):
                query = user_input.split(":", 1)[1].strip()
                if query:
                    pending_queries.append(query)
                    logger.info("已添加手工检索：%s", query)
                continue

            pending_guidance.append(user_input)
            logger.info("已添加人工指导：%s", user_input)

        if stop_requested:
            break

    final_report = last_literature_report
    summary_payload = {
        "task": {
            "name": task_name,
            "description": goal_description,
            "domain": domain,
            "background": background,
            "constraints": constraints,
            "task_dir": task_dir,
        },
        "config": {
            "config_path": loaded_config_path,
            "max_rounds": args.max_rounds,
            "max_papers": args.max_papers or survey_agent.max_papers,
            "search_depth": args.search_depth or survey_agent.search_depth,
        },
        "iterations": iteration_records,
        "final_report": final_report or {},
        "final_papers_count": len(accumulated_papers),
        "latest_iteration_file": iteration_records[-1]["result_file"] if iteration_records else None,
        "generated_at": datetime.now().isoformat(),
    }

    summary_path = osp.join(output_dir, "survey_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, ensure_ascii=False, indent=2)

    logger.info("Survey completed. Summary saved to %s", summary_path)


def main() -> None:
    args = parse_arguments()
    logger = setup_logging(args.verbose)

    try:
        asyncio.run(run_survey(args, logger))
    except KeyboardInterrupt:
        logger.warning("Survey interrupted by user.")
    except Exception as exc:  # pragma: no cover - runtime error path
        logger.error("Survey failed: %s", exc)
        raise


if __name__ == "__main__":
    main()

