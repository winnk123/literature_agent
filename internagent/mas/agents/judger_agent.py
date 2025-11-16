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
                        "novelty": {"type": "number", "minimum": 0, "maximum": 10},
                        "feasibility": {"type": "number", "minimum": 0, "maximum": 10},
                        "technical_quality": {"type": "number", "minimum": 0, "maximum": 10}
                    },
                    "required": ["novelty", "feasibility", "technical_quality"]
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
            "You are an AI research reviewer. Evaluate research plans critically but constructively. "
            "Focus on novelty, feasibility, and technical quality."
        )
        
        generation_prompt = (
            "Evaluate this research plan and provide:\n"
            "1. overall_score (0-10): Overall quality assessment\n"
            "2. scores: Individual scores for:\n"
            "   - novelty: Innovation and originality\n"
            "   - feasibility: Realistic and achievable\n"
            "   - technical_quality: Sound LLM/AI methodology\n"
            "3. key_issues: 2-4 main concerns (if any)\n"
            "4. suggestions: 2-4 actionable improvements\n"
            "5. recommendation: Based on overall_score:\n"
            "   - 'approve' if score >= 8.0 AND no critical issues\n"
            "   - 'revise' if score 5.0-7.9 OR has addressable issues\n"
            "   - 'reject' if score < 5.0 OR has fundamental flaws\n"
            f"Plan to evaluate:\n\n{plan_text}\n\n"
            "Be concise and actionable."
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