"""
Logical Coherence Reviewer Agent - 逻辑连贯性审稿人
专注于内容的逻辑结构和章节间的连贯性
"""

import logging
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class LogicalCoherenceReviewerAgent(BaseAgent):
    """
    逻辑连贯性审稿人 - 确保章节之间逻辑流畅，结构合理
    """

    def __init__(self, model, config: Dict[str, Any]):
        super().__init__(model, config)
        self.reviewer_name = config.get("reviewer_name", "Logical Coherence Reviewer")
        self.min_coherence_score = config.get("min_coherence_score", 7.0)

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行逻辑连贯性审查
        
        关注点：
        1. 章节内部的逻辑流程
        2. 章节之间的逻辑关系
        3. 依赖关系是否清晰
        4. 前后内容是否一致
        5. 整体结构是否合理
        """
        engineering_plan = context.get("engineering_plan")
        if not engineering_plan:
            raise AgentExecutionError("需要 engineering_plan")

        review_round = context.get("review_round", 1)
        logger.info(f"[{self.reviewer_name}] 开始第 {review_round} 轮逻辑审查...")

        packages = engineering_plan.get("project_packages", [])
        
        # 审查每个package的内部逻辑
        package_reviews = []
        for idx, package in enumerate(packages, 1):
            if package.get("status") != "success":
                continue
            
            logger.info(f"  审查 Package {idx} 内部逻辑...")
            review = await self._review_package_logic(package, idx, params)
            package_reviews.append(review)

        # 审查packages之间的逻辑关系
        logger.info("  审查跨Package逻辑连贯性...")
        cross_package_review = await self._review_cross_package_logic(packages, params)

        overall_assessment = self._generate_overall_assessment(package_reviews, cross_package_review)

        return {
            "reviewer_type": "logical_coherence",
            "reviewer_name": self.reviewer_name,
            "review_round": review_round,
            "package_reviews": package_reviews,
            "cross_package_review": cross_package_review,
            "overall_assessment": overall_assessment,
            "requires_revision": self._check_revision_needed(overall_assessment)
        }

    async def _review_package_logic(
        self,
        package: Dict[str, Any],
        package_index: int,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审查单个package的内部逻辑"""
        
        prompt = self._build_logic_prompt(package, package_index)
        schema = self._build_logic_schema()

        try:
            response = await self._call_model(
                prompt=prompt,
                system_prompt=self._build_system_prompt(),
                schema=schema,
                temperature=0.3
            )

            response["package_index"] = package_index
            response["package_title"] = package.get("package_title", f"Package {package_index}")
            
            return response

        except Exception as exc:
            logger.error(f"逻辑审查失败: {exc}")
            raise

    def _build_logic_prompt(self, package: Dict[str, Any], package_index: int) -> str:
        """构建逻辑审查prompt"""
        
        title = package.get("package_title", "")
        overview = package.get("overview", "")
        structure = package.get("project_structure", "")
        theory = package.get("theoretical_foundation", "")
        concepts = package.get("concept_explanations", [])
        steps = package.get("implementation_steps", [])
        
        # 提取步骤流程
        step_flow = []
        for i, step in enumerate(steps, 1):
            step_flow.append(f"{i}. **{step.get('component_name', '')}** (`{step.get('file_path', '')}`)")
            step_flow.append(f"   Purpose: {step.get('purpose', '')[:120]}")
        
        # 提取概念列表
        concept_list = []
        for concept in concepts:
            if isinstance(concept, dict):
                concept_name = concept.get('concept_name', 'Unknown')
                related = concept.get('related_concepts', [])
                concept_list.append(f"- **{concept_name}**" + (f" (related to: {', '.join(related)})" if related else ""))
        
        prompt = f"""You are reviewing a technical tutorial package for **logical coherence** and **structural soundness**.

# Package to Review

## Package {package_index}: {title}

**Overview**: {overview}

**Project Structure**:
```
{structure}
```

**Theoretical Foundation**:
{theory[:600]}...

{"**Concept Explanations**:" if concept_list else ""}
{chr(10).join(concept_list) if concept_list else "No concept explanations provided."}

**Implementation Flow** ({len(steps)} steps):
{chr(10).join(step_flow)}

---

# Your Review Task

Evaluate the **logical structure and flow** within this package:

## 1. Sequential Logic
- Do steps follow a **logical order**?
- Is there a natural progression from simple to complex?
- Are any steps out of order or misplaced?
- Should any steps come earlier or later?

## 2. Dependencies & Relationships
- Are dependencies between components **clearly stated**?
- Does each step properly build on previous steps?
- Are there missing intermediate steps?
- Are circular dependencies present?

## 3. Concept Explanations Logic & Consistency
**Evaluate the "Concept Explanations" section for logical coherence:**
- Are concepts explained in a **logical order** (prerequisites before dependent concepts)?
- Do the **related concepts** listed make sense and are relationships clear?
- Are there **contradictions** between how concepts are explained in different places?
- Are concepts used **consistently** between the concept explanations and implementation steps?
- Do the concept explanations **align with** how concepts are used in the code?
- Are there **missing connections** between related concepts?
- Is the **sequence of concept explanations** logical (simple to complex)?

## 4. Internal Consistency
- Are concepts used **consistently** throughout the package?
- Do variable/function names align with descriptions?
- Are there any **contradictions** in approach or terminology?
- Is the naming convention consistent?

## 5. Completeness of Logic
- Are all concepts used in implementation steps **explained in the Concept Explanations section**?
- Are all referenced components actually implemented?
- Are there **logical gaps** in the implementation chain?
- Are assumptions clearly stated?
- Are there missing connections between concepts and their usage?

## 6. Structural Clarity
- How do components relate to each other?
- Are data flows clear and explicit?
- Are control flows well-defined?
- Is the overall architecture coherent?

---

# Output Requirements

For each logical issue:
- **Be specific**: Cite exact steps or components
- **Explain the problem**: What is the logical flaw?
- **Suggest the fix**: How to improve the logical flow?
- **Consider dependencies**: How does this affect other parts?

Focus on ensuring a clear, logical progression that makes sense.
"""
        
        return prompt

    def _build_logic_schema(self) -> Dict[str, Any]:
        """逻辑审查输出schema"""
        return {
            "type": "object",
            "properties": {
                "coherence_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Internal logical coherence score (1-10)"
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 4,
                    "description": "Logical strengths (2-4 items)"
                },
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [
                                    "wrong_order",
                                    "missing_step",
                                    "logical_gap",
                                    "circular_dependency",
                                    "inconsistent_naming",
                                    "unclear_relationship",
                                    "contradiction",
                                    "missing_dependency_declaration"
                                ]
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "major", "minor"]
                            },
                            "location": {
                                "type": "string",
                                "description": "Where the logical issue occurs (specific step or component)"
                            },
                            "problem": {
                                "type": "string",
                                "description": "Description of the logical problem"
                            },
                            "suggestion": {
                                "type": "string",
                                "description": "How to fix the logical flow"
                            }
                        },
                        "required": ["category", "severity", "location", "problem", "suggestion"]
                    }
                },
                "requires_revision": {
                    "type": "boolean",
                    "description": "Whether logical improvements are needed"
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 sentence summary of logical coherence"
                }
            },
            "required": ["coherence_score", "strengths", "issues", "requires_revision", "summary"]
        }

    async def _review_cross_package_logic(
        self,
        packages: List[Dict[str, Any]],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审查packages之间的逻辑关系"""
        
        # 提取各package的摘要信息
        package_summaries = []
        for idx, pkg in enumerate(packages, 1):
            if pkg.get("status") == "success":
                package_summaries.append({
                    "index": idx,
                    "title": pkg.get("package_title", ""),
                    "overview": pkg.get("overview", "")[:200],
                    "action_item": pkg.get("action_item", "")[:150]
                })

        if len(package_summaries) < 2:
            # 只有一个package，没有跨包问题
            return {
                "overall_coherence_score": 10,
                "issues": [],
                "suggested_reordering": [],
                "summary": "Single package - no cross-package issues."
            }

        prompt = self._build_cross_package_prompt(package_summaries)
        schema = self._build_cross_package_schema()

        try:
            response = await self._call_model(
                prompt=prompt,
                system_prompt=self._build_system_prompt(),
                schema=schema,
                temperature=0.3
            )
            return response
        except Exception as exc:
            logger.error(f"跨Package逻辑审查失败: {exc}")
            return {
                "overall_coherence_score": 7,
                "issues": [],
                "suggested_reordering": [],
                "summary": "Cross-package review failed."
            }

    def _build_cross_package_prompt(self, package_summaries: List[Dict[str, Any]]) -> str:
        """构建跨package审查prompt"""
        
        summaries_text = []
        for pkg in package_summaries:
            summaries_text.append(f"\n### Package {pkg['index']}: {pkg['title']}")
            summaries_text.append(f"**Action**: {pkg['action_item']}")
            summaries_text.append(f"**Overview**: {pkg['overview']}")
        
        prompt = f"""You are reviewing the **logical connections and flow between multiple packages** in a research implementation project.

# All Packages ({len(package_summaries)} total)

{chr(10).join(summaries_text)}

---

# Your Review Task

Evaluate the **logical coherence across packages**:

## 1. Sequential Logic & Order
- Do packages build on each other logically?
- Is the order of packages sensible?
- Should any packages be **reordered**?
- Is there a natural progression?

## 2. Inter-Package Dependencies
- Are connections between packages clear?
- Does Package N properly reference outputs from Package N-1?
- Are there **missing connections** or handoffs?
- Are interfaces between packages well-defined?

## 3. Consistency Across Packages
- Are naming conventions **consistent**?
- Are similar concepts explained consistently?
- Is the overall technical approach coherent?
- Are there conflicting methodologies?

## 4. Completeness of Workflow
- Are there **gaps** in the overall workflow?
- Do packages collectively address the research goal?
- Are transitions between packages smooth?
- Are there missing intermediate packages?

## 5. Redundancy & Efficiency
- Is there unnecessary **duplication** across packages?
- Could any packages be merged?
- Are there overlapping responsibilities?
- Is the division of work logical?

---

# Output Requirements

- Identify cross-package logical issues
- If reordering would improve flow, suggest the new order
- Be specific about which packages are affected
- Explain how to improve the overall structure
"""
        
        return prompt

    def _build_cross_package_schema(self) -> Dict[str, Any]:
        """跨package审查schema"""
        return {
            "type": "object",
            "properties": {
                "overall_coherence_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall cross-package coherence score (1-10)"
                },
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "affected_packages": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Package indices involved in this issue"
                            },
                            "issue_type": {
                                "type": "string",
                                "enum": [
                                    "wrong_sequence",
                                    "missing_connection",
                                    "inconsistent_approach",
                                    "redundant_content",
                                    "gap_in_workflow",
                                    "unclear_handoff"
                                ]
                            },
                            "problem": {
                                "type": "string",
                                "description": "Description of the cross-package issue"
                            },
                            "suggestion": {
                                "type": "string",
                                "description": "How to improve the overall structure"
                            }
                        },
                        "required": ["affected_packages", "issue_type", "problem", "suggestion"]
                    }
                },
                "suggested_reordering": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Suggested package order if reordering needed (empty array if current order is good)"
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 sentence summary of cross-package coherence"
                }
            },
            "required": ["overall_coherence_score", "issues", "suggested_reordering", "summary"]
        }

    def _build_system_prompt(self) -> str:
        """系统prompt"""
        return """You are an expert technical editor, systems architect, and logical reasoning specialist.

**Your expertise**:
- Identifying logical inconsistencies and structural flaws
- Spotting missing connections and dependencies
- Ensuring proper information flow
- Detecting circular reasoning
- Improving structural coherence
- Evaluating architectural soundness

**Your approach**:
- Think like an architect: Does the structure make sense?
- Follow the logic: Is each step justified by previous ones?
- Check consistency: Are concepts used uniformly?
- Identify gaps: What's missing in the logical chain?
- Be precise and constructive

Your goal: Ensure the content has rock-solid logical structure and flow."""

    def _generate_overall_assessment(
        self,
        package_reviews: List[Dict[str, Any]],
        cross_package_review: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成总体评估"""
        if not package_reviews:
            return {
                "average_internal_coherence": 0,
                "cross_package_coherence": 0,
                "total_internal_issues": 0,
                "total_cross_package_issues": 0,
                "packages_needing_revision": 0
            }
        
        avg_internal = sum(r["coherence_score"] for r in package_reviews) / len(package_reviews)
        cross_score = cross_package_review.get("overall_coherence_score", 0)
        
        internal_issues = sum(len(r.get("issues", [])) for r in package_reviews)
        cross_issues = len(cross_package_review.get("issues", []))
        
        needs_revision = sum(1 for r in package_reviews if r.get("requires_revision"))
        
        return {
            "average_internal_coherence": round(avg_internal, 1),
            "cross_package_coherence": cross_score,
            "overall_coherence": round((avg_internal + cross_score) / 2, 1),
            "total_internal_issues": internal_issues,
            "total_cross_package_issues": cross_issues,
            "packages_needing_revision": needs_revision,
            "assessment": self._get_assessment_text(avg_internal, cross_score)
        }

    def _get_assessment_text(self, internal: float, cross: float) -> str:
        """生成评估文本"""
        overall = (internal + cross) / 2
        if overall >= 8:
            return "Excellent logical structure. Clear flow and coherence."
        elif overall >= 7:
            return "Good logic overall. Minor improvements possible."
        elif overall >= 5:
            return "Moderate coherence. Some logical issues need addressing."
        else:
            return "Poor logical structure. Significant restructuring required."

    def _check_revision_needed(self, assessment: Dict[str, Any]) -> bool:
        """判断是否需要修改"""
        overall_coherence = assessment.get("overall_coherence", 0)
        return overall_coherence < self.min_coherence_score