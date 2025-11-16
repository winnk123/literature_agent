"""
Task Decomposition Agent for InternAgent

Parses multimodal inputs (images + optional text guidance) or text-only inputs
and produces a structured task plan with actionable subtasks and research topics.
"""

import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class TaskDecompositionAgent(BaseAgent):
    """Generates structured task breakdowns from multimodal or text-only requirements."""

    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        images = context.get("images") or []
        if isinstance(images, str):
            images = [images]
        
        # 支持文本输入：如果提供了text_input，可以使用文本输入而不是图像
        text_input = context.get("text_input") or context.get("text") or ""
        use_text_input = bool(text_input and not images)
        
        if not images and not text_input:
            raise AgentExecutionError(
                "Task decomposition requires either: (1) at least one image input via 'images', "
                "or (2) text input via 'text_input' or 'text' field"
            )

        description = context.get("description", "")
        domain = context.get("domain", "")
        manual_guidance = context.get("manual_guidance", [])
        if isinstance(manual_guidance, str):
            manual_guidance = [manual_guidance]
        previous_plan = context.get("previous_plan")
        feedback_history = context.get("feedback", [])
        
        prompt_sections: List[str] = []

        if description:
            prompt_sections.append(f"Task Description: {description}")
        if domain:
            prompt_sections.append(f"Domain: {domain}")
        if manual_guidance:
            guidance_text = ", ".join(manual_guidance)
            prompt_sections.append(f"Guidance: {guidance_text}")
        if feedback_history:
            feedback_lines = []
            for entry in feedback_history[-3:]:
                if isinstance(entry, dict):
                    text = entry.get("text") or entry.get("feedback")
                else:
                    text = str(entry)
                if text:
                    feedback_lines.append(text)
            if feedback_lines:
                prompt_sections.append(f"Previous Feedback: {'; '.join(feedback_lines)}")
        if previous_plan:
            prompt_sections.append(f"Previous Plan: {previous_plan[:500]}...")  # 截断

        additional_context = "\n".join(prompt_sections) if prompt_sections else ""

        # 简化的 Schema - 与 prompt 匹配
        schema = {
            "type": "object",
            "properties": {
                "problem_overview": {
                    "type": "string",
                    "description": "2-3 sentence summary of the core problem"
                },
                "main_objectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 core objectives",
                    "minItems": 3,
                    "maxItems": 5
                },
                "key_steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_id": {"type": "string"},
                            "step_name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["step_id", "step_name", "description"]
                    },
                    "description": "4-5 executable research steps",
                    "minItems": 4,
                    "maxItems": 5
                },
                "scientific_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-6 generalized keywords (2-4 words each, e.g., 'video analysis')",
                    "minItems": 3,
                    "maxItems": 6
                }
            },
            "required": ["problem_overview", "main_objectives", "key_steps", "scientific_keywords"]
        }

        # 根据输入类型选择不同的prompt和调用方式
        if use_text_input:
            # 文本输入模式
            system_prompt = (
                "You are an AI research planning expert. Analyze text descriptions of research projects "
                "to create structured research plans with clear objectives, steps, and keywords."
            )
            
            generation_prompt = (
                f"Analyze the following research problem description:\n\n{text_input}\n\n"
                "Provide a structured plan in JSON format with:\n\n"
                "1. problem_overview: Summarize the core problem in 2-3 sentences\n"
                "2. main_objectives: List 3-5 specific, measurable objectives\n"
                "3. key_steps: Break down into 4-6 executable steps, each with:\n"
                "   - step_id (e.g., 'step_1')\n"
                "   - step_name (concise title)\n"
                "   - description (what to do and expected outcome)\n"
                "4. scientific_keywords: Extract 3-6 generalized technical terms "
                "(e.g., 'multimodal learning', 'video analysis')\n\n"
                "You MUST frame all steps and solutions using LLM/AI technologies (e.g., GPT, BERT, Vision-Language Models, Diffusion Models, Multimodal LLMs). "
                "Ensure all fields are filled with meaningful content. "
                "IMPORTANT: You MUST output all text fields in Chinese (简体中文) EXCEPT scientific_keywords. "
                "scientific_keywords must be in English because they will be used for literature search (e.g., 'multimodal learning', 'video analysis', 'deep learning'). "
                "All other fields (problem_overview, main_objectives, step_name, description) must be in Chinese."
            )
            
            if additional_context:
                generation_prompt += f"\n\nAdditional Context:\n{additional_context}"
            
            logger.info("Using text input mode for task decomposition")
            try:
                response = await self._call_model(
                    prompt=generation_prompt,
                    system_prompt=system_prompt,
                    schema=schema,
                    temperature=self.config.get("temperature", 0.7)
                )
                
                # 验证响应不为空
                if not response.get("problem_overview") or not response.get("key_steps"):
                    logger.warning("Received incomplete response, retrying with relaxed constraints")
                    # 可以在这里添加重试逻辑
                    
                return response
                
            except Exception as exc:
                logger.error(f"Task decomposition failed: {exc}")
                raise AgentExecutionError("Task decomposition failed") from exc
        else:
            # 图像输入模式（原有逻辑）
            system_prompt = (
                "You are an AI research planning expert. Analyze multimodal inputs (images + text) "
                "to create structured research plans with clear objectives, steps, and keywords."
            )
            
            generation_prompt = (
                "Analyze the attached image(s) describing a research project. "
                "Provide a structured plan in JSON format with:\n\n"
                "1. problem_overview: Summarize the core problem in 2-3 sentences\n"
                "2. main_objectives: List 3-5 specific, measurable objectives\n"
                "3. key_steps: Break down into 4-6 executable steps, each with:\n"
                "   - step_id (e.g., 'step_1')\n"
                "   - step_name (concise title)\n"
                "   - description (what to do and expected outcome)\n"
                "4. scientific_keywords: Extract 3-6 generalized technical terms "
                "(e.g., 'multimodal learning', 'video analysis')\n\n"
                "You MUST frame all steps and solutions using LLM/AI technologies (e.g., GPT, BERT, Vision-Language Models, Diffusion Models, Multimodal LLMs). "
                "Ensure all fields are filled with meaningful content. "
                "IMPORTANT: You MUST output all text fields in Chinese (简体中文) EXCEPT scientific_keywords. "
                "scientific_keywords must be in English because they will be used for literature search (e.g., 'multimodal learning', 'video analysis', 'deep learning'). "
                "All other fields (problem_overview, main_objectives, step_name, description) must be in Chinese."
            )
            
            if additional_context:
                generation_prompt += f"\n\nAdditional Context:\n{additional_context}"
            
            logger.info(f"Using image input mode for task decomposition ({len(images)} image(s))")
            try:
                response = await self._call_model_multimodal(
                    prompt=generation_prompt,
                    images=images,
                    system_prompt=system_prompt,
                    schema=schema,
                    temperature=self.config.get("temperature", 0.7)
                )
            
                # 验证响应不为空
                if not response.get("problem_overview") or not response.get("key_steps"):
                    logger.warning("Received incomplete response, retrying with relaxed constraints")
                    # 可以在这里添加重试逻辑
                    
                return response
                
            except Exception as exc:
                logger.error(f"Task decomposition failed: {exc}")
                raise AgentExecutionError("Task decomposition failed") from exc