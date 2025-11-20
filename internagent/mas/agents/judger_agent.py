"""
Judger Agent for InternAgent - Simplified Version

Evaluates task decomposition proposals on core quality dimensions.
"""

import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class JudgerAgent(BaseAgent):
    """Evaluates research plans with streamlined feedback."""

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a task decomposition plan.
        Expected context:
            - plan: Dict - The task decomposition output to evaluate
            - original_images: List[str] - Original requirement images (optional)
            - domain: str - Research domain (optional)
        """
        plan = context.get("plan")
        if not plan:
            raise AgentExecutionError("Judger requires a plan to evaluate")
        
        original_images = context.get("original_images", [])
        domain = context.get("domain", "")
        
        # Prepare evaluation context
        plan_text = self._format_plan_for_evaluation(plan)
        
        # 简化的 Schema
        schema = {
            "type": "object",
            "properties": {
                "overall_score": {
                    "type": "number",
                    "description": "Overall quality score (0-10)",
                    "minimum": 0,
                    "maximum": 10
                },
                "scores": {
                    "type": "object",
                    "properties": {
                        "clarity_structure": {"type": "number", "minimum": 0, "maximum": 10, "description": "Logical ordering and structural clarity"},
                        "accuracy_depth": {"type": "number", "minimum": 0, "maximum": 10, "description": "Technical accuracy and appropriate depth"}
                    },
                    "required": ["clarity_structure", "accuracy_depth"]
                },
                "key_issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 main problems or concerns",
                    "minItems": 0,
                    "maxItems": 4
                },
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 specific improvement suggestions",
                    "minItems": 2,
                    "maxItems": 4
                },
                "recommendation": {
                    "type": "string",
                    "enum": ["approve", "revise", "reject"],
                    "description": "Final recommendation"
                }
            },
            "required": ["overall_score", "scores", "suggestions", "recommendation"]
        }
        
        system_prompt = (
     "You are an AI Technical Editor evaluating research task decomposition plans. "
    "Focus on logical step sequencing, completeness, and clarity for learners following a structured tutorial."
        )
        
        generation_prompt = (
     "You are an expert technical editor evaluating a **Task Decomposition Plan** for a technical tutorial. "
    "Your goal is to assess whether the plan provides a clear, complete roadmap for learners to follow.\n\n"
    
    "**Evaluation Criteria:**\n"
    "1. overall_score (0-10): Weighted assessment of the plan's quality as a learning roadmap.\n"
    "2. scores: Individual scores (0-10) for:\n"
    "   - clarity_structure: Are steps logically ordered? Is each step distinct and unambiguous? Do the steps cover the complete task from start to finish?\n"
    "     **CRITICAL**: Check if steps follow a logical progression from foundational to advanced concepts.\n"
    "     - As a tutorial, steps must progress from simple to complex, from shallow to deep\n"
    "     - Basic/fundamental concepts must come BEFORE advanced concepts that build upon them\n"
    "     - Example of WRONG order: Step 1 introduces multimodal large language models (advanced) → Step 2 introduces basic large language models (foundational)\n"
    "       This violates tutorial logic - you cannot explain advanced concepts before their foundational prerequisites\n"
    "     - Each step should build upon previous steps - later steps should use concepts from earlier steps\n"
    "     - Steps must be unique and non-overlapping—avoid repeating the same component/file in multiple steps unless there is a clearly stated new goal\n"
    "     - Plans MUST contain exactly 3-5 key_steps. If there are fewer than 3 or more than 5 steps, this is a critical structural error.\n"
    "     - Step IDs must follow sequential 'step_1', 'step_2', ... format with no gaps; step names must be concise action phrases tied to the project scope.\n"
    "   - accuracy_depth: Is the technical approach sound? Is the scope appropriate for the stated task difficulty?\n"
    "     - Ensure each key_step is strongly relevant to the stated problem_overview/objectives (flag steps that feel tangential or unnecessary)\n"
    "3. key_issues: Identify 2-4 critical problems:\n"
    "   - Missing essential steps (e.g., skipping data preparation, model validation)\n"
    "   - Ambiguous or overlapping step descriptions\n"
    "   - Logical gaps in the workflow (e.g., step 3 requires output from non-existent step)\n"
    "   - **CRITICAL**: Steps in wrong order - advanced concepts appearing before foundational concepts\n"
    "     Example: Step 1 introduces multimodal LLMs (advanced) → Step 2 introduces basic LLMs (foundational) - this is WRONG\n"
    "   - **CRITICAL**: Conceptual dependency violations - later steps introducing prerequisites that should have been in earlier steps\n"
    "     As a tutorial, you must progress from simple to complex, from foundational to advanced\n"
    "   - Redundant or weakly-related steps (e.g., multiple steps targeting the same module, or steps unrelated to the stated problem)\n"
    "   - Incorrect step count or naming (e.g., not exactly 3-5 steps, missing step IDs, non-sequential numbering)\n"
"   - When referencing specific steps, ALWAYS use the format \"Step X\" where X is an integer between 1 and 5 (no decimals or zero). Do NOT invent step numbers outside this range.\n"
    "   If the plan is solid, state: 'No critical issues identified.'\n"
    "4. suggestions: Provide 2-4 concrete improvements:\n"
    "   - Reorganize step order for better logical flow (especially if basic concepts appear after advanced concepts)\n"
    "   - Split overly complex steps into substeps\n"
    "   - Add missing prerequisite or validation steps\n"
    "   - Fix conceptual ordering - ensure foundational concepts come before advanced implementations\n"
    "   - Remove or merge redundant steps; ensure each step directly supports the stated goals\n"
"   - When referencing steps in suggestions, ONLY use \"Step 1\" ... \"Step 5\" format (integers only)\n"
    "   If the plan is solid, state: 'Plan is well-structured as-is.'\n"
    "5. recommendation:\n"
    "   - 'approve': Score ≥ 8.0 AND all essential steps present AND clear execution path\n"
    "   - 'revise': Score 5.0-7.9 OR has ambiguous steps OR missing key components\n"
    "   - 'reject': Score < 5.0 OR fundamentally flawed logic OR incomplete workflow\n\n"
    
    f"**Task Decomposition Plan:**\n{plan_text}\n\n"
    
    "**Important Constraints:**\n"
    "- Evaluate ONLY the step decomposition logic, NOT implementation details or code\n"
    "- Do NOT suggest adding tutorials, examples, or explanatory content\n"
    "- Focus on: step completeness, ordering, and clarity of task boundaries\n"
    "- This is a standardized tutorial template—prioritize structural soundness over novelty"
)
        
        if domain:
            generation_prompt += f"\nDomain: {domain}"
        
        try:
            if original_images:
                response = await self._call_model_multimodal(
                    prompt=generation_prompt,
                    images=original_images,
                    system_prompt=system_prompt,
                    schema=schema,
                    temperature=0.3
                )
            else:
                response = await self._call_model(
                    prompt=generation_prompt,
                    system_prompt=system_prompt,
                    schema=schema,
                    temperature=0.3
                )
            
            logger.info(f"Plan evaluation: {response.get('overall_score'):.1f}/10 - "
                       f"{response.get('recommendation')}")
            
            return response
            
        except Exception as exc:
            logger.error(f"Plan evaluation failed: {exc}")
            raise AgentExecutionError("Plan evaluation failed") from exc
    
    def _format_plan_for_evaluation(self, plan: Dict[str, Any]) -> str:
        """Format plan into concise text."""
        parts = []
        
        if "problem_overview" in plan:
            parts.append(f"Problem: {plan['problem_overview']}")
        
        if "main_objectives" in plan:
            parts.append(f"Objectives: {', '.join(plan['main_objectives'][:3])}")
        
        if "key_steps" in plan:
            steps = [f"{s.get('step_id')}: {s.get('step_name')}" 
                    for s in plan["key_steps"][:5]]
            parts.append(f"Steps: {'; '.join(steps)}")
        
        if "scientific_keywords" in plan:
            parts.append(f"Keywords: {', '.join(plan['scientific_keywords'])}")
        
        return "\n".join(parts)