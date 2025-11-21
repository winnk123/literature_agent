"""
Engineer Agent for InternAgent - 完整实现版本
"""

import logging
import os
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import asyncio
from pathlib import Path

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)

if repair_json is None:
    logger.warning("json_repair not available, using basic JSON repair")


class EngineerAgent(BaseAgent):
    """
    Engineer Agent - 生成结构化的、易读的项目包教程
    """

    def __init__(self, model, config: Dict[str, Any]):
        super().__init__(model, config)
        self.max_actions = config.get("max_actions", 6)
        self.default_language = config.get("default_language", "python")
        self.process_parallel = config.get("process_parallel", False)
        self.output_dir = config.get("output_dir", "./output")

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整的教程式实现指南"""
        goal_description = context.get("goal_description")
        
        if not goal_description:
            raise AgentExecutionError("需要 goal_description")

        # 从多个来源收集references
        all_references_sources = []
        
        # 来源1: context中的references
        if context.get("references"):
            refs = context.get("references")
            if isinstance(refs, list):
                all_references_sources.extend(refs)
                logger.info(f"来源1 (context.references): 获取到 {len(refs)} 篇参考文献")
            else:
                logger.warning(f"来源1 (context.references): 类型错误，期望list，实际得到 {type(refs)}")
        
        # 来源2: summary_report中的references
        if context.get("summary_report", {}).get("references"):
            refs = context.get("summary_report", {}).get("references")
            if isinstance(refs, list):
                all_references_sources.extend(refs)
                logger.info(f"来源2 (summary_report.references): 获取到 {len(refs)} 篇参考文献")
            else:
                logger.warning(f"来源2 (summary_report.references): 类型错误，期望list，实际得到 {type(refs)}")
        
        # 来源3: 从papers中提取
        papers = context.get("papers") or context.get("paper_lst") or []
        if papers:
            extracted_refs = self._extract_references_from_papers(papers)
            if extracted_refs:
                all_references_sources.extend(extracted_refs)
                logger.info(f"来源3 (从papers提取): 提取了 {len(extracted_refs)} 篇参考文献")
        else:
            logger.warning("来源3 (从papers提取): 未找到papers字段")
        
        # 去重合并所有references
        references = self._deduplicate_references(all_references_sources)
        if all_references_sources and len(all_references_sources) > len(references):
            logger.info(f"参考文献去重: 从 {len(all_references_sources)} 篇去重到 {len(references)} 篇")
        
        # 记录文献调研结果
        logger.info(f"📚 文献调研结果:")
        logger.info(f"  - 参考文献数量: {len(references)}")
        if references:
            logger.info(f"  - 主要参考文献:")
            for idx, ref in enumerate(references[:5], 1):
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                logger.info(f"    [{idx}] {authors} ({year}). {title[:60]}...")

        # 获取 task decomposition 信息
        task_decomposition = (
            context.get("task_decomposition")
            or {}
        )
        
        # 获取任务难度用于动态调整生成策略
        task_difficulty = task_decomposition.get("task_difficulty", 3)  # Default to moderate (3)
        if not isinstance(task_difficulty, (int, float)):
            try:
                task_difficulty = int(task_difficulty)
            except (ValueError, TypeError):
                task_difficulty = 3
        task_difficulty = max(1, min(5, task_difficulty))  # Clamp to 1-5
        logger.info(f"Task difficulty detected in EngineerAgent: {task_difficulty}/5")
        
        # 从 task_decomposition 中提取关键步骤（取代 action_items 输入）
        candidate_keys = [
            "key_steps", "key_step"
        ]
        extracted_actions = []
        for key in candidate_keys:
            if isinstance(task_decomposition, dict) and key in task_decomposition:
                value = task_decomposition.get(key)
                if isinstance(value, list):
                    # 列表场景：可能是对象或字符串，优先解析对象
                    for item in value:
                        if isinstance(item, dict):
                            # 针对 key_steps 标准结构：step_id / step_name / description
                            step_id = item.get("step_id") or item.get("id") or ""
                            step_name = item.get("step_name") or item.get("name") or ""
                            desc = item.get("description") or item.get("desc") or ""
                            # 组合成清晰的步骤文本
                            text_parts = []
                            if step_id:
                                text_parts.append(f"[{step_id}]")
                            if step_name:
                                text_parts.append(step_name)
                            if desc:
                                text_parts.append(f": {desc}")
                            combined = " ".join(text_parts).strip()
                            if combined:
                                extracted_actions.append(combined)
                            else:
                                # 回退到字典的字符串化
                                extracted_actions.append(str(item))
                        else:
                            extracted_actions.append(str(item))
                elif isinstance(value, dict):
                    # 可能是编号到对象/文本的映射，尽量提取可读标题
                    for _, item in value.items():
                        if isinstance(item, dict):
                            title = (
                                item.get("title")
                                or item.get("name")
                                or item.get("description")
                                or ""
                            )
                            if title:
                                extracted_actions.append(title)
                        else:
                            extracted_actions.append(str(item))
                elif value:
                    extracted_actions.append(str(value))
        
        # 兼容某些可能的扁平结构（如放在 context 顶层的 task_decomposition_key_steps 等）
        if not extracted_actions:
            fallback_keys = [
                "key_steps", "task_decomposition_steps"
            ]
            for key in fallback_keys:
                v = context.get(key)
                if isinstance(v, list):
                    extracted_actions.extend(v)
                elif v:
                    extracted_actions.append(str(v))
        
        if not extracted_actions:
            raise AgentExecutionError("需要 task_decomposition 中的关键步骤（优先使用 key_steps: [{step_id, step_name, description}]）")
        
        # 规范化为字符串列表并裁剪
        action_items = [str(a) for a in extracted_actions if a]
        trimmed_actions = action_items[: self.max_actions]

        shared_context = {
            "goal_description": goal_description,
            "sections": {},
            "references": references,
            "task_decomposition": task_decomposition,
            "task_difficulty": task_difficulty,  # 用于动态调整生成策略
            "used_files": set(),
            "implemented_files": {},
        }

        logger.info(f"开始处理 {len(trimmed_actions)} 个步骤...")
        
        # 跟踪已生成的概念，避免跨步骤重复
        seen_concepts = set()
        # 跟踪已讲解的理论主题，避免理论基础部分重复
        seen_theory_topics = []
        
        # 逐个处理
        project_packages = []
        package_timings = []
        implemented_files = shared_context.get("implemented_files")
        
        for idx, action in enumerate(trimmed_actions, 1):
            try:
                pkg_start = time.time()
                result = await self._process_single_action(
                    action, idx, shared_context, params, seen_concepts, seen_theory_topics, shared_context.get("used_files"), implemented_files
                )
                pkg_time = time.time() - pkg_start
                package_timings.append((idx, pkg_time))
                logger.info(f"  ⏱️  Package {idx} 总耗时: {pkg_time:.1f}秒 ({pkg_time/60:.1f}分钟)")
                project_packages.append(result)
                used_files = shared_context.get("used_files")
                implemented_files = shared_context.get("implemented_files")
                if isinstance(used_files, set):
                    for step in result.get("implementation_steps", []):
                        fp = step.get("file_path")
                        if fp:
                            used_files.add(fp)
                            if isinstance(implemented_files, dict):
                                if not self._is_non_tutorial_file(fp):
                                    implemented_files[fp] = {
                                        "package_index": idx,
                                        "file_path": fp,
                                        "component_name": step.get("component_name", ""),
                                        "purpose": step.get("purpose", ""),
                                        "code": step.get("code", ""),
                                        "language": step.get("language", "python"),
                                        "action_index": idx,
                                        "step_number": step.get("step_number"),
                                        "package_title": result.get("package_title"),
                                    }
                
                # 更新已生成的概念列表和理论基础主题
                if result.get("status") == "success":
                    # 更新概念列表
                    concepts = result.get("concept_explanations", [])
                    for concept in concepts:
                        concept_name = concept.get("concept_name", "")
                        if concept_name:
                            seen_concepts.add(concept_name.lower().strip())
                    
                    # 更新理论基础主题列表（保存包标题和理论基础摘要）
                    package_title = result.get("package_title", f"Package {idx}")
                    theory_foundation = result.get("theoretical_foundation", "")
                    if theory_foundation:
                        # 提取理论基础的关键主题（前80字作为摘要，减少prompt长度）
                        theory_summary = theory_foundation[:80].strip()
                        seen_theory_topics.append({
                            "package_index": idx,
                            "package_title": package_title,
                            "theory_summary": theory_summary
                        })
            except Exception as exc:
                logger.error(f"处理步骤 {idx} 失败: {exc}")
                pkg_time = time.time() - pkg_start if 'pkg_start' in locals() else 0
                package_timings.append((idx, pkg_time))
                project_packages.append({
                    "action_item": action,
                    "error": str(exc),
                    "status": "failed"
                })

        # 输出所有package的时间统计
        if package_timings:
            total_pkg_time = sum(t for _, t in package_timings)
            logger.info("=" * 80)
            logger.info("⏱️  Engineer Agent Package 时间统计")
            logger.info("=" * 80)
            for pkg_idx, pkg_time in package_timings:
                percentage = (pkg_time / total_pkg_time) * 100 if total_pkg_time > 0 else 0
                logger.info(f"  Package {pkg_idx}: {pkg_time:.1f}秒 ({pkg_time/60:.1f}分钟, {percentage:.1f}%)")
            logger.info(f"总计: {total_pkg_time:.1f}秒 ({total_pkg_time/60:.1f}分钟)")
            logger.info("=" * 80)

        # 获取 task_decomposition 信息
        task_decomposition = shared_context.get("task_decomposition", {})

        # 基于问题概述用大模型凝练教程标题（写入 task_decomposition.concise_title）
        try:
            problem_overview_text = (
                task_decomposition.get("problem_overview")
                or task_decomposition.get("problem_formulation")
                or goal_description
                or ""
            )
            if isinstance(problem_overview_text, str) and problem_overview_text.strip():
                condensed = await self._condense_project_title(problem_overview_text.strip())
                if condensed:
                    task_decomposition = dict(task_decomposition or {})
                    task_decomposition["concise_title"] = condensed
        except Exception as _title_exc:
            logger.warning(f"标题凝练失败，使用默认标题: {_title_exc}")

        # 生成所有输出文件
        output_structure = self._generate_and_save_outputs(
            goal_description,
            project_packages,
            references,
            task_decomposition,
            params
        )

        return {
            "goal_description": goal_description,
            "project_packages": project_packages,
            "output_structure": output_structure,
            "task_decomposition": task_decomposition,
            "references": references,
            "total_actions": len(trimmed_actions),
            "successful_actions": sum(1 for item in project_packages if item.get("status") == "success"),
            "output_directory": self.output_dir
        }

    async def _process_single_action(
        self,
        action_item: str,
        action_index: int,
        shared_context: Dict[str, Any],
        params: Dict[str, Any],
        seen_concepts: set = None,
        seen_theory_topics: List[Dict[str, Any]] = None,
        used_files: Optional[set] = None,
        implemented_files: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        处理单个 action item（支持分块处理）
        
        策略：
        1. 先生成整体框架（标题、概述、结构、理论基础）
        2. 然后分块生成实现步骤（每批最多5个步骤）
        3. 逐步构建完整的package
        """
        logger.info(f"正在处理步骤 {action_index}: {action_item[:50]}...")
        pkg_start_time = time.time()
        params = params or {}
        
        max_steps_per_batch = params.get("max_steps_per_batch", 5)
        single_step_mode = params.get("single_step_generation", True)
        if single_step_mode:
            max_steps_per_batch = 1
        
        # 第零步：预先规划所有拆解步骤及其对应的文件
        logger.info(f"  Step 0: 预先规划 Package {action_index} 的所有拆解步骤...")
        planning_start = time.time()
        global_used_files = used_files if isinstance(used_files, set) else set()
        implemented_files = implemented_files if isinstance(implemented_files, dict) else {}
        used_files_hint = ""
        if global_used_files:
            filtered_used = [
                fp for fp in sorted(list(global_used_files))
                if not self._is_non_tutorial_file(fp)
            ]
            if filtered_used:
                preview = "\n".join(f"- `{fp}`" for fp in filtered_used[:20])
                extra = ""
                if len(filtered_used) > 20:
                    extra = f"\n- ...（还有 {len(filtered_used) - 20} 个文件已使用）"
                used_files_hint = (
                    "\n\n**CRITICAL - 已实现的文件（前序Package）:**\n"
                    "以下文件已经在之前的Package中实现，**不得在本Package中重新规划实现**。"
                    "如果需要相同功能，请规划为复用前序实现，而不是重新编写。\n"
                    f"{preview}{extra}\n"
                )
        
        step_plan = await self._plan_implementation_steps(
            action_item=action_item,
            action_index=action_index,
            goal_description=shared_context["goal_description"],
            sections=shared_context["sections"],
            references=shared_context["references"],
            task_difficulty=shared_context.get("task_difficulty", 3),
            params=params,
            used_files=global_used_files,
            used_files_hint=used_files_hint,
        )
        
        planning_time = time.time() - planning_start
        logger.info(f"    ⏱️  步骤规划耗时: {planning_time:.1f}秒")
        
        if not step_plan or not step_plan.get("steps"):
            raise AgentExecutionError(f"无法为步骤 {action_index} 生成实现步骤规划")
        
        # 验证步骤规划
        validation_result = self._validate_step_plan(step_plan, action_item)
        if not validation_result.get("valid", False):
            issues = validation_result.get("issues", [])
            logger.warning(f"步骤规划验证发现问题: {issues}")
            # 可以选择继续或重新规划
        
        # 打印步骤规划
        raw_planned_steps = step_plan.get("steps", []) if step_plan else []
        planned_steps = self._sort_planned_steps(raw_planned_steps)
        if not planned_steps:
            planned_steps = raw_planned_steps
        planned_steps_count = len(planned_steps)
        logger.info(f"  ✓ 已规划 {planned_steps_count} 个拆解步骤:")
        for idx, step_info in enumerate(planned_steps, 1):
            step_name = step_info.get("step_name", "未知步骤")
            file_path = step_info.get("file_path", "未分配")
            component = step_info.get("component_name", "未知组件")
            logger.info(f"    步骤 {idx}: {step_name} ({component}) -> {file_path}")
        
        reuse_steps_map: Dict[int, Dict[str, Any]] = {}
        if implemented_files:
            for idx_sorted, step_info in enumerate(planned_steps, 1):
                file_path = (step_info.get("file_path") or "").strip()
                if file_path and file_path in implemented_files:
                    reuse_steps_map[idx_sorted] = {
                        "step_info": step_info,
                        "existing_info": implemented_files[file_path],
                    }
                    source_pkg = implemented_files[file_path].get("package_index", "?")
                    logger.info(
                        f"    ↺ 步骤 {step_info.get('step_number', idx_sorted)} 的文件 {file_path} "
                        f"已在 Package {source_pkg} 中实现，将复用该实现。"
                    )
        
        # 第一步：基于步骤规划生成整体框架
        logger.info(f"  Step 1: 基于步骤规划生成 Package {action_index} 的整体框架...")
        framework_start = time.time()
        if seen_concepts is None:
            seen_concepts = set()
        if seen_theory_topics is None:
            seen_theory_topics = []
        if seen_concepts:
            logger.info(f"    已生成的概念（避免重复）: {', '.join(sorted(list(seen_concepts))[:10])}" + (f" 等共{len(seen_concepts)}个" if len(seen_concepts) > 10 else ""))
        if seen_theory_topics:
            logger.info(f"    已讲解的理论基础（避免重复）: {len(seen_theory_topics)} 个包")
        if shared_context.get("references"):
            logger.info(f"    将使用 {len(shared_context['references'])} 篇参考文献")
        
        task_difficulty = shared_context.get("task_difficulty", 3)
        framework_prompt = self._build_framework_prompt(
            action_item=action_item,
            action_index=action_index,
            goal_description=shared_context["goal_description"],
            sections=shared_context["sections"],
            references=shared_context["references"],
            seen_concepts=seen_concepts,
            seen_theory_topics=seen_theory_topics,
            task_difficulty=task_difficulty,
            params=params,
            step_plan=step_plan,  # 传入步骤规划
        )
        
        framework_schema = self._build_framework_schema()
        
        try:
            framework_response = await self._call_model(
                prompt=framework_prompt,
                system_prompt=self._build_tutorial_system_prompt(),
                schema=framework_schema,
                temperature=params.get("temperature", self.config.get("temperature", 0.2)),
            )
            framework_time = time.time() - framework_start
            logger.info(f"    ⏱️  框架生成耗时: {framework_time:.1f}秒")
            
            # 验证响应格式
            if not isinstance(framework_response, dict):
                logger.error(f"框架响应格式错误: 期望 dict，实际得到 {type(framework_response)}")
                logger.error(f"响应内容: {str(framework_response)[:500]}")
                raise AgentExecutionError(f"模型返回了无效的响应格式（期望字典）")
            
            # 第二步：分块生成实现步骤
            # 优先使用步骤规划中的步骤数量
            if step_plan and step_plan.get("steps"):
                estimated_steps = len(step_plan.get("steps", []))
                logger.info(f"  ✓ 使用步骤规划中的步骤数量: {estimated_steps}")
            else:
                estimated_steps = framework_response.get("estimated_steps", 10)
            
            total_batches = (estimated_steps + max_steps_per_batch - 1) // max_steps_per_batch
            if total_batches <= 0:
                total_batches = 1
            
            # 保存框架到输出目录（在知道total_batches后）
            if self.output_dir:
                framework_package = framework_response.copy()
                framework_package["action_item"] = action_item
                framework_package["action_index"] = action_index
                framework_package["status"] = "framework"
                framework_package["implementation_steps"] = []  # 框架阶段还没有步骤
                self._save_package_intermediate(
                    framework_package,
                    action_index,
                    0,  # batch_num = 0 表示框架
                    total_batches,
                    references=shared_context.get("references", [])
                )
            
            logger.info(f"  Step 2: 分 {total_batches} 批生成实现步骤（预计 {estimated_steps} 个步骤）...")
            steps_start_time = time.time()
            
            all_implementation_steps = []
            # 确保 current_package 是字典
            if not isinstance(framework_response, dict):
                logger.error(f"框架响应不是字典类型: {type(framework_response)}")
                raise AgentExecutionError(f"框架响应格式错误: 期望字典，实际是 {type(framework_response)}")
            current_package = framework_response.copy()
            
            # 确保 current_package 包含必要的字段
            if "implementation_steps" not in current_package:
                current_package["implementation_steps"] = []
            
            # 解析框架中的项目结构，提取允许的文件清单，用于后续步骤校验
            # 优先使用步骤规划中的文件列表
            allowed_files = set()
            if planned_steps:
                # 从步骤规划中提取所有文件路径
                planned_files = [step.get("file_path", "") for step in planned_steps]
                planned_files = [fp for fp in planned_files if fp and not self._is_non_tutorial_file(fp)]
                allowed_files = set(planned_files)
                logger.info(f"  ✓ 允许引用的文件（来自步骤规划）: {len(allowed_files)} 个")
            
            # 如果步骤规划中没有文件，则从项目结构中解析
            if not allowed_files:
                try:
                    allowed_files = self._parse_structure_files(current_package.get("project_structure", ""))
                    if allowed_files:
                        logger.info(f"  ✓ 允许引用的文件（来自项目结构）: {len(allowed_files)} 个")
                except Exception as _:
                    logger.warning("无法解析项目结构中的文件清单，将仅依赖提示约束避免生成不存在的文件")
            # 用于快速按文件名匹配
            allowed_by_basename = {}
            for p in allowed_files:
                allowed_by_basename.setdefault(p.split('/')[-1], []).append(p)
            package_used_files = set()
            global_used_files = used_files if isinstance(used_files, set) else set()
            available_allowed_files = [
                fp for fp in sorted(list(allowed_files))
                if not global_used_files or fp not in global_used_files
            ]
            
            # 记录step和file_path的唯一映射关系
            step_file_mapping = {}  # {step_number: file_path} 用于确保唯一映射
            file_to_step_mapping = {}  # {file_path: step_number} 用于反向查找
            
            # 使用步骤规划中的文件分配（如果存在）
            step_file_plan = []
            if planned_steps:
                step_file_plan = [step.get("file_path", "") for step in planned_steps]
                step_file_plan = [fp for fp in step_file_plan if fp]  # 过滤空值
                logger.info(f"  ✓ 使用步骤规划中的文件分配: {len(step_file_plan)} 个文件")
            else:
                # 如果没有步骤规划，使用原来的规划方法
                step_file_plan = self._plan_step_file_mapping(
                    available_allowed_files=available_allowed_files,
                    estimated_steps=estimated_steps,
                    single_step_mode=single_step_mode,
                    action_item=action_item
                )
                if step_file_plan:
                    logger.info(f"  ✓ 已预先规划 {len(step_file_plan)} 个步骤的文件分配")
                    for step_idx, file_path in enumerate(step_file_plan, 1):
                        logger.info(f"    步骤 {step_idx}: {file_path}")
            
            # 确定总批次数
            if single_step_mode:
                if available_allowed_files:
                    total_batches = len(available_allowed_files)
                else:
                    total_batches = max(1, total_batches)
            elif planned_steps:
                # 使用步骤规划的数量
                total_batches = len(planned_steps)
            elif step_file_plan:
                # 如果有文件规划，使用规划的数量
                total_batches = len(step_file_plan)
            
            for batch_num in range(1, total_batches + 1):
                logger.info(f"    生成第 {batch_num}/{total_batches} 批实现步骤{'（单步模式）' if single_step_mode else ''}...")
                batch_start = time.time()
                
                reuse_payload = reuse_steps_map.get(batch_num)
                if reuse_payload:
                    reuse_step = self._build_reuse_step_entry(
                        reuse_payload["step_info"],
                        reuse_payload["existing_info"],
                        action_index
                    )
                    all_implementation_steps.append(reuse_step)
                    file_path = reuse_step.get("file_path", "")
                    step_number = (reuse_step.get("step_number") or "").strip()
                    if file_path:
                        package_used_files.add(file_path)
                        if step_number:
                            step_file_mapping[step_number] = file_path
                        file_to_step_mapping[file_path] = step_number
                        global_used_files.add(file_path)
                    logger.info(
                        f"    ↺ 第 {batch_num} 批复用文件 {file_path} "
                        f"(来源 Package {reuse_payload['existing_info'].get('package_index', '?')})"
                    )
                    continue
                
                max_json_regen_attempts = params.get("json_regen_attempts") or self.config.get("json_regen_attempts", 2)
                regen_attempt = 0
                valid_steps = []
                
                while regen_attempt < max_json_regen_attempts:
                    enforce_json = regen_attempt > 0
                    pending_files = [
                        fp for fp in available_allowed_files
                        if fp not in package_used_files
                    ]
                    
                    # 获取当前批次应该生成的文件（如果已规划）
                    assigned_file = None
                    assigned_step_info = None
                    if planned_steps and batch_num <= len(planned_steps):
                        assigned_step_info = planned_steps[batch_num - 1]
                        assigned_file = assigned_step_info.get("file_path", "")
                        # 检查规划的文件是否已被使用（当前包内）
                        if assigned_file in package_used_files:
                            logger.error(
                                f"第 {batch_num} 批规划文件 '{assigned_file}' 已在当前包的步骤中使用，"
                                f"这违反了规划的一对一映射原则。将跳过该批次并记录错误。"
                            )
                            assigned_file = None
                            assigned_step_info = None
                        else:
                            logger.info(f"第 {batch_num} 批规划步骤: {assigned_step_info.get('step_name', '')} -> {assigned_file}")
                    elif step_file_plan and batch_num <= len(step_file_plan):
                        # 使用文件规划
                        assigned_file = step_file_plan[batch_num - 1]
                        # 检查该文件是否已被使用
                        if assigned_file in package_used_files:
                            # 如果已被使用，从pending_files中选择下一个
                            remaining = [fp for fp in pending_files if fp not in [step_file_plan[i] for i in range(batch_num - 1)]]
                            if remaining:
                                assigned_file = remaining[0]
                                logger.warning(f"第 {batch_num} 批原规划文件已被使用，改用: {assigned_file}")
                            else:
                                assigned_file = None
                        else:
                            logger.info(f"第 {batch_num} 批规划文件: {assigned_file}")
                    
                    steps_prompt = self._build_steps_batch_prompt(
                        action_item=action_item,
                        action_index=action_index,
                        goal_description=shared_context["goal_description"],
                        framework=current_package,
                        batch_num=batch_num,
                        total_batches=total_batches,
                        max_steps=max_steps_per_batch,
                        existing_steps=all_implementation_steps,
                        task_difficulty=task_difficulty,
                        params=params,
                        enforce_strict_json=enforce_json,
                        used_files=used_files,
                        pending_files=pending_files,
                        single_step_mode=single_step_mode,
                        allowed_files=allowed_files,
                        available_allowed_files=available_allowed_files,
                        package_used_files=package_used_files,
                        assigned_file=assigned_file,  # 传入预先分配的文件
                        assigned_step_info=assigned_step_info,  # 传入步骤规划信息
                    )
                    
                    steps_schema = self._build_steps_batch_schema()
                    
                    steps_response = None
                    raw_response_text = None
                    
                    try:
                        llm_call_start = time.time()
                        steps_response = await self._call_model(
                            prompt=steps_prompt,
                            system_prompt=self._build_tutorial_system_prompt(),
                            schema=steps_schema,
                            temperature=params.get("temperature", self.config.get("temperature", 0.2)),
                        )
                        llm_call_time = time.time() - llm_call_start
                        if regen_attempt == 0:  # 只在第一次成功时记录
                            logger.debug(f"      LLM调用耗时: {llm_call_time:.1f}秒")
                    except (ValueError, json.JSONDecodeError) as json_exc:
                        logger.warning(f"第 {batch_num} 批步骤 JSON 解析失败，尝试从异常中提取: {json_exc}")
                        exc_str = str(json_exc)
                        if "Model returned invalid JSON:" in exc_str:
                            try:
                                parts = exc_str.split("Model returned invalid JSON:", 1)
                                if len(parts) > 1:
                                    raw_response_text = parts[1].strip()
                            except:
                                pass
                        elif "Model did not return valid JSON:" in exc_str:
                            try:
                                parts = exc_str.split("Model did not return valid JSON:", 1)
                                if len(parts) > 1:
                                    raw_response_text = parts[1].strip()
                            except:
                                pass
                        
                        if raw_response_text:
                            try:
                                if repair_json:
                                    repaired = repair_json(raw_response_text)
                                    if repaired:
                                        steps_response = json.loads(repaired)
                                        logger.info(f"第 {batch_num} 批通过JSON修复成功提取响应")
                            except Exception as repair_exc:
                                logger.warning(f"第 {batch_num} 批JSON修复也失败: {repair_exc}")
                        
                        if steps_response is None and raw_response_text:
                            try:
                                parsed = json.loads(raw_response_text)
                                steps_response = parsed
                                logger.info(f"第 {batch_num} 批直接解析JSON成功")
                            except:
                                try:
                                    import re
                                    json_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', raw_response_text, re.DOTALL)
                                    if json_match:
                                        json_str = json_match.group(1)
                                        steps_response = json.loads(json_str)
                                        logger.info(f"第 {batch_num} 批从代码块中提取JSON成功")
                                    else:
                                        start_idx = raw_response_text.find('{')
                                        if start_idx == -1:
                                            start_idx = raw_response_text.find('[')
                                        if start_idx >= 0:
                                            brace_count = 0
                                            bracket_count = 0
                                            end_idx = start_idx
                                            for i in range(start_idx, len(raw_response_text)):
                                                if raw_response_text[i] == '{':
                                                    brace_count += 1
                                                elif raw_response_text[i] == '}':
                                                    brace_count -= 1
                                                elif raw_response_text[i] == '[':
                                                    bracket_count += 1
                                                elif raw_response_text[i] == ']':
                                                    bracket_count -= 1
                                                
                                                if brace_count == 0 and bracket_count == 0:
                                                    end_idx = i + 1
                                                    break
                                            
                                            if end_idx > start_idx:
                                                json_str = raw_response_text[start_idx:end_idx]
                                                steps_response = json.loads(json_str)
                                                logger.info(f"第 {batch_num} 批从文本中提取JSON成功")
                                except Exception as extract_exc:
                                    logger.warning(f"第 {batch_num} 批从文本提取JSON失败: {extract_exc}")
                        
                    except Exception as exc:
                        logger.error(f"第 {batch_num} 批步骤生成失败: {exc}")
                        exc_str = str(exc)
                        if "Model returned invalid JSON" in exc_str or "Model did not return valid JSON" in exc_str:
                            try:
                                if "Model returned invalid JSON:" in exc_str:
                                    parts = exc_str.split("Model returned invalid JSON:", 1)
                                elif "Model did not return valid JSON:" in exc_str:
                                    parts = exc_str.split("Model did not return valid JSON:", 1)
                                else:
                                    parts = None
                                
                                if parts and len(parts) > 1:
                                    raw_response_text = parts[1].strip()
                                    if repair_json and raw_response_text:
                                        repaired = repair_json(raw_response_text)
                                        if repaired:
                                            steps_response = json.loads(repaired)
                                            logger.info(f"第 {batch_num} 批从异常中修复JSON成功")
                            except:
                                pass
                    
                    batch_steps = []
                    if steps_response is None:
                        regen_attempt += 1
                        logger.warning(f"第 {batch_num} 批步骤响应为 None（尝试 {regen_attempt}/{max_json_regen_attempts}），将重新生成")
                        continue
                    
                    if isinstance(steps_response, dict):
                        batch_steps = steps_response.get("implementation_steps", [])
                    elif isinstance(steps_response, list) and len(steps_response) > 0:
                        logger.warning(f"第 {batch_num} 批步骤响应是列表格式，尝试提取第一个元素")
                        first_item = steps_response[0]
                        if isinstance(first_item, dict):
                            batch_steps = first_item.get("implementation_steps", [])
                            if not batch_steps and "implementation_steps" in first_item:
                                potential_steps = first_item.get("implementation_steps")
                                if isinstance(potential_steps, list):
                                    batch_steps = potential_steps
                            if not batch_steps:
                                if all(isinstance(item, dict) for item in steps_response):
                                    if any("step_number" in item or "component_name" in item for item in steps_response):
                                        batch_steps = steps_response
                    else:
                        logger.error(f"第 {batch_num} 批步骤响应格式错误: 期望 dict 或 list，实际得到 {type(steps_response)}")
                        logger.error(f"响应内容: {str(steps_response)[:500]}")
                        if isinstance(steps_response, str):
                            try:
                                parsed = json.loads(steps_response)
                                if isinstance(parsed, dict):
                                    batch_steps = parsed.get("implementation_steps", [])
                                elif isinstance(parsed, list) and len(parsed) > 0:
                                    if isinstance(parsed[0], dict):
                                        batch_steps = parsed[0].get("implementation_steps", [])
                            except:
                                pass
                    
                    if not isinstance(batch_steps, list):
                        logger.warning(f"第 {batch_num} 批 implementation_steps 格式错误: 期望 list，实际得到 {type(batch_steps)}")
                        batch_steps = []
                    
                    if not batch_steps:
                        regen_attempt += 1
                        logger.warning(f"第 {batch_num} 批未能提取到有效的步骤，准备重新生成（尝试 {regen_attempt}/{max_json_regen_attempts}）")
                        continue
                    
                    parsed_steps = []
                    batch_file_paths = set()  # 用于检查同一批次内的重复
                    for idx, step in enumerate(batch_steps):
                        if not isinstance(step, dict):
                            logger.warning(f"第 {batch_num} 批步骤 {idx+1} 格式错误，跳过: {type(step)}")
                            continue
                        
                        expected_step_fields = {"step_number", "component_name", "file_path", "purpose", "explanation", "code", "language", "important_notes"}
                        if not any(field in step for field in expected_step_fields):
                            try:
                                if parsed_steps:
                                    fragment_text = json.dumps(step, ensure_ascii=False, indent=2)
                                    prev_code = parsed_steps[-1].get("code") or ""
                                    if isinstance(prev_code, str):
                                        parsed_steps[-1]["code"] = (prev_code + "\n" + fragment_text).strip()
                                    else:
                                        parsed_steps[-1]["code"] = fragment_text
                                    logger.info(f"第 {batch_num} 批将非步骤字段片段合并到前一条步骤代码中")
                                    continue
                            except Exception:
                                logger.warning(f"第 {batch_num} 批遇到无法识别的片段，已跳过")
                                continue
                        
                        required_fields = {
                            "step_number": f"Step {idx+1}",
                            "component_name": "Unknown Component",
                            "file_path": "src/unknown.py",
                            "purpose": "",
                            "explanation": "",
                            "code": "",
                            "language": "python"
                        }
                        
                        for field, default_value in required_fields.items():
                            if field not in step or step[field] is None:
                                step[field] = default_value
                        
                        raw_path = step.get("file_path") or ""
                        normalized_path = str(raw_path).strip().strip('`').replace('\\', '/')
                        if normalized_path.startswith('./'):
                            normalized_path = normalized_path[2:]
                        step["file_path"] = normalized_path or "src/unknown.py"
                        
                        step_number = step.get("step_number", "").strip()
                        
                        # 验证1: 检查文件路径是否在允许的文件列表中
                        if allowed_files:
                            if step["file_path"] not in allowed_files:
                                base = step["file_path"].split('/')[-1]
                                candidates = allowed_by_basename.get(base, [])
                                if len(candidates) == 1:
                                    logger.info(f"第 {batch_num} 批步骤 {idx+1} 文件路径纠正: {step['file_path']} -> {candidates[0]}")
                                    step["file_path"] = candidates[0]
                                else:
                                    available_preview = list(available_allowed_files - package_used_files)[:5]
                                    logger.warning(
                                        f"第 {batch_num} 批步骤 {idx+1} (step_number: {step_number}) 引用了项目结构中不存在的文件 '{step['file_path']}'，"
                                        f"可用文件示例: {available_preview}，将跳过并重新生成"
                                    )
                                    parsed_steps = []
                                    break
                        
                        # 验证2: 检查同一批次内是否有重复的文件路径
                        if step["file_path"] in batch_file_paths:
                            logger.warning(
                                f"第 {batch_num} 批步骤 {idx+1} (step_number: {step_number}) 与同批次其他步骤重复使用文件 '{step['file_path']}'，"
                                "每个文件只能在一个步骤中出现，将重新生成该批次。"
                            )
                            parsed_steps = []
                            break
                        batch_file_paths.add(step["file_path"])
                        
                        # 验证3: 检查该文件是否已经在之前的步骤中使用过
                        # 但如果这是预先分配的文件，允许使用（因为可能是规划好的）
                        if step["file_path"] in file_to_step_mapping:
                            # 检查是否是预先分配的文件
                            is_assigned = (assigned_file and step["file_path"] == assigned_file)
                            if not is_assigned:
                                existing_step = file_to_step_mapping[step["file_path"]]
                                logger.warning(
                                    f"第 {batch_num} 批步骤 {idx+1} (step_number: {step_number}) 试图复用已实现文件 '{step['file_path']}'，"
                                    f"该文件已在步骤 {existing_step} 中使用，教程要求每个文件只能对应一个步骤，将重新生成该批次。"
                                )
                                parsed_steps = []
                                break
                            else:
                                # 如果是预先分配的文件，但已经被使用，说明规划有问题
                                logger.warning(
                                    f"第 {batch_num} 批步骤 {idx+1} 的预先分配文件 '{assigned_file}' 已被使用，将重新生成该批次。"
                                )
                                parsed_steps = []
                                break
                        
                        # 验证4: 检查该step_number是否已经映射到其他文件
                        if step_number in step_file_mapping:
                            existing_file = step_file_mapping[step_number]
                            logger.warning(
                                f"第 {batch_num} 批步骤 {idx+1} (step_number: {step_number}) 已映射到文件 '{existing_file}'，"
                                f"现在试图映射到 '{step['file_path']}'，每个步骤只能对应一个文件，将重新生成该批次。"
                            )
                            parsed_steps = []
                            break
                        
                        if "code" in step:
                            if not isinstance(step["code"], str):
                                logger.warning(f"第 {batch_num} 批步骤 {idx+1} 代码字段类型错误，转换为字符串")
                                step["code"] = str(step["code"]) if step["code"] else ""
                            else:
                                try:
                                    json.dumps({"test": step["code"]})
                                except (TypeError, ValueError) as e:
                                    logger.warning(f"第 {batch_num} 批步骤 {idx+1} 代码字段有格式问题，尝试修复: {e}")
                                    step["code"] = self._fix_code_string(step["code"])
                        
                        if "important_notes" not in step:
                            step["important_notes"] = []
                        elif not isinstance(step["important_notes"], list):
                            if step["important_notes"]:
                                step["important_notes"] = [str(step["important_notes"])]
                            else:
                                step["important_notes"] = []
                        
                        # 记录step和file_path的唯一映射关系
                        step_file_mapping[step_number] = step["file_path"]
                        file_to_step_mapping[step["file_path"]] = step_number
                        parsed_steps.append(step)
                    
                    if not parsed_steps:
                        regen_attempt += 1
                        logger.warning(f"第 {batch_num} 批解析步骤为空，将重新生成（尝试 {regen_attempt}/{max_json_regen_attempts}）")
                        continue
                    
                    if single_step_mode and len(parsed_steps) > 1:
                        logger.warning(f"单步模式下第 {batch_num} 批返回 {len(parsed_steps)} 个步骤，自动截取第一个有效步骤")
                        parsed_steps = parsed_steps[:1]
                    
                    valid_steps = parsed_steps
                    batch_time = time.time() - batch_start
                    logger.info(f"第 {batch_num} 批成功提取到 {len(valid_steps)} 个步骤（尝试 {regen_attempt+1}/{max_json_regen_attempts}，耗时 {batch_time:.1f}秒）")
                    # 打印每个步骤对应的文件
                    for step in valid_steps:
                        step_num = step.get("step_number", "未知")
                        file_path = step.get("file_path", "未知")
                        component = step.get("component_name", "未知组件")
                        logger.info(f"    ✓ 步骤 {step_num}: {component} -> 文件: {file_path}")
                    break
                
                if not valid_steps:
                    logger.error(f"第 {batch_num} 批连续 {max_json_regen_attempts} 次生成均失败，跳过该批次")
                    continue
                
                all_implementation_steps.extend(valid_steps)
                for step in valid_steps:
                    fp_val = (step.get("file_path") or "").strip()
                    step_num = (step.get("step_number") or "").strip()
                    component = step.get("component_name", "未知组件")
                    if fp_val:
                        package_used_files.add(fp_val)
                        # 确保映射关系已记录（双重检查）
                        if step_num and step_num not in step_file_mapping:
                            step_file_mapping[step_num] = fp_val
                        if fp_val not in file_to_step_mapping:
                            file_to_step_mapping[fp_val] = step_num
                        # 记录步骤-文件映射关系
                        logger.info(f"  📝 步骤 {step_num} ({component}) 已映射到文件: {fp_val}")
                
                # 验证 current_package 仍然是字典
                if not isinstance(current_package, dict):
                    logger.error(f"current_package 不是字典类型: {type(current_package)}")
                    logger.error(f"current_package 内容: {str(current_package)[:500]}")
                    raise AgentExecutionError(f"current_package 格式错误: 期望字典，实际是 {type(current_package)}")
                
                # 更新当前package
                current_package["implementation_steps"] = all_implementation_steps.copy()
                
                # 每生成一批步骤后，立即保存中间结果到输出目录
                if self.output_dir:
                    try:
                        self._save_package_intermediate(
                            current_package,
                            action_index,
                            batch_num,
                            total_batches,
                            shared_context.get("references", [])
                        )
                    except Exception as save_exc:
                        logger.error(f"保存中间结果失败: {save_exc}", exc_info=True)
                        # 继续处理，不中断流程
            
            # 合并最终结果
            # 最终验证 current_package 格式
            if not isinstance(current_package, dict):
                logger.error(f"最终 current_package 不是字典类型: {type(current_package)}")
                raise AgentExecutionError(f"current_package 格式错误: 期望字典，实际是 {type(current_package)}")
            
            final_package = current_package.copy()
            final_package["action_item"] = action_item
            final_package["action_index"] = action_index
            final_package["status"] = "success"
            final_package["total_steps"] = len(all_implementation_steps)
            final_package["generated_in_batches"] = total_batches > 1
            
            # 确保 implementation_steps 存在且是列表
            if "implementation_steps" not in final_package:
                final_package["implementation_steps"] = all_implementation_steps.copy()
            elif not isinstance(final_package["implementation_steps"], list):
                final_package["implementation_steps"] = all_implementation_steps.copy()
            
            if used_files is not None:
                filtered_steps = []
                seen_local = set()
                seen_step_numbers = set()
                for step in final_package.get("implementation_steps", []):
                    fp_val = (step.get("file_path") or "").strip()
                    step_num = (step.get("step_number") or "").strip()
                    
                    # 检查文件路径重复
                    if fp_val and fp_val in seen_local:
                        logger.warning(
                            f"教程去重: Package {action_index} 中重复文件 '{fp_val}' (step_number: {step_num}) 的后续步骤已被移除，避免重复讲解"
                        )
                        continue
                    
                    # 检查step_number重复
                    if step_num and step_num in seen_step_numbers:
                        logger.warning(
                            f"教程去重: Package {action_index} 中重复step_number '{step_num}' (file_path: {fp_val}) 的后续步骤已被移除"
                        )
                        continue
                    
                    if fp_val:
                        seen_local.add(fp_val)
                    if step_num:
                        seen_step_numbers.add(step_num)
                    filtered_steps.append(step)
                
                final_package["implementation_steps"] = filtered_steps
                used_files.update(seen_local)
                
                # 记录最终的映射关系到package中，便于调试和验证
                final_package["step_file_mapping"] = {
                    step.get("step_number", ""): step.get("file_path", "")
                    for step in filtered_steps
                    if step.get("step_number") and step.get("file_path")
                }
                logger.info(f"Package {action_index} 最终映射关系: {len(final_package.get('step_file_mapping', {}))} 个步骤-文件对")
            else:
                final_package["implementation_steps"] = all_implementation_steps.copy()
            
            coverage_report = self._audit_step_file_coverage(allowed_files, final_package["implementation_steps"])
            if coverage_report:
                final_package["file_coverage"] = coverage_report
                missing = coverage_report.get("missing_files") or []
                redundant = coverage_report.get("redundant_files") or []
                if missing:
                    logger.warning(f"Package {action_index} 教程未覆盖 {len(missing)} 个结构文件: {missing[:5]}" + (f" 等" if len(missing) > 5 else ""))
                if redundant:
                    logger.warning(f"Package {action_index} 教程包含未在结构中声明的文件: {redundant[:5]}" + (f" 等" if len(redundant) > 5 else ""))
            
            steps_total_time = time.time() - steps_start_time
            pkg_total_time = time.time() - pkg_start_time
            logger.info(f"步骤 {action_index} 处理成功（共 {len(all_implementation_steps)} 个子步骤）")
            logger.info(f"  ⏱️  Package {action_index} 时间分解: 框架 {framework_time:.1f}秒, 步骤生成 {steps_total_time:.1f}秒 ({steps_total_time/60:.1f}分钟), 总计 {pkg_total_time:.1f}秒")
            
            # 打印最终的步骤-文件映射关系
            if step_file_mapping:
                logger.info(f"  📋 Package {action_index} 最终步骤-文件映射关系:")
                # 按步骤编号排序
                def get_step_number(step_item):
                    """提取步骤编号用于排序"""
                    import re as re_module
                    step_key = str(step_item[0])
                    match = re_module.search(r'\d+', step_key)
                    return int(match.group()) if match else 999
                sorted_steps = sorted(step_file_mapping.items(), key=get_step_number)
                for step_num, file_path in sorted_steps:
                    # 查找对应的组件名
                    component_name = "未知组件"
                    for step in all_implementation_steps:
                        if (step.get("step_number") or "").strip() == step_num:
                            component_name = step.get("component_name", "未知组件")
                            break
                    logger.info(f"    步骤 {step_num}: {component_name} -> {file_path}")
            
            return final_package
            
        except Exception as exc:
            logger.error(f"处理步骤 {action_index} 失败: {exc}")
            raise AgentExecutionError(f"无法为步骤 {action_index} 生成实现方案") from exc

    def _deduplicate_references(self, references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对参考文献列表进行去重
        
        去重策略：
        1. 优先使用DOI（如果存在且唯一）
        2. 其次使用标题的规范化版本（转小写，去除标点）
        3. 如果标题相同，进一步比较作者和年份
        
        Args:
            references: 参考文献列表
            
        Returns:
            去重后的参考文献列表（保持顺序，保留第一个出现的）
        """
        if not references:
            return []
        
        seen = set()
        unique_refs = []
        
        for ref in references:
            if not isinstance(ref, dict):
                continue
            
            # 生成唯一标识符
            identifiers = []
            
            # 1. DOI（最可靠）
            doi = ref.get("doi") or ref.get("DOI") or ""
            if doi:
                identifiers.append(f"doi:{doi.lower().strip()}")
            
            # 2. 标题（规范化：转小写，去除标点）
            title = ref.get("title") or ref.get("Title") or ""
            if title:
                # 规范化标题
                normalized_title = re.sub(r'[^\w\s]', '', title.lower())
                normalized_title = ' '.join(normalized_title.split())
                if normalized_title:
                    identifiers.append(f"title:{normalized_title}")
            
            # 3. 作者+年份（辅助判断）
            authors = ref.get("authors") or ref.get("Authors") or ref.get("author") or ""
            year = ref.get("year") or ref.get("Year") or ref.get("publication_year") or ""
            
            if authors and year:
                # 规范化作者（取前两个作者，转小写）
                if isinstance(authors, list):
                    author_names = [str(a).lower().strip() for a in authors[:2]]
                else:
                    author_names = [str(authors).lower().strip()]
                author_key = "+".join(sorted(author_names))
                identifiers.append(f"author_year:{author_key}+{year}")
            
            # 检查是否已存在
            is_duplicate = False
            for identifier in identifiers:
                if identifier in seen:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # 添加所有标识符到seen集合
                for identifier in identifiers:
                    seen.add(identifier)
                unique_refs.append(ref)
        
        return unique_refs

    def _extract_references_from_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从papers列表中提取references格式的数据
        
        Args:
            papers: 论文列表，每个paper包含title, authors, year等字段
            
        Returns:
            格式化的references列表
        """
        references = []
        for idx, paper in enumerate(papers, 1):
            # 处理authors字段（可能是list或string）
            authors = paper.get("authors", [])
            if isinstance(authors, str):
                authors = [authors]
            if not authors:
                authors = ["Unknown"]
            
            # 格式化作者字符串
            if len(authors) <= 3:
                author_str = ", ".join(authors)
            else:
                author_str = ", ".join(authors[:3]) + " et al."
            
            ref_entry = {
                "id": idx,
                "title": paper.get("title", "Untitled"),
                "authors": author_str,
                "year": paper.get("year", ""),
                "journal": paper.get("journal") or paper.get("venue", ""),
                "venue": paper.get("venue", ""),
                "doi": paper.get("doi", ""),
                "url": paper.get("url", ""),
                "citation_count": paper.get("citations", 0),
                "score": paper.get("score", 0),
            }
            references.append(ref_entry)
        
        return references

    def _sort_references_by_difficulty(self, references: List[Dict[str, Any]], task_difficulty: int) -> List[Dict[str, Any]]:
        """
        根据任务难度对参考文献进行排序和筛选
        
        Args:
            references: 参考文献列表
            task_difficulty: 任务难度 (1-5)
            
        Returns:
            排序后的参考文献列表
        """
        if not references:
            return []
        
        def parse_year(ref: Dict[str, Any]) -> int:
            """解析年份，返回整数，无法解析时返回0"""
            year = ref.get("year", "")
            if isinstance(year, int):
                return year
            if isinstance(year, str):
                try:
                    # 尝试提取4位数字年份
                    match = re.search(r'\b(20\d{2}|19\d{2})\b', year)
                    if match:
                        return int(match.group(1))
                except:
                    pass
            return 0
        
        # 根据任务难度排序
        if task_difficulty <= 2:
            # 简单任务：优先较早的文献（2015-2020）
            def sort_key(ref):
                year = parse_year(ref)
                if 2015 <= year <= 2020:
                    return (0, -year)  # 最优先，按年份降序（较新的在前）
                elif year < 2015:
                    return (1, -year)  # 2015之前的放在后面
                else:
                    return (2, -year)  # 2021+放在最后
            sorted_refs = sorted(references, key=sort_key)
            
        elif task_difficulty == 3:
            # 中等任务：保持原顺序或按年份混合排序
            sorted_refs = sorted(references, key=lambda ref: -parse_year(ref))  # 按年份降序
            
        else:  # 4-5
            # 复杂任务：强烈优先2024-2025年的文献（最新技术）
            def sort_key(ref):
                year = parse_year(ref)
                if 2024 <= year <= 2025:
                    return (0, -year)  # 最高优先级，按年份降序（2025 > 2024）
                elif year == 2023:
                    return (1, -year)  # 第二优先级
                elif year == 2022:
                    return (2, -year)  # 第三优先级
                elif year >= 2020:
                    return (3, -year)  # 第四优先级
                else:
                    return (4, -year)  # 2020之前的放在最后
            sorted_refs = sorted(references, key=sort_key)
        
        return sorted_refs

    def _build_framework_prompt(
        self,
        action_item: str,
        action_index: int,
        goal_description: str,
        sections: Dict[str, Any],
        references: List[Dict[str, Any]],
        seen_concepts: set = None,
        seen_theory_topics: List[Dict[str, Any]] = None,
        task_difficulty: int = 3,
        params: Dict[str, Any] = None,
        step_plan: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建生成框架的prompt（不包含详细实现步骤）"""
        section_lines: List[str] = []
        key_sections = [
            "current_landscape",
            "approach_taxonomy",
            "critical_gaps",
            "forward_path",
        ]

        for key in key_sections:
            value = sections.get(key)
            if value:
                # 精简文献综述：只保留关键信息（前200字符），减少prompt长度
                section_lines.append(f"### {key.replace('_', ' ').title()}\n{value[:200]}")
        
        # 处理参考文献 - 根据任务难度排序和筛选
        if references:
            # 根据任务难度对参考文献进行排序（复杂任务优先最近年份）
            sorted_refs = self._sort_references_by_difficulty(references, task_difficulty)
            
            ref_lines = []
            # 显示更多参考文献（最多15篇）以便在生成内容时引用
            for idx, ref in enumerate(sorted_refs[:15], 1):
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown authors")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                ref_line = f"[{idx}] {authors} ({year}). *{title}*. {venue}"
                ref_lines.append(ref_line)
            ref_text = "### Key References\n" + "\n".join(ref_lines) + "\n\n**IMPORTANT**: You MUST cite these references in your explanations using ONLY the format [作者, 年份]. For example: [Smith, 2020]。不要使用序号引用如 [1]。"
            section_lines.append(ref_text)
        
        # 处理已生成的概念列表（避免重复）
        seen_concepts_text = ""
        if seen_concepts:
            seen_list = sorted(list(seen_concepts))
            seen_concepts_text = f"\n\n**CRITICAL - Avoid Duplicate Concepts**:\nThe following concepts have already been explained in previous steps. DO NOT generate explanations for these concepts again:\n- " + "\n- ".join(seen_list) + "\n\nInstead, focus on concepts specific to this step that have NOT been explained before."

        # 处理已讲解的理论基础（避免重复）
        seen_theory_text = ""
        if seen_theory_topics:
            theory_list = []
            for topic in seen_theory_topics:
                pkg_idx = topic.get("package_index", "")
                pkg_title = topic.get("package_title", "")
                theory_summary = topic.get("theory_summary", "")
                theory_list.append(f"- **Package {pkg_idx}: {pkg_title}**\n  {theory_summary}...")
            seen_theory_text = f"\n\n**CRITICAL - Avoid Duplicate Theoretical Foundation**:\nThe following theoretical foundations have already been explained in previous packages:\n\n" + "\n\n".join(theory_list) + "\n\n**IMPORTANT**: In your Theoretical Foundation section, you should:\n1. Focus on theories/methods that are **unique to this specific step**\n2. If a theory was already explained in a previous package, **briefly reference it** (e.g., 'As explained in Package X...') instead of repeating the full explanation\n3. Only provide detailed explanations for **new theoretical content** that hasn't been covered before\n4. Build upon previous theoretical foundations rather than re-explaining them from scratch"

        sections_text = "\n\n".join(section_lines) if section_lines else "No additional context provided."
        preferred_language = params.get("default_language", self.default_language) if params else self.default_language
        
        # 如果有步骤规划，添加到prompt中
        step_plan_text = ""
        if step_plan and step_plan.get("steps"):
            steps = step_plan.get("steps", [])
            step_plan_text = "\n\n# Pre-planned Implementation Steps (预先规划的拆解步骤)\n"
            step_plan_text += "The following steps have been pre-planned. You MUST generate a project structure that includes ALL these files:\n\n"
            for step in steps:
                step_num = step.get("step_number", "")
                step_name = step.get("step_name", "")
                component = step.get("component_name", "")
                file_path = step.get("file_path", "")
                purpose = step.get("purpose", "")
                step_plan_text += f"- **步骤 {step_num}**: {step_name} ({component})\n"
                step_plan_text += f"  - 文件: `{file_path}`\n"
                step_plan_text += f"  - 目的: {purpose}\n\n"
            step_plan_text += "**CRITICAL**: Your project_structure MUST include all the files listed above. Do NOT add extra files that are not in this plan.\n"

        # 根据任务难度生成调整指导
        difficulty_guidance = ""
        if task_difficulty <= 2:
            difficulty_guidance = (
                "\n\n**TASK DIFFICULTY: SIMPLE (1-2/5)**\n"
                "This is a simple task suitable for beginners:\n"
                "- Use **foundational, well-established technologies** (2015-2020 era, stable and mature)\n"
                "- Prioritize **classic references** from earlier years (2020-2022) over very recent ones\n"
                "- Explain concepts from **absolute basics** - assume zero prior knowledge\n"
                "- Use **simple, clear language** - avoid advanced terminology unless absolutely necessary\n"
                "- Provide **extra detailed explanations** - every concept should be explained thoroughly\n"
                "- Focus on **educational value** and **clarity** over cutting-edge techniques\n"
                "- Emphasize **understanding fundamental concepts** rather than using the latest methods\n"
            )
        elif task_difficulty == 3:
            difficulty_guidance = (
                "\n\n**TASK DIFFICULTY: MODERATE (3/5)**\n"
                "This is a moderate task:\n"
                "- Use **balanced, modern technologies** (2020-2025 era, well-established)\n"
                "- Reference **both classic and recent papers** (2020-2025) as appropriate\n"
                "- Explain concepts clearly but can assume some basic knowledge\n"
                "- Use **standard terminology** with brief explanations when needed\n"
                "- Provide **comprehensive explanations** suitable for intermediate learners\n"
            )
        else:  # 4-5
            difficulty_guidance = (
                "\n\n**TASK DIFFICULTY: COMPLEX (4-5/5)**\n"
                "This is a complex, cutting-edge task:\n"
                "- Use **state-of-the-art, recent technologies** (2020-2025 era, latest methods)\n"
                "- **STRONGLY PRIORITIZE 2024-2025 references** - these represent the most cutting-edge techniques and latest innovations\n"
                "- **Prioritize recent references** from 2022-2025 over older ones - focus on cutting-edge techniques\n"
                "- **Encourage citing 2024-2025 papers** - even if they have lower citations, they represent the latest research trends\n"
                "- Can assume **intermediate to advanced** knowledge - readers should have some background\n"
                "- Can use **advanced terminology** with brief explanations - readers are expected to be familiar with basics\n"
                "- Focus on **latest methodologies** and **current best practices** from 2024-2025\n"
                "- Emphasize **state-of-the-art approaches** and **recent innovations** in the field (especially 2024-2025)\n"
                "- Can reference **foundational papers briefly** but focus on recent developments, particularly 2024-2025\n"
            )

        prompt = f"""You are Dr. Chen, a **renowned technical educator and senior software engineer** with over 15 years of experience. 
You are now preparing a comprehensive tutorial package for your students. Your teaching style is patient, thorough, and focused on helping learners truly understand concepts, not just memorize them.
{difficulty_guidance}

**Your Teaching Approach:**
- You believe in building knowledge step by step, ensuring each concept is fully understood before moving to the next
- You use real-world analogies and concrete examples to make abstract concepts tangible
- You anticipate questions learners might have and address them proactively
- You connect new concepts to what learners already know, creating a coherent learning journey
- You write as if you're sitting next to a learner, guiding them with enthusiasm and clarity

# Overall Research Goal
{goal_description}

# 步骤 {action_index}
{action_item}

# Supporting Literature Context
{sections_text}
{seen_concepts_text}
{seen_theory_text}
{step_plan_text}

# Your Task - Generate Framework Only

As Dr. Chen, create the FRAMEWORK structure for this tutorial package (do NOT generate detailed implementation steps yet). 
Think of this as preparing the outline and foundation for your lesson. Make sure it's well-structured and sets up learners for success:

## 1. Package Title and Overview
- Clear title (e.g., "Package {action_index}: [Descriptive Name]")
- 3-4 sentences explaining what this accomplishes and how it fits the overall goal
- **MUST be written in Chinese (中文)**

## 2. Project Structure
**CRITICAL**: Design a project structure that is SPECIFIC and APPROPRIATE for implementing "{action_item}". 

Think carefully about what files are actually needed based on the step decomposition and the specific requirements of "{action_item}":
- Analyze the step decomposition: what modules/components are needed? What files will contain them?
- If this step requires a main entry point, include `main.py` or equivalent
- If this step requires data files, include appropriate data files
- If this step requires configuration, include config files
- **Design flexibly based on actual needs**, not based on generic templates or blindly copying from examples

Complete directory structure with ALL needed files for implementing "{action_item}":
```
package-{action_index:02d}-[name]/
├── README.md
├── requirements.txt
├── src/
│   ├── [module files needed for {action_item}]
│   └── [other modules as needed]
├── configs/
│   └── config.yaml (if needed)
└── data/
    └── [data files if needed]
```

**IMPORTANT Requirements:**
- **Design based on the actual requirements** of "{action_item}" - analyze what files are truly needed for this specific step
- **DO NOT blindly copy example structures** from previous packages or generic templates - each step should have its own appropriate structure
- **Include files that serve a clear purpose** for implementing "{action_item}" - if a file is needed, include it; if not, don't include it
- **Be flexible and practical** - the structure should match what will actually be implemented in the tutorial steps
- **Think about the step decomposition** - what modules/components are needed? What files will contain them?

## 3. Theoretical Foundation
As Dr. Chen, provide a **COMPREHENSIVE and DETAILED** explanation of the technical and scientific basis that is **SPECIFIC TO THIS STEP**, why this approach was chosen, trade-offs and design decisions.

**Write this section as if you're giving a lecture to your students:**
- Start with an engaging introduction that captures their attention
- Use analogies and real-world examples to make abstract concepts concrete
- Build understanding step by step, ensuring each paragraph flows naturally to the next
- Connect theory to practice - show how these concepts will be applied in the implementation
- End with a clear summary that reinforces the key takeaways

**CRITICAL REQUIREMENTS:**
- **MUST be written in Chinese (中文)**
- **Length**: Write **6-9 paragraphs** (NOT just 2-3 sentences!) - This is a CRITICAL requirement
- **MUST cite relevant references** from the Key References section above using the format [作者, 年份]（只允许作者-年份格式，禁止使用数字序号） - **Cite 2-4 references** throughout the explanation
- **Focus on core theoretical foundations** - Stay focused on what's needed for implementing "{action_item}"
- **MUST include mathematical formulas and equations** when explaining theoretical foundations - Use LaTeX format for formulas:
  * **Inline formulas** (within text): Use single dollar signs, e.g., `$f(x) = \\sum_{{i=1}}^{{n}} w_i x_i + b$`
  * **Display formulas** (centered on separate line): Use double dollar signs, e.g., `$$\\mathcal{{L}} = \\frac{{1}}{{N}}\\sum_{{i=1}}^{{N}} L(y_i, \\hat{{y}}_i)$$`
  * **CRITICAL**: Every formula MUST start with `$` or `$$` and end with `$` or `$$` respectively. Do NOT forget the closing dollar signs.
  * If the theory involves mathematical concepts, algorithms, or models, you MUST include the relevant formulas, equations, or mathematical expressions.
  * Explain what each symbol means and how the formula is used in practice.
  * **Verification Requirement**: 在输出前**逐条检查**每一个公式，确保：
    - 仅使用合法的 LaTeX 运算符（例如使用 `\\in` 而不是 `\\[` 表示集合关系）
    - `$...$` / `$$...$$` 成对出现，不存在遗漏
    - 没有混入 Markdown 语法或中文标点到公式分隔符内部
    - 公式在 MathJax 中能正确渲染（思考是否存在未闭合的括号、转义符等）
- **Writing style**: Write as Dr. Chen would - with enthusiasm, clarity, and a genuine desire to help learners understand
- **Focus on UNIQUE theories for this step** - See the "Avoid Duplicate Theoretical Foundation" section above:
  * If a theory was already explained in a previous package, **briefly reference it** (e.g., "如 Package X 中所述，[理论名] 已经在之前包中详细讲解...") instead of repeating the full explanation
  * Only provide **detailed explanations** for theoretical content that is **new and unique** to this specific step
  * Build upon previous theoretical foundations rather than re-explaining them from scratch
- **Structure the explanation**:
  1. Start with the **background and motivation specific to this step** - Why is THIS particular problem important? What unique challenges exist here?
  2. Explain the **theoretical foundations that are UNIQUE to this step** - What are the core theories/principles this specific approach is based on? [Cite references] **Include relevant mathematical formulas/equations in LaTeX format** - Use `$公式$` for inline formulas or `$$公式$$` for display formulas. **Always include both opening and closing dollar signs.**
  3. Describe the **approach in detail** - How does THIS specific method work? What are the key components unique to this step? **If the approach has mathematical formulations, include them in proper LaTeX format with `$...$` or `$$...$$`**
  4. Discuss **why this approach was chosen for this step** - What are the advantages specific to solving this problem? What problems does it solve?
  5. Explain **trade-offs and design decisions** - What are the limitations? Why these specific design choices for THIS step?
  6. Relate to **existing literature and previous packages** - How does this build upon previous work and previous packages? [Cite references]
  7. Provide **concrete examples or applications specific to this step** - Make it tangible and understandable, **show how formulas are applied in practice**
- **Be thorough and detailed** - Explain concepts step-by-step, avoid skipping intermediate steps
- **Use clear language** - Even when discussing complex topics, break them down into understandable parts
- **IMPORTANT**: Do NOT repeat theoretical content already covered in previous packages. Focus on what is unique and specific to THIS step. Do NOT write just a brief summary. This section should be comprehensive enough for readers to understand the full theoretical context relevant to THIS specific step.

## 4. Concept Explanations
As Dr. Chen, provide **clear and focused** explanations of key concepts that are **essential prerequisites** for implementing this package.

**Your teaching approach for each concept:**
- Imagine a student sitting in front of you, asking "Can you explain this concept to me from scratch?"
- Start from the very basics, as if the learner has never heard of this concept before
- Use multiple analogies - if one doesn't click, another might
- Show enthusiasm for the concept - your passion for teaching should shine through
- Anticipate questions like "Why is this important?" and "How does this relate to what we learned before?"
- **Stay focused on what's needed for the core implementation** - connect concepts to how they're used in "{action_item}"

**CRITICAL**: These explanations must be so detailed and clear that a complete beginner can understand them without prior knowledge.

- List all the key concepts used in this project that is related to artificial intelligence in the Theoretical Foundation section (e.g., technical terms, algorithms, design patterns, theoretical foundations)
- **IMPORTANT**: Do NOT generate explanations for concepts that have already been explained in previous steps (see the list above)
- Focus on concepts that are **unique to this step** and have NOT been covered before
- For each concept, provide:
  - **Concept Name**: Clear name of the concept
  
  - **Explanation**: **Clear and focused** explanation in Chinese (中文) - **3-6 paragraphs minimum** that:
    * Start from the very basics (assume zero prior knowledge) - Don't assume any prior understanding
    * Explain what the concept is in simple terms first - Use everyday language before introducing technical terms
    * Then explain how it works step-by-step - Break down every step, don't skip intermediate reasoning
    * Provide the mathematical or theoretical foundation if applicable - **MUST include formulas in LaTeX format**:
      - **Inline formulas** (within text): Use `$公式内容$` format, e.g., `$f(x) = \\sum_{{i=1}}^{{n}} w_i x_i$`
      - **Display formulas** (centered): Use `$$公式内容$$` format, e.g., `$$\\mathcal{{L}} = \\frac{{1}}{{N}}\\sum_{{i=1}}^{{N}} L(y_i, \\hat{{y}}_i)$$`
      - **CRITICAL**: Every formula MUST start and end with dollar signs (`$` or `$$`). Never forget the closing dollar signs.
      - Explain clearly what each symbol means and how the formula is used
      - **Verification Requirement**: 输出前逐条核查所有公式：仅使用正确的 LaTeX 命令（如 `\\in` 而不是 `\\[`）、确保 `$`/`$$` 成对、没有未闭合的括号或多余转义，确认在 MathJax 中可正常渲染
    * Explain why it matters and where it's used - Give context and real-world relevance
    * Use analogies and real-world examples to make it concrete - At least 1-2 different analogies/examples per concept
    * Break down complex ideas into smaller, digestible parts - Each paragraph should build on the previous one
    * Avoid jargon or explain every technical term used - If you use a term, immediately explain what it means
    * Make sure a complete beginner can follow the entire explanation - Test your explanation mentally: would a beginner understand?
    * **Cite relevant references** from the Key References section using format [作者, 年份]（仅作者-年份格式，禁止数字序号） when explaining theoretical foundations or related work - **Cite at least 1-2 references per concept**
    * **Be thorough but focused** - Explain what's needed clearly, stay focused on core concepts needed for "{action_item}"
  
  - **Why Important**: Detailed explanation of why this concept is crucial for understanding this package - explain the connection clearly
  
  - **Related Concepts**: Other concepts that should be understood together (list them and explain the relationships)
  
  - **Examples**: **Multiple concrete examples or analogies** to help understanding - use everyday analogies when possible
  
- **MUST be written in Chinese (中文)**
- **Focus on making concepts accessible to beginners** - write as if explaining to someone with no background knowledge
- **Be thorough but focused** - explain what's essential for the implementation, stay focused on core concepts needed for "{action_item}"
- Focus on concepts that are essential prerequisites for understanding the implementation

## 5. Estimated Implementation Steps
Provide an estimate of how many implementation steps will be needed (typically 5-15 steps).

## 6. Dependencies and Installation (preliminary)
List expected dependencies with purpose.

# Critical Requirements
- Use {preferred_language} as primary language for code
- **MANDATORY: All text content (overview, theoretical_foundation, concept_explanations) MUST be written in Chinese (中文)**
- **CRITICAL - Project Structure Requirements:**
  - **Design flexibly based on the step decomposition and actual needs** - analyze what files are truly required for implementing "{action_item}"
  - **DO NOT blindly copy example structures or generic templates** - each step should have its own appropriate structure based on its specific requirements
  - **Include files that serve a clear purpose** - if a file is needed for the implementation (e.g., main entry point, data files, specific modules), include it; if not needed, don't include it
  - **Think about the step decomposition** - what modules/components are needed? What files will contain them?
  - **Be practical and flexible** - the structure should match what will actually be implemented, not follow a rigid template
- Be comprehensive but concise
- Do NOT include detailed code or implementation steps yet
- Focus on structure and planning
"""
        return prompt

    def _build_framework_schema(self) -> Dict[str, Any]:
        """框架生成的schema（不包含详细实现步骤）"""
        return {
            "type": "object",
            "properties": {
                "package_title": {
                    "type": "string",
                    "description": "Clear, descriptive title for this project package"
                },
                "overview": {
                    "type": "string",
                    "description": "3-4 sentence comprehensive overview"
                },
                "project_structure": {
                    "type": "string",
                    "description": "Complete directory tree structure as formatted text with all files. Design flexibly based on the step decomposition and actual requirements of the action_item. Include files that serve a clear purpose for implementing the action_item. DO NOT blindly copy example structures or generic templates - each step should have its own appropriate structure based on its specific needs."
                },
                "theoretical_foundation": {
                    "type": "string",
                    "description": "Detailed explanation of theoretical background and design rationale"
                },
                "concept_explanations": {
                    "type": "array",
                    "description": "Detailed explanations of key concepts used in this package",
                    "items": {
                        "type": "object",
                        "properties": {
                            "concept_name": {
                                "type": "string",
                                "description": "Name of the concept (e.g., 'Transformer', 'Attention Mechanism')"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Detailed explanation of the concept in Chinese (中文)"
                            },
                            "why_important": {
                                "type": "string",
                                "description": "Why this concept is important for understanding this package"
                            },
                            "related_concepts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Related concepts that should be understood together"
                            },
                            "examples": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Concrete examples or analogies to help understand"
                            }
                        },
                        "required": ["concept_name", "explanation", "why_important"]
                    }
                },
                "estimated_steps": {
                    "type": "integer",
                    "description": "Estimated number of implementation steps needed (5-15)",
                    "minimum": 5,
                    "maximum": 20
                },
                "dependencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "version": {"type": "string"},
                            "purpose": {"type": "string"}
                        },
                        "required": ["name", "purpose"]
                    }
                },
                "setup_instructions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "usage_examples": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "scenario": {"type": "string"},
                            "code": {"type": "string"},
                            "expected_output": {"type": "string"}
                        },
                        "required": ["title", "scenario", "code", "expected_output"]
                    }
                }
            },
            "required": [
                "package_title",
                "overview",
                "project_structure",
                "theoretical_foundation",
                "concept_explanations",
                "estimated_steps",
                "dependencies",
                "setup_instructions",
                "usage_examples"
            ]
        }

    def _build_steps_batch_prompt(
        self,
        action_item: str,
        action_index: int,
        goal_description: str,
        framework: Dict[str, Any],
        batch_num: int,
        total_batches: int,
        max_steps: int,
        existing_steps: List[Dict[str, Any]],
        task_difficulty: int = 3,
        params: Dict[str, Any] = None,
        enforce_strict_json: bool = False,
        used_files: Optional[set] = None,
        pending_files: Optional[List[str]] = None,
        single_step_mode: bool = False,
        allowed_files: Optional[set] = None,
        available_allowed_files: Optional[List[str]] = None,
        package_used_files: Optional[set] = None,
        assigned_file: Optional[str] = None,  # 预先分配的文件
        assigned_step_info: Optional[Dict[str, Any]] = None,  # 步骤规划信息
    ) -> str:
        """构建生成步骤批次的prompt"""
        preferred_language = params.get("default_language", self.default_language) if params else self.default_language
        
        existing_steps_summary = ""
        if existing_steps:
            existing_steps_summary = "\n## Already Generated Steps:\n"
            for step in existing_steps[-3:]:  # 只显示最后3个步骤作为上下文
                existing_steps_summary += f"- {step.get('step_number', '')}: {step.get('component_name', '')}\n"
        
        duplication_warning = ""
        if used_files:
            filtered_files = [
                fp for fp in sorted(list(used_files))
                if not self._is_non_tutorial_file(fp)
            ]
            if filtered_files:
                preview_lines = [f"- {fp}" for fp in filtered_files[:12]]
                extra_line = ""
                if len(filtered_files) > 12:
                    extra_line = f"\n- ...（另有 {len(filtered_files) - 12} 个文件已完成）"
                duplication_warning = (
                    "\n\n**Avoid Duplicate Work:**\n"
                    "以下文件/组件已在之前的步骤中完成，实现当前步骤时如非必要请不要重复实现；"
                    "若确需扩展，请明确说明与之前实现的区别，并只描述新增/修改的部分。\n"
                    + "\n".join(preview_lines)
                    + extra_line
                    + "\n"
                )
        
        start_step = len(existing_steps) + 1
        end_step = start_step + max_steps - 1
        if single_step_mode:
            end_step = start_step
        
        # 根据任务难度生成调整指导
        difficulty_guidance = ""
        if task_difficulty <= 2:
            difficulty_guidance = (
                "\n\n**TASK DIFFICULTY: SIMPLE (1-2/5)**\n"
                "This is a simple task for beginners:\n"
                "- Use **foundational technologies** and **classic approaches** (2015-2020 era)\n"
                "- Prioritize **classic references** (2020-2022) over very recent ones\n"
                "- Explain **every single concept** from absolute basics - assume zero prior knowledge\n"
                "- Use **simple, clear language** - avoid advanced terminology\n"
                "- Provide **extra detailed step-by-step explanations** - no step should be skipped\n"
                "- Focus on **educational clarity** over cutting-edge methods\n"
            )
        elif task_difficulty == 3:
            difficulty_guidance = (
                "\n\n**TASK DIFFICULTY: MODERATE (3/5)**\n"
                "This is a moderate task:\n"
                "- Use **balanced, modern technologies** (2020-2022 era)\n"
                "- Reference **both classic and recent papers** (2020-2024) as appropriate\n"
                "- Explain concepts clearly but can assume some basic knowledge\n"
                "- Use **standard terminology** with brief explanations when needed\n"
            )
        else:  # 4-5
            difficulty_guidance = (
                "\n\n**TASK DIFFICULTY: COMPLEX (4-5/5)**\n"
                "This is a complex, cutting-edge task:\n"
                "- Use **state-of-the-art, recent technologies** (2022-2025 era, especially 2024-2025)\n"
                "- **STRONGLY PRIORITIZE 2024-2025 references** - these represent the most cutting-edge techniques\n"
                "- **Prioritize recent references** (2022-2025) - focus on cutting-edge techniques, especially 2024-2025\n"
                "- **Encourage citing 2024-2025 papers** - even if they have lower citations, they represent the latest research\n"
                "- Can assume **intermediate to advanced** knowledge - readers have background\n"
                "- Can use **advanced terminology** with brief explanations\n"
                "- Focus on **latest methodologies** and **current best practices** from 2024-2025\n"
                "- Emphasize recent developments, particularly 2024-2025, over older references\n"
            )
        
        # 如果有预先分配的文件和步骤信息，优先使用
        assigned_file_hint = ""
        if assigned_step_info:
            step_name = assigned_step_info.get("step_name", "")
            component_name = assigned_step_info.get("component_name", "")
            purpose = assigned_step_info.get("purpose", "")
            description = assigned_step_info.get("description", "")
            assigned_file_hint = (
                f"\n\n**⚠️ CRITICAL - Pre-planned Step (预先规划的步骤):**\n"
                f"**步骤 {batch_num} 的规划信息:**\n"
                f"- **步骤名称**: {step_name}\n"
                f"- **组件名称**: {component_name}\n"
                f"- **文件路径**: `{assigned_file}`\n"
                f"- **目的**: {purpose}\n"
                f"- **描述**: {description}\n"
                f"\n**你必须严格按照以上规划生成步骤，文件路径必须是 `{assigned_file}`，组件名称应该是 `{component_name}`。**\n"
            )
        elif assigned_file:
            assigned_file_hint = (
                f"\n\n**⚠️ CRITICAL - Assigned File for This Step (此步骤必须生成的文件):**\n"
                f"**你必须为步骤 {batch_num} 生成文件: `{assigned_file}`**\n"
                f"这是预先规划好的文件分配，请严格按照此文件路径生成步骤。\n"
            )
        
        pending_files_hint = ""
        if pending_files:
            preview = "\n".join(f"- {fp}" for fp in pending_files[:15])
            extra = ""
            if len(pending_files) > 15:
                extra = f"\n- ...（另有 {len(pending_files) - 15} 个文件待覆盖）"
            pending_files_hint = (
                "\n\n**⚠️ CRITICAL - Remaining Files Requiring Implementation (必须从以下文件中选择):**\n"
                "以下文件尚未在教程中讲解，**你必须从这些文件中选择一个**进行实现，确保每个文件只讲解一次：\n"
                f"{preview}{extra}\n"
                "**重要约束**: \n"
                "1. 每个步骤的`file_path`必须从上述列表中选择，不能创造新文件\n"
                "2. 每个步骤只能对应一个唯一的文件，不能重复\n"
                "3. 如果生成的步骤中的`file_path`不在上述列表中，或者与已有步骤重复，整个批次将被拒绝并重新生成\n"
            )
        elif allowed_files and package_used_files and available_allowed_files:
            # 如果没有pending_files但还有可用文件，说明可能已经全部覆盖
            remaining = set(available_allowed_files) - package_used_files
            if remaining:
                preview = "\n".join(f"- {fp}" for fp in list(remaining)[:15])
                pending_files_hint = (
                    "\n\n**⚠️ CRITICAL - Available Files (必须从以下文件中选择):**\n"
                    f"{preview}\n"
                    "**重要约束**: 你必须从上述文件中选择，不能创造新文件。每个步骤只能对应一个唯一的文件。\n"
                )
        
        prompt = f"""You are Dr. Chen, a **renowned technical educator and senior software engineer** with over 15 years of experience.
You are now writing the detailed implementation tutorial for your students. Your teaching style is patient, thorough, and focused on helping learners truly understand every line of code.
{difficulty_guidance}

**Your Teaching Philosophy:**
- You believe that great tutorials don't just show code—they explain the reasoning behind every decision
- You write as if you're pair-programming with a learner, explaining your thought process as you go
- You use encouraging language: "Let's build this together...", "You'll notice that...", "This is important because..."
- You anticipate confusion points and address them before learners get stuck
- You connect each step to the bigger picture, helping learners see how everything fits together
- Keep explanations concise: 聚焦关键信息，避免冗长重复的叙述
- 如果某个文件/类在前序步骤已实现，本步骤仅描述新增逻辑或差异，引用旧实现时可摘要但不要整份重复

# Research Goal
{goal_description}

# 步骤 {action_index}
{action_item}

{duplication_warning}{existing_steps_summary}
{assigned_file_hint}{pending_files_hint}

# Package Framework
**Title**: {framework.get('package_title', '')}
**Overview**: {framework.get('overview', '')}
**Project Structure**:
```
{framework.get('project_structure', '')}
```
**Theoretical Foundation**: {framework.get('theoretical_foundation', '')[:500]}...

# Your Task - Generate Step{'s' if not single_step_mode or max_steps > 1 else ''} {start_step if start_step == end_step else f"{start_step} to {end_step}"} (Batch {batch_num}/{total_batches})

As Dr. Chen, generate the next batch of implementation steps. Write each step as if you're teaching a live coding session, 
explaining not just what to write, but why you're writing it this way. Each step should include:

⚠️ **CRITICAL - File Path Constraints (MANDATORY - 严格约束)**:
1. **你只能使用上方"Project Structure"中列出的文件路径，绝对禁止创造新文件路径**
2. **每个步骤必须对应一个唯一的文件，同一个文件不能出现在多个步骤中（一对一映射关系）**
3. **如果某个文件已经在之前的步骤中讲解过，绝对不能再次生成该文件的教程**
4. **禁止新增任何文件名，只能从Project Structure中选择**
5. **如果Project Structure中没有列出某个文件，即使你认为需要它，也不能生成该文件的教程**
6. **每个步骤的`file_path`字段必须唯一，不能与任何已有步骤的`file_path`重复**

⚠️ **Excluded Files (禁止讲解)**: 以下类型的文件**绝对不得**生成教程步骤：
- `__init__.py` 文件（初始化文件）
- `config*.py`、`settings*.py` 等配置文件
- `requirements.txt`、`requirement.txt` 等依赖文件
- `README*.md` 等文档文件（除非是guide类文档）
- `test*.py`、`*_test.py` 等测试文件
- 任何位于 `config/` 或 `tests/` 目录下的文件

这些文件不需要在教程中单独讲解，请跳过它们，只生成核心实现代码文件的教程步骤。

⚠️ **CRITICAL - One-to-One Mapping Rule (一对一映射规则)**:
- **每个步骤的`file_path`必须是唯一的，不能与之前任何步骤的`file_path`重复**
- **每个文件只能对应一个步骤，每个步骤只能对应一个文件（严格的一对一映射关系）**
- **如果生成的步骤中`file_path`与已有步骤重复，或者不在Project Structure中，整个批次将被拒绝并重新生成**
- **严格按照Project Structure中的文件顺序或逻辑顺序生成，确保每个文件只被讲解一次**

### Step X.Y: [Component Name]
**File:** `path/to/file.{preferred_language}`
**Purpose:** What this component does (MUST be in Chinese/中文)

**Detailed Explanation:**
[**6-10 paragraphs minimum** - MUST be in Chinese/中文, focused on CORE implementation] that:
- **Transition (衔接)**: 开头先用1-2段话回顾上一步（若存在）的产出与当前步骤的关系，明确本步骤如何在此基础上推进；指出依赖与承接的数据/中间结果
- **Start with the purpose** - What problem does this component solve? Why is it needed? What role does it play in the overall system?
- **Explain the approach in detail** - What method or algorithm does it use? How does it work step-by-step? Break down every major step
- **Describe the implementation logic thoroughly** - Walk through the code logic line by line, explain every key decision, why each part is written this way
- **Explain data flow comprehensively** - How does data move through this component? What are the inputs/outputs? What transformations happen? Show the data flow diagrammatically if helpful
- **Discuss design choices in depth** - Why this specific implementation? What alternatives exist? What are the trade-offs?
- **Provide context and connections** - How does this component fit into the overall system? How does it interact with other components?
- **Use clear, beginner-friendly language** - Break down complex logic into understandable parts, avoid jargon or explain every technical term
- **Include concrete examples** - Show how the component handles specific cases, provide before/after examples if applicable
- **Explain edge cases** - What happens in unusual situations? How are errors handled?
- **Be thorough but focused** - A complete beginner should be able to understand the entire explanation without prior knowledge, stay focused on core implementation for "{action_item}"
- **Avoid duplication** - 如果某文件/模块已在前序步骤完成，仅在需要扩展时说明差异；引用旧实现时只总结关键点，重点描述新增/修改内容

**Dependencies & Hand-offs (依赖与交接):**
- 依赖（来自前序步骤的输入/中间结果）：[列出并说明如何使用]
- 产出（提供给后续步骤的输出/接口）：[列出并说明如何被下一步消费]
- 集成点（与其它组件/步骤的接口）：[明确接口与数据契约]

**Complete Code:**
```{preferred_language}
[Full, runnable code with EXTREMELY DETAILED comments - NO PLACEHOLDERS]

**CRITICAL CODE REQUIREMENTS:**
- **Every function/method** must have a detailed docstring explaining: purpose, parameters, return values, usage examples
- **Every complex block** (loop, conditional, algorithm) must have inline comments explaining what it does and why
- **Every non-obvious line** should have a comment explaining its purpose
- **Code structure** should be self-documenting with clear variable/function names
- **Include type hints** if using Python (or equivalent in other languages)
- **Add error handling** with clear error messages
- **Include validation** for inputs where applicable
- **Code should be production-ready** - not just a prototype, but well-structured, maintainable code
- **Comments MUST be in Chinese (中文)** for explanations, but code can use English keywords
```

**Important Notes:**
[**3-5 detailed notes minimum** - MUST be in Chinese/中文]:
- [Key implementation details - explain WHY these details matter, not just WHAT they are]
- [Performance considerations - explain the impact and optimization strategies]
- [Common pitfalls and how to avoid them - provide specific examples]
- [Best practices specific to this component - explain the reasoning]
- [Integration points with other components - how to connect this with other parts]

# Critical Requirements

**CRITICAL - Code Quality and Detail:**
- Generate exactly {1 if single_step_mode or max_steps == 1 else max_steps} step{'s' if (single_step_mode or max_steps == 1) is False and max_steps > 1 else ''} (or fewer if this is the last batch)
- Steps should build logically on previous steps
- **ALL code must be COMPLETE and RUNNABLE** (no "...", "TODO", placeholders, or incomplete implementations)
- **Code must be PRODUCTION-READY** - well-structured, maintainable, with proper error handling
- **Include EXTREMELY DETAILED comments** - every function, every complex block, every non-obvious line should be commented
- **Comments should explain WHY, not just WHAT** - explain the reasoning behind code decisions
- **Code should be self-documenting** - use clear, descriptive variable and function names
- **Include comprehensive docstrings** for all functions/methods (purpose, parameters, return values, examples)
- **Add type hints** where applicable (Python) or equivalent in other languages
- **Include error handling** with meaningful error messages
- **Add input validation** where appropriate

**CRITICAL - Explanation Detail:**
- **Explanation must be 6-10 paragraphs minimum** - be thorough but focused on core implementation
- **Explain every aspect** - purpose, approach, logic, data flow, design choices, context, examples, edge cases
- **Write for beginners** - assume zero prior knowledge, explain every technical term
- **Use clear, simple language** - break down complex concepts into understandable parts
- **Provide concrete examples** - show how the code works with real examples
- **Explain connections** - how this step relates to previous steps and the overall system
- **Add explicit transitions** - 在每个步骤开头加入"Transition (衔接)"段，回顾上一步与本步骤的关系；在结尾点明"Forward Link (前瞻)"本步骤的产出将如何被下一步使用
- **Stay focused on "{action_item}"** - stay focused on core implementation, avoid unnecessary extensions

**CRITICAL - Important Notes:**
- **Must include 2-4 detailed notes minimum**
- **Each note should be comprehensive** - not just a bullet point, but a detailed explanation
- **Explain WHY, not just WHAT** - explain the reasoning and implications
- **Stay focused on core implementation** - focus on what's needed for "{action_item}"

**Language Requirements:**
- Use {preferred_language} as primary language for code
- **MANDATORY: All explanation text (purpose, explanation, important_notes) MUST be written in Chinese (中文)**
- Code comments and docstrings MUST be in Chinese (中文) for explanations
- Code keywords can be in English

**Numbering:**
- Number steps starting from {start_step}
"""
        json_requirements = (
            "\n\n# JSON 输出要求\n"
            "- 你必须返回一个严格符合给定 JSON Schema 的 JSON 对象，且 **不得** 包含任何额外文本或注释。\n"
            "- 根节点必须是 {\"implementation_steps\": [...] }，数组中的每个元素都必须包含 schema 要求的字段。\n"
            "- 不要在 JSON 前后添加说明性文字、Markdown、代码块或多余的逗号/注释。\n"
            "- 若需要换行，请在字符串内部使用 `\\n`，不要破坏 JSON 结构。\n"
            "- 请在输出前自行校验 JSON 是否可以被标准解析器解析。\n"
        )
        if enforce_strict_json:
            json_requirements += (
                "\n⚠️ 上一次尝试因为 JSON 不合法而被拒绝，请务必返回严格符合 schema 的 JSON。"
                " 如果无法生成完整内容，也必须输出符合 schema 的结构（字段留空字符串），"
                " 绝不能输出额外文本。"
            )
        
        prompt += json_requirements
        return prompt

    def _build_steps_batch_schema(self) -> Dict[str, Any]:
        """步骤批次的schema"""
        return {
            "type": "object",
            "properties": {
                "implementation_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {"type": "string"},
                            "component_name": {"type": "string"},
                            "file_path": {"type": "string"},
                            "purpose": {"type": "string"},
                            "explanation": {"type": "string"},
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "important_notes": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["step_number", "component_name", "file_path", "purpose", "explanation", "code", "language"]
                    },
                    "minItems": 1,
                    "maxItems": 10
                }
            },
            "required": ["implementation_steps"]
        }

    def _build_tutorial_prompt(
        self,
        action_item: str,
        action_index: int,
        goal_description: str,
        sections: Dict[str, Any],
        references: List[Dict[str, Any]],
        full_report: str,
        params: Dict[str, Any],
    ) -> str:
        """构建教程式的 prompt"""
        section_lines: List[str] = []
        key_sections = [
            "current_landscape",
            "approach_taxonomy",
            "critical_gaps",
            "forward_path",
        ]

        for key in key_sections:
            value = sections.get(key)
            if value:
                section_lines.append(f"### {key.replace('_', ' ').title()}\n{value[:500]}")

        if references:
            ref_lines = []
            for ref in references[:5]:
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown authors")
                year = ref.get("year", "n.d.")
                ref_line = f"- {title} ({year}) — {authors}"
                ref_lines.append(ref_line)
            section_lines.append("### Key References\n" + "\n".join(ref_lines))

        sections_text = "\n\n".join(section_lines) if section_lines else "No additional context provided."
        preferred_language = params.get("default_language", self.default_language)

        prompt = f"""You are a AI engineering and education researcher who is now creating a comprehensive, tutorial-style project package for the following action item.

# Overall Research Goal
{goal_description}

# 步骤 {action_index}
{action_item}

# Supporting Literature Context
{sections_text}

# Your Task
Create a COMPLETE, TUTORIAL-STYLE project package with these 6 sections:

## 1. Package Title and Overview
- Clear title (e.g., "Package {action_index}: [Descriptive Name]")
- 3-4 sentences explaining what this accomplishes and how it fits the overall goal

## 2. Project Structure
Complete directory structure with ALL needed files:
```
package-{action_index:02d}-[name]/
├── README.md
├── requirements.txt
├── src/
│   ├── main.{preferred_language}
│   └── [other modules]
├── configs/
│   └── config.yaml
├── data/
│   └── [data files]
└── docs/
    └── usage.md
```

## 3. Theoretical Foundation
Explain the technical and scientific basis related to artificial intelligence in the context of this project, why this approach was chosen, trade-offs and design decisions.

## 4. Step-by-Step Implementation
For EACH major component:

### Step 4.X: [Component Name]
**File:** `path/to/file.{preferred_language}`
**Purpose:** What this component does

**Detailed Explanation:**
[2-3 paragraphs explaining logic, algorithms, data flow]

**Complete Code:**
```{preferred_language}
[Full, runnable code with detailed comments - NO PLACEHOLDERS]
```

**Important Notes:**
- [Key implementation details]
- [Performance considerations]

## 5. Dependencies and Installation
List each dependency with version and purpose.
Provide step-by-step setup commands.

## 6. Usage Tutorial
Provide 2-3 COMPLETE usage examples from basic to advanced. Each example MUST include:
- **title**: Clear example title
- **scenario**: Detailed scenario description (in Chinese)
- **code**: Complete, runnable code demonstrating the usage (NO placeholders, NO "...")
- **expected_output**: Detailed description of what the output should look like (in Chinese)

# Critical Requirements
- Use {preferred_language} as primary language
- ALL code must be COMPLETE and RUNNABLE (no "...", "TODO", placeholders)
- Include detailed comments
- Provide realistic examples
- Explain WHY decisions were made
"""
        return prompt

    def _build_project_package_schema(self) -> Dict[str, Any]:
        """定义项目包的 JSON schema"""
        return {
            "type": "object",
            "properties": {
                "package_title": {
                    "type": "string",
                    "description": "Clear, descriptive title for this project package"
                },
                "overview": {
                    "type": "string",
                    "description": "3-4 sentence comprehensive overview"
                },
                "project_structure": {
                    "type": "string",
                    "description": "Complete directory tree structure as formatted text with all files"
                },
                "theoretical_foundation": {
                    "type": "string",
                    "description": "Detailed explanation of theoretical background and design rationale"
                },
                "concept_explanations": {
                    "type": "array",
                    "description": "Detailed explanations of key concepts used in this package",
                    "items": {
                        "type": "object",
                        "properties": {
                            "concept_name": {
                                "type": "string",
                                "description": "Name of the concept (e.g., 'Transformer', 'Attention Mechanism')"
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Detailed explanation of the concept in Chinese (中文)"
                            },
                            "why_important": {
                                "type": "string",
                                "description": "Why this concept is important for understanding this package"
                            },
                            "related_concepts": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Related concepts that should be understood together"
                            },
                            "examples": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Concrete examples or analogies to help understand"
                            }
                        },
                        "required": ["concept_name", "explanation", "why_important"]
                    }
                },
                "implementation_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {"type": "string"},
                            "component_name": {"type": "string"},
                            "file_path": {"type": "string"},
                            "purpose": {"type": "string"},
                            "explanation": {"type": "string"},
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "important_notes": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["step_number", "component_name", "file_path", "purpose", "explanation", "code", "language"]
                    }
                },
                "dependencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "version": {"type": "string"},
                            "purpose": {"type": "string"}
                        },
                        "required": ["name", "purpose"]
                    }
                },
                "setup_instructions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "usage_examples": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "scenario": {"type": "string"},
                            "code": {"type": "string"},
                            "expected_output": {"type": "string"}
                        },
                        "required": ["title", "scenario", "code", "expected_output"]
                    }
                }
            },
            "required": [
                "package_title",
                "overview",
                "project_structure",
                "theoretical_foundation",
                "concept_explanations",
                "implementation_steps",
                "dependencies",
                "setup_instructions",
                "usage_examples"
            ]
        }

    def _fix_code_string(self, code: str) -> str:
        """
        修复代码字符串中的 JSON 转义问题
        
        处理常见问题：
        - 未转义的换行符
        - 控制字符
        - 特殊字符
        """
        if not isinstance(code, str):
            return str(code) if code else ""
        
        # 标准化换行符
        fixed = code.replace('\r\n', '\n').replace('\r', '\n')
        
        # 尝试用 JSON 编码/解码来确保字符串是有效的 JSON 字符串
        try:
            # 先用 JSON 编码，再用 JSON 解码，这样可以确保转义正确
            encoded = json.dumps(fixed)
            decoded = json.loads(encoded)
            return decoded
        except Exception:
            # 如果 JSON 编码失败，尝试基本的清理
            # 移除可能导致问题的控制字符（保留 \n, \t 等）
            cleaned = ''.join(
                char if ord(char) >= 32 or char in '\n\t\r' else ' '
                for char in fixed
            )
            return cleaned

    def _build_tutorial_system_prompt(self) -> str:
        """系统 prompt"""
        return (
            "You are Dr. Chen, a **renowned technical educator and senior software engineer** with over 15 years of experience in AI and software development.\n"
            "You have a passion for teaching and are known for your ability to explain complex concepts in simple, understandable ways.\n"
            "Your teaching philosophy is: 'Every learner deserves a clear path from confusion to understanding.'\n\n"
            "**Your Role & Personality:**\n"
            "- You are patient, thorough, and genuinely care about your students' learning journey\n"
            "- You believe that good code is self-documenting, but great tutorials explain the 'why' behind every decision\n"
            "- You use analogies, real-world examples, and step-by-step breakdowns to make complex topics accessible\n"
            "- You write as if you're sitting next to a learner, guiding them through each concept with enthusiasm and clarity\n"
            "- You anticipate common questions and pitfalls, addressing them proactively in your explanations\n\n"
            "**Your Mission:**\n"
            "Create comprehensive, tutorial-style project packages that are:\n"
            "1. COMPLETE - All code fully functional, no placeholders\n"
            "2. EDUCATIONAL - Explain WHY decisions were made, not just WHAT the code does\n"
            "3. PRACTICAL - Real, working examples that learners can run and experiment with\n"
            "4. WELL-STRUCTURED - Follow best practices and industry standards\n"
            "5. ACCESSIBLE - Clear for beginners, valuable for intermediate developers\n"
            "6. CHINESE EXPLANATIONS - All explanations, descriptions, and documentation text MUST be in Chinese (中文)\n"
            "   - The 'explanation' field in each step MUST be written in Chinese\n"
            "   - The 'purpose' field in each step MUST be written in Chinese\n"
            "   - Code comments can be in English, but explanations should be in Chinese\n\n"
            "**Your Writing Style:**\n"
            "- Write as if you're having a conversation with a curious learner\n"
            "- Use encouraging language: 'Let's explore...', 'You'll notice that...', 'This is important because...'\n"
            "- Break down complex ideas: 'Think of it this way...', 'Imagine that...', 'Here's what's happening...'\n"
            "- Connect concepts: 'Remember when we...', 'This builds on...', 'Later you'll see...'\n"
            "- Be thorough but not overwhelming - guide learners step by step\n\n"
            "Teach by example with production-quality code, and remember: your goal is to empower learners, not just inform them."
        )

    def _save_package_intermediate(
        self,
        package: Dict[str, Any],
        action_index: int,
        batch_num: int,
        total_batches: int,
        references: List[Dict[str, Any]]
    ) -> None:
        """保存package的中间结果（每批步骤生成后立即保存）"""
        try:
            # 验证 package 格式
            if not isinstance(package, dict):
                logger.error(f"Package {action_index} 格式错误: 期望 dict，实际得到 {type(package)}")
                logger.error(f"Package 内容: {str(package)[:500]}")
                raise ValueError(f"package 必须是字典类型，实际是 {type(package)}")
            
            # 确保 implementation_steps 存在且是列表
            if "implementation_steps" not in package:
                package["implementation_steps"] = []
            elif not isinstance(package["implementation_steps"], list):
                logger.warning(f"Package {action_index} 的 implementation_steps 不是列表，转换为列表")
                package["implementation_steps"] = []
            
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            packages_dir = output_dir / "packages"
            packages_dir.mkdir(exist_ok=True)
            
            package_name = self._sanitize_filename(package.get("package_title", f"package-{action_index}"))
            package_dir = packages_dir / f"{action_index:02d}-{package_name}"
            package_dir.mkdir(exist_ok=True)
            
            # 保存当前批次的README（包含已生成的步骤）
            package_readme = self._create_package_readme(package, references)
            package_readme_path = package_dir / "README.md"
            package_readme_path.write_text(package_readme, encoding='utf-8')
            
            # 保存当前批次的Notebook（包含已生成的步骤）
            try:
                package_notebook = self._create_package_notebook(package, references)
                if not package_notebook or not package_notebook.get("cells"):
                    logger.warning(f"  ⚠️  Package {action_index} 的 Notebook 为空，跳过保存")
                else:
                    package_notebook_path = package_dir / f"{package_name}.ipynb"
                    with open(package_notebook_path, 'w', encoding='utf-8') as f:
                        json.dump(package_notebook, f, ensure_ascii=False, indent=2)
                    logger.info(f"  ✓ 已保存 Package {action_index} 的 Notebook: {package_notebook_path}")
            except Exception as notebook_exc:
                logger.warning(f"  ⚠️  保存 Package {action_index} 的 Notebook 失败: {notebook_exc}")
            
            # 保存中间状态的JSON（包含批次信息）
            if batch_num == 0:
                # 框架阶段
                intermediate_json_path = package_dir / "framework.json"
                status_msg = "框架"
            else:
                # 步骤批次
                intermediate_json_path = package_dir / f"intermediate_batch_{batch_num:02d}.json"
                status_msg = f"第 {batch_num}/{total_batches} 批"
            
            intermediate_data = {
                "package": package,
                "batch_info": {
                    "current_batch": batch_num,
                    "total_batches": total_batches,
                    "steps_generated": len(package.get("implementation_steps", [])),
                    "status": "framework" if batch_num == 0 else ("in_progress" if batch_num < total_batches else "completed")
                }
            }
            with open(intermediate_json_path, "w", encoding="utf-8") as f:
                json.dump(intermediate_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"  ✓ 已保存 Package {action_index} {status_msg}中间结果到: {package_readme_path}")
            
        except Exception as exc:
            logger.warning(f"保存 Package {action_index} 中间结果失败: {exc}")

    def _generate_and_save_outputs_incremental(
        self,
        goal_description: str,
        project_packages: List[Dict[str, Any]],
        modified_package_indices: set,
        references: List[Dict[str, Any]],
        task_decomposition: Dict[str, Any],
        params: Dict[str, Any],
        existing_output_structure: Dict[str, str]
    ) -> Dict[str, str]:
        """
        增量更新输出文件：只替换修改过的package，其他保持不变
        
        策略：
        1. 只重新生成被修改的package的独立文件（README、Notebook）
        2. 在full tutorial中定位并替换被修改的package部分
        3. 重新计算引用编号（因为可能有新增引用）
        4. 更新主README中的package概述（如果修改了）
        """
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = existing_output_structure.copy() if existing_output_structure else {}
        
        # 1. 只重新生成被修改的package的独立文件
        packages_dir = output_dir / "packages"
        packages_dir.mkdir(exist_ok=True)
        
        for pkg_idx in modified_package_indices:
            if pkg_idx < 1 or pkg_idx > len(project_packages):
                continue
            package = project_packages[pkg_idx - 1]
            if package.get("status") != "success":
                continue
            
            logger.info(f"重新生成 Package {pkg_idx} 的独立文件...")
            package_name = self._sanitize_filename(package.get("package_title", f"package-{pkg_idx}"))
            package_dir = packages_dir / f"{pkg_idx:02d}-{package_name}"
            package_dir.mkdir(exist_ok=True)
            
            # 生成 README
            package_readme = self._create_package_readme(package, references)
            package_readme_path = package_dir / "README.md"
            package_readme_path.write_text(package_readme, encoding='utf-8')
            output_files[f'package_{pkg_idx}_readme'] = str(package_readme_path)
            logger.info(f"已更新包 {pkg_idx} 的 README: {package_readme_path}")
            
            # 生成 Notebook
            package_notebook = self._create_package_notebook(package, references)
            package_notebook_path = package_dir / f"{package_name}.ipynb"
            with open(package_notebook_path, 'w', encoding='utf-8') as f:
                json.dump(package_notebook, f, ensure_ascii=False, indent=2)
            output_files[f'package_{pkg_idx}_notebook'] = str(package_notebook_path)
            logger.info(f"已更新包 {pkg_idx} 的 Notebook: {package_notebook_path}")
        
        # 2. 增量更新 FULL_TUTORIAL.md：只替换被修改的package部分
        full_tutorial_path = output_dir / "FULL_TUTORIAL.md"
        if full_tutorial_path.exists() and modified_package_indices:
            logger.info(f"增量更新 FULL_TUTORIAL.md（替换 {len(modified_package_indices)} 个package）...")
            try:
                existing_tutorial = full_tutorial_path.read_text(encoding='utf-8')
                updated_tutorial = self._replace_packages_in_tutorial(
                    existing_tutorial,
                    project_packages,
                    modified_package_indices,
                    references,
                    task_decomposition
                )
                full_tutorial_path.write_text(updated_tutorial, encoding='utf-8')
                output_files['full_tutorial'] = str(full_tutorial_path)
                logger.info(f"已增量更新完整教程 (Markdown): {full_tutorial_path}")
            except Exception as exc:
                logger.warning(f"增量更新 FULL_TUTORIAL.md 失败，回退到全量重新生成: {exc}")
                # 回退到全量重新生成
                full_tutorial = self._create_full_tutorial(goal_description, project_packages, references, task_decomposition)
                full_tutorial_path.write_text(full_tutorial, encoding='utf-8')
                output_files['full_tutorial'] = str(full_tutorial_path)
        else:
            # 如果文件不存在或没有修改，全量生成
            logger.info("全量生成 FULL_TUTORIAL.md...")
            full_tutorial = self._create_full_tutorial(goal_description, project_packages, references, task_decomposition)
            full_tutorial_path.write_text(full_tutorial, encoding='utf-8')
            output_files['full_tutorial'] = str(full_tutorial_path)
        
        # 3. 增量更新 FULL_TUTORIAL.ipynb（类似逻辑）
        full_tutorial_notebook_path = output_dir / "FULL_TUTORIAL.ipynb"
        if full_tutorial_notebook_path.exists() and modified_package_indices:
            logger.info(f"增量更新 FULL_TUTORIAL.ipynb（替换 {len(modified_package_indices)} 个package）...")
            try:
                with open(full_tutorial_notebook_path, 'r', encoding='utf-8') as f:
                    existing_notebook = json.load(f)
                updated_notebook = self._replace_packages_in_notebook(
                    existing_notebook,
                    project_packages,
                    modified_package_indices,
                    references,
                    task_decomposition
                )
                with open(full_tutorial_notebook_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_notebook, f, ensure_ascii=False, indent=2)
                output_files['full_tutorial_notebook'] = str(full_tutorial_notebook_path)
                logger.info(f"已增量更新完整教程 (Notebook): {full_tutorial_notebook_path}")
            except Exception as exc:
                logger.warning(f"增量更新 FULL_TUTORIAL.ipynb 失败，回退到全量重新生成: {exc}")
                full_tutorial_notebook = self._create_full_tutorial_notebook(goal_description, project_packages, references, task_decomposition)
                with open(full_tutorial_notebook_path, 'w', encoding='utf-8') as f:
                    json.dump(full_tutorial_notebook, f, ensure_ascii=False, indent=2)
                output_files['full_tutorial_notebook'] = str(full_tutorial_notebook_path)
        else:
            # 如果文件不存在或没有修改，全量生成
            logger.info("全量生成 FULL_TUTORIAL.ipynb...")
            full_tutorial_notebook = self._create_full_tutorial_notebook(goal_description, project_packages, references, task_decomposition)
            with open(full_tutorial_notebook_path, 'w', encoding='utf-8') as f:
                json.dump(full_tutorial_notebook, f, ensure_ascii=False, indent=2)
            output_files['full_tutorial_notebook'] = str(full_tutorial_notebook_path)
        
        # 4. 更新主 README（如果package概述改变了）
        if modified_package_indices:
            logger.info("更新主 README...")
            main_readme = self._create_main_readme(goal_description, project_packages, references)
            main_readme_path = output_dir / "README.md"
            main_readme_path.write_text(main_readme, encoding='utf-8')
            output_files['main_readme'] = str(main_readme_path)
        
        # 5. 更新项目结构和快速开始（如果package数量或结构改变了）
        if modified_package_indices:
            logger.info("更新项目结构和快速开始...")
            structure_overview = self._create_structure_overview(goal_description, project_packages)
            structure_path = output_dir / "PROJECT_STRUCTURE.md"
            structure_path.write_text(structure_overview, encoding='utf-8')
            output_files['project_structure'] = str(structure_path)
            
            quickstart = self._create_quickstart_guide(project_packages)
            quickstart_path = output_dir / "QUICKSTART.md"
            quickstart_path.write_text(quickstart, encoding='utf-8')
            output_files['quickstart'] = str(quickstart_path)
        
        return output_files

    def _generate_and_save_outputs(
        self,
        goal_description: str,
        project_packages: List[Dict[str, Any]],
        references: List[Dict[str, Any]],
        task_decomposition: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, str]:
        """生成并保存所有输出文件"""
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        # 1. 主 README
        main_readme = self._create_main_readme(goal_description, project_packages, references)
        main_readme_path = output_dir / "README.md"
        main_readme_path.write_text(main_readme, encoding='utf-8')
        output_files['main_readme'] = str(main_readme_path)
        logger.info(f"已生成主 README: {main_readme_path}")
        
        # 2. 每个包的 README
        packages_dir = output_dir / "packages"
        packages_dir.mkdir(exist_ok=True)
        
        for idx, package in enumerate(project_packages, 1):
            if package.get("status") != "success":
                continue
                
            package_name = self._sanitize_filename(package.get("package_title", f"package-{idx}"))
            package_dir = packages_dir / f"{idx:02d}-{package_name}"
            package_dir.mkdir(exist_ok=True)
            
            # 生成 README (保留用于文档)
            package_readme = self._create_package_readme(package, references)
            package_readme_path = package_dir / "README.md"
            package_readme_path.write_text(package_readme, encoding='utf-8')
            output_files[f'package_{idx}_readme'] = str(package_readme_path)
            logger.info(f"已生成包 {idx} 的 README: {package_readme_path}")
        
            # 生成 Jupyter Notebook (主要教程格式)
            package_notebook = self._create_package_notebook(package, references)
            package_notebook_path = package_dir / f"{package_name}.ipynb"
            with open(package_notebook_path, 'w', encoding='utf-8') as f:
                json.dump(package_notebook, f, ensure_ascii=False, indent=2)
            output_files[f'package_{idx}_notebook'] = str(package_notebook_path)
            logger.info(f"已生成包 {idx} 的 Notebook: {package_notebook_path}")
        
        # 3. 完整教程 (Markdown 格式)
        full_tutorial = self._create_full_tutorial(goal_description, project_packages, references, task_decomposition)
        tutorial_path = output_dir / "FULL_TUTORIAL.md"
        tutorial_path.write_text(full_tutorial, encoding='utf-8')
        output_files['full_tutorial'] = str(tutorial_path)
        logger.info(f"已生成完整教程 (Markdown): {tutorial_path}")
        
        # 3b. 完整教程 (Notebook 格式)
        full_tutorial_notebook = self._create_full_tutorial_notebook(goal_description, project_packages, references, task_decomposition)
        tutorial_notebook_path = output_dir / "FULL_TUTORIAL.ipynb"
        with open(tutorial_notebook_path, 'w', encoding='utf-8') as f:
            json.dump(full_tutorial_notebook, f, ensure_ascii=False, indent=2)
        output_files['full_tutorial_notebook'] = str(tutorial_notebook_path)
        logger.info(f"已生成完整教程 (Notebook): {tutorial_notebook_path}")
        
        # 4. 项目结构
        structure_overview = self._create_structure_overview(goal_description, project_packages)
        structure_path = output_dir / "PROJECT_STRUCTURE.md"
        structure_path.write_text(structure_overview, encoding='utf-8')
        output_files['project_structure'] = str(structure_path)
        logger.info(f"已生成项目结构: {structure_path}")
        
        # 5. 快速开始
        quickstart = self._create_quickstart_guide(project_packages)
        quickstart_path = output_dir / "QUICKSTART.md"
        quickstart_path.write_text(quickstart, encoding='utf-8')
        output_files['quickstart'] = str(quickstart_path)
        logger.info(f"已生成快速开始: {quickstart_path}")
        
        return output_files

    def _create_main_readme(self, goal_description: str, packages: List[Dict[str, Any]], references: List[Dict[str, Any]] = None) -> str:
        """生成主 README"""
        content = []
        
        content.append("# 研究实现项目\n\n")
        content.append("## 🎯 研究目标\n\n")
        content.append(f"{goal_description}\n\n")
        content.append(f"## 📦 项目包概览\n\n")
        content.append(f"本项目包含 **{len(packages)}** 个独立的实现包，每个包对应一个具体的行动项：\n\n")
        
        for idx, pkg in enumerate(packages, 1):
            if pkg.get("status") == "success":
                title = pkg.get("package_title", f"Package {idx}")
                overview = pkg.get("overview", "")[:150]
                content.append(f"### {idx}. {title}\n\n")
                content.append(f"{overview}...\n\n")
        
        content.append("\n## 🚀 快速开始\n\n")
        content.append("查看 [QUICKSTART.md](./QUICKSTART.md) 获取快速上手指南。\n\n")
        content.append("## 📚 完整文档\n\n")
        content.append("- **[完整教程](./FULL_TUTORIAL.md)** - 包含所有包的详细实现指南\n")
        content.append("- **[项目结构](./PROJECT_STRUCTURE.md)** - 项目组织结构说明\n")
        content.append("- **[各包 README](./packages/)** - 每个包的独立文档\n\n")
        
        content.append("## 📂 文件结构\n\n")
        content.append("```\n")
        content.append(".\n")
        content.append("├── README.md\n")
        content.append("├── QUICKSTART.md\n")
        content.append("├── FULL_TUTORIAL.md\n")
        content.append("├── PROJECT_STRUCTURE.md\n")
        content.append("└── packages/\n")
        content.append("    ├── 01-package-name/\n")
        content.append("    │   └── README.md\n")
        content.append("    └── ...\n")
        content.append("```\n\n")
        
        content.append("## 📄 许可证\n\n[在此添加许可证信息]\n\n")
        content.append("## 🤝 贡献\n\n[在此添加贡献指南]\n")
        
        # 添加参考文献部分
        if references and len(references) > 0:
            content.append("---\n\n## 📚 参考文献\n\n")
            for idx, ref in enumerate(references[:20], 1):
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                content.append(f"{idx}. {authors} ({year}). *{title}*. {venue}\n")
            content.append("\n")
        
        return "".join(content)

    def _create_package_readme(self, package: Dict[str, Any], references: List[Dict[str, Any]] = None) -> str:
        """为单个包生成 README"""
        content = []
        
        content.append(f"# {package.get('package_title', 'Package')}\n\n")
        content.append("## 📋 概述\n\n")
        content.append(f"{package.get('overview', '')}\n\n")
        content.append("## 📂 项目结构\n\n```\n")
        content.append(f"{package.get('project_structure', '')}\n")
        content.append("```\n\n")
        content.append("## 💡 理论基础\n\n")
        content.append(f"{package.get('theoretical_foundation', '')}\n\n")
        
        # 添加概念解释部分
        concepts = package.get('concept_explanations', [])
        if concepts:
            content.append("---\n\n## 📖 核心概念详解\n\n")
            content.append("在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。\n\n")
            
            for concept in concepts:
                if isinstance(concept, dict):
                    concept_name = concept.get('concept_name', 'Unknown')
                    explanation = concept.get('explanation', '')
                    why_important = concept.get('why_important', '')
                    related_concepts = concept.get('related_concepts', [])
                    examples = concept.get('examples', [])
                    
                    content.append(f"### {concept_name}\n\n")
                    content.append(f"{explanation}\n\n")
                    
                    if why_important:
                        content.append(f"**为什么重要**: {why_important}\n\n")
                    
                    if related_concepts:
                        content.append("**相关概念**: ")
                        content.append(", ".join(related_concepts))
                        content.append("\n\n")
                    
                    if examples:
                        content.append("**示例与类比**:\n\n")
                        for example in examples:
                            content.append(f"- {example}\n")
                        content.append("\n")
                    
                    content.append("---\n\n")
        
        content.append("## 🔧 实现步骤\n\n")
        
        for step in package.get('implementation_steps', []):
            content.append(f"### {step.get('step_number', '')} {step.get('component_name', '')}\n\n")
            content.append(f"**文件**: `{step.get('file_path', '')}`\n\n")
            content.append(f"**目的**: {step.get('purpose', '')}\n\n")
            content.append("#### 详细说明\n\n")
            content.append(f"{step.get('explanation', '')}\n\n")
            content.append("#### 完整实现\n\n")
            content.append(f"```{step.get('language', 'python')}\n")
            content.append(f"{step.get('code', '')}\n")
            content.append("```\n\n")
            content.append("#### 重要提示\n\n")
            for note in step.get('important_notes', []):
                content.append(f"- {note}\n")
            content.append("\n")
        
        content.append("---\n\n## 📦 依赖安装\n\n### 所需依赖\n\n")
        for dep in package.get('dependencies', []):
            version = f" ({dep.get('version', '')})" if dep.get('version') else ""
            content.append(f"- **{dep.get('name', '')}{version}**: {dep.get('purpose', '')}\n")
        
        content.append("\n### 安装步骤\n\n```bash\n")
        for instruction in package.get('setup_instructions', []):
            content.append(f"{instruction}\n")
        content.append("```\n\n")
        content.append("---\n\n## 🎮 使用教程\n\n")
        
        for example in package.get('usage_examples', []):
            content.append(f"### {example.get('title', '')}\n\n")
            content.append(f"**场景**: {example.get('scenario', '')}\n\n")
            content.append("```python\n")
            content.append(f"{example.get('code', '')}\n")
            content.append("```\n\n")
            content.append(f"**预期输出**: {example.get('expected_output', '')}\n\n")
        
        content.append("---\n\n## 📝 行动项\n\n")
        content.append(f"> {package.get('action_item', '')}\n")
        
        # 添加参考文献部分
        if references and len(references) > 0:
            content.append("\n---\n\n## 📚 参考文献\n\n")
            content.append("本包实现基于以下研究文献。在阅读理论基础和概念解释部分时，请注意文中引用的文献标记，如 [作者, 年份] 或 [序号]。\n\n")
            for idx, ref in enumerate(references[:20], 1):
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                content.append(f"{idx}. {authors} ({year}). *{title}*. {venue}\n")
            content.append("\n")
        
        return "".join(content)

    def _create_package_notebook(self, package: Dict[str, Any], references: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """为单个包生成 Jupyter Notebook (ipynb 格式)"""
        cells = []
        
        # 1. 标题和概述
        title_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# {package.get('package_title', 'Package')}\n\n",
                "## 📋 概述\n\n",
                f"{package.get('overview', '')}\n"
            ]
        }
        cells.append(title_cell)
        
        # 2. 项目结构
        structure_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 📂 项目结构\n\n",
                "```\n",
                f"{package.get('project_structure', '')}\n",
                "```\n"
            ]
        }
        cells.append(structure_cell)
        
        # 3. 理论基础
        theory_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 💡 理论基础\n\n",
                f"{package.get('theoretical_foundation', '')}\n"
            ]
        }
        cells.append(theory_cell)
        
        # 4. 核心概念详解
        concepts = package.get('concept_explanations', [])
        if concepts:
            concepts_header = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "---\n\n",
                    "## 📖 核心概念详解\n\n",
                    "在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。\n"
                ]
            }
            cells.append(concepts_header)
            
            for concept in concepts:
                if isinstance(concept, dict):
                    concept_name = concept.get('concept_name', 'Unknown')
                    explanation = concept.get('explanation', '')
                    why_important = concept.get('why_important', '')
                    related_concepts = concept.get('related_concepts', [])
                    examples = concept.get('examples', [])
                    
                    concept_source = [f"### {concept_name}\n\n", f"{explanation}\n\n"]
                    
                    if why_important:
                        concept_source.append(f"**为什么重要**: {why_important}\n\n")
                    
                    if related_concepts:
                        concept_source.append("**相关概念**: ")
                        concept_source.append(", ".join(related_concepts))
                        concept_source.append("\n\n")
                    
                    if examples:
                        concept_source.append("**示例与类比**:\n\n")
                        for example in examples:
                            concept_source.append(f"- {example}\n")
                        concept_source.append("\n")
                    
                    concept_cell = {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": concept_source
                    }
                    cells.append(concept_cell)
        
        # 5. 实现步骤
        steps_header = {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## 🔧 实现步骤\n"]
        }
        cells.append(steps_header)
        
        for step in package.get('implementation_steps', []):
            # 步骤说明 (markdown)
            step_info_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"### {step.get('step_number', '')} {step.get('component_name', '')}\n\n",
                    f"**文件**: `{step.get('file_path', '')}`\n\n",
                    f"**目的**: {step.get('purpose', '')}\n\n",
                    "#### 详细说明\n\n",
                    f"{step.get('explanation', '')}\n"
                ]
            }
            cells.append(step_info_cell)
            
            # 代码实现 (code cell)
            code_language = step.get('language', 'python')
            code_source = step.get('code', '')
            code_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": code_source.split('\n') if code_source else [],
                "outputs": []
            }
            cells.append(code_cell)
            
            # 重要提示 (markdown)
            if step.get('important_notes'):
                notes_source = ["#### 重要提示\n\n"]
                for note in step.get('important_notes', []):
                    notes_source.append(f"- {note}\n")
                
                notes_cell = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": notes_source
                }
                cells.append(notes_cell)
        
        # 6. 依赖安装
        deps_header = {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["---\n\n", "## 📦 依赖安装\n\n", "### 所需依赖\n\n"]
        }
        cells.append(deps_header)
        
        for dep in package.get('dependencies', []):
            version = f" ({dep.get('version', '')})" if dep.get('version') else ""
            dep_text = f"- **{dep.get('name', '')}{version}**: {dep.get('purpose', '')}\n"
            dep_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [dep_text]
            }
            cells.append(dep_cell)
        
        # 安装步骤 (code cell - bash)
        install_instructions = package.get('setup_instructions', [])
        if install_instructions:
            install_source = [f"{inst}\n" for inst in install_instructions]
            install_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "tags": ["bash"]
                },
                "source": install_source,
                "outputs": []
            }
            cells.append(install_cell)
        
        # 7. 使用教程
        usage_header = {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["---\n\n", "## 🎮 使用教程\n"]
        }
        cells.append(usage_header)
        
        for example in package.get('usage_examples', []):
            # 场景说明
            example_header_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"### {example.get('title', '')}\n\n",
                    f"**场景**: {example.get('scenario', '')}\n"
                ]
            }
            cells.append(example_header_cell)
            
            # 代码示例
            example_code = example.get('code', '')
            if example_code:
                example_code_cell = {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "source": example_code.split('\n'),
                    "outputs": []
                }
                cells.append(example_code_cell)
            
            # 预期输出
            expected_output = example.get('expected_output', '')
            if expected_output:
                output_cell = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "**预期输出**:\n\n",
                        f"{expected_output}\n"
                    ]
                }
                cells.append(output_cell)
        
        # 8. 行动项
        action_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "---\n\n",
                "## 📝 行动项\n\n",
                f"> {package.get('action_item', '')}\n"
            ]
        }
        cells.append(action_cell)
        
        # 9. 参考文献
        if references and len(references) > 0:
            ref_header_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "\n---\n\n",
                    "## 📚 参考文献\n\n",
                    "本包实现基于以下研究文献。在阅读理论基础和概念解释部分时，请注意文中引用的文献标记，如 [作者, 年份] 或 [序号]。\n\n"
                ]
            }
            cells.append(ref_header_cell)
            
            ref_list_source = []
            for idx, ref in enumerate(references[:20], 1):
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                ref_list_source.append(f"{idx}. {authors} ({year}). *{title}*. {venue}\n")
            
            ref_list_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": ref_list_source
            }
            cells.append(ref_list_cell)
        
        # 构建 notebook 结构
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        return notebook
    
    def _is_non_tutorial_file(self, file_path: str) -> bool:
        """
        判断某个文件是否属于无需在教程中单独讲解的类型（config、__init__、README、测试文件、requirements.txt等）
        """
        if not file_path:
            return True
        path = file_path.lower()
        filename = path.split("/")[-1]
        
        if filename.startswith("__init__"):
            return True
        if "readme" in filename:
            return True
        if "config" in filename or "settings" in filename:
            return True
        if filename == "requirements.txt" or filename == "requirement.txt":
            return True
        if filename.startswith("test") or filename.endswith("_test.py") or filename.endswith("_tests.py"):
            return True
        if "/tests/" in path or path.startswith("tests/"):
            return True
        if "/config/" in path or path.startswith("config/"):
            return True
        if filename.endswith(".md") and "guide" not in filename:
            return True
        return False
    
    async def _plan_implementation_steps(
        self,
        action_item: str,
        action_index: int,
        goal_description: str,
        sections: Dict[str, Any],
        references: List[Dict[str, Any]],
        task_difficulty: int,
        params: Dict[str, Any],
        used_files: Optional[set] = None,
        used_files_hint: str = "",
    ) -> Dict[str, Any]:
        """
        预先规划所有拆解步骤及其对应的文件
        
        Returns:
            包含steps列表的字典，每个step包含：
            - step_number: 步骤编号
            - step_name: 步骤名称
            - component_name: 组件名称
            - file_path: 对应的文件路径
            - purpose: 步骤目的
            - description: 步骤描述
        """
        preferred_language = params.get("default_language", self.default_language) if params else self.default_language
        
        # 构建规划prompt
        planning_prompt = f"""You are Dr. Chen, a technical educator planning a tutorial implementation.

# Overall Research Goal
{goal_description}

# 步骤 {action_index}
{action_item}

# Your Task
Plan ALL implementation steps needed to implement "{action_item}". For each step, you must:
1. Assign a unique step number (1, 2, 3, ...)
2. Provide a clear step name (what component/module will be implemented)
3. Assign a specific file path where this step's code will be written
4. Ensure each file is used by exactly ONE step (one-to-one mapping)
5. Ensure all steps together can fully implement "{action_item}"

**CRITICAL Requirements:**
- Each step must correspond to exactly ONE code file
- Each code file can only be used by ONE step
- Steps must be logically ordered (foundational before advanced)
- All steps together must fully implement "{action_item}"
- File paths should follow standard Python project structure (e.g., src/module.py)
- Do NOT include config files, __init__.py, README, test files, or requirements.txt
{used_files_hint}

Return a JSON object with:
{{
  "steps": [
    {{
      "step_number": "1",
      "step_name": "Component Name",
      "component_name": "ComponentName",
      "file_path": "src/component.py",
      "purpose": "What this step accomplishes",
      "description": "Detailed description of what will be implemented"
    }},
    ...
  ]
}}
"""
        
        planning_schema = {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_number": {"type": "string"},
                            "step_name": {"type": "string"},
                            "component_name": {"type": "string"},
                            "file_path": {"type": "string"},
                            "purpose": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["step_number", "step_name", "component_name", "file_path", "purpose", "description"]
                    }
                }
            },
            "required": ["steps"]
        }
        
        try:
            response = await self._call_model(
                prompt=planning_prompt,
                system_prompt=self._build_tutorial_system_prompt(),
                schema=planning_schema,
                temperature=params.get("temperature", self.config.get("temperature", 0.2)),
            )
            return response if isinstance(response, dict) else {"steps": []}
        except Exception as e:
            logger.error(f"步骤规划失败: {e}")
            return {"steps": []}
    
    def _validate_step_plan(self, step_plan: Dict[str, Any], action_item: str) -> Dict[str, Any]:
        """
        验证步骤规划
        
        Returns:
            {
                "valid": bool,
                "issues": List[str],
                "warnings": List[str]
            }
        """
        issues = []
        warnings = []
        
        if not step_plan or not step_plan.get("steps"):
            issues.append("步骤规划为空")
            return {"valid": False, "issues": issues, "warnings": warnings}
        
        steps = step_plan.get("steps", [])
        
        # 检查1: 每个步骤是否有唯一的step_number
        step_numbers = [s.get("step_number", "") for s in steps]
        if len(step_numbers) != len(set(step_numbers)):
            issues.append("存在重复的step_number")
        
        # 检查2: 每个步骤是否有唯一的file_path（一对一映射）
        file_paths = [s.get("file_path", "") for s in steps]
        file_paths = [fp for fp in file_paths if fp]  # 过滤空值
        if len(file_paths) != len(set(file_paths)):
            duplicates = [fp for fp in file_paths if file_paths.count(fp) > 1]
            issues.append(f"存在重复的file_path: {set(duplicates)}")
        
        # 检查3: 文件路径是否有效（不是非教程文件）
        for step in steps:
            file_path = step.get("file_path", "")
            if file_path and self._is_non_tutorial_file(file_path):
                issues.append(f"步骤 {step.get('step_number')} 的文件路径 '{file_path}' 是非教程文件类型")
        
        # 检查4: 步骤是否能够实现action_item
        step_names = [s.get("step_name", "") for s in steps]
        step_descriptions = [s.get("description", "") for s in steps]
        # 简单检查：步骤名称和描述是否与action_item相关
        action_keywords = set(action_item.lower().split())
        all_step_text = " ".join(step_names + step_descriptions).lower()
        # 这里可以添加更复杂的检查逻辑
        
        # 检查5: 步骤顺序是否合理（step_number是否连续）
        try:
            import re as re_module
            step_nums = []
            for s in steps:
                step_num_str = str(s.get("step_number", ""))
                match = re_module.search(r'\d+', step_num_str)
                if match:
                    step_nums.append(int(match.group()))
            step_nums.sort()
            expected = list(range(1, len(step_nums) + 1))
            if step_nums != expected:
                warnings.append(f"步骤编号不连续: {step_nums} vs {expected}")
        except:
            warnings.append("无法解析步骤编号")
        
        valid = len(issues) == 0
        return {
            "valid": valid,
            "issues": issues,
            "warnings": warnings
        }
    
    def _plan_step_file_mapping(
        self,
        available_allowed_files: List[str],
        estimated_steps: int,
        single_step_mode: bool,
        action_item: str
    ) -> List[str]:
        """
        预先规划每个步骤应该生成哪个文件
        
        Args:
            available_allowed_files: 可用的文件列表
            estimated_steps: 预计的步骤数量
            single_step_mode: 是否为单步模式
            action_item: 当前步骤的任务描述
            
        Returns:
            文件路径列表，索引对应步骤编号（从1开始，所以索引0对应步骤1）
        """
        if not available_allowed_files:
            return []
        
        # 如果单步模式，直接按顺序分配
        if single_step_mode:
            return list(available_allowed_files)
        
        # 多步模式：根据estimated_steps和文件数量来规划
        file_count = len(available_allowed_files)
        
        # 如果文件数量少于或等于estimated_steps，每个文件一个步骤
        if file_count <= estimated_steps:
            return list(available_allowed_files)
        
        # 如果文件数量多于estimated_steps，需要合理分配
        # 策略：优先分配核心文件，尽量让每个步骤都有文件
        # 可以按文件路径排序，或者按重要性排序
        sorted_files = sorted(available_allowed_files)
        
        # 简单策略：均匀分配，每个步骤分配一个文件
        # 如果文件太多，可以后续步骤合并多个文件
        step_file_plan = []
        files_per_step = max(1, file_count // estimated_steps)
        
        for i in range(estimated_steps):
            start_idx = i * files_per_step
            end_idx = min((i + 1) * files_per_step, file_count)
            if start_idx < file_count:
                # 每个步骤分配一个文件（优先策略）
                step_file_plan.append(sorted_files[start_idx])
        
        # 如果还有剩余文件，分配到最后一个步骤
        if len(step_file_plan) < file_count:
            remaining = sorted_files[len(step_file_plan):]
            # 将剩余文件也分配（可以合并到最后一个步骤，或者创建新步骤）
            for file_path in remaining:
                if len(step_file_plan) < estimated_steps:
                    step_file_plan.append(file_path)
                else:
                    # 如果步骤数已满，将剩余文件合并到最后一个步骤
                    # 这里我们选择创建新步骤（如果允许）
                    step_file_plan.append(file_path)
        
        return step_file_plan
    
    def _sort_planned_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not steps:
            return []
        def extract(step: Dict[str, Any]) -> int:
            import re as re_module
            step_num_str = str(step.get("step_number", "0"))
            match = re_module.search(r'\d+', step_num_str)
            return int(match.group()) if match else 999
        try:
            return sorted(steps, key=extract)
        except Exception:
            return steps
    
    def _build_reuse_step_entry(
        self,
        planned_step: Dict[str, Any],
        existing_info: Dict[str, Any],
        package_index: int,
    ) -> Dict[str, Any]:
        file_path = planned_step.get("file_path", "")
        step_number = planned_step.get("step_number", "")
        component_name = planned_step.get("component_name", existing_info.get("component_name", ""))
        purpose = planned_step.get("purpose", existing_info.get("purpose", ""))
        description = planned_step.get("description", "")
        source_pkg = existing_info.get("package_index", "?")
        explanation_parts = []
        if description:
            explanation_parts.append(description)
        explanation_parts.append(
            f"该文件 `{file_path}` 已在 Package {source_pkg} 中完成实现（组件：{existing_info.get('component_name', '未知组件')}）。"
            "本步骤直接复用此前实现的核心代码，并说明如何在当前场景中使用和集成。"
        )
        code = existing_info.get("code")
        if not code:
            code = (
                f"# 复用自 Package {source_pkg} 的 `{file_path}`，此处直接引用已有实现，"
                "可在对应包的实现中查看完整代码。\n"
            )
        language = existing_info.get("language") or self.default_language
        important_notes = planned_step.get("important_notes") or []
        important_notes = [
            f"复用说明：该文件在 Package {source_pkg} 中已实现，此处直接引用，无需重复实现。"
        ] + important_notes
        return {
            "status": "reused",
            "step_number": step_number,
            "component_name": component_name,
            "file_path": file_path,
            "purpose": purpose,
            "description": description or f"复用 Package {source_pkg} 的实现。",
            "explanation": "\n\n".join(explanation_parts),
            "code": code,
            "language": language,
            "important_notes": important_notes,
            "reuse_from": {
                "package_index": source_pkg,
                "file_path": file_path,
                "component_name": existing_info.get("component_name"),
            }
        }
    
    def _parse_structure_files(self, structure_text: str) -> set:
        """
        从项目结构文本中解析出所有文件相对路径集合。
        仅识别在树形结构中以常见文件扩展名结尾的行，忽略目录。
        """
        if not structure_text or not isinstance(structure_text, str):
            return set()
        import re
        files = set()
        # 去掉围栏与缩进，逐行解析
        for raw_line in structure_text.splitlines():
            line = raw_line.strip(" \t`")
            if not line:
                continue
            # 去掉树形符号与边框（├── └── │）
            line = line.replace("├──", "").replace("└──", "").replace("│", "").strip()
            # 简单判断是否是文件（包含扩展名）
            if re.search(r"\.[A-Za-z0-9]+$", line):
                # 还原出相对路径：寻找目录前缀（如 package-xx-.../src/main.py），若行中包含斜杠则直接加入
                path_candidate = line
                # 过滤“[other modules]”这类占位
                if "[" in path_candidate or "]" in path_candidate or "..." in path_candidate:
                    continue
                # 规范化
                path_candidate = path_candidate.replace("\\", "/").lstrip("./")
                if self._is_non_tutorial_file(path_candidate):
                    continue
                files.add(path_candidate)
        return files
    
    def _audit_step_file_coverage(self, allowed_files: set, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        检查实现步骤与项目结构的对应关系，确保没有遗漏或冗余文件。
        """
        if not allowed_files:
            return {}
        
        allowed_sorted = sorted(list(allowed_files))
        step_files: List[str] = []
        for step in steps or []:
            fp = (step.get("file_path") or "").strip()
            if fp:
                step_files.append(fp)
        
        missing_files = [fp for fp in allowed_sorted if fp not in step_files]
        redundant_files = [fp for fp in step_files if fp not in allowed_files]
        duplicates = []
        seen = set()
        for fp in step_files:
            if fp in seen:
                duplicates.append(fp)
            else:
                seen.add(fp)
        
        coverage_ratio = 0.0
        if allowed_sorted:
            coverage_ratio = round((len(allowed_sorted) - len(missing_files)) / len(allowed_sorted), 3)
        
        return {
            "total_structure_files": len(allowed_sorted),
            "documented_files": len(set(step_files)),
            "coverage_ratio": coverage_ratio,
            "missing_files": missing_files,
            "redundant_files": redundant_files,
            "duplicate_entries": duplicates,
        }

    def _create_full_tutorial(
        self,
        goal_description: str,
        packages: List[Dict[str, Any]],
        references: List[Dict[str, Any]],
        task_decomposition: Dict[str, Any] = None
    ) -> str:
        """生成完整的教程文档（带全局首次引用顺序的数字编号）"""
        content = []
        
        # 顶部标题：仅使用模型凝练得到的 concise_title（不做兜底/派生）
        project_title = ""
        if isinstance(task_decomposition, dict):
            project_title = task_decomposition.get("concise_title") or ""
        content.append(f"# {project_title or '教程'}\n\n")
        
        # 添加 Task Decomposition 信息（最前面）
        if task_decomposition:
            content.append("## 📋 任务分解概览\n\n")
            
            # 问题概述
            problem_overview = task_decomposition.get("problem_overview") or task_decomposition.get("problem_formulation") or ""
            if problem_overview:
                content.append("### 问题描述\n\n")
                content.append(f"{problem_overview}\n\n")
            
            # 主要目标
            main_objectives = task_decomposition.get("main_objectives") or []
            if main_objectives:
                content.append("### 主要目标\n\n")
                for obj in main_objectives:
                    content.append(f"- {obj}\n")
                content.append("\n")
            
            # 关键步骤（key_steps）
            key_steps = task_decomposition.get("key_steps") or []
            if key_steps and isinstance(key_steps, list):
                content.append("### 关键步骤\n\n")
                for idx, step in enumerate(key_steps, 1):
                    if isinstance(step, dict):
                        step_id = step.get("step_id")
                        step_name = step.get("step_name", "")
                        desc = step.get("description", "")
                        prefix = f"[{step_id}] " if step_id else ""
                        content.append(f"{idx}. {prefix}{step_name} - {desc}\n")
                    else:
                        content.append(f"{idx}. {str(step)}\n")
                content.append("\n")
            
            content.append("---\n\n")
        
        for idx, package in enumerate(packages, 1):
            if package.get("status") != "success":
                content.append(f"## Package {idx}: 处理失败\n\n")
                content.append(f"错误: {package.get('error', '未知错误')}\n\n")
                content.append("---\n\n")
                continue
            
            content.append("=" * 100 + "\n\n")
            content.append(f"# Package {idx}: {package.get('package_title', '')}\n\n")
            content.append("=" * 100 + "\n\n")
            content.append("## 📋 概述\n\n")
            content.append(f"{package.get('overview', '')}\n\n")
            content.append("## 📂 项目结构\n\n```\n")
            content.append(f"{package.get('project_structure', '')}\n")
            content.append("```\n\n")
            content.append("## 💡 理论基础\n\n")
            content.append(f"{package.get('theoretical_foundation', '')}\n\n")
            
            # 添加概念解释部分
            concepts = package.get('concept_explanations', [])
            if concepts:
                content.append("---\n\n## 📖 核心概念详解\n\n")
                content.append("在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。\n\n")
                
                for concept in concepts:
                    if isinstance(concept, dict):
                        concept_name = concept.get('concept_name', 'Unknown')
                        explanation = concept.get('explanation', '')
                        why_important = concept.get('why_important', '')
                        related_concepts = concept.get('related_concepts', [])
                        examples = concept.get('examples', [])
                        
                        content.append(f"### {concept_name}\n\n")
                        content.append(f"{explanation}\n\n")
                        
                        if why_important:
                            content.append(f"**为什么重要**: {why_important}\n\n")
                        
                        if related_concepts:
                            content.append("**相关概念**: ")
                            content.append(", ".join(related_concepts))
                            content.append("\n\n")
                        
                        if examples:
                            content.append("**示例与类比**:\n\n")
                            for example in examples:
                                content.append(f"- {example}\n")
                            content.append("\n")
                        
                        content.append("---\n\n")
            
            content.append("## 🔧 分步实现\n\n")
            
            for step in package.get('implementation_steps', []):
                content.append(f"### Step {step.get('step_number', '')}: {step.get('component_name', '')}\n\n")
                content.append(f"**文件**: `{step.get('file_path', '')}`\n\n")
                content.append(f"**目的**: {step.get('purpose', '')}\n\n")
                content.append("**详细说明**:\n\n")
                content.append(f"{step.get('explanation', '')}\n\n")
                content.append("**完整代码**:\n\n")
                content.append(f"```{step.get('language', 'python')}\n")
                content.append(f"{step.get('code', '')}\n")
                content.append("```\n\n")
                content.append("**重要提示**:\n\n")
                for note in step.get('important_notes', []):
                    content.append(f"- {note}\n")
                content.append("\n")
            
            content.append("## 📦 依赖与安装\n\n### 所需依赖\n\n")
            for dep in package.get('dependencies', []):
                version_str = f" ({dep.get('version', '')})" if dep.get('version') else ""
                content.append(f"- **{dep.get('name', '')}{version_str}**: {dep.get('purpose', '')}\n")
            
            content.append("\n### 安装步骤\n\n```bash\n")
            for instruction in package.get('setup_instructions', []):
                content.append(f"{instruction}\n")
            content.append("```\n\n")
            content.append("## 🎮 使用教程\n\n")
            
            for example in package.get('usage_examples', []):
                content.append(f"### {example.get('title', '')}\n\n")
                content.append(f"**场景**: {example.get('scenario', '')}\n\n")
                content.append("```python\n")
                content.append(f"{example.get('code', '')}\n")
                content.append("```\n\n")
                content.append(f"**预期输出**: {example.get('expected_output', '')}\n\n")
            
            content.append("\n---\n\n")
        
        # 引用后处理：按全文首次出现顺序生成数字编号，并替换正文中的作者-年份为数字引用
        full_text = "".join(content)
        if references:
            unique_references = self._deduplicate_references(references)
            ordered_refs, author_year_to_num = self._build_global_citation_order_from_text(full_text, unique_references)
            # 将作者-年份引用替换为数字引用
            full_text = self._replace_author_year_with_numeric(full_text, author_year_to_num)
            # 追加参考文献（按首次引用顺序）
            full_text += "\n---\n\n# 📚 参考文献\n\n"
            for ref in ordered_refs[:200]:  # 安全上限
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                idx_num = author_year_to_num.get(self._make_author_year_key(ref), None)
                prefix = f"[{idx_num}] " if idx_num is not None else ""
                full_text += f"- {prefix}{authors} ({year}). *{title}*. {venue}\n"
            return full_text
        
        return full_text

    def _create_full_tutorial_notebook(
        self,
        goal_description: str,
        packages: List[Dict[str, Any]],
        references: List[Dict[str, Any]],
        task_decomposition: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """生成完整的教程文档（Jupyter Notebook 格式，支持全局首次引用顺序编号）"""
        cells = []
        
        # 顶部标题：仅使用模型凝练得到的 concise_title（不做兜底/派生）
        project_title = ""
        if isinstance(task_decomposition, dict):
            project_title = task_decomposition.get("concise_title") or ""
        
        # 一级标题：项目名称
        title_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# 项目：{project_title}\n\n"
            ]
        }
        cells.append(title_cell)
        
        # 二级标题：项目概述
        project_overview_source = ["## 项目概述\n\n"]
        
        # 从 task_decomposition 或 goal_description 获取概述
        if task_decomposition:
            problem_overview = task_decomposition.get("problem_overview") or task_decomposition.get("problem_formulation") or ""
            if problem_overview:
                project_overview_source.append(f"{problem_overview}\n\n")
        
        if not project_overview_source or len(project_overview_source) == 1:  # 只有标题
            project_overview_source.append(f"{goal_description}\n\n")
        
        overview_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": project_overview_source
        }
        cells.append(overview_cell)
        
        # 二级标题：项目拆解（放 key_steps）
        decomposition_source = ["## 项目拆解\n\n"]
        
        # 获取 key_steps
        key_steps = []
        if task_decomposition:
            key_steps = task_decomposition.get("key_steps") or []
        
        if key_steps and isinstance(key_steps, list):
            for idx, step in enumerate(key_steps, 1):
                if isinstance(step, dict):
                    step_id = step.get("step_id")
                    step_name = step.get("step_name", "")
                    desc = step.get("description", "")
                    prefix = f"[{step_id}] " if step_id else ""
                    decomposition_source.append(f"{idx}. {prefix}{step_name} - {desc}\n")
                else:
                    decomposition_source.append(f"{idx}. {str(step)}\n")
            decomposition_source.append("\n")
        else:
            decomposition_source.append("（暂无项目拆解信息）\n\n")
        
        decomposition_cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": decomposition_source
        }
        cells.append(decomposition_cell)
        
        # 将每个 package 作为一个步骤（二级标题：步骤一、步骤二...）
        for idx, package in enumerate(packages, 1):
            if package.get("status") != "success":
                # 步骤X：处理失败
                error_cell = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"## 步骤{idx}\n\n",
                        f"### 处理失败\n\n",
                        f"错误: {package.get('error', '未知错误')}\n"
                    ]
                }
                cells.append(error_cell)
                continue
            
            # 步骤标题（二级标题）
            step_number = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
            step_name = step_number[idx-1] if idx <= 10 else str(idx)
            
            # 获取步骤标题（从package_title或action_item）
            step_title = package.get('package_title', '')
            if ":" in step_title:
                step_title = step_title.split(":", 1)[1].strip()
            elif not step_title:
                step_title = package.get('action_item', f'步骤{step_name}')
            
            step_header_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"## 步骤{step_name}：{step_title}\n\n"
                ]
            }
            cells.append(step_header_cell)
            
            # 概述（三级标题）
            overview_source = ["### 概述\n\n", f"{package.get('overview', '')}\n\n"]
            overview_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": overview_source
            }
            cells.append(overview_cell)
            
            # 项目结构（三级标题）
            structure_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 项目结构\n\n",
                    "```\n",
                    f"{package.get('project_structure', '')}\n",
                    "```\n\n"
                ]
            }
            cells.append(structure_cell)
            
            # 理论基础（三级标题）
            theory_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "### 理论基础\n\n",
                    f"{package.get('theoretical_foundation', '')}\n\n"
                ]
            }
            cells.append(theory_cell)
            
            # 核心概念详解（三级标题）
            concepts = package.get('concept_explanations', [])
            if concepts:
                concepts_header_source = ["### 核心概念详解\n\n", "在开始实现之前，请先理解以下核心概念。这些概念是理解本步骤实现的关键前提。\n\n"]
                concepts_header = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": concepts_header_source
                }
                cells.append(concepts_header)
                
                for concept in concepts:
                    if isinstance(concept, dict):
                        concept_name = concept.get('concept_name', 'Unknown')
                        explanation = concept.get('explanation', '')
                        why_important = concept.get('why_important', '')
                        related_concepts = concept.get('related_concepts', [])
                        examples = concept.get('examples', [])
                        
                        # 概念名称（四级标题）
                        concept_source = [f"#### {concept_name}\n\n", f"{explanation}\n\n"]
                        
                        if why_important:
                            concept_source.append(f"**为什么重要**: {why_important}\n\n")
                        
                        if related_concepts:
                            concept_source.append("**相关概念**: ")
                            concept_source.append(", ".join(related_concepts))
                            concept_source.append("\n\n")
                        
                        if examples:
                            concept_source.append("**示例与类比**:\n\n")
                            for example in examples:
                                concept_source.append(f"- {example}\n")
                            concept_source.append("\n")
                        
                        concept_cell = {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": concept_source
                        }
                        cells.append(concept_cell)
            
            # 实现步骤（三级标题）
            implementation_steps = package.get('implementation_steps', [])
            if implementation_steps:
                impl_steps_header = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["### 实现步骤\n\n"]
                }
                cells.append(impl_steps_header)
                
                for step in implementation_steps:
                    # 子步骤（四级标题）
                    step_info_source = [
                        f"#### {step.get('component_name', '')}\n\n",
                        f"**文件**: `{step.get('file_path', '')}`\n\n",
                        f"**目的**: {step.get('purpose', '')}\n\n"
                    ]
                    
                    # 详细说明（五级标题或加粗文本）
                    if step.get('explanation'):
                        step_info_source.append("**详细说明**\n\n")
                        step_info_source.append(f"{step.get('explanation', '')}\n\n")
                    
                    step_info_cell = {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": step_info_source
                    }
                    cells.append(step_info_cell)
                    
                    # 代码实现
                    code_source = step.get('code', '')
                    if code_source:
                        code_cell = {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "source": code_source.split('\n') if code_source else [],
                            "outputs": []
                        }
                        cells.append(code_cell)
                    
                    # 重要提示（五级标题或加粗文本）
                    if step.get('important_notes'):
                        notes_source = ["**重要提示**\n\n"]
                        for note in step.get('important_notes', []):
                            notes_source.append(f"- {note}\n")
                        notes_source.append("\n")
                        
                        notes_cell = {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": notes_source
                        }
                        cells.append(notes_cell)
            
            # 依赖与安装（三级标题）
            deps = package.get('dependencies', [])
            setup_instructions = package.get('setup_instructions', [])
            if deps or setup_instructions:
                deps_header_source = ["### 依赖与安装\n\n"]
                
                if deps:
                    deps_header_source.append("#### 所需依赖\n\n")
                    for dep in deps:
                        version_str = f" ({dep.get('version', '')})" if dep.get('version') else ""
                        deps_header_source.append(f"- **{dep.get('name', '')}{version_str}**: {dep.get('purpose', '')}\n")
                    deps_header_source.append("\n")
                
                deps_header = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": deps_header_source
                }
                cells.append(deps_header)
                
                # 安装步骤（四级标题）
                if setup_instructions:
                    install_header = {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": ["#### 安装步骤\n\n"]
                    }
                    cells.append(install_header)
                    
                    install_source = [f"{inst}\n" for inst in setup_instructions]
                    install_cell = {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {"tags": ["bash"]},
                        "source": install_source,
                        "outputs": []
                    }
                    cells.append(install_cell)
            
            # 使用教程（三级标题）
            usage_examples = package.get('usage_examples', [])
            if usage_examples:
                usage_header = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["### 使用教程\n\n"]
                }
                cells.append(usage_header)
                
                for example in usage_examples:
                    # 示例标题（四级标题）
                    example_title = example.get('title', '')
                    example_source = [f"#### {example_title}\n\n"] if example_title else []
                    example_source.append(f"**场景**: {example.get('scenario', '')}\n\n")
                    
                    example_header = {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": example_source
                    }
                    cells.append(example_header)
                    
                    # 代码示例
                    example_code = example.get('code', '')
                    if example_code:
                        example_code_cell = {
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "source": example_code.split('\n'),
                            "outputs": []
                        }
                        cells.append(example_code_cell)
                    
                    # 预期输出（加粗文本）
                    expected_output = example.get('expected_output', '')
                    if expected_output:
                        output_source = ["**预期输出**\n\n", f"{expected_output}\n\n"]
                        output_cell = {
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": output_source
                        }
                        cells.append(output_cell)
        
        # 参考文献后处理：计算全文首次引用顺序并替换为数字引用
        if references:
            # 聚合所有 markdown 文本
            all_text = []
            for c in cells:
                if c.get("cell_type") == "markdown":
                    src = "".join(c.get("source", []))
                    all_text.append(src)
            combined_text = "\n".join(all_text)
            unique_references = self._deduplicate_references(references)
            ordered_refs, author_year_to_num = self._build_global_citation_order_from_text(combined_text, unique_references)
            # 替换每个 markdown 单元格中的作者-年份为数字引用
            for c in cells:
                if c.get("cell_type") == "markdown":
                    src = "".join(c.get("source", []))
                    replaced = self._replace_author_year_with_numeric(src, author_year_to_num)
                    c["source"] = [replaced]
            # 追加参考文献区块（按首次引用顺序）
            ref_header = {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["\n---\n\n", "# 📚 参考文献\n\n"]
            }
            cells.append(ref_header)
            ref_list_source = []
            for ref in ordered_refs[:200]:
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                idx_num = author_year_to_num.get(self._make_author_year_key(ref), None)
                prefix = f"[{idx_num}] " if idx_num is not None else ""
                ref_list_source.append(f"- {prefix}{authors} ({year}). *{title}*. {venue}\n")
            ref_list_cell = {
                "cell_type": "markdown",
                "metadata": {},
                "source": ref_list_source
            }
            cells.append(ref_list_cell)
        
        # 构建 notebook 结构
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        return notebook
    
    async def _condense_project_title(self, problem_overview: str) -> str:
        """
        使用大模型从 problem_overview 凝练中文教程标题（简短、有指向性，建议以“教程”结尾）
        """
        if not problem_overview:
            return ""
        prompt = (
            "你是资深技术作者，请将以下研究问题概述，凝练为一个中文教程标题：\n"
            "要求：\n"
            "1) 简洁有力，8-12字为宜（硬性上限14字）\n"
            "2) 能概括问题与方法场景\n"
            "3) 以“教程”结尾（若已包含“教程”则不必重复）\n"
            "4) 不要出现问句或标点（如？、。等），不以“如何/怎样/怎么”开头\n"
            "5) 只输出标题本身\n\n"
            f"【问题概述】\n{problem_overview}\n"
        )
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "简洁教程标题，仅标题文本"}
            },
            "required": ["title"]
        }
        try:
            resp = await self._call_model(
                prompt=prompt,
                system_prompt="你是擅长中文技术写作的编辑，输出高质量中文标题。",
                schema=schema,
                temperature=0.2
            )
            title = (resp or {}).get("title", "").strip()
            return title
        except Exception:
            return ""
    
    def _derive_title_from_text(self, text: str) -> str:
        """
        纯规则的标题凝练兜底方案：截断 + 去引导词 + 加“教程”
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        base = text.strip().rstrip("？?。.")
        if len(base) > 30:
            base = base[:30].strip()
        for prefix in ["如何", "怎样", "怎么", "请问", "基于", "面向"]:
            if base.startswith(prefix):
                base = base[len(prefix):].strip()
                break
        if base and not base.endswith("教程") and "教程" not in base:
            base = f"{base}教程"
        return base

    def _make_author_year_key(self, ref: Dict[str, Any]) -> str:
        """生成用于匹配的 author-year 键（使用第一作者姓氏的简化形式 + 年份）"""
        authors = ref.get("authors") or ""
        year = str(ref.get("year") or "").strip()
        if isinstance(authors, list):
            first_author = str(authors[0]) if authors else ""
        else:
            # 形如 "A, B, C" 取第一个逗号或 and 前的名字
            first_author = str(authors).split(",")[0]
        # 只保留字母和连字符，转小写
        import re
        surname = re.sub(r"[^A-Za-z\-]", "", first_author).lower()
        return f"{surname}:{year}"
    
    def _build_global_citation_order_from_text(
        self,
        text: str,
        references: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        扫描全文，按作者-年份引用首次出现顺序建立编号，并返回有序参考文献列表与映射。
        仅基于作者-年份模式 [Surname, 2020] 进行编号；无法可靠映射已有的数字引用。
        """
        import re
        # 预构建 author-year -> ref 的索引
        key_to_ref = {}
        for ref in references:
            key = self._make_author_year_key(ref)
            if key and key not in key_to_ref:
                key_to_ref[key] = ref
        # 按出现顺序建立编号
        author_year_to_num: Dict[str, int] = {}
        ordered_refs: List[Dict[str, Any]] = []
        # 匹配 [Surname, 2020] / [Smith 2020] 等（允许逗号可选，允许空格）
        pattern = re.compile(r"\[([A-Za-z\-\.\s]+),?\s*(\d{4})\]")
        for match in pattern.finditer(text or ""):
            surname_raw = match.group(1)
            year = match.group(2)
            surname = re.sub(r"[^A-Za-z\-]", "", surname_raw).lower()
            key = f"{surname}:{year}"
            if key in key_to_ref and key not in author_year_to_num:
                author_year_to_num[key] = len(author_year_to_num) + 1
                ordered_refs.append(key_to_ref[key])
        # 将未出现但在参考列表中的条目追加到末尾
        for ref in references:
            key = self._make_author_year_key(ref)
            if key and key not in author_year_to_num:
                author_year_to_num[key] = len(author_year_to_num) + 1
                ordered_refs.append(ref)
        return ordered_refs, author_year_to_num
    
    def _replace_author_year_with_numeric(self, text: str, author_year_to_num: Dict[str, int]) -> str:
        """将文本中的 [Surname, 2020] 样式替换为对应的数字引用 [n]。"""
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
    
    def _extract_package_section_from_tutorial(self, tutorial_text: str, package_index: int) -> Tuple[int, int]:
        """
        从tutorial文本中定位某个package的起始和结束位置
        
        Returns:
            (start_pos, end_pos) - package内容的起始和结束字符位置，如果找不到返回(-1, -1)
        """
        import re
        # 匹配package标题：`# Package {idx}: {title}` 或 `## Package {idx}: {title}`
        # 前面可能有分隔线 `=` * 100
        pattern_start = re.compile(
            rf"(?:=+\s*\n\s*)?#+\s*Package\s+{package_index}\s*:\s*[^\n]+\n",
            re.IGNORECASE
        )
        
        # 查找package开始位置
        match_start = pattern_start.search(tutorial_text)
        if not match_start:
            return (-1, -1)
        
        start_pos = match_start.start()
        
        # 查找package结束位置：下一个package的开始，或者参考文献部分
        # 下一个package的模式
        pattern_next_package = re.compile(
            rf"(?:=+\s*\n\s*)?#+\s*Package\s+{package_index + 1}\s*:\s*[^\n]+\n",
            re.IGNORECASE
        )
        
        # 参考文献部分
        pattern_refs = re.compile(r"\n---\s*\n\s*#+\s*📚\s*参考文献\s*\n", re.IGNORECASE)
        
        # 查找下一个package或参考文献的位置
        next_package_match = pattern_next_package.search(tutorial_text, start_pos + 1)
        refs_match = pattern_refs.search(tutorial_text, start_pos + 1)
        
        # 取最近的一个作为结束位置
        end_pos = len(tutorial_text)
        if next_package_match:
            end_pos = min(end_pos, next_package_match.start())
        if refs_match:
            end_pos = min(end_pos, refs_match.start())
        
        return (start_pos, end_pos)
    
    def _generate_package_section_for_tutorial(
        self,
        package: Dict[str, Any],
        package_index: int
    ) -> str:
        """生成单个package在full tutorial中的内容（不包含引用编号处理）"""
        content = []
        
        content.append("=" * 100 + "\n\n")
        content.append(f"# Package {package_index}: {package.get('package_title', '')}\n\n")
        content.append("=" * 100 + "\n\n")
        content.append("## 📋 概述\n\n")
        content.append(f"{package.get('overview', '')}\n\n")
        content.append("## 📂 项目结构\n\n```\n")
        content.append(f"{package.get('project_structure', '')}\n")
        content.append("```\n\n")
        content.append("## 💡 理论基础\n\n")
        content.append(f"{package.get('theoretical_foundation', '')}\n\n")
        
        # 添加概念解释部分
        concepts = package.get('concept_explanations', [])
        if concepts:
            content.append("---\n\n## 📖 核心概念详解\n\n")
            content.append("在开始实现之前，请先理解以下核心概念。这些概念是理解本包实现的关键前提。\n\n")
            
            for concept in concepts:
                if isinstance(concept, dict):
                    concept_name = concept.get('concept_name', 'Unknown')
                    explanation = concept.get('explanation', '')
                    why_important = concept.get('why_important', '')
                    related_concepts = concept.get('related_concepts', [])
                    examples = concept.get('examples', [])
                    
                    content.append(f"### {concept_name}\n\n")
                    content.append(f"{explanation}\n\n")
                    
                    if why_important:
                        content.append(f"**为什么重要**: {why_important}\n\n")
                    
                    if related_concepts:
                        content.append("**相关概念**: ")
                        content.append(", ".join(related_concepts))
                        content.append("\n\n")
                    
                    if examples:
                        content.append("**示例与类比**:\n\n")
                        for example in examples:
                            content.append(f"- {example}\n")
                        content.append("\n")
                    
                    content.append("---\n\n")
        
        content.append("## 🔧 分步实现\n\n")
        
        for step in package.get('implementation_steps', []):
            content.append(f"### Step {step.get('step_number', '')}: {step.get('component_name', '')}\n\n")
            content.append(f"**文件**: `{step.get('file_path', '')}`\n\n")
            content.append(f"**目的**: {step.get('purpose', '')}\n\n")
            content.append("**详细说明**:\n\n")
            content.append(f"{step.get('explanation', '')}\n\n")
            content.append("**完整代码**:\n\n")
            content.append(f"```{step.get('language', 'python')}\n")
            content.append(f"{step.get('code', '')}\n")
            content.append("```\n\n")
            content.append("**重要提示**:\n\n")
            for note in step.get('important_notes', []):
                content.append(f"- {note}\n")
            content.append("\n")
        
        content.append("## 📦 依赖与安装\n\n### 所需依赖\n\n")
        for dep in package.get('dependencies', []):
            version_str = f" ({dep.get('version', '')})" if dep.get('version') else ""
            content.append(f"- **{dep.get('name', '')}{version_str}**: {dep.get('purpose', '')}\n")
        
        content.append("\n### 安装步骤\n\n```bash\n")
        for instruction in package.get('setup_instructions', []):
            content.append(f"{instruction}\n")
        content.append("```\n\n")
        content.append("## 🎮 使用教程\n\n")
        
        for example in package.get('usage_examples', []):
            content.append(f"### {example.get('title', '')}\n\n")
            content.append(f"**场景**: {example.get('scenario', '')}\n\n")
            content.append("```python\n")
            content.append(f"{example.get('code', '')}\n")
            content.append("```\n\n")
            content.append(f"**预期输出**: {example.get('expected_output', '')}\n\n")
        
        content.append("\n---\n\n")
        
        return "".join(content)
    
    def _replace_packages_in_tutorial(
        self,
        existing_tutorial: str,
        project_packages: List[Dict[str, Any]],
        modified_package_indices: set,
        references: List[Dict[str, Any]],
        task_decomposition: Dict[str, Any]
    ) -> str:
        """
        在existing_tutorial中替换被修改的package部分
        
        策略：
        1. 定位每个被修改的package在tutorial中的位置
        2. 生成新的package内容
        3. 替换旧内容
        4. 重新计算并更新引用编号（因为可能有新增引用）
        """
        updated_tutorial = existing_tutorial
        
        # 按索引从大到小替换，避免位置偏移问题
        for pkg_idx in sorted(modified_package_indices, reverse=True):
            if pkg_idx < 1 or pkg_idx > len(project_packages):
                continue
            package = project_packages[pkg_idx - 1]
            if package.get("status") != "success":
                continue
            
            # 定位package位置
            start_pos, end_pos = self._extract_package_section_from_tutorial(updated_tutorial, pkg_idx)
            if start_pos == -1:
                logger.warning(f"无法在tutorial中定位 Package {pkg_idx}，跳过替换")
                continue
            
            # 生成新的package内容
            new_package_content = self._generate_package_section_for_tutorial(package, pkg_idx)
            
            # 替换
            updated_tutorial = updated_tutorial[:start_pos] + new_package_content + updated_tutorial[end_pos:]
            logger.info(f"已替换 Package {pkg_idx} 在tutorial中的内容")
        
        # 重新计算引用编号（因为可能有新增引用）
        if references:
            unique_references = self._deduplicate_references(references)
            ordered_refs, author_year_to_num = self._build_global_citation_order_from_text(
                updated_tutorial, unique_references
            )
            # 将作者-年份引用替换为数字引用
            updated_tutorial = self._replace_author_year_with_numeric(updated_tutorial, author_year_to_num)
            
            # 更新参考文献部分
            import re
            refs_pattern = re.compile(r"\n---\s*\n\s*#+\s*📚\s*参考文献\s*\n.*", re.DOTALL)
            new_refs_section = "\n---\n\n# 📚 参考文献\n\n"
            for ref in ordered_refs[:200]:
                title = ref.get("title", "Untitled")
                authors = ref.get("authors", "Unknown")
                year = ref.get("year", "n.d.")
                venue = ref.get("journal") or ref.get("venue") or ""
                idx_num = author_year_to_num.get(self._make_author_year_key(ref), None)
                prefix = f"[{idx_num}] " if idx_num is not None else ""
                new_refs_section += f"- {prefix}{authors} ({year}). *{title}*. {venue}\n"
            
            if refs_pattern.search(updated_tutorial):
                updated_tutorial = refs_pattern.sub(new_refs_section, updated_tutorial)
            else:
                updated_tutorial += new_refs_section
        
        return updated_tutorial
    
    def _replace_packages_in_notebook(
        self,
        existing_notebook: Dict[str, Any],
        project_packages: List[Dict[str, Any]],
        modified_package_indices: set,
        references: List[Dict[str, Any]],
        task_decomposition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        在existing_notebook中替换被修改的package部分
        
        策略类似Markdown版本，但需要处理Notebook的cell结构
        """
        # TODO: 实现Notebook版本的增量替换
        # 由于Notebook结构更复杂，暂时回退到全量重新生成
        # 可以后续优化：定位到对应的cells，替换内容
        logger.warning("Notebook增量替换尚未实现，使用全量重新生成")
        raise NotImplementedError("Notebook增量替换功能待实现")

    def _create_structure_overview(self, goal_description: str, packages: List[Dict[str, Any]]) -> str:
        """生成项目结构概览"""
        content = []
        
        content.append("# 项目结构概览\n\n")
        content.append("## 研究目标\n\n")
        content.append(f"{goal_description}\n\n")
        content.append(f"## 包组织结构\n\n")
        content.append(f"本项目由 {len(packages)} 个互联的包组成：\n\n```\nresearch-implementation/\n│\n")
        
        for idx, pkg in enumerate(packages, 1):
            if pkg.get("status") == "success":
                title = pkg.get("package_title", f"Package {idx}")
                package_name = self._sanitize_filename(title)
                content.append(f"├── package-{idx:02d}-{package_name}/\n")
                content.append(f"│   # {pkg.get('overview', '')[:80]}...\n")
                content.append("│\n")
        
        content.append("├── docs/\n")
        content.append("│   ├── FULL_TUTORIAL.md\n")
        content.append("│   └── QUICKSTART.md\n")
        content.append("│\n")
        content.append("└── README.md\n")
        content.append("```\n\n")
        content.append("## 包详细信息\n\n")
        
        for idx, pkg in enumerate(packages, 1):
            if pkg.get("status") == "success":
                content.append(f"### Package {idx}: {pkg.get('package_title', '')}\n\n")
                content.append(f"{pkg.get('overview', '')}\n\n")
                content.append(f"**对应行动项**: {pkg.get('action_item', '')}\n\n")
        
        return "".join(content)

    def _create_quickstart_guide(self, packages: List[Dict[str, Any]]) -> str:
        """生成快速开始指南"""
        content = []
        
        content.append("# 🚀 快速开始指南\n\n")
        content.append("## 前置要求\n\n- Python 3.8+\n- pip 或 conda\n\n")
        content.append("## 安装步骤\n\n### 1. 克隆或下载项目\n\n```bash\n")
        content.append("git clone <repository-url>\n")
        content.append("cd research-implementation\n```\n\n")
        content.append("### 2. 按顺序设置每个包\n\n")
        
        for idx, pkg in enumerate(packages, 1):
            if pkg.get("status") != "success":
                continue
            
            title = pkg.get("package_title", f"Package {idx}")
            content.append(f"#### Package {idx}: {title}\n\n```bash\n")
            content.append(f"cd packages/{idx:02d}-{self._sanitize_filename(title)}\n\n")
            content.append("# 创建虚拟环境\n")
            content.append("python -m venv venv\n")
            content.append("source venv/bin/activate  # Linux/Mac\n\n")
            content.append("# 安装依赖\n")
            
            deps = pkg.get('dependencies', [])
            if deps:
                dep_names = []
                for dep in deps[:3]:
                    name = dep.get('name', '')
                    version = dep.get('version', '')
                    if version:
                        dep_names.append(f"{name}=={version}")
                    else:
                        dep_names.append(name)
                content.append(f"pip install {' '.join(dep_names)}")
                if len(deps) > 3:
                    content.append(" ...")
                content.append("\n")
            
            content.append("\n# 查看完整说明\ncat README.md\n```\n\n")
        
        content.append("## 🎯 基础使用示例\n\n")
        
        for idx, pkg in enumerate(packages, 1):
            if pkg.get("status") != "success":
                continue
            
            examples = pkg.get('usage_examples', [])
            if examples:
                first_example = examples[0]
                content.append(f"### Package {idx} 示例\n\n")
                content.append(f"{first_example.get('scenario', '')}\n\n```python\n")
                code = first_example.get('code', '')
                if len(code) > 500:
                    content.append(f"{code[:500]}...\n")
                else:
                    content.append(f"{code}\n")
                content.append("```\n\n")
                content.append(f"详见: `packages/{idx:02d}-*/README.md`\n\n")
        
        content.append("## 📚 进一步学习\n\n")
        content.append("- 查看每个包的 `README.md`\n")
        content.append("- 阅读 `FULL_TUTORIAL.md`\n")
        content.append("- 参考 `PROJECT_STRUCTURE.md`\n\n")
        content.append("## ❓ 获取帮助\n\n")
        content.append("如有问题，请查看文档或提交 issue。\n")
        
        return "".join(content)

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        import re
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '-', name)
        return name.lower()[:50]
    
    # 在 EngineerAgent 中添加这个方法

    async def revise_based_on_dual_review(
        self,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据双审稿人的反馈修改方案
        
        Expected context:
            - original_plan: 原始plan
            - pedagogical_review: 教学性审稿人的完整评审
            - logical_review: 逻辑性审稿人的完整评审
            - consolidated_feedback: 整合后的反馈
            - goal_description: 研究目标
        """
        original_plan = context.get("original_plan")
        consolidated_feedback = context.get("consolidated_feedback")
        goal_description = context.get("goal_description")
        
        if not original_plan or not consolidated_feedback:
            raise AgentExecutionError("需要 original_plan 和 consolidated_feedback")
        
        logger.info("根据双审稿人反馈修改方案...")
        
        package_feedback = consolidated_feedback.get("package_feedback", {})
        cross_issues = consolidated_feedback.get("cross_package_issues", [])
        
        # 逐个修改需要改进的package
        revised_packages = []
        for pkg_idx, pkg in enumerate(original_plan.get("project_packages", []), 1):
            if pkg.get("status") != "success":
                revised_packages.append(pkg)
                continue
            
            pkg_feedback_data = package_feedback.get(pkg_idx)
            
            if not pkg_feedback_data or not pkg_feedback_data.get("requires_revision"):
                logger.info(f"Package {pkg_idx} 无需修改")
                revised_packages.append(pkg)
                continue
            
            logger.info(f"修改 Package {pkg_idx}: {pkg.get('package_title', '')}")
            
            revised_pkg = await self._revise_package_with_dual_feedback(
                package=pkg,
                package_index=pkg_idx,
                feedback=pkg_feedback_data,
                cross_issues=cross_issues,
                goal_description=goal_description,
                params=params
            )
            
            revised_packages.append(revised_pkg)
        
        # 构建修改后的plan
        revised_plan = original_plan.copy()
        revised_plan["project_packages"] = revised_packages
        
        # 增量更新输出文件（只替换修改过的package）
        logger.info("增量更新输出文件...")
        # 获取 task_decomposition 信息（如果原始plan中有）
        task_decomposition = (
            context.get("task_decomposition")
            or original_plan.get("task_decomposition")
            or {}
        )
        
        # 识别哪些package被修改了
        modified_package_indices = set()
        for pkg_idx, (original_pkg, revised_pkg) in enumerate(
            zip(original_plan.get("project_packages", []), revised_packages), 1
        ):
            if original_pkg.get("status") == "success" and revised_pkg.get("status") == "success":
                # 检查是否真的被修改了（通过revised_by_dual_reviewers标记）
                if revised_pkg.get("revised_by_dual_reviewers"):
                    modified_package_indices.add(pkg_idx)
        
        output_structure = self._generate_and_save_outputs_incremental(
            goal_description,
            revised_packages,
            modified_package_indices,
            original_plan.get("references") or context.get("references") or [],
            task_decomposition,
            params,
            original_plan.get("output_structure", {})  # 传入现有的输出结构
        )
        revised_plan["output_structure"] = output_structure
        
        return revised_plan

    async def _revise_package_with_dual_feedback(
        self,
        package: Dict[str, Any],
        package_index: int,
        feedback: Dict[str, Any],
        cross_issues: List[Dict[str, Any]],
        goal_description: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于双审稿人反馈修改单个package（细粒度修改策略）
        
        策略：
        1. 解析location，识别需要修改的具体step和字段
        2. 按step分组问题，只修改受影响的step
        3. 使用patch/merge策略，保持其他内容不变
        4. 优先处理critical和major问题
        """
        current_package = package.copy()
        implementation_steps = current_package.get("implementation_steps", [])
        
        # 整理所有问题并按优先级排序
        all_issues = self._organize_issues_by_priority(feedback, cross_issues, package_index)
        
        if not all_issues:
            logger.info(f"Package {package_index} 没有需要修改的问题")
            return current_package
        
        # 检查是否有critical或major问题，决定修改策略
        has_critical = any(issue.get('severity', '').lower() == 'critical' for issue in all_issues)
        has_major = any(issue.get('severity', '').lower() == 'major' for issue in all_issues)
        revision_aggressiveness = "aggressive" if (has_critical or has_major) else "moderate"
        logger.info(f"Package {package_index} 修改策略: {revision_aggressiveness} (critical: {has_critical}, major: {has_major})")
        
        # 解析location，识别需要修改的step和字段
        step_modifications = self._parse_issues_to_step_modifications(all_issues, implementation_steps)
        
        # 处理非step级别的修改（如overview, theoretical_foundation等）
        non_step_modifications = [issue for issue in all_issues 
                                 if not self._is_step_location(issue.get("location", ""))]
        
        # 先处理非step级别的修改
        if non_step_modifications:
            logger.info(f"Package {package_index} 处理 {len(non_step_modifications)} 个非step级别的修改...")
            current_package = await self._revise_non_step_fields(
                current_package,
                non_step_modifications,
                goal_description,
                params
            )
        
        # 按step分组处理修改
        for step_index, modifications in step_modifications.items():
            if step_index < 0 or step_index >= len(implementation_steps):
                logger.warning(f"Package {package_index} Step {step_index} 索引超出范围，跳过")
                continue
            
            logger.info(f"Package {package_index} 修改 Step {step_index + 1} ({len(modifications)} 个修改意见)...")
            
            # 细粒度修改单个step
            revised_step = await self._revise_single_step(
                implementation_steps[step_index],
                modifications,
                current_package,
                goal_description,
                params,
                revision_aggressiveness=revision_aggressiveness
            )
            
            # 合并修改后的step回原package
            implementation_steps[step_index] = revised_step
        
        # 更新package的steps
        current_package["implementation_steps"] = implementation_steps
        current_package["action_item"] = package.get("action_item")
        current_package["action_index"] = package_index
        current_package["status"] = "success"
        current_package["revised_by_dual_reviewers"] = True
        
        logger.info(f"Package {package_index} 细粒度修改完成（共修改 {len(step_modifications)} 个step）")
        return current_package
    
    def _is_step_location(self, location: str) -> bool:
        """判断location是否指向step"""
        if not location or not isinstance(location, str):
            return False
        location_lower = location.lower()
        # 匹配 "Step X", "Step X.Y", "步骤X" 等格式
        import re
        step_patterns = [
            r'step\s+\d+',  # "Step 1", "Step 4.2"
            r'步骤\s*\d+',   # "步骤1"
            r'step\s*\d+\.\d+',  # "Step 4.2"
        ]
        for pattern in step_patterns:
            if re.search(pattern, location_lower):
                return True
        return False
    
    def _parse_step_number(self, location: str) -> int:
        """从location中解析step编号（返回0-based索引）"""
        import re
        # 匹配 "Step 1", "Step 4.2", "步骤1" 等
        match = re.search(r'(?:step|步骤)\s*(\d+)', location.lower())
        if match:
            step_num = int(match.group(1))
            return step_num - 1  # 转换为0-based索引
        return -1
    
    def _parse_issues_to_step_modifications(
        self,
        issues: List[Dict[str, Any]],
        implementation_steps: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        解析问题列表，按step索引分组
        
        返回: {step_index: [issue1, issue2, ...]}
        """
        step_modifications = {}
        
        for issue in issues:
            location = issue.get("location", "")
            if not self._is_step_location(location):
                continue
            
            step_index = self._parse_step_number(location)
            if step_index < 0 or step_index >= len(implementation_steps):
                # 如果无法解析或超出范围，尝试通过step_number字段匹配
                step_number = issue.get("step_number")
                if step_number:
                    step_index = step_number - 1
                else:
                    logger.warning(f"无法解析location '{location}' 的step编号，跳过")
                    continue
            
            if step_index not in step_modifications:
                step_modifications[step_index] = []
            step_modifications[step_index].append(issue)
        
        return step_modifications
    
    async def _revise_single_step(
        self,
        step: Dict[str, Any],
        modifications: List[Dict[str, Any]],
        package_context: Dict[str, Any],
        goal_description: str,
        params: Dict[str, Any],
        revision_aggressiveness: str = "moderate"
    ) -> Dict[str, Any]:
        """
        细粒度修改单个step的指定字段
        
        策略：
        1. 识别需要修改的字段（explanation, code, purpose等）
        2. 根据严重程度决定修改幅度（aggressive vs moderate）
        3. 使用merge策略合并
        """
        # 识别需要修改的字段
        fields_to_revise = set()
        for mod in modifications:
            category = mod.get("category", "")
            # 根据category推断需要修改的字段
            if "explanation" in category.lower() or "concept" in category.lower():
                fields_to_revise.add("explanation")
            if "code" in category.lower() or "comment" in category.lower():
                fields_to_revise.add("code")
            if "purpose" in category.lower() or "description" in category.lower():
                fields_to_revise.add("purpose")
            # 默认修改explanation和code
            if not fields_to_revise:
                fields_to_revise.add("explanation")
                fields_to_revise.add("code")
        
        # 构建修改prompt
        prompt = self._build_step_revision_prompt(
            step,
            modifications,
            fields_to_revise,
            package_context,
            goal_description,
            revision_aggressiveness=revision_aggressiveness
        )
        
        # 构建schema（只包含需要修改的字段）
        schema = self._build_step_revision_schema(fields_to_revise)
        
        # 根据修改策略调整temperature：aggressive时使用更高temperature以允许更大改动
        temperature = 0.4 if revision_aggressiveness == "aggressive" else 0.3
        
        try:
            response = await self._call_model(
                prompt=prompt,
                system_prompt=self._build_step_revision_system_prompt(fields_to_revise, revision_aggressiveness),
                schema=schema,
                temperature=temperature
            )
            
            # 合并修改：只更新指定的字段，保持其他字段不变
            revised_step = step.copy()
            for field in fields_to_revise:
                if field in response:
                    revised_step[field] = response[field]
            
            return revised_step
            
        except Exception as exc:
            logger.error(f"修改step失败: {exc}")
            return step  # 返回原step
    
    async def _revise_non_step_fields(
        self,
        package: Dict[str, Any],
        modifications: List[Dict[str, Any]],
        goal_description: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """修改非step级别的字段（如overview, theoretical_foundation等）"""
        # 识别需要修改的字段
        fields_to_revise = set()
        for mod in modifications:
            location = mod.get("location", "").lower()
            if "overview" in location:
                fields_to_revise.add("overview")
            if "theory" in location or "theoretical" in location:
                fields_to_revise.add("theoretical_foundation")
            if "structure" in location:
                fields_to_revise.add("project_structure")
        
        if not fields_to_revise:
            # 默认修改overview
            fields_to_revise.add("overview")
        
        # 构建修改prompt
        prompt = self._build_non_step_revision_prompt(
            package,
            modifications,
            fields_to_revise,
            goal_description
        )
        
        # 构建schema
        schema = self._build_non_step_revision_schema(fields_to_revise)
        
        try:
            fields_str = ', '.join(fields_to_revise)
            system_prompt = (
                f"You are an expert technical educator making a SURGICAL revision. "
                f"You are revising ONLY the following field(s): {fields_str}. "
                f"Keep all other package fields exactly as they are. "
                f"Be precise and focused. Apply the suggested fixes while maintaining consistency."
            )
            response = await self._call_model(
                prompt=prompt,
                system_prompt=system_prompt,
                schema=schema,
                temperature=0.2
            )
            
            # 合并修改
            revised_package = package.copy()
            for field in fields_to_revise:
                if field in response:
                    revised_package[field] = response[field]
            
            return revised_package
            
        except Exception as exc:
            logger.error(f"修改非step字段失败: {exc}")
            return package
    
    def _organize_issues_by_priority(
        self,
        feedback: Dict[str, Any],
        cross_issues: List[Dict[str, Any]],
        package_index: int
    ) -> List[Dict[str, Any]]:
        """按优先级组织问题：critical -> major -> minor"""
        all_issues = []
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        
        # 添加教学性问题
        for issue in feedback.get("pedagogical_issues", []):
            if isinstance(issue, dict):
                issue["issue_type"] = "pedagogical"
                all_issues.append(issue)
        
        # 添加逻辑性问题
        for issue in feedback.get("logical_issues", []):
            if isinstance(issue, dict):
                issue["issue_type"] = "logical"
                all_issues.append(issue)
        
        # 添加缺失概念（作为pedagogical问题）
        for concept in feedback.get("missing_concepts", []):
            if isinstance(concept, dict):
                all_issues.append({
                    "issue_type": "pedagogical",
                    "category": "missing_concept",
                    "severity": "major",
                    "location": concept.get("where_to_add", "unknown"),
                    "problem": f"缺失概念: {concept.get('concept', '')}",
                    "suggestion": concept.get("suggested_explanation", concept.get("why_needed", "")),
                    "concept_data": concept
                })
        
        # 添加相关的跨package问题
        for issue in cross_issues:
            if isinstance(issue, dict) and package_index in issue.get("affected_packages", []):
                issue["issue_type"] = "cross_package"
                all_issues.append(issue)
        
        # 按严重程度排序
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "minor"), 2))
        
        return all_issues
    
    def _split_issues_into_batches(
        self,
        issues: List[Dict[str, Any]],
        max_per_batch: int
    ) -> List[List[Dict[str, Any]]]:
        """将问题列表分割成多个批次"""
        batches = []
        for i in range(0, len(issues), max_per_batch):
            batches.append(issues[i:i + max_per_batch])
        return batches
    
    def _create_batch_feedback(
        self,
        issue_batch: List[Dict[str, Any]],
        original_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """为当前批次创建反馈对象"""
        batch_feedback = {
            "pedagogical_issues": [],
            "logical_issues": [],
            "missing_concepts": [],
            "requires_revision": True
        }
        
        for issue in issue_batch:
            issue_type = issue.get("issue_type", "pedagogical")
            
            if issue_type == "pedagogical":
                if issue.get("category") == "missing_concept":
                    # 恢复为concept格式
                    concept_data = issue.get("concept_data")
                    if concept_data:
                        batch_feedback["missing_concepts"].append(concept_data)
                    else:
                        # 如果没有原始数据，创建一个
                        batch_feedback["missing_concepts"].append({
                            "concept": issue.get("problem", "").replace("缺失概念: ", ""),
                            "why_needed": issue.get("suggestion", ""),
                            "where_to_add": issue.get("location", "")
                        })
                else:
                    batch_feedback["pedagogical_issues"].append(issue)
            elif issue_type == "logical":
                batch_feedback["logical_issues"].append(issue)
        
        return batch_feedback

    def _build_step_revision_prompt(
        self,
        step: Dict[str, Any],
        modifications: List[Dict[str, Any]],
        fields_to_revise: set,
        package_context: Dict[str, Any],
        goal_description: str,
        revision_aggressiveness: str = "moderate"
    ) -> str:
        """构建单个step修改的prompt"""
        # 列出需要修改的问题
        issues_text = []
        critical_count = 0
        major_count = 0
        for idx, mod in enumerate(modifications, 1):
            severity = mod.get('severity', 'minor').upper()
            category = mod.get('category', 'unknown')
            problem = mod.get('problem', '')
            suggestion = mod.get('suggestion', '暂无建议')
            
            if severity == 'CRITICAL':
                critical_count += 1
            elif severity == 'MAJOR':
                major_count += 1
            
            issues_text.append(f"\n### 修改意见 {idx}:")
            issues_text.append(f"**严重程度**: {severity}")
            issues_text.append(f"**类别**: {category}")
            issues_text.append(f"**问题**: {problem}")
            issues_text.append(f"**建议**: {suggestion}")
            if mod.get("example_fix"):
                issues_text.append(f"**示例**: {mod['example_fix']}")
        
        # 当前step的内容
        step_info = f"""
**Step Number**: {step.get('step_number', 'N/A')}
**Component Name**: {step.get('component_name', '')}
**File Path**: {step.get('file_path', '')}
**Purpose**: {step.get('purpose', '')}
"""
        
        fields_content = {}
        if "explanation" in fields_to_revise:
            fields_content["explanation"] = step.get('explanation', '')
        if "code" in fields_to_revise:
            fields_content["code"] = step.get('code', '')
        if "purpose" in fields_to_revise:
            fields_content["purpose"] = step.get('purpose', '')
        
        prompt = f"""You are a engineering and education researcher who is now revising a SINGLE implementation step to address specific feedback.

# Research Goal
{goal_description}

# Package Context
**Title**: {package_context.get('package_title', '')}
**Overview**: {package_context.get('overview', '')[:200]}...

# Current Step to Revise
{step_info}

# Current Content (Fields to Revise)
{chr(10).join([f"**{field.upper()}**:{chr(10)}{content[:500]}..." if len(str(content)) > 500 else f"**{field.upper()}**:{chr(10)}{content}" for field, content in fields_content.items()])}

---

# ⚠️ Specific Issues to Fix

You need to revise ONLY the following field(s): {', '.join(fields_to_revise)}

{chr(10).join(issues_text)}

**STRICT PROHIBITION / 严格禁止**: 在修改后的内容中 **绝对不要** 提及“修改意见”“审稿人”“issue”“comment”等字样，也不要引用任何编号（例如“修改意见 #9”）。生成的文本必须面向学习者，好像这些审稿记录从未存在。

---

# Your Revision Task

{f"**⚠️ AGGRESSIVE REVISION MODE**: This step has {critical_count} CRITICAL and {major_count} MAJOR issues. You MUST make SUBSTANTIAL changes to fully address these problems. Do not be conservative - rewrite the content if necessary to completely solve the issues." if revision_aggressiveness == "aggressive" else "**CRITICAL**: You are making a revision to address the issues above."}

## Revision Strategy:
{f"- **For CRITICAL/MAJOR issues**: Make SUBSTANTIAL changes. Rewrite entire sections if needed. Do not just make minor tweaks." if revision_aggressiveness == "aggressive" else "- **For all issues**: Make sufficient changes to fully address each problem."}
- **Modify the field(s)**: {', '.join(fields_to_revise)}
- **Keep other fields unchanged**: step_number, component_name, file_path, etc.

## What to Do:
1. **Read each issue carefully** - understand what is wrong and why
2. **Apply the suggested fixes COMPLETELY** - do not partially address issues
3. **Make changes that FULLY resolve the problems** - if the current content is fundamentally flawed, rewrite it
4. **Ensure the revised content is correct, clear, and complete**
{f"5. **For CRITICAL issues**: You may need to significantly restructure or rewrite the content. This is acceptable and expected." if revision_aggressiveness == "aggressive" else "5. **Maintain consistency** with the rest of the step where possible"}

## For Each Field to Revise:
- Read the current content carefully
- Identify what is wrong based on the issues
- **Make sufficient changes to fully address ALL issues** - do not leave problems partially fixed
- If the current approach is wrong, change it completely
- Ensure the revised content is correct and complete

---

# Output Requirements

Return ONLY the revised field(s). Do NOT return unchanged fields.
All code must remain COMPLETE and RUNNABLE (no placeholders).
**MANDATORY: If revising 'explanation' or 'purpose' fields, they MUST be written in Chinese (中文).**
"""
        return prompt
    
    def _build_step_revision_schema(self, fields_to_revise: set) -> Dict[str, Any]:
        """构建step修改的schema（只包含需要修改的字段）"""
        properties = {}
        
        if "explanation" in fields_to_revise:
            properties["explanation"] = {
                "type": "string",
                "description": "Revised detailed explanation"
            }
        if "code" in fields_to_revise:
            properties["code"] = {
                "type": "string",
                "description": "Revised complete code"
            }
        if "purpose" in fields_to_revise:
            properties["purpose"] = {
                "type": "string",
                "description": "Revised purpose description"
            }
        
        return {
            "type": "object",
            "properties": properties,
            "required": list(fields_to_revise)
        }
    
    def _build_step_revision_system_prompt(self, fields_to_revise: set, revision_aggressiveness: str = "moderate") -> str:
        """构建step修改的系统prompt"""
        fields_str = ', '.join(fields_to_revise)
        chinese_note = ""
        if "explanation" in fields_to_revise or "purpose" in fields_to_revise:
            chinese_note = " **MANDATORY: If revising 'explanation' or 'purpose' fields, they MUST be written in Chinese (中文).**"
        
        base_prompt = f"You are an expert technical educator making revisions to address specific feedback. "
        base_prompt += f"You are revising the following field(s): {fields_str}. "
        
        if revision_aggressiveness == "aggressive":
            base_prompt += (
                f"**IMPORTANT**: The issues are CRITICAL or MAJOR. You MUST make SUBSTANTIAL changes to fully resolve them. "
                f"Do not be conservative - if the current content is wrong or insufficient, rewrite it completely. "
                f"Partial fixes are not acceptable for critical issues. "
            )
        else:
            base_prompt += (
                f"Make sufficient changes to fully address all feedback. "
                f"Keep other fields unchanged. "
            )
        
        base_prompt += f"Apply the suggested fixes completely.{chinese_note}"
        return base_prompt
    
    def _build_non_step_revision_prompt(
        self,
        package: Dict[str, Any],
        modifications: List[Dict[str, Any]],
        fields_to_revise: set,
        goal_description: str
    ) -> str:
        """构建非step字段修改的prompt"""
        issues_text = []
        for idx, mod in enumerate(modifications, 1):
            severity = mod.get('severity', 'minor').upper()
            category = mod.get('category', 'unknown')
            location = mod.get('location', '')
            problem = mod.get('problem', '')
            suggestion = mod.get('suggestion', '暂无建议')
            
            issues_text.append(f"\n### 修改意见 {idx}:")
            issues_text.append(f"**位置**: {location}")
            issues_text.append(f"**严重程度**: {severity}")
            issues_text.append(f"**类别**: {category}")
            issues_text.append(f"**问题**: {problem}")
            issues_text.append(f"**建议**: {suggestion}")
        
        current_content = {}
        for field in fields_to_revise:
            current_content[field] = package.get(field, '')
        
        prompt = f"""You are revising specific fields of a package to address feedback.

# Research Goal
{goal_description}

# Package Title
{package.get('package_title', '')}

# Current Content (Fields to Revise)
{chr(10).join([f"**{field.upper()}**:{chr(10)}{content[:800]}..." if len(str(content)) > 800 else f"**{field.upper()}**:{chr(10)}{content}" for field, content in current_content.items()])}

---

# ⚠️ Specific Issues to Fix

You need to revise ONLY the following field(s): {', '.join(fields_to_revise)}

{chr(10).join(issues_text)}

**STRICT PROHIBITION / 严格禁止**: 在所有修改后的内容中 **绝对不要** 出现“修改意见”“审稿人”“issue”“comment”等字样，也不要引用任何编号（例如“修改意见 #9”）。输出必须面向最终读者，仿佛这些审稿记录从未存在。

---

# Your Revision Task

**CRITICAL**: Only modify the specified field(s). Keep all other package content unchanged.

Apply the suggested fixes while maintaining consistency with the rest of the package.
"""
        return prompt
    
    def _build_non_step_revision_schema(self, fields_to_revise: set) -> Dict[str, Any]:
        """构建非step字段修改的schema"""
        properties = {}
        
        if "overview" in fields_to_revise:
            properties["overview"] = {
                "type": "string",
                "description": "Revised overview"
            }
        if "theoretical_foundation" in fields_to_revise:
            properties["theoretical_foundation"] = {
                "type": "string",
                "description": "Revised theoretical foundation"
            }
        if "project_structure" in fields_to_revise:
            properties["project_structure"] = {
                "type": "string",
                "description": "Revised project structure"
            }
        
        return {
            "type": "object",
            "properties": properties,
            "required": list(fields_to_revise)
        }
    
    def _build_single_revision_prompt(
        self,
        package: Dict[str, Any],
        issue_batch: List[Dict[str, Any]],
        batch_feedback: Dict[str, Any],
        cross_issues: List[Dict[str, Any]],
        goal_description: str,
        revision_num: int,
        total_revisions: int
    ) -> str:
        """
        构建单个修改意见的prompt（聚焦处理少量修改意见）
        
        每次只处理1-2个修改意见，让模型更聚焦
        """
        # 详细列出当前要处理的修改意见
        issues_to_fix = []
        for idx, issue in enumerate(issue_batch, 1):
            if not isinstance(issue, dict):
                continue
            
            issue_type = issue.get("issue_type", "unknown")
            severity = issue.get('severity', 'minor').upper()
            category = issue.get('category', 'unknown')
            location = issue.get('location', 'unknown')
            problem = issue.get('problem', '')
            suggestion = issue.get('suggestion', '暂无建议')
            
            issue_desc = f"\n### 修改意见 {idx}:\n"
            issue_desc += f"**类型**: {issue_type} ({severity})\n"
            issue_desc += f"**类别**: {category}\n"
            issue_desc += f"**位置**: {location}\n"
            issue_desc += f"**问题**: {problem}\n"
            issue_desc += f"**建议**: {suggestion}\n"
            
            if issue.get("example_fix"):
                issue_desc += f"**示例**: {issue['example_fix']}\n"
            
            issues_to_fix.append(issue_desc)
        
        # 缺失概念
        missing_concepts_text = []
        for concept in batch_feedback.get("missing_concepts", []):
            if isinstance(concept, dict):
                missing_concepts_text.append(f"\n- **{concept.get('concept', '')}**")
                missing_concepts_text.append(f"  原因: {concept.get('why_needed', '')}")
                missing_concepts_text.append(f"  添加位置: {concept.get('where_to_add', '')}")
                if concept.get("suggested_explanation"):
                    missing_concepts_text.append(f"  建议解释: {concept.get('suggested_explanation', '')}")
        
        # 跨package问题
        cross_issues_text = []
        for issue in cross_issues:
            if isinstance(issue, dict):
                cross_issues_text.append(f"\n- **{issue.get('issue_type', '')}**")
                cross_issues_text.append(f"  问题: {issue.get('problem', '')}")
                cross_issues_text.append(f"  建议: {issue.get('suggestion', '暂无建议')}")
        
        prompt = f"""You are revising a technical tutorial package to address SPECIFIC feedback items.

# Research Goal
{goal_description}

# Current Package (may have been partially revised)
**Title**: {package.get('package_title', '')}
**Overview**: {package.get('overview', '')}

---

# ⚠️ FOCUS: Specific Issues to Fix (Revision {revision_num}/{total_revisions})

You need to address ONLY the following {len(issue_batch)} specific issue(s):

{chr(10).join(issues_to_fix)}

{"## Missing Concepts to Add:" if missing_concepts_text else ""}
{chr(10).join(missing_concepts_text) if missing_concepts_text else ""}

{"## Cross-Package Considerations:" if cross_issues_text else ""}
{chr(10).join(cross_issues_text) if cross_issues_text else ""}

---

# Your Revision Task

⚠️ **CRITICAL**: You MUST strictly follow and implement ALL feedback items listed above. Partial compliance is NOT acceptable. Every issue must be FULLY addressed.

**IMPORTANT**: You are making a FOCUSED revision. Only modify the parts of the package that address the specific issues listed above, but make sure you address ALL of them COMPLETELY.

## What to Do:
1. **Locate the specific sections** mentioned in the issues (e.g., "{issue_batch[0].get('location', 'unknown') if issue_batch else 'unknown'}")
2. **Apply the suggested fixes** for EVERY issue listed above
3. **Follow the specific suggestions** provided for each issue
4. **Use example fixes** if provided as a reference
5. **Keep everything else unchanged** unless it's directly related to the fixes
6. **Maintain consistency** with the rest of the package

## For Each Issue (MANDATORY):
- Read the problem description carefully
- Understand the specific suggestion provided
- Apply the suggested fix COMPLETELY (not partially)
- If an example is provided, use it as a reference
- Ensure the fix integrates smoothly with existing content
- Verify that the issue is FULLY resolved in your revision

⚠️ **VERIFICATION**: Before finalizing, check that you have addressed EVERY issue above. If you skip any issue, your revision is incomplete.

---

# Critical Requirements - **MANDATORY**

- ⚠️ **MUST address ALL issues** listed above (partial compliance is unacceptable)
- **ONLY modify** the parts mentioned in the issues above
- **Keep all other content** exactly as it is
- ALL code must remain **COMPLETE and RUNNABLE** (no placeholders)
- Maintain the overall structure and flow
- Ensure changes are consistent with the rest of the package
- **Follow specific suggestions** - do not create your own fixes if suggestions are provided

Generate the REVISED package with ALL specific issues FULLY addressed.
"""
        return prompt

    def _build_single_revision_system_prompt(self, revision_num: int, total_revisions: int) -> str:
        """单个修改意见的系统prompt"""
        batch_note = ""
        if total_revisions > 1:
            batch_note = f"\n\n⚠️ FOCUSED REVISION: You are working on revision {revision_num} of {total_revisions}. Address ONLY the specific issues provided. Keep everything else unchanged."
        
        return (
            "You are an expert technical educator and software engineer. "
            "You're making a FOCUSED revision to address specific feedback items. "
            "\n\n"
            "⚠️ CRITICAL: You MUST fully comply with ALL feedback items provided. "
            "Every issue must be addressed COMPLETELY, not partially. "
            "Skipping or partially addressing issues is NOT acceptable. "
            "\n\n"
            "Your approach (MANDATORY):\n"
            "1. Read each issue and its suggestion carefully\n"
            "2. Identify the exact locations mentioned in the issues\n"
            "3. Apply the suggested fixes PRECISELY and COMPLETELY for EVERY issue\n"
            "4. Use example fixes if provided as your reference\n"
            "5. Keep all other content unchanged\n"
            "6. Ensure fixes integrate smoothly\n"
            "7. Verify that ALL issues are fully addressed before finalizing\n"
            "\n"
            "Be surgical and precise. Only modify what needs to be fixed, "
            "but ensure EVERY issue is FULLY fixed. Full compliance is mandatory."
            + batch_note
        )

    def _build_dual_feedback_revision_prompt(
        self,
        package: Dict[str, Any],
        feedback: Dict[str, Any],
        cross_issues: List[Dict[str, Any]],
        goal_description: str,
        batch_num: int = 1,
        total_batches: int = 1
    ) -> str:
        """构建基于双审稿人反馈的修改prompt（支持分批处理）"""
        
        # 整理教学性问题
        ped_issues_text = []
        for issue in feedback.get("pedagogical_issues", []):
            if not isinstance(issue, dict):
                continue
            severity = issue.get('severity', 'minor').upper()
            category = issue.get('category', 'unknown')
            location = issue.get('location', 'unknown')
            problem = issue.get('problem', '')
            suggestion = issue.get('suggestion', '')
            
            ped_issues_text.append(f"\n**[{severity}] {category}** @ {location}")
            ped_issues_text.append(f"- 问题: {problem}")
            if suggestion:
                ped_issues_text.append(f"- 建议: {suggestion}")
            if issue.get("example_fix"):
                ped_issues_text.append(f"- 示例: {issue['example_fix']}")
        
        # 整理逻辑性问题
        logic_issues_text = []
        for issue in feedback.get("logical_issues", []):
            if not isinstance(issue, dict):
                continue
            severity = issue.get('severity', 'minor').upper()
            category = issue.get('category', 'unknown')
            location = issue.get('location', 'unknown')
            problem = issue.get('problem', '')
            suggestion = issue.get('suggestion', '')
            
            logic_issues_text.append(f"\n**[{severity}] {category}** @ {location}")
            logic_issues_text.append(f"- 问题: {problem}")
            if suggestion:
                logic_issues_text.append(f"- 建议: {suggestion}")
        
        # 整理缺失概念
        missing_concepts_text = []
        for concept in feedback.get("missing_concepts", []):
            # 处理两种情况：字典对象或字符串
            if isinstance(concept, dict):
                missing_concepts_text.append(f"\n- **{concept.get('concept', '')}**")
                missing_concepts_text.append(f"  原因: {concept.get('why_needed', '')}")
                missing_concepts_text.append(f"  添加位置: {concept.get('where_to_add', '')}")
                if concept.get("suggested_explanation"):
                    missing_concepts_text.append(f"  建议解释: {concept.get('suggested_explanation', '')}")
            elif isinstance(concept, str):
                # 如果是字符串，直接使用
                missing_concepts_text.append(f"\n- **{concept}**")
            else:
                # 其他类型，转换为字符串
                missing_concepts_text.append(f"\n- **{str(concept)}**")
        
        # 相关的跨package问题
        relevant_cross_issues = []
        if isinstance(cross_issues, list):
            relevant_cross_issues = [
                issue for issue in cross_issues
                if isinstance(issue, dict) and package.get("action_index") in issue.get("affected_packages", [])
            ]
        
        cross_issues_text = []
        for issue in relevant_cross_issues:
            if isinstance(issue, dict):
                cross_issues_text.append(f"\n- **{issue.get('issue_type', '')}**")
                cross_issues_text.append(f"  问题: {issue.get('problem', '')}")
                cross_issues_text.append(f"  建议: {issue.get('suggestion', '暂无建议')}")
        
        # 批次信息
        batch_info = ""
        if total_batches > 1:
            batch_info = f"""
    # ⚠️ IMPORTANT: Batch Processing
    This is batch {batch_num} of {total_batches} batches.
    You are currently addressing a SUBSET of the total issues.
    Focus ONLY on the issues listed below in this batch.
    The package will be revised in multiple rounds to address all issues.
    
    """
        
        prompt = f"""You are revising a technical tutorial package based on feedback from TWO expert reviewers.
{batch_info}
    # Research Goal
    {goal_description}

    # Current Package (may have been partially revised in previous batches)
    **Title**: {package.get('package_title', '')}
    **Overview**: {package.get('overview', '')}

    ---

    # Feedback from Pedagogical Reviewer (Batch {batch_num}/{total_batches})

    **Summary**: {feedback.get('pedagogical_summary', '')}

    ## Teaching Quality Issues
    {chr(10).join(ped_issues_text) if ped_issues_text else "No pedagogical issues."}

    ## Missing Concepts to Add
    {chr(10).join(missing_concepts_text) if missing_concepts_text else "No missing concepts."}

    ---

    # Feedback from Logical Coherence Reviewer

    **Summary**: {feedback.get('logical_summary', '')}

    ## Logical Structure Issues
    {chr(10).join(logic_issues_text) if logic_issues_text else "No logical issues."}

    {"---" if cross_issues_text else ""}
    {"# Cross-Package Considerations" if cross_issues_text else ""}
    {chr(10).join(cross_issues_text) if cross_issues_text else ""}

    ---

    # Your Revision Task (Batch {batch_num}/{total_batches})

    ⚠️ **CRITICAL**: You MUST strictly follow and implement ALL feedback from the reviewers above. Do NOT skip or partially address any issues. Each issue listed above must be fully resolved.

    Focus on addressing the issues listed above in this batch.{" Since this is part of a multi-batch revision, maintain consistency with previous changes." if batch_num > 1 else ""}
    
    ## From Pedagogical Reviewer (Teaching Quality) - **MUST ADDRESS ALL ISSUES**
    
    **⚠️ IMPORTANT**: The Pedagogical Reviewer has identified specific teaching quality issues. You MUST:
    1. **Address EVERY issue listed above** in the "Teaching Quality Issues" section
    2. **Add EVERY missing concept** listed in the "Missing Concepts to Add" section
    3. **Follow the specific suggestions** provided for each issue
    4. **Use the example fixes** if provided
    
    Specific actions required:

    1. **Add missing concept explanations** (for all concepts listed above)
    - Define technical terms when first used
    - Add background explanations for assumed knowledge
    - Include examples and analogies
    - Add step-by-step explanations for complex operations (be more detailed)
    - **Use the suggested explanations** if provided

    2. **Improve code clarity** (for all issues related to code)
    - Add more detailed code comments
    - Explain complex logic in plain language
    - Use clearer variable names if needed
    - **Follow the specific suggestions** for each code-related issue

    3. **Smooth learning curve** (for all progression issues)
    - Break down complex steps
    - Add transitional explanations
    - Provide more examples
    - **Address each specific issue** mentioned in the feedback

    ## From Logical Coherence Reviewer (Structure & Flow)

    1. **Fix logical flow**
    - Reorder steps if needed
    - Fill logical gaps
    - Clarify dependencies

    2. **Ensure consistency**
    - Use terminology consistently
    - Align naming across components
    - Remove contradictions

    3. **Improve structure**
    - Make relationships explicit
    - Clarify component interactions
    - Fix architectural issues

    ---

    # Critical Requirements - **MANDATORY**

    ⚠️ **VERIFICATION CHECKLIST**: Before finalizing your revision, verify:
    - ✅ Have you addressed ALL pedagogical issues listed above?
    - ✅ Have you added ALL missing concepts listed above?
    - ✅ Have you followed the specific suggestions for each issue?
    - ✅ Have you used the example fixes if provided?
    - ✅ Is your revision comprehensive, not partial?

    - ALL code must remain **COMPLETE and RUNNABLE** (no placeholders, no "...")
    - **Address EVERY specific suggestion** from both reviewers (do not skip any)
    - Add **explanatory comments** in code where clarification is needed
    - Maintain or improve existing strengths
    - Keep overall structure intact unless reviewers suggest major changes
    - **Partial compliance is not acceptable** - fully address all feedback

    Generate the REVISED package that is **both beginner-friendly AND logically sound**, with ALL reviewer feedback fully addressed.
    """
        
        return prompt

    def _build_dual_feedback_revision_system_prompt(self, batch_num: int = 1, total_batches: int = 1) -> str:
        """双审稿人修改的系统prompt（支持分批处理）"""
        batch_note = ""
        if total_batches > 1:
            batch_note = f"\n\n⚠️ BATCH PROCESSING: You are working on batch {batch_num} of {total_batches}. Focus on the issues in this batch only. Maintain consistency with previous batches if any."
        
        return (
            "You are an expert technical educator and software engineer. "
            "You're revising content based on feedback from TWO expert reviewers: "
            "one focused on teaching quality, one focused on logical coherence. "
            "\n\n"
            "⚠️ CRITICAL: You MUST strictly comply with ALL feedback from the reviewers. "
            "Partial compliance or skipping issues is NOT acceptable. "
            "Every issue, every suggestion, and every missing concept MUST be fully addressed. "
            "\n\n"
            "Your goals (in priority order):\n"
            "1. **MUST**: Address EVERY pedagogical issue and add EVERY missing concept suggested by the Pedagogical Reviewer\n"
            "2. **MUST**: Fix EVERY logical issue identified by the Logical Coherence Reviewer\n"
            "3. Make content more detailed, clearer and more accessible for learners\n"
            "4. Improve logical structure and flow\n"
            "5. Ensure all code is well-commented and understandable\n"
            "\n\n"
            "⚠️ COMPLIANCE REQUIREMENTS:\n"
            "- Read each issue carefully and address it COMPLETELY\n"
            "- Use the specific suggestions provided\n"
            "- Follow example fixes if provided\n"
            "- Do NOT skip any issues, even if they seem minor\n"
            "- Verify that your revision fully addresses all feedback before finalizing\n"
            "\n\n"
            "Balance pedagogical clarity with logical rigor. "
            "Be THOROUGH and COMPREHENSIVE in addressing all feedback points in the current batch. "
            "Full compliance is mandatory."
            + batch_note
        )