"""
Method Development Agent for InternAgent

This module implements the Method Development Agent, which transforms conceptual
research hypotheses into detailed, implementable methods with mathematical formulations,
algorithms, and theoretical foundations. The agent focuses on providing comprehensive
technical specifications that enable other researchers to implement the proposed methods.
"""

import logging
from typing import Dict, Any, List, Optional
import os
from .base_agent import BaseAgent, AgentExecutionError

logger = logging.getLogger(__name__)


class MethodDevelopmentAgent(BaseAgent):
    """
    Method Development Agent transforms conceptual ideas into concrete methods.
    
    This agent takes evolving hypotheses and develops them into detailed methods
    with mathematical formulations, algorithms, and implementation details.
    """
    
    def __init__(self, model, config: Dict[str, Any]):
        """
        Initialize the method development agent.
        
        Args:
            model: Language model to use
            config: Configuration dictionary
        """
        super().__init__(model, config)
        
        # Load agent-specific configuration
        self.detail_level = config.get("detail_level", "high")  # low, medium, high
        
    async def execute(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a conceptual hypothesis into a detailed method implementation.
        
        Args:
            context: Dictionary containing:
                - goal: Research goal information
                - hypothesis: The hypothesis to develop into a method
                - paper_context: Relevant papers and literature (optional)
                - feedback: List of feedback entries (optional)
                - iteration: Current iteration number
            params: Dictionary containing optional configuration overrides
                
        Returns:
            Dictionary containing:
                - method_details: Structured method details
        """
        # Extract parameters
        goal = context.get("goal", {})
        hypothesis = context.get("hypothesis", {})
        paper_context = context.get("paper_context", "")
        feedback = context.get("feedback", [])
        baseline_summary = context.get("baseline_summary", "")
        
        if not goal or not hypothesis:
            raise AgentExecutionError("Research goal and hypothesis are required for method development")
        
        # Extract text from hypothesis
        hypothesis_text = hypothesis.get("text", "")
        if not hypothesis_text:
            raise AgentExecutionError("Hypothesis text is required for method development")
            
        # Extract optional parameters
        iteration = context.get("iteration", 0)
        detail_level = params.get("detail_level", self.detail_level)
        
        # Create a JSON schema for the expected output
        output_schema = {
            "type": "object",
            "properties": {
                "method_details": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "A concise name for the method"
                        },
                        "title": {
                            "type": "string",
                            "description": "A descriptive title for the method"
                        },
                        "description": {
                            "type": "string",
                            "description": "High-level overview of the approach"
                        },
                        "statement":{
                            "type": "string",
                            "description": "Statement of novelty and theoretical contributions"
                        },
                        "method": {
                            "type": "string",
                            "description": "Detailed explanation of the method including key steps and techniques. Describe the progression of ideas in a detailed, stepwise manner, clarifying how each stage builds upon the previous ones."
                        },
                    },
                    "required": ["name", "title", "description", "statement", "method"]
                }
            },
            "required": ["method_details"]
        }
        
        # Build the prompt
        prompt = self._build_method_development_prompt(
            goal=goal,
            hypothesis=hypothesis,
            paper_context=paper_context,
            baseline_summary=baseline_summary,
            feedback=feedback,
            iteration=iteration,
            detail_level=detail_level
        )
        
        # Call the model
        system_prompt = self._build_system_prompt()

        try:
            response = await self._call_model(
                prompt=prompt,
                system_prompt=system_prompt,
                schema=output_schema
            )
            
            # Process the response
            method_details = response.get("method_details", {})
            
            if not method_details or not method_details.get("method"):
                logger.warning("Method development agent returned incomplete method details")
                
            # Build the result
            result = {
                "method_details": method_details,
                "metadata": {
                    "hypothesis_id": hypothesis.get("id", ""),
                    "iteration": iteration
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Method development agent execution failed: {str(e)}")
            raise AgentExecutionError(f"Failed to develop method: {str(e)}")
    
    def _build_method_development_prompt(self,
                                      goal: Dict[str, Any],
                                      hypothesis: Dict[str, Any],
                                      paper_context: str,
                                      feedback: List[Dict[str, Any]],
                                      baseline_summary: str,
                                      iteration: int,
                                      detail_level: str) -> str:
        """
        Build the method development prompt.
        
        Args:
            goal: Research goal dictionary
            hypothesis: Hypothesis dictionary
            paper_context: Relevant papers and literature
            feedback: List of feedback entries
            iteration: Current iteration number
            detail_level: Level of detail (low, medium, high)
            
        Returns:
            Formatted prompt string
        """
        # Extract information
        goal_description = goal.get("description", "")
        domain = goal.get("domain", "")
        ref_code_path = goal.get("ref_code_path", "")
        if os.path.exists(ref_code_path):
            if os.path.isfile(ref_code_path):
                logger.info("[FILE] Provide the experimental plan based on the baseline code.")
                with open(ref_code_path, 'r') as f:
                    ref_code= f.read()
            elif os.path.isdir(ref_code_path):
                ref_code = ""
                logger.info("TODO: [PRJ] Provide the experimental plan based on the baseline code.")  
        else:
            ref_code = ""
            logger.error("Default: No reference Code, simple idea-gen")
            
        hypothesis_text = hypothesis.get("text", "")
        hypothesis_rationale = hypothesis.get("rationale", "")
        ori_hypothesis_method = hypothesis.get("method_details", "")
        
        # Build the prompt
        prompt = f"# Research Goal\n{goal_description}\n\n"
        
        # Add domain if available
        if domain:
            prompt += f"# Domain\n{domain}\n\n"
            
        # Add the hypothesis
        prompt += f"# Hypothesis to Implement\n{hypothesis_text}\n\n"
        
        # Add the rationale if available
        if hypothesis_rationale:
            prompt += f"# Hypothesis Rationale\n{hypothesis_rationale}\n\n"
        
        # Add paper context if available
        if paper_context:
            prompt += "# Relevant Literature\n"
            prompt += paper_context + "\n\n"
        
        # if have original hypothesis method, add it
        if ori_hypothesis_method:
            prompt += "# Original Hypothesis Method to be improved\n"
            prompt += ori_hypothesis_method + "\n\n"

        # Add reference code path if available
        if ref_code:
            prompt += f"# Baseline Code \n{ref_code}\n\n"
            
        if baseline_summary:
            prompt += f"# Baseline Summary (Here is a summary of the baseline method. Our method will be adapted and improved based on the baseline code in the future)\n{baseline_summary}\n\n"

        # Add recent feedback
        if feedback:
            prompt += "# Scientist Feedback\n"
            # Sort by iteration and take the most recent
            recent_feedback = sorted(
                feedback, 
                key=lambda x: x.get("iteration", 0),
                reverse=True
            )[:3]
            
            for entry in recent_feedback:
                feedback_text = entry.get("text", "")
                feedback_iter = entry.get("iteration", 0)
                
                if feedback_text:
                    prompt += f"From iteration {feedback_iter}: {feedback_text}\n\n"
        
        # Add task description
        prompt += '''# Task
Transform the hypothesis into a concrete, implementable method with comprehensive technical details and theoretical foundations. 
**You don't need to do method conversions on everything that idea mentions. It should be emphasized that only **1-2** key, innovative, and clearly defined contributions are required, while removing any redundant, unimportant, or superfluous parts.**

Your output should include:
1. A concise name for the method
2. A descriptive title
3. A high-level overview of the approach (1-2 paragraphs)
4. A statement of novelty and theoretical contributions 
5. A detailed explanation of the method

## Method Structure Requirements

### System Architecture
- Provide a clear end-to-end architecture description
- Explicitly explain how different modules interact with each other
- Detail the information flow from input to output
- Specify the role and purpose of each component

### Mathematical Formulations
- Use clear, consistent notation throughout
- Begin with a "Notation" section defining ALL symbols, variables, and parameters
- Provide precise mathematical definitions with domains and constraints
- Explain the rationale behind key mathematical design choices
- Include derivations where non-trivial
- Analyze theoretical properties (convergence, optimality, complexity)

### Algorithmic Workflow
- Present a holistic algorithm that shows the complete execution flow
- Include appropriately abstracted pseudocode (not implementation code)
- Structure pseudocode at the algorithm concept level, avoiding language-specific syntax
- For each complex operation, explain the computational procedure
- Provide time and space complexity analysis

### Implementation Feasibility
- Ensure the method description contains sufficient information for future code implementation
- Include clear algorithmic workflows or pseudocode where appropriate
- Define key data structures and computational procedures conceptually
- Consider computational complexity and practical constraints

### Innovation Statement
- Clearly articulate what makes the approach novel
- Compare theoretical advantages over existing methods
- Highlight unique mathematical or algorithmic contributions
- Identify theoretical guarantees or improvements

Note: Only 1 or 2 clear contributions are required. Do not exceed this amount limit and do not stack contributions together.

Focus on developing a method with strong theoretical foundations and clear algorithmic specifications that others could implement based solely on your description, emphasizing the method's theory and implementation rather than experimental procedures.'''

        return prompt
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the method development agent.
        
        Returns:
            System prompt string
        """
        return """You are a method-development specialist in a multi-agent scientific ideation system with expertise in theoretical computer science, algorithm design, and mathematical modeling. Your task is to transform a conceptual idea into a detailed method with strong theoretical foundations and clear implementation pathways.

Guidelines:
- Provide an integrated view of the entire method, showing how components work together
- Ensure all modules have clear interfaces and interaction patterns
- Define ALL mathematical symbols before using them
- Write pseudocode at the appropriate abstraction level (algorithmic concepts, not programming language syntax)
- Explicitly state the method's novelty and theoretical contributions
- Focus on mathematical soundness and algorithmic clarity
- Ensure the method is theoretically justified and practically implementable
- Balance formal rigor with intuitive explanation

Avoid common pitfalls:
- Don't present modules in isolation without explaining their interactions
- Don't use undefined symbols or notation in formulations
- Don't write pseudocode that's either too abstract (just module names) or too implementation-specific (language-dependent code)
- Don't neglect to highlight what makes the method novel or innovative
- Don't focus on experimental procedures over theoretical foundations
- Don't leave ambiguities in algorithm descriptions that would hinder implementation

**It should be emphasized that only 1-2 key, innovative, and clearly defined contributions are required, while removing any redundant, unimportant, or superfluous parts.**

Your goal is to develop a method with strong theoretical grounding and clear algorithmic specifications that could be implemented by other researchers based on your detailed description of its mathematical foundations and computational procedures.
"""