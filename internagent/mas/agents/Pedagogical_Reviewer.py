"""
Pedagogical Reviewer Agent - 教学性审稿人
专注于内容的可理解性和教学质量
"""

import logging
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class PedagogicalReviewerAgent(BaseAgent):
    """
    教学性审稿人 - 确保内容通俗易懂，适合初学者
    """

    def __init__(self, model, config: Dict[str, Any]):
        super().__init__(model, config)
        self.reviewer_name = config.get("reviewer_name", "Pedagogical Reviewer")
        self.target_audience = config.get("target_audience", "beginners")
        self.min_clarity_score = config.get("min_clarity_score", 7.0)

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行教学性审查
        
        关注点：
        1. 概念解释是否充分
        2. 术语是否有定义
        3. 代码注释是否足够
        4. 示例是否清晰
        5. 学习曲线是否平滑
        """
        engineering_plan = context.get("engineering_plan")
        if not engineering_plan:
            raise AgentExecutionError("需要 engineering_plan")

        review_round = context.get("review_round", 1)
        logger.info(f"[{self.reviewer_name}] 开始第 {review_round} 轮教学性审查...")

        packages = engineering_plan.get("project_packages", [])
        package_reviews = []

        for idx, package in enumerate(packages, 1):
            if package.get("status") != "success":
                continue
            
            logger.info(f"  审查 Package {idx}: {package.get('package_title', '')[:50]}...")
            review = await self._review_package_pedagogy(package, idx, params)
            package_reviews.append(review)

        overall_assessment = self._generate_overall_assessment(package_reviews)

        return {
            "reviewer_type": "pedagogical",
            "reviewer_name": self.reviewer_name,
            "review_round": review_round,
            "package_reviews": package_reviews,
            "overall_assessment": overall_assessment,
            "requires_revision": overall_assessment["average_clarity_score"] < self.min_clarity_score
        }

    async def _review_package_pedagogy(
        self,
        package: Dict[str, Any],
        package_index: int,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审查单个package的教学质量"""
        
        prompt = self._build_pedagogical_prompt(package, package_index)
        schema = self._build_pedagogical_schema()

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
            logger.error(f"教学性审查失败: {exc}")
            raise

    def _build_pedagogical_prompt(self, package: Dict[str, Any], package_index: int) -> str:
        """构建教学性审查prompt"""
        
        title = package.get("package_title", "")
        overview = package.get("overview", "")
        theory = package.get("theoretical_foundation", "")
        concepts = package.get("concept_explanations", [])
        steps = package.get("implementation_steps", [])
        
        # 提取关键信息
        step_details = []
        for i, step in enumerate(steps[:3], 1):
            step_details.append(f"\n### Step {i}: {step.get('component_name', '')}")
            step_details.append(f"**Purpose**: {step.get('purpose', '')}")
            step_details.append(f"**Explanation**: {step.get('explanation', '')[:300]}...")
            step_details.append(f"**Code snippet**:\n```\n{step.get('code', '')[:400]}...\n```")
        
        # 提取概念解释
        concept_details = []
        for concept in concepts:
            if isinstance(concept, dict):
                concept_name = concept.get('concept_name', 'Unknown')
                explanation = concept.get('explanation', '')
                why_important = concept.get('why_important', '')
                examples = concept.get('examples', [])
                
                concept_details.append(f"\n### Concept: {concept_name}")
                concept_details.append(f"**Explanation** ({len(explanation)} chars): {explanation[:400]}...")
                concept_details.append(f"**Why Important**: {why_important[:200]}...")
                if examples:
                    concept_details.append(f"**Examples**: {len(examples)} examples provided")
        
        prompt = f"""You are a beginner with few artificial intelligence knowledge. You are now reviewing a technical tutorial package for **pedagogical quality** and **beginner-friendliness**.

**Target Audience**: {self.target_audience}

# Package to Review

## Package {package_index}: {title}

**Overview**: {overview}

**Theoretical Foundation**:
{theory[:600]}...

{"**Concept Explanations**:" if concept_details else ""}
{chr(10).join(concept_details) if concept_details else "No concept explanations provided."}

**Sample Implementation Steps**:
{chr(10).join(step_details)}

---

# Your Review Task

Evaluate this package from a **teaching and learning perspective**:

## 1. Concept Explanations Quality (CRITICAL)
**Evaluate the "Concept Explanations" section specifically:**
- Are the explanations **detailed enough** for a complete beginner? (Should be 4-8 paragraphs per concept)
- Do explanations start from the **very basics** (zero prior knowledge assumed)?
- Are complex ideas **broken down** into smaller, digestible parts?
- Are **analogies and examples** provided? Are they clear and helpful?
- Is technical jargon **avoided or fully explained**?
- Can a beginner **follow the entire explanation** without getting lost?
- Are explanations **comprehensive** (covering what, how, why)?
- Are **related concepts** explained and their relationships clear?
- **Is the explanation length sufficient?** (Too brief = major issue)

**If concept explanations are missing or insufficient:**
- Identify which concepts need explanation
- Specify what details are missing
- Suggest how to make explanations more beginner-friendly

## 2. Concept Clarity (General)
- Are concepts explained **before** being used in implementation steps?
- Is technical jargon properly **defined** in the concept explanations?
- Are there any "knowledge gaps" (unexplained jumps) between concepts?
- Are prerequisites clearly stated?

## 3. Code Understandability
- Are code comments **sufficient and helpful**?
- Are variable/function names **self-explanatory**?
- Is the code structure **easy to follow**?
- Are complex operations explained?

## 4. Learning Progression
- Does complexity increase **gradually**?
- Are there clear learning milestones?
- Does each step build logically on the previous?
- Is the learning curve smooth or too steep?

## 5. Examples & Analogies
- Are there enough **concrete examples**?
- Are examples relevant and practical?
- Are there helpful analogies for complex concepts?
- Are edge cases explained?

## 6. Missing Conceptual Support
- **What concepts are used in the implementation but NOT explained in the Concept Explanations section?**
- **What background knowledge is assumed but not stated?**
- **Which concept explanations need to be more detailed?**
- **What additional examples or analogies would help learners?**
- **Where would analogies be useful?**

---

# Output Requirements

For each issue you identify:
- **Be specific**: Cite exact locations (e.g., "Step 4.2", "Overview paragraph 2")
- **Explain the problem**: Why is this confusing for learners?
- **Provide concrete suggestions**: What exactly should be added or changed?
- **Give examples**: Show what a better explanation would look like

Focus on making this content accessible to {self.target_audience}.
"""
        
        return prompt

    def _build_pedagogical_schema(self) -> Dict[str, Any]:
        """教学性审查输出schema"""
        return {
            "type": "object",
            "properties": {
                "clarity_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall clarity and understandability score (1-10)"
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 4,
                    "description": "Teaching strengths (2-4 items)"
                },
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [
                                    "missing_concept_explanation",
                                    "unclear_terminology",
                                    "insufficient_code_comments",
                                    "abrupt_complexity_jump",
                                    "missing_prerequisites",
                                    "poor_examples",
                                    "confusing_explanation",
                                    "knowledge_gap"
                                ]
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "major", "minor"]
                            },
                            "location": {
                                "type": "string",
                                "description": "Specific location (e.g., 'Step 4.2', 'Overview', 'Theory section')"
                            },
                            "problem": {
                                "type": "string",
                                "description": "What is confusing or unclear for learners"
                            },
                            "suggestion": {
                                "type": "string",
                                "description": "Concrete, actionable improvement suggestion"
                            },
                            "example_fix": {
                                "type": "string",
                                "description": "Example of better explanation or what to add"
                            }
                        },
                        "required": ["category", "severity", "location", "problem", "suggestion"]
                    }
                },
                "missing_concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "concept": {
                                "type": "string",
                                "description": "What concept needs explanation"
                            },
                            "why_needed": {
                                "type": "string",
                                "description": "Why this concept is important for understanding"
                            },
                            "where_to_add": {
                                "type": "string",
                                "description": "Where to add this explanation (specific location)"
                            },
                            "suggested_explanation": {
                                "type": "string",
                                "description": "Brief example of how to explain it"
                            }
                        },
                        "required": ["concept", "why_needed", "where_to_add"]
                    },
                    "description": "Concepts that need to be added or explained"
                },
                "requires_revision": {
                    "type": "boolean",
                    "description": "Whether pedagogical improvements are needed"
                },
                "summary": {
                    "type": "string",
                    "description": "2-3 sentence summary of pedagogical quality"
                }
            },
            "required": ["clarity_score", "strengths", "issues", "missing_concepts", "requires_revision", "summary"]
        }

    def _build_system_prompt(self) -> str:
        """系统prompt"""
        return f"""You are an expert technical educator and instructional designer.

**Your mission**: Ensure technical content is accessible and understandable for {self.target_audience}.

**Your expertise**:
- Identifying knowledge gaps and missing explanations
- Simplifying complex concepts without losing accuracy
- Creating clear learning paths
- Recognizing when terminology needs definition
- Evaluating code clarity and comment quality

**Your approach**:
- Put yourself in the learner's shoes
- Identify what might confuse or overwhelm them
- Be specific and constructive in feedback
- Provide concrete examples of improvements
- Balance technical depth with accessibility

Your goal: Help every learner succeed with this content."""

    def _generate_overall_assessment(self, package_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成总体评估"""
        if not package_reviews:
            return {
                "average_clarity_score": 0,
                "total_pedagogical_issues": 0,
                "missing_concepts_count": 0,
                "packages_needing_revision": 0
            }
        
        # 安全获取 clarity_score，如果缺失则使用默认值
        clarity_scores = [r.get("clarity_score", 5) for r in package_reviews if isinstance(r, dict)]
        avg_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 5.0
        total_issues = sum(len(r.get("issues", [])) for r in package_reviews if isinstance(r, dict))
        missing_concepts = sum(len(r.get("missing_concepts", [])) for r in package_reviews if isinstance(r, dict))
        needs_revision = sum(1 for r in package_reviews if isinstance(r, dict) and r.get("requires_revision"))
        
        return {
            "average_clarity_score": round(avg_clarity, 1),
            "total_pedagogical_issues": total_issues,
            "missing_concepts_count": missing_concepts,
            "packages_needing_revision": needs_revision,
            "assessment": self._get_assessment_text(avg_clarity, total_issues)
        }

    def _get_assessment_text(self, avg_clarity: float, issues: int) -> str:
        """生成评估文本"""
        if avg_clarity >= 8 and issues <= 3:
            return "Excellent teaching quality. Very accessible for learners."
        elif avg_clarity >= 7:
            return "Good foundation. Some clarifications needed for better learning experience."
        elif avg_clarity >= 5:
            return "Moderate quality. Significant improvements needed for target audience."
        else:
            return "Poor pedagogical quality. Major revisions required for accessibility."