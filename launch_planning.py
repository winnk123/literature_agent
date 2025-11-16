"""
Launch planning pipeline: image-based task decomposition + literature survey.
"""

import argparse
import asyncio
import json
import logging
import os
import os.path as osp
from pyexpat import model
import sys
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from internagent.mas.agents.agent_factory import AgentFactory
from internagent.mas.models.model_factory import ModelFactory
# ReviewCoordinator will be imported locally when needed

load_dotenv()

ROOT_DIR = osp.dirname(osp.abspath(__file__))


def setup_logging(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger("PlanningPipeline")


def slugify(value: str) -> str:
    import re

    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value or "planning"


def load_config(config_path: Optional[str]) -> Tuple[Dict[str, Any], str]:
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
                    except ImportError as exc:
                        raise RuntimeError("PyYAML is required to load YAML configuration files.") from exc
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)
            return data, path

    raise FileNotFoundError(f"Unable to locate configuration. Paths tried: {', '.join(candidates)}")


def load_task_definition(task_arg: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
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
        data = json.load(f)

    return data, task_dir, task_name

def wrap_text(text: str, width: int = 90) -> str:
    return textwrap.fill(text, width=width) if text else ""

def _generate_revision_suggestions(review_history: List[Dict[str, Any]]) -> str:
    """
    从评审历史中生成修改意见文档
    
    Args:
        review_history: 评审历史列表，每轮包含教学性和逻辑性评审结果
        
    Returns:
        Markdown格式的修改意见文档
    """
    content = []
    content.append("# 📝 修改意见汇总\n\n")
    content.append("本文档汇总了所有审稿人提出的修改建议，方便查看和实施。\n\n")
    content.append("---\n\n")
    
    for round_data in review_history:
        round_num = round_data.get("round", 0)
        ped_review = round_data.get("pedagogical_review", {})
        logic_review = round_data.get("logical_review", {})
        
        content.append(f"## 第 {round_num} 轮评审修改意见\n\n")
        
        # 教学性审稿人意见
        content.append("### 📖 教学性审稿人意见\n\n")
        ped_packages = ped_review.get("package_reviews", [])
        if ped_packages:
            for pkg_review in ped_packages:
                pkg_title = pkg_review.get("package_title", f"Package {pkg_review.get('package_index', '?')}")
                content.append(f"#### {pkg_title}\n\n")
                
                # 教学性问题
                issues = pkg_review.get("issues", [])
                if issues:
                    content.append("**需要修改的问题：**\n\n")
                    for idx, issue in enumerate(issues, 1):
                        if not isinstance(issue, dict):
                            continue
                        severity_emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(issue.get("severity", "minor"), "⚪")
                        category = issue.get('category', 'unknown')
                        location = issue.get('location', 'unknown')
                        problem = issue.get('problem', '')
                        suggestion = issue.get('suggestion', '暂无建议')
                        
                        content.append(f"{idx}. {severity_emoji} **[{category}]** @ {location}\n")
                        content.append(f"   - **问题**: {problem}\n")
                        content.append(f"   - **建议**: {suggestion}\n")
                        if issue.get("example_fix"):
                            content.append(f"   - **示例**: {issue.get('example_fix')}\n")
                        content.append("\n")
                
                # 缺失概念
                missing_concepts = pkg_review.get("missing_concepts", [])
                if missing_concepts:
                    content.append("**需要补充的概念：**\n\n")
                    for idx, concept in enumerate(missing_concepts, 1):
                        if isinstance(concept, dict):
                            concept_name = concept.get('concept', '')
                            why_needed = concept.get('why_needed', '')
                            where_to_add = concept.get('where_to_add', '')
                            suggested_explanation = concept.get('suggested_explanation', '')
                            
                            content.append(f"{idx}. **{concept_name}**\n")
                            if why_needed:
                                content.append(f"   - **原因**: {why_needed}\n")
                            if where_to_add:
                                content.append(f"   - **添加位置**: {where_to_add}\n")
                            if suggested_explanation:
                                content.append(f"   - **建议解释**: {suggested_explanation}\n")
                        elif isinstance(concept, str):
                            content.append(f"{idx}. **{concept}**\n")
                        content.append("\n")
        else:
            content.append("无教学性问题。\n\n")
        
        # 逻辑性审稿人意见
        content.append("### 🔗 逻辑性审稿人意见\n\n")
        logic_packages = logic_review.get("package_reviews", [])
        if logic_packages:
            for pkg_review in logic_packages:
                pkg_title = pkg_review.get("package_title", f"Package {pkg_review.get('package_index', '?')}")
                content.append(f"#### {pkg_title}\n\n")
                
                # 逻辑性问题
                issues = pkg_review.get("issues", [])
                if issues:
                    content.append("**需要修改的问题：**\n\n")
                    for idx, issue in enumerate(issues, 1):
                        if not isinstance(issue, dict):
                            continue
                        severity_emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(issue.get("severity", "minor"), "⚪")
                        category = issue.get('category', 'unknown')
                        location = issue.get('location', 'unknown')
                        problem = issue.get('problem', '')
                        suggestion = issue.get('suggestion', '暂无建议')
                        
                        content.append(f"{idx}. {severity_emoji} **[{category}]** @ {location}\n")
                        content.append(f"   - **问题**: {problem}\n")
                        content.append(f"   - **建议**: {suggestion}\n")
                        content.append("\n")
        else:
            content.append("无逻辑性问题。\n\n")
        
        # 跨package问题
        cross_review = logic_review.get("cross_package_review", {})
        cross_issues = cross_review.get("issues", [])
        if cross_issues:
            content.append("#### 跨Package逻辑问题\n\n")
            for idx, issue in enumerate(cross_issues, 1):
                if not isinstance(issue, dict):
                    continue
                affected = issue.get("affected_packages", [])
                issue_type = issue.get('issue_type', '')
                problem = issue.get('problem', '')
                suggestion = issue.get('suggestion', '暂无建议')
                
                content.append(f"{idx}. **涉及Package**: {', '.join(map(str, affected))}\n")
                if issue_type:
                    content.append(f"   - **类型**: {issue_type}\n")
                if problem:
                    content.append(f"   - **问题**: {problem}\n")
                content.append(f"   - **建议**: {suggestion}\n")
                content.append("\n")
            
            # 建议重排序
            suggested_reordering = cross_review.get("suggested_reordering", [])
            if suggested_reordering:
                content.append("**建议Package顺序**: " + " → ".join(map(str, suggested_reordering)) + "\n\n")
        
        content.append("---\n\n")
    
    # 添加总结
    content.append("## 📋 修改建议总结\n\n")
    content.append("请根据上述意见逐项修改，重点关注：\n\n")
    content.append("1. **教学性问题**: 补充缺失概念、改进代码注释、增加示例\n")
    content.append("2. **逻辑性问题**: 调整步骤顺序、明确依赖关系、保持一致性\n")
    content.append("3. **跨Package问题**: 优化整体结构、改进包之间的连接\n\n")
    content.append("修改完成后，可以重新运行评审流程验证改进效果。\n")
    
    return "".join(content)

def summarize_plan(plan: Dict[str, Any], logger: logging.Logger) -> None:
    logger.info("=" * 80)
    logger.info("Task Decomposition Summary")
    logger.info("Problem Overview: %s", plan.get("problem_overview", "(none)"))
    
    main_objectives = plan.get("main_objectives", [])
    if main_objectives:
        logger.info("\nMain Objectives:")
        for obj in main_objectives:
            logger.info("  - %s", obj)
    
    key_steps = plan.get("key_steps", [])
    if key_steps:
        logger.info("\nKey Research Steps:")
        for step in key_steps:
            step_name = step.get("step_name", "Unknown")
            step_desc = step.get("description", "")
            logger.info("  - [%s] %s", step_name, step_desc)
    
    scientific_keywords = plan.get("scientific_keywords", [])
    if scientific_keywords:
        logger.info("\nScientific Keywords: %s", ", ".join(scientific_keywords))
    
    logger.info("=" * 80)


def parse_survey_selection(command: str) -> Optional[List[str]]:
    command = command.strip()
    if not command:
        return None
    if command.lower() in {"survey all", "survey_all"}:
        return []  # sentinel for "all"
    if command.lower().startswith("survey "):
        ids = command.split(" ", 1)[1]
        return [item.strip() for item in ids.split(",") if item.strip()]
    return None


def build_output_directory(base_dir: Optional[str], name_hint: str) -> str:
    if base_dir:
        out_dir = osp.abspath(base_dir)
    else:
        out_dir = osp.join(ROOT_DIR, "results", name_hint, "planning")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(osp.join(out_dir, "iterations"), exist_ok=True)
    return out_dir

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task planning (image or text) + literature survey pipeline")
    parser.add_argument("--image", action="append", dest="images", default=[], help="Path to requirement image (repeatable)")
    parser.add_argument("--text-input", type=str, dest="text_input", help="Text description of the research problem (alternative to --image)")
    parser.add_argument("--task", type=str, help="Task name or path (reads prompt.json for defaults)")
    parser.add_argument("--description", type=str, help="Override textual description")
    parser.add_argument("--domain", type=str, help="Override domain")
    parser.add_argument("--background", type=str, help="Additional background text")
    parser.add_argument("--config", type=str, default=None, help="Config file path")
    parser.add_argument("--output_dir", type=str, default=None, help="Custom output directory")
    parser.add_argument("--max_rounds", type=int, default=2, help="Max planning iterations")
    parser.add_argument("--max_papers", type=int, default=None, help="Max papers per survey")
    parser.add_argument("--survey_depth", type=str, choices=["shallow", "moderate", "deep"], help="Override survey depth")
    parser.add_argument("--auto_survey", action="store_true", help="Automatically survey all subtasks marked requires_survey")
    parser.add_argument("--non_interactive", action="store_true", help="Disable interactive feedback")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--enable_judger", action="store_true", help="Enable plan evaluation with JudgerAgent")
    parser.add_argument("--min_acceptable_score", type=float, default=8.0, help="Minimum acceptable score (0-10) for plan approval (default: 8.0)")
    parser.add_argument("--enable_review", action="store_true", help="Enable dual-reviewer (pedagogical + logical coherence) review process")
    parser.add_argument( "--max_revision_rounds",type=int,default=2,help="最大评审-修改轮次（默认2）")
    parser.add_argument("--target_audience", type=str,default="intermediate developers",help="目标受众，用于教学性评审（默认: intermediate developers）")
    parser.add_argument( "--min_clarity_score", type=float,default=7.0,help="教学质量最低分要求（1-10，默认7.0）" )
    parser.add_argument( "--min_coherence_score",type=float,default=7.0,help="逻辑连贯性最低分要求（1-10，默认7.0）" )
    return parser.parse_args()

async def run_planning(args: argparse.Namespace, logger: logging.Logger) -> None:
    prompt_data, task_dir, task_name = load_task_definition(args.task)

    # 支持图像或文本输入
    if not args.images and not args.text_input:
        raise ValueError("Please provide either: (1) at least one requirement image via --image, or (2) text description via --text-input")

    goal_description = args.description or (prompt_data or {}).get("task_description") or ""
    domain = args.domain or (prompt_data or {}).get("domain") or ""
    background = args.background or (prompt_data or {}).get("background") or ""
    constraints = (prompt_data or {}).get("constraints", [])

    if not task_name:
        task_name = slugify(domain or goal_description[:50])

    output_dir = build_output_directory(args.output_dir, task_name)
    logger.info("Planning outputs stored in %s", output_dir)

    config, loaded_config_path = load_config(args.config)
    config["config_path"] = loaded_config_path
    config["work_dir"] = output_dir
    config["task_name"] = task_name

    agent_settings = config.get("agents", {})
    model_factory = ModelFactory()

    # Instantiate agents
    planning_cfg = agent_settings.get("task_decomposition", {}).copy()
    planning_cfg["_global_config"] = config
    task_agent = AgentFactory.create_agent("task_decomposition", planning_cfg, model_factory)
    
    # 创建judger_agent实例
    judger_cfg = agent_settings.get("judger",{}).copy()
    judger_cfg["_global_config"] = config
    judger_agent = AgentFactory.create_agent("judger", judger_cfg, model_factory)

    survey_cfg = agent_settings.get("survey", {}).copy()
    if args.max_papers:
        survey_cfg["max_papers"] = args.max_papers
    if args.survey_depth:
        survey_cfg["search_depth"] = args.survey_depth
    survey_cfg["_global_config"] = config
    survey_agent = AgentFactory.create_agent("survey", survey_cfg, model_factory)
    summary_cfg = agent_settings.get("literature_summary", {}).copy()
    summary_cfg["_global_config"] = config
    summary_agent = AgentFactory.create_agent("literature_summary", summary_cfg, model_factory)

    engineer_cfg = agent_settings.get("engineer", {}).copy()
    engineer_cfg["_global_config"] = config
    engineer_agent = AgentFactory.create_agent("engineer", engineer_cfg, model_factory)
    
    # 创建审稿人（仅在启用评审时创建）
    pedagogical_reviewer = None
    logical_reviewer = None
    review_coordinator = None
    
    if args.enable_review:
        # 配置教学性审稿人
        ped_cfg = agent_settings.get("pedagogical_reviewer", {}).copy()
        ped_cfg["_global_config"] = config
        ped_cfg["target_audience"] = args.target_audience
        ped_cfg["min_clarity_score"] = args.min_clarity_score
        pedagogical_reviewer = AgentFactory.create_agent("pedagogical_reviewer", ped_cfg, model_factory)
        
        # 配置逻辑性审稿人
        logic_cfg = agent_settings.get("logical_coherence_reviewer", {}).copy()
        logic_cfg["_global_config"] = config
        logic_cfg["min_coherence_score"] = args.min_coherence_score
        logical_reviewer = AgentFactory.create_agent("logical_coherence_reviewer", logic_cfg, model_factory)
        
        # 创建评审协调器（直接使用已创建的审稿人实例）
        from internagent.mas.agents.Review_Coordinator import ReviewCoordinator
        review_coordinator_cfg = {
            "max_revision_rounds": args.max_revision_rounds
        }
        review_coordinator = ReviewCoordinator(
            pedagogical_reviewer=pedagogical_reviewer,
            logical_reviewer=logical_reviewer,
            config=review_coordinator_cfg
        )
        logger.info("评审协调器已初始化（教学性审稿人 + 逻辑性审稿人）")
    
    guidance_history: List[str] = []  ## 反馈建议
    feedback_history: List[str] = [] 
    previous_plan_text: Optional[str] = None
    planning_iterations: List[Dict[str, Any]] = []
    survey_iterations: List[Dict[str, Any]] = []
    evaluation_history: List[Dict[str, Any]] = [] ## 评估记录
    interactive = not args.non_interactive

    for iteration in range(1, args.max_rounds + 1):
        context = {
            "images": args.images if args.images else [],  # 图像输入（可选）
            "text_input": args.text_input,  # 文本输入（可选）
            "description": goal_description,
            "domain": domain,
            "manual_guidance": guidance_history,
            "feedback": feedback_history,
            "previous_plan": previous_plan_text,
            "background": background,
            "constraints": constraints,
        }

        logger.info("Running task decomposition iteration %d", iteration)
        plan = await task_agent.execute(context, {})
        
        planning_iterations.append(plan)
        previous_plan_text = json.dumps(plan, ensure_ascii=False, indent=2)
        plan_path = osp.join(output_dir, "iterations", f"iteration_{iteration:02d}_plan.json")
        # 确保目录存在
        os.makedirs(osp.dirname(plan_path), exist_ok=True)
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        summarize_plan(plan, logger)
        
        # 评估当前计划
        if args.enable_judger:
            evaluation = await judger_agent.execute({"plan": plan, "domain": domain}, {})
            eval_path = osp.join(output_dir, "iterations", f"iteration_{iteration:02d}_evaluation.json")
            
            # 确保目录存在
            os.makedirs(osp.dirname(eval_path), exist_ok=True)
            
            with open(eval_path, "w", encoding="utf-8") as f:
                json.dump(evaluation, f, ensure_ascii=False, indent=2)
            score = evaluation.get("overall_score", 0)
            logger.info(f"Score: {score:.1f}/10 - {evaluation.get('recommendation')}")
            
            if score < args.min_acceptable_score and iteration < args.max_rounds:
                logger.info("Adding feedback for next iteration...")
                for sugg in evaluation.get("suggestions", [])[:3]:  
                    feedback_history.append(f"[Judger] {sugg}")
                continue
            logger.info("Score acceptable or max rounds reached")
        should_run_survey = args.auto_survey or (not args.non_interactive)
        
        if should_run_survey:
            # Build guidance from task decomposition
            guidance = []
            if plan.get("main_objectives"):
                objectives_text = "\n".join(f"- {obj}" for obj in plan["main_objectives"])
                guidance.append(f"Main Objectives:\n{objectives_text}")
            if plan.get("key_steps"):
                steps_text = "\n".join(
                    f"- {step.get('step_name', '')}: {step.get('description', '')}"
                    for step in plan["key_steps"][:5]
                )
                guidance.append(f"Key Research Steps:\n{steps_text}")
            
            # Build survey context with task decomposition information
            survey_context = {
                "description": plan.get("problem_overview") or goal_description,
                "domain": domain,
                "task_decomposition": {
                    "problem_overview": plan.get("problem_overview", ""),
                    "domain": domain,
                    "scientific_keywords": plan.get("scientific_keywords", []),
                    "main_objectives": plan.get("main_objectives", []),
                    "key_steps": plan.get("key_steps", [])
                },
                "manual_guidance": guidance_history + guidance,
                "max_papers": args.max_papers,
                "force_iteration": bool(guidance_history or guidance),
            }
            
            logger.info("启动文献调研：基于任务分解结果")
            survey_result = await survey_agent.execute(survey_context, {})
            papers = survey_result.get("papers", [])
            queries = survey_result.get("search_queries", [])
            
            logger.info("收集到 %d 篇论文，执行了 %d 个查询", len(papers), len(queries))
            
            # Generate literature summary report
            summary_context = {
                "description": plan.get("problem_overview") or goal_description,
                "domain": domain,
                "papers": papers,
                "search_queries": queries,
                "manual_guidance": guidance_history + guidance,
                "max_papers": args.max_papers,
                "round_results": survey_result.get("round_results", []),
                "all_selected_papers": survey_result.get("all_selected_papers", []),
                "final_selected_papers": survey_result.get("final_selected_papers", []),
                "selection_method": survey_result.get("selection_method"),
                "selection_metadata": {
                    "papers_per_round": survey_result.get("papers_per_round"),
                    "top_per_round": survey_result.get("top_per_round"),
                    "total_rounds": survey_result.get("total_rounds"),
                },
                "task_decomposition": plan,
            }
            summary_report = await summary_agent.execute(summary_context, {})
            # 调整为使用 task_decomposition.key_steps 作为 EngineerAgent 的输入来源
            if plan.get("key_steps"):
                engineer_context = {
                    "goal_description": summary_report.get("problem_formulation") or plan.get("problem_overview") or goal_description,
                    "literature_summary": summary_report,  # 传递完整的summary_report
                    "papers": papers,  # 传递papers列表以便提取references
                    "references": summary_report.get("references") if summary_report else None,  # 直接传递references
                    "task_decomposition": plan,  # 传递task decomposition结果，包含问题描述、主要目标、关键步骤、科学关键词等
                }
                logger.info("Step 1: Engineer Agent 生成初始实现方案（基于 key_steps）...")
                engineering_plan = await engineer_agent.execute(engineer_context, {})
            else:
                logger.warning("Skipping EngineerAgent: task_decomposition 未提供 key_steps。")
                engineering_plan = None
            
            # 执行双审稿人评审流程（如果启用且engineering_plan存在）
            review_result = None
            if args.enable_review and engineering_plan and review_coordinator:
                logger.info("=" * 80)
                logger.info("启动双审稿人评审流程")
                logger.info("=" * 80)
                
                try:
                    review_result = await review_coordinator.conduct_review_and_revision(
                        engineering_plan=engineering_plan,
                        engineer_agent=engineer_agent
                    )
                    
                    # 更新engineering_plan为评审后的版本
                    if review_result.get("status") == "approved":
                        engineering_plan = review_result.get("final_plan", engineering_plan)
                        logger.info("✅ 工程计划已通过双审稿人评审")
                        logger.info(f"   最终教学质量评分: {review_result.get('final_scores', {}).get('pedagogy', 0):.1f}/10")
                        logger.info(f"   最终逻辑连贯性评分: {review_result.get('final_scores', {}).get('logic', 0):.1f}/10")
                    elif review_result.get("status") == "max_rounds_reached":
                        engineering_plan = review_result.get("final_plan", engineering_plan)
                        logger.warning("⚠️ 已达到最大评审轮次，使用当前版本")
                        logger.info(f"   当前教学质量评分: {review_result.get('final_scores', {}).get('pedagogy', 0):.1f}/10")
                        logger.info(f"   当前逻辑连贯性评分: {review_result.get('final_scores', {}).get('logic', 0):.1f}/10")
                    
                    # 保存评审报告
                    if review_result.get("review_history"):
                        review_report = review_coordinator.generate_review_report(review_result["review_history"])
                        review_report_path = osp.join(
                            output_dir,
                            "iterations",
                            f"iteration_{iteration:02d}_review_report.md"
                        )
                        # 确保目录存在
                        os.makedirs(osp.dirname(review_report_path), exist_ok=True)
                        with open(review_report_path, "w", encoding="utf-8") as f:
                            f.write(review_report)
                        logger.info("评审报告已保存到: %s", review_report_path)
                        
                        # 生成并保存修改意见文档
                        revision_suggestions = _generate_revision_suggestions(review_result["review_history"])
                        suggestions_path = osp.join(
                            output_dir,
                            "iterations",
                            f"iteration_{iteration:02d}_revision_suggestions.md"
                        )
                        # 确保目录存在
                        os.makedirs(osp.dirname(suggestions_path), exist_ok=True)
                        with open(suggestions_path, "w", encoding="utf-8") as f:
                            f.write(revision_suggestions)
                        logger.info("修改意见已保存到: %s", suggestions_path)
                    
                    # 保存评审结果JSON
                    review_result_path = osp.join(
                        output_dir,
                        "iterations",
                        f"iteration_{iteration:02d}_review_result.json"
                    )
                    # 确保目录存在
                    os.makedirs(osp.dirname(review_result_path), exist_ok=True)
                    with open(review_result_path, "w", encoding="utf-8") as f:
                        json.dump(review_result, f, ensure_ascii=False, indent=2)
                    logger.info("评审结果已保存到: %s", review_result_path)
                    
                except Exception as exc:
                    logger.error(f"评审流程执行失败: {exc}", exc_info=True)
                    logger.warning("继续使用原始工程计划")
        
            survey_payload = {
                "iteration": iteration,
                "plan": {
                    "problem_overview": plan.get("problem_overview"),
                    "main_objectives": plan.get("main_objectives"),
                    "scientific_keywords": plan.get("scientific_keywords"),
                },
                "papers": papers,
                "search_queries": queries,
                "report": summary_report,
                "engineering_plan": engineering_plan,
                "review_result": review_result if args.enable_review else None,
            }
            survey_iterations.append(survey_payload)
            
            survey_path = osp.join(
                output_dir,
                "iterations",
                f"iteration_{iteration:02d}_survey.json"
            )
            # 确保目录存在
            os.makedirs(osp.dirname(survey_path), exist_ok=True)
            with open(survey_path, "w", encoding="utf-8") as f:
                json.dump(survey_payload, f, ensure_ascii=False, indent=2)
            
            logger.info("文献调研结果已保存到 %s", survey_path)

        if iteration == args.max_rounds:
            break

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
            "survey_depth": args.survey_depth or survey_agent.search_depth,
        },
        "images": args.images,
        "planning_iterations": planning_iterations,
        "survey_iterations": survey_iterations,
        "generated_at": datetime.now().isoformat(),
    }

    summary_path = osp.join(output_dir, "planning_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, ensure_ascii=False, indent=2)

    logger.info("Planning pipeline completed. Summary saved to %s", summary_path)


def main() -> None:
    args = parse_arguments()
    logger = setup_logging(args.verbose)

    try:
        asyncio.run(run_planning(args, logger))
    except KeyboardInterrupt:
        logger.warning("Planning pipeline interrupted by user")
    except Exception as exc:
        logger.error("Planning pipeline failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
