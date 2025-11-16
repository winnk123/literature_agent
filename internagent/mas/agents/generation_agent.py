"""
Generation Agent for InternAgent

Implements the idea generation agent that creates novel research hypotheses
based on research goals, domain constraints, literature, and optional code baselines.
The agent supports iterative refinement through feedback incorporation and provides
configurable creativity levels for idea generation.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional

from ..models.base_model import BaseModel
from .base_agent import BaseAgent, AgentExecutionError
from .codeview_agent import get_repo_structure


logger = logging.getLogger(__name__)


class GenerationAgent(BaseAgent):
    """
    Agent that generates novel, scientifically plausible research hypotheses.

    Creates multiple idea candidates based on research goals, domain knowledge,
    literature surveys, and optional code baselines. Supports iterative refinement
    through feedback and adjustable creativity levels. Can analyze file-level or
    project-level code to generate code-aware hypotheses.

    Attributes:
        do_survey (bool): Whether to include literature information
        generation_count (int): Number of hypotheses to generate per call
        creativity (float): Creativity level 0-1 (higher = more creative)
        diversity_threshold (float): Minimum diversity between hypotheses
        temperature (float): Model sampling temperature
    """
    
    def __init__(self, model, config: Dict[str, Any]):
        """
        Initialize the generation agent with model and configuration.

        Args:
            model (BaseModel): Language model for idea generation
            config (Dict[str, Any]): Configuration with keys:
                - do_survey (bool): Include literature (default: False)
                - generation_count (int): Hypotheses per call (default: 5)
                - creativity (float): Creativity 0-1 (default: 0.9)
                - diversity_threshold (float): Min diversity (default: 0.3)
                - temperature (float): Sampling temperature (optional)
        """
        super().__init__(model, config)
        
        # Load agent-specific configuration
        self.do_survey = config.get("do_survey", False)
        self.generation_count = config.get("generation_count", 5)
        self.creativity = config.get("creativity", 0.9)  # Higher = more creative
        self.diversity_threshold = config.get("diversity_threshold", 0.3)
        self.temperature = config.get("temperature", None)
        
    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate novel research ideas based on provided context.

        Generates multiple idea candidates using the configured language model,
        incorporating research goals, domain knowledge, literature, code baselines,
        and iterative feedback. Returns structured ideas with rationales.

        Args:
            context (Dict[str, Any]): Execution context with keys:
                - goal (Dict): Research goal with description, domain, constraints
                - iteration (int): Current iteration number
                - feedback (List[Dict]): Previous feedback entries (optional)
                - paper_lst (List[Dict]): Literature papers if do_survey=True
            params (Dict[str, Any]): Runtime parameters:
                - count (int): Override generation_count (optional)
                - creativity (float): Override creativity level (optional)

        Returns:
            Dict[str, Any]: Results containing:
                - hypotheses (List[Dict]): Generated hypotheses with text/rationale
                - metadata (Dict): Generation info (count, creativity, reasoning)
                - baseline_summary (str): Code baseline summary if applicable

        Raises:
            AgentExecutionError: If goal missing or generation fails
        """
        # Extract parameters
        goal = context.get("goal", {})
        if not goal or not goal.get("description"):
            raise AgentExecutionError("Research goal is required for idea generation")
            
        # Extract and override parameters if provided
        count = params.get("count", self.generation_count)
        creativity = params.get("creativity", self.creativity)
        iteration = context.get("iteration", 0)
        feedback = context.get("feedback", [])
        paper_lst = context.get("paper_lst", [])
        
        # Create a JSON schema for the expected output
        output_schema = {
            "type": "object",
            "properties": {
                "hypotheses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The idea statement"
                            },
                            "rationale": {
                                "type": "string",
                                "description": "Reasoning for why this idea is plausible"
                            }
                        },
                        "required": ["text", "rationale"]
                    }
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation of the generation approach"
                },
                "baseline_summary":{
                    "type": "string",
                    "description": "Summary of the baseline code understanding"
                }
            },
            "required": ["hypotheses", "reasoning"]
        }
        
        if os.path.exists(goal.get("ref_code_path", "")):
            output_schema["required"] = ["hypotheses", "reasoning", "baseline_summary"]
                    
        # Build the prompt
        prompt = self._build_generation_prompt(
            goal=goal,
            count=count,
            iteration=iteration,
            feedback=feedback,
            paper_lst=paper_lst
        )
        
        # Call the model
        system_prompt = self._build_system_prompt(creativity)
        
        try:
            response = await self._call_model(
                prompt=prompt,
                system_prompt=system_prompt,
                schema=output_schema,
                temperature=self.temperature,
            )
            
            # Validate the response
            hypotheses = response.get("hypotheses", [])
            if not hypotheses:
                logger.warning("Generation agent returned no hypotheses")
                
            # Add metadata to the response
            result = {
                "hypotheses": hypotheses,
                "metadata": {
                    "count": len(hypotheses),
                    "creativity": creativity,
                    "iteration": iteration,
                    "reasoning": response.get("reasoning", "")
                },
                "baseline_summary": response.get("baseline_summary", "")
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Generation agent execution failed: {str(e)}")
            raise AgentExecutionError(f"Failed to generate hypotheses: {str(e)}")
    
    def _build_generation_prompt(self,
                               goal: Dict[str, Any],
                               count: int,
                               iteration: int,
                               feedback: List[Dict[str, Any]],
                               paper_lst: List[Dict]) -> str:
        """
        Construct comprehensive prompt for idea generation.

        Builds a structured prompt incorporating research goals, domain constraints,
        background information, literature, code baselines, and iterative feedback.
        Handles both file-level and project-level code analysis.

        Args:
            goal (Dict[str, Any]): Goal with description/domain/constraints/background
            count (int): Number of hypotheses to generate
            iteration (int): Current iteration number for feedback context
            feedback (List[Dict[str, Any]]): Previous feedback entries
            paper_lst (List[Dict]): Literature papers for survey mode

        Returns:
            str: Formatted multi-section prompt for the language model
        """
        
        # Extract goal information
        goal_description = goal.get("description", "")
        domain = goal.get("domain", "")
        constraints = goal.get("constraints", [])
        background = goal.get("background", "")
        
        # Start with the goal
        prompt = f"# Research Goal\n{goal_description}\n\n"
        
        # Add domain if available
        if domain:
            prompt += f"# Domain\n{domain}\n\n"
            
        # Add background if available
        if background:
            prompt += "Background Information is a detailed description of the baseline method. Please analyze the provided Background Information and give novel hypotheses based on the research goal and the background information.\n\n"
            prompt += f"# Background Information\n{background}\n\n"
            
        # Add constraints if available
        if constraints:
            prompt += "# Constraints\n"
            for constraint in constraints:
                prompt += f"- {constraint}\n"
            prompt += "\n"

        # if do_survey, literature information is included in goal, and need prompt
        if self.do_survey and paper_lst:
            logger.info("Add literature information to prompt")
            literature_prompt = "# Literature Information\n"
            for paper in paper_lst:
                literature_prompt += f"- {paper['title']} ({paper['year']})\n {paper['abstract']} \n\n"
            prompt += literature_prompt
            prompt += "Please analyze the provided Literature Information and give novel hypotheses based on the research goal and the literature."
            
        # Add reference code if available
        # load code if exist, judge file/dir/not exist
        ref_code_path = goal.get("ref_code_path", "")
        if os.path.exists(ref_code_path):
            if os.path.isfile(ref_code_path):
                logger.info("Perform #file-level# code understanding and generation")
                with open(ref_code_path, 'r') as f:
                    ref_code = f.read()
                logger.info("Add reference code (RAW) to prompt")
                prompt += f"# Reference Code\n```python\n{ref_code}\n```\n\n"
                
            elif os.path.isdir(ref_code_path):
                logger.info("Perform #project-level# code understanding and generation")
                logger.info("Loading codeivew Agent ...")
                if os.path.exists(os.path.join(ref_code_path, "code_summary.json")):
                    logger.info("Code summary exists! Loading code summary from file.")
                    with open(os.path.join(ref_code_path, "code_summary.json"), 'r') as f:
                        ref_code = f.read()
                    ref_code = json.loads(ref_code)
                else:
                    logger.info("Code summary does not exist! Generating code summary.")
                    # Use codeview agent to generate code summary
                    ref_code = get_repo_structure(
                        project_path=ref_code_path,
                        output_dir=ref_code_path,
                        output_name="code_summary.json",
                        ignore_list=None,
                        model=self.model.model_name,
                        provider="user"
                    )
                ref_code = ref_code['summary'] + "\n\n" + ref_code['key_files']
                logger.info("Add reference code (CODEVIEW) to prompt")
                prompt += f"# Reference Code (Repo Summary) \n{ref_code}\n\n"
            
            prompt += "The Reference Code serves as the baseline code aligned with the Research Goal. The proposed idea should be innovative, building upon the Reference Code to enhance task performance."
            prompt += "Please analyze the provided Reference Code and give a brief summary from the following perspectives: \n 1. Methods and Concepts: Describe the main methods and concepts used in the code. How do they support the functionality? 2. Model Structure: If applicable, outline the model architecture and design choices. How does the structure serve its purpose? 3. Limitations: What are the limitations of the code? How can they be addressed?"
        else:
            ref_code = ""
            logger.error("Default: No reference Code, simple idea-gen")
        
        if background and ref_code:
            prompt += "The Background Information and Reference Code are closely related. The proposed idea should be innovative, building upon the Background Information and Reference Code to enhance task performance."
        
        # Add feedback from previous iterations
        if feedback and iteration > 0:
            prompt += "# Previous Feedback\n"
            # Take the most recent feedback entries, up to 3
            recent_feedback = sorted(
                feedback, 
                key=lambda x: x.get("iteration", 0), 
                reverse=True
            )[:3]
            
            for entry in recent_feedback:
                feedback_text = entry.get("text", "")
                feedback_iter = entry.get("iteration", 0)
                prompt += f"Iteration {feedback_iter}: {feedback_text}\n\n"
                
        # Add task description
        prompt += f"# Task\n"
        prompt += f"Generate {count} scientifically plausible hypotheses for the research goal above."
        
        if iteration > 0:
            prompt += f" This is iteration {iteration}, so incorporate the feedback provided."
        
        return prompt
    
    def _build_system_prompt(self, creativity: float) -> str:
        """
        Build system prompt tailored to creativity level.

        Creates system-level instructions that guide the model's idea generation
        style based on the creativity parameter, ranging from conservative to highly
        innovative approaches.

        Args:
            creativity (float): Creativity level 0-1 where:
                >0.8: highly innovative and out-of-the-box
                >0.5: creative but grounded in principles
                <=0.5: conservative and evidence-based

        Returns:
            str: System prompt with tone and quality guidelines
        """
        if creativity > 0.8:
            tone = "highly innovative and out-of-the-box"
        elif creativity > 0.5:
            tone = "creative but grounded in scientific principles"
        else:
            tone = "conservative and strictly evidence-based"
            
        return f"""You are a creative scientific idea generator. Your task is to generate {tone} scientific hypotheses based on all the information given by the user.
Ensure that each idea:
1.Are novel, not obvious from existing literature, and grounded in scientific principles.
2.Propose specific mechanisms or pathways and include a brief explanation of them.
3.Are specific, testable, and can be tested experimentally.
4.Address the research goal directly and have clear scientific significance.
5.Consider constraints and domain knowledge.

Be creative but scientifically rigorous. Propose hypotheses that make unexpected connections between concepts, challenge conventional wisdom, or apply principles from one field to another.

The different scientific hypotheses proposed need to remain separate and cannot be similar.

Your hypotheses should be detailed enough for a scientist in the field to understand and evaluate, but not so detailed that they require specialized knowledge outside the domain. 
"""

    @classmethod
    def from_config(cls, config: Dict[str, Any], model: 'BaseModel') -> 'GenerationAgent':
        """
        Factory method to create GenerationAgent from configuration.

        Args:
            config (Dict[str, Any]): Agent configuration dictionary
            model (BaseModel): Language model instance

        Returns:
            GenerationAgent: Configured instance
        """
        return cls(model, config) 