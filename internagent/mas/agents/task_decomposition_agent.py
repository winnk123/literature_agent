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
                    "description": "3-5 executable research steps",
                    "minItems": 3,
                    "maxItems": 5
                },
                "scientific_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 generalized keywords (2-4 words each, e.g., 'video analysis')",
                    "minItems": 3,
                    "maxItems": 5
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
            
            # Check if task_difficulty is manually specified in context
            manual_difficulty = context.get("task_difficulty")
            if manual_difficulty is not None:
                try:
                    task_difficulty = int(manual_difficulty)
                    task_difficulty = max(1, min(5, task_difficulty))
                    difficulty_reasoning = f"Manually specified difficulty: {task_difficulty}/5"
                    logger.info(f"Using manually specified task difficulty: {task_difficulty}/5")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid manual difficulty '{manual_difficulty}', will auto-assess")
                    manual_difficulty = None
            
            # Auto-assess task difficulty if not manually specified
            if manual_difficulty is None:
                difficulty_assessment_prompt = (
                    f"Analyze the following research problem description and assess its difficulty:\n\n{text_input}\n\n"
                    "Rate the task difficulty on a scale of 1-5:\n"
                    "1-2: Simple tasks (e.g., basic image classification like MNIST/digit recognition, simple regression, basic NLP tasks)\n"
                    "3: Moderate tasks (e.g., object detection, sentiment analysis, standard deep learning applications)\n"
                    "4-5: Complex tasks (e.g., multimodal learning, advanced generation tasks, complex reasoning, cutting-edge research)\n\n"
                    "**IMPORTANT**: Some tasks (e.g., video retrieval, image search, text classification) can be implemented at multiple difficulty levels:\n"
                    "- Simple version: Use basic methods (e.g., simple feature extraction + similarity search)\n"
                    "- Complex version: Use state-of-the-art methods (e.g., advanced deep learning, transformer models)\n"
                    "If the task can be implemented at multiple levels, assess based on the **typical implementation** or **user expectations** for this task.\n\n"
                    "Return ONLY a JSON object with:\n"
                    '{"difficulty": <1-5>, "reasoning": "<brief explanation, including whether multiple difficulty levels are possible>"}'
                )
                
                try:
                    difficulty_schema = {
                        "type": "object",
                        "properties": {
                            "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
                            "reasoning": {"type": "string"}
                        },
                        "required": ["difficulty", "reasoning"]
                    }
                    difficulty_response = await self._call_model(
                        prompt=difficulty_assessment_prompt,
                        schema=difficulty_schema,
                        temperature=0.3
                    )
                    task_difficulty = difficulty_response.get("difficulty", 3)
                    difficulty_reasoning = difficulty_response.get("reasoning", "")
                    logger.info(f"Task difficulty assessed: {task_difficulty}/5 - {difficulty_reasoning}")
                except Exception as e:
                    logger.warning(f"Difficulty assessment failed, defaulting to moderate (3): {e}")
                    task_difficulty = 3
                    difficulty_reasoning = ""
            
            # Generate technology stack recommendations based on difficulty
            tech_stack_guidance = ""
            if task_difficulty <= 2:
                tech_stack_guidance = (
                    "\n\n**TECHNOLOGY STACK GUIDANCE FOR SIMPLE TASKS:**\n"
                    "Use established, well-understood deep learning technologies:\n"
                    "- Basic CNNs (LeNet, AlexNet, ResNet-18/34) for image tasks\n"
                    "- Simple RNNs/LSTMs or basic Transformers for text tasks\n"
                    "- Standard architectures from 2012-2020 (well-documented, stable)\n"
                    "- DO NOT use cutting-edge LLMs or complex multimodal models unless absolutely necessary\n"
                    "- Focus on simplicity, clarity, and educational value\n"
                    "Examples: CNN for digit recognition, simple LSTM for text classification, basic GAN for simple generation"
                )
            elif task_difficulty == 3:
                tech_stack_guidance = (
                    "\n\n**TECHNOLOGY STACK GUIDANCE FOR MODERATE TASKS:**\n"
                    "Use balanced deep learning technologies:\n"
                    "- Modern architectures (ResNet-50/101, EfficientNet, BERT-base, GPT-2)\n"
                    "- Well-established frameworks from 2020-2022\n"
                    "- Standard Transformer-based models for NLP/vision\n"
                    "- Can use some advanced techniques but keep them accessible\n"
                    "Examples: ResNet for object detection, BERT for NLP, standard vision transformers"
                )
            else:  # 4-5
                tech_stack_guidance = (
                    "\n\n**TECHNOLOGY STACK GUIDANCE FOR COMPLEX TASKS:**\n"
                    "Use advanced deep learning technologies:\n"
                    "- State-of-the-art models (GPT-4, CLIP, Diffusion Models, Multimodal LLMs)\n"
                    "- Recent architectures from 2022-2025\n"
                    "- Advanced Transformer variants (Vision-Language Models, Diffusion Transformers)\n"
                    "- Cutting-edge but not bleeding-edge (stable enough for tutorials)\n"
                    "Examples: Diffusion models for generation, CLIP for multimodal tasks, advanced LLMs for complex reasoning"
                )
            
            generation_prompt = (
                f"Analyze the following research problem description:\n\n{text_input}\n\n"
                f"Task Difficulty Assessment: {task_difficulty}/5 - {difficulty_reasoning}\n"
                "Provide a structured plan in JSON format with:\n\n"
                "1. problem_overview: Summarize the core problem in 2-3 sentences\n"
                "2. main_objectives: List 3-5 specific, measurable objectives\n"
                "3. key_steps: Break down into exactly 3-5 executable steps total, each with (Step count outside 3-5 is invalid):\n"
                "   - step_id (e.g., 'step_1')\n"
                "   - step_name (concise title)\n"
                "   - description (what to do and expected outcome)\n"
                "   - Step identifiers must follow the format 'step_1', 'step_2', ... in sequential order with no gaps\n"
                "   - Step names should start with an action verb (e.g., \"实现...\", \"构建...\") and remain under 20 Chinese characters\n"
                "   **CRITICAL - Step Ordering Requirements:**\n"
                "   - Steps MUST follow a logical progression from foundational concepts to advanced implementations\n"
                "   - Basic/fundamental concepts MUST come BEFORE advanced concepts that build upon them\n"
                "   - Each step should build upon previous steps - later steps should use concepts introduced in earlier steps\n"
                "   - As a tutorial, you need to break down key steps from simple to complex, from shallow to deep\n"
                "   - You CANNOT introduce advanced concepts before their foundational prerequisites\n"
                "   - Example WRONG order: (1) Learn multimodal large language models → (2) Learn basic large language models\n"
                "   - Example WRONG order: (1) Learn vision transformer → (2) Learn Multi-head attention\n"
                "     This is wrong because you cannot explain multimodal LLMs (advanced) before explaining basic LLMs (foundational)\n"
                "   - Example correct order: (1) Understand basic LLMs → (2) Understand vision encoders → (3) Learn multimodal fusion → (4) Build multimodal LLM\n"
                "   - Always ensure foundational concepts are introduced before advanced concepts that depend on them\n"
                "   **CRITICAL - Step Uniqueness and Scope Requirements:**\n"
                "   - Each key_step must focus on a distinct module or milestone (avoid overlapping or restating the same component)\n"
                "   - Do NOT create multiple steps that target the exact same file/architecture unless they handle clearly different sub-problems\n"
                "   - **CRITICAL - Avoid Conceptual Overlap:**\n"
                "     * If Step 1 introduces a concept (e.g., 'image patching' theory), Step 2 should NOT re-introduce the same concept\n"
                "     * Step 2 should only implement what was explained in Step 1, without repeating the theoretical explanation\n"
                "     * Example WRONG: Step 1 explains 'image patching concept' → Step 2 explains 'image patching concept' again and then implements it\n"
                "     * Example CORRECT: Step 1 explains 'image patching concept' → Step 2 implements 'image patching' (assumes understanding from Step 1)\n"
                "   - **CRITICAL - Clear Scope Definition:** Each step description must clearly specify:\n"
                "     * What concepts/components are INCLUDED in this step (what will be covered)\n"
                "     * What concepts/components are EXPLICITLY EXCLUDED (what will NOT be covered, as it belongs to other steps)\n"
                "     * What is the INPUT of this step (what knowledge/code from previous steps is required)\n"
                "     * What is the OUTPUT of this step (what will be produced/delivered for subsequent steps)\n"
                "   - Clearly define the scope of each step so that, when combined, they cover the full solution without redundancy\n"
                "   - Each step should have a distinct deliverable/milestone that does not overlap with other steps\n"
                "4. scientific_keywords: Extract 3-6 generalized technical terms "
                "(e.g., 'multimodal learning', 'video analysis')\n\n"
                "**CRITICAL TECHNOLOGY SELECTION REQUIREMENTS:**\n"
                "- Select deep learning technologies from the 2015-2025 timeframe (can extend to earlier years if needed for foundational concepts)\n"
                "- Technologies should be mature enough to have good documentation and tutorials (not too new)\n"
                "- Technologies should be modern enough to reflect current best practices (not too old)\n"
                "- Match technology complexity to task difficulty:\n"
                f"{tech_stack_guidance}\n"
                "- For simple tasks (difficulty 1-2): Prefer simpler, well-established models\n"
                "- For complex tasks (difficulty 4-5): Use advanced, state-of-the-art models\n"
                "- Ensure all fields are filled with meaningful content. "
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
                
                # Add difficulty assessment to response
                response["task_difficulty"] = task_difficulty
                response["difficulty_reasoning"] = difficulty_reasoning
                    
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
            
            # Check if task_difficulty is manually specified in context
            manual_difficulty = context.get("task_difficulty")
            if manual_difficulty is not None:
                try:
                    task_difficulty = int(manual_difficulty)
                    task_difficulty = max(1, min(5, task_difficulty))
                    difficulty_reasoning = f"Manually specified difficulty: {task_difficulty}/5"
                    logger.info(f"Using manually specified task difficulty: {task_difficulty}/5")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid manual difficulty '{manual_difficulty}', will auto-assess")
                    manual_difficulty = None
            
            # Auto-assess task difficulty if not manually specified
            if manual_difficulty is None:
                difficulty_assessment_prompt = (
                    "Analyze the attached image(s) describing a research project and assess its difficulty.\n"
                    "Rate the task difficulty on a scale of 1-5:\n"
                    "1-2: Simple tasks (e.g., basic image classification like MNIST/digit recognition, simple regression, basic NLP tasks)\n"
                    "3: Moderate tasks (e.g., object detection, sentiment analysis, standard deep learning applications)\n"
                    "4-5: Complex tasks (e.g., multimodal learning, advanced generation tasks, complex reasoning, cutting-edge research)\n\n"
                    "**IMPORTANT**: Some tasks (e.g., video retrieval, image search, text classification) can be implemented at multiple difficulty levels:\n"
                    "- Simple version: Use basic methods (e.g., simple feature extraction + similarity search)\n"
                    "- Complex version: Use state-of-the-art methods (e.g., advanced deep learning, transformer models)\n"
                    "If the task can be implemented at multiple levels, assess based on the **typical implementation** or **user expectations** for this task.\n\n"
                    "Return ONLY a JSON object with:\n"
                    '{"difficulty": <1-5>, "reasoning": "<brief explanation, including whether multiple difficulty levels are possible>"}'
                )
                
                try:
                    difficulty_schema = {
                        "type": "object",
                        "properties": {
                            "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
                            "reasoning": {"type": "string"}
                        },
                        "required": ["difficulty", "reasoning"]
                    }
                    difficulty_response = await self._call_model_multimodal(
                        prompt=difficulty_assessment_prompt,
                        images=images,
                        schema=difficulty_schema,
                        temperature=0.3
                    )
                    task_difficulty = difficulty_response.get("difficulty", 3)
                    difficulty_reasoning = difficulty_response.get("reasoning", "")
                    logger.info(f"Task difficulty assessed: {task_difficulty}/5 - {difficulty_reasoning}")
                except Exception as e:
                    logger.warning(f"Difficulty assessment failed, defaulting to moderate (3): {e}")
                    task_difficulty = 3
                    difficulty_reasoning = ""
            
            # Generate technology stack recommendations based on difficulty
            tech_stack_guidance = ""
            if task_difficulty <= 2:
                tech_stack_guidance = (
                    "\n\n**TECHNOLOGY STACK GUIDANCE FOR SIMPLE TASKS:**\n"
                    "Use established, well-understood deep learning technologies:\n"
                    "- Basic CNNs (LeNet, AlexNet, ResNet-18/34) for image tasks\n"
                    "- Simple RNNs/LSTMs or basic Transformers for text tasks\n"
                    "- Standard architectures from 2012-2020 (well-documented, stable)\n"
                    "- DO NOT use cutting-edge LLMs or complex multimodal models unless absolutely necessary\n"
                    "- Focus on simplicity, clarity, and educational value\n"
                    "Examples: CNN for digit recognition, simple LSTM for text classification, basic GAN for simple generation"
                )
            elif task_difficulty == 3:
                tech_stack_guidance = (
                    "\n\n**TECHNOLOGY STACK GUIDANCE FOR MODERATE TASKS:**\n"
                    "Use balanced deep learning technologies:\n"
                    "- Modern architectures (ResNet-50/101, EfficientNet, BERT-base, GPT-2)\n"
                    "- Well-established frameworks from 2020-2025\n"
                    "- Standard Transformer-based models for NLP/vision\n"
                    "- Can use some advanced techniques but keep them accessible\n"
                    "Examples: ResNet for object detection, BERT for NLP, standard vision transformers"
                )
            else:  # 4-5
                tech_stack_guidance = (
                    "\n\n**TECHNOLOGY STACK GUIDANCE FOR COMPLEX TASKS:**\n"
                    "Use advanced deep learning technologies:\n"
                    "- State-of-the-art models (GPT-4, CLIP, Diffusion Models, Multimodal LLMs)\n"
                    "- Recent architectures from 2020-2025\n"
                    "- Advanced Transformer variants (Vision-Language Models, Diffusion Transformers)\n"
                    "- Cutting-edge but not bleeding-edge (stable enough for tutorials)\n"
                    "Examples: Diffusion models for generation, CLIP for multimodal tasks, advanced LLMs for complex reasoning"
                )
            
            generation_prompt = (
                "Analyze the attached image(s) describing a research project. "
                f"Task Difficulty Assessment: {task_difficulty}/5 - {difficulty_reasoning}\n"
                "Provide a structured plan in JSON format with:\n\n"
                "1. problem_overview: Summarize the core problem in 2-3 sentences\n"
                "2. main_objectives: List 3-5 specific, measurable objectives\n"
                "3. key_steps: Break down into exactly 3-5 executable steps total, each with (Step count outside 3-5 is invalid):\n"
                "   - step_id (e.g., 'step_1')\n"
                "   - step_name (concise title)\n"
                "   - description (what to do and expected outcome)\n"
                "   - Step identifiers must follow the format 'step_1', 'step_2', ... in sequential order with no gaps\n"
                "   - Step names should start with an action verb (e.g., \"实现...\", \"构建...\") and remain under 20 Chinese characters\n"
                "   **CRITICAL - Step Ordering Requirements:**\n"
                "   - Steps MUST follow a logical progression from foundational concepts to advanced implementations\n"
                "   - Basic/fundamental concepts MUST come BEFORE advanced concepts that build upon them\n"
                "   - Each step should build upon previous steps - later steps should use concepts introduced in earlier steps\n"
                "   - As a tutorial, you need to break down key steps from simple to complex, from shallow to deep\n"
                "   - You CANNOT introduce advanced concepts before their foundational prerequisites\n"
                "   - Example WRONG order: (1) Learn multimodal large language models → (2) Learn basic large language models\n"
                "   - Example WRONG order: (1) Learn vision transformer → (2) Learn Multi-head attention\n"
                "     This is wrong because you cannot explain multimodal LLMs (advanced) before explaining basic LLMs (foundational)\n"
                "   - Example correct order: (1) Understand basic LLMs → (2) Understand vision encoders → (3) Learn multimodal fusion → (4) Build multimodal LLM\n"
                "   - Always ensure foundational concepts are introduced before advanced concepts that depend on them\n"
                "   **CRITICAL - Step Uniqueness and Scope Requirements:**\n"
                "   - Each key_step must focus on a distinct module or milestone (avoid overlapping or restating the same component)\n"
                "   - Do NOT create multiple steps that target the exact same file/architecture unless they handle clearly different sub-problems\n"
                "   - **CRITICAL - Avoid Conceptual Overlap:**\n"
                "     * If Step 1 introduces a concept (e.g., 'image patching' theory), Step 2 should NOT re-introduce the same concept\n"
                "     * Step 2 should only implement what was explained in Step 1, without repeating the theoretical explanation\n"
                "     * Example WRONG: Step 1 explains 'image patching concept' → Step 2 explains 'image patching concept' again and then implements it\n"
                "     * Example CORRECT: Step 1 explains 'image patching concept' → Step 2 implements 'image patching' (assumes understanding from Step 1)\n"
                "   - **CRITICAL - Clear Scope Definition:** Each step description must clearly specify:\n"
                "     * What concepts/components are INCLUDED in this step (what will be covered)\n"
                "     * What concepts/components are EXPLICITLY EXCLUDED (what will NOT be covered, as it belongs to other steps)\n"
                "     * What is the INPUT of this step (what knowledge/code from previous steps is required)\n"
                "     * What is the OUTPUT of this step (what will be produced/delivered for subsequent steps)\n"
                "   - Clearly define the scope of each step so that, when combined, they cover the full solution without redundancy\n"
                "   - Each step should have a distinct deliverable/milestone that does not overlap with other steps\n"
                "4. scientific_keywords: Extract 3-6 generalized technical terms "
                "(e.g., 'multimodal learning', 'video analysis')\n\n"
                "**CRITICAL TECHNOLOGY SELECTION REQUIREMENTS:**\n"
                "- Select deep learning technologies from the 2015-2025 timeframe (can extend to earlier years if needed for foundational concepts)\n"
                "- Technologies should be mature enough to have good documentation and tutorials (not too new)\n"
                "- Technologies should be modern enough to reflect current best practices (not too old)\n"
                "- Match technology complexity to task difficulty:\n"
                f"{tech_stack_guidance}\n"
                "- For simple tasks (difficulty 1-2): Prefer simpler, well-established models\n"
                "- For complex tasks (difficulty 4-5): Use advanced, state-of-the-art models\n"
                "- Ensure all fields are filled with meaningful content. "
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
                
                # Add difficulty assessment to response
                response["task_difficulty"] = task_difficulty
                response["difficulty_reasoning"] = difficulty_reasoning
                    
                return response
                
            except Exception as exc:
                logger.error(f"Task decomposition failed: {exc}")
                raise AgentExecutionError("Task decomposition failed") from exc