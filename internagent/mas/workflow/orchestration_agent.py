"""
Orchestration Agent for InternAgent

Implements central workflow orchestration coordinating multi-agent idea generation,
refinement, and selection. Manages iterative flow between specialized agents (generation,
reflection, evolution, ranking, method development, refinement), literature sources,
and scientist feedback. Controls state transitions through workflow phases, handles
concurrent task execution with semaphores, and maintains session persistence via memory
manager. Supports configurable iteration limits, top-N idea selection, and dynamic
agent routing based on workflow state.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from ..agents.base_agent import BaseAgent
from ..memory.memory_manager import MemoryManager
from ..models.model_factory import ModelFactory
from .data_type import Idea, Task, WorkflowSession, WorkflowState

logger = logging.getLogger(__name__)


class OrchestrationAgent:
    """
    Central coordinator for multi-agent research workflow.

    Orchestrates complete research pipeline from idea generation through method
    refinement. Manages workflow sessions with state machines (INITIAL → GENERATING →
    REFLECTING → EXTERNAL_DATA → EVOLVING → RANKING → METHOD_DEVELOPMENT → REFINING →
    COMPLETED), coordinates specialized agents, handles scientist feedback integration,
    and ensures proper sequencing of research phases. Supports concurrent task execution,
    session persistence, state change callbacks, and iterative refinement cycles.

    Attributes:
        config (Dict[str, Any]): Configuration dictionary
        memory_manager (MemoryManager): Persistent storage manager
        model_factory (ModelFactory): Model instance creator
        agent_registry (Dict[str, BaseAgent]): Registered specialized agents
        max_iterations (int): Maximum refinement iterations
        top_ideas_count (int): Number of top ideas to select
        top_ideas_evo (bool): Evolve only top ideas in iterations
        max_concurrent_tasks (int): Concurrent task limit
        active_sessions (Dict): Currently active workflow sessions
        session_callbacks (Dict): State change callback functions
    """

    def __init__(self,
                config: Dict[str, Any],
                memory_manager: MemoryManager,
                model_factory: ModelFactory = None,
                agent_registry: Dict[str, BaseAgent] = None):
        """
        Initialize orchestration agent with configuration and dependencies.

        Loads workflow configuration (max iterations, top ideas count, concurrency limits),
        initializes agent registry and model factory, and prepares session tracking structures.

        Args:
            config (Dict[str, Any]): Configuration with workflow settings
            memory_manager (MemoryManager): Manager for session persistence
            model_factory (ModelFactory): Factory for model creation (optional)
            agent_registry (Dict[str, BaseAgent]): Specialized agents by type (optional)
        """
        self.config = config
        self.memory_manager = memory_manager
        self.model_factory = model_factory or ModelFactory()
        self.agent_registry = agent_registry or {}

        # Load workflow configuration
        workflow_config = config.get("workflow", {})
        self.max_iterations = workflow_config.get("max_iterations", 2)
        self.top_ideas_count = workflow_config.get("top_ideas_count", 3)
        self.top_ideas_evo = workflow_config.get("top_ideas_evo", False)
        self.max_concurrent_tasks = workflow_config.get("max_concurrent_tasks", 5)

        # Active session tracking
        self.active_sessions = {}
        self.session_callbacks = {}

        logger.info(f"OrchestrationAgent initialized with max_iterations={self.max_iterations}, "
                   f"top_ideas_count={self.top_ideas_count}")

    async def create_session(self,
                           goal_description: str,
                           domain: str,
                           background: str = "",
                           ref_code_path: str = None,
                           constraints: List[str] = None) -> str:
        """
        Create new workflow session for research task.

        Initializes workflow session with research goal, domain context, and constraints.
        Creates task and session objects, stores in memory, and activates for execution.

        Args:
            goal_description (str): Research objective description
            domain (str): Research domain (e.g., "machine learning", "NLP")
            background (str): Additional context (optional)
            ref_code_path (str): Path to reference code baseline (optional)
            constraints (List[str]): Research constraints (optional)

        Returns:
            str: Unique session identifier for tracking
        """
        task_id = f"task_{int(time.time())}"
        task = Task(
            id=task_id,
            description=goal_description,
            domain=domain,
            background=background,
            ref_code_path=ref_code_path,
            constraints=constraints or []
        )

        session_id = f"session_{int(time.time())}"
        session = WorkflowSession(
            id=session_id,
            task=task,
            max_iterations=self.max_iterations
        )

        await self.memory_manager.store_session(session)
        self.active_sessions[session_id] = session

        logger.info(f"Created new session {session_id} for task: {goal_description}")
        return session_id

    async def run_session(self,
                        session_id: str,
                        on_state_change: Optional[Callable] = None) -> WorkflowSession:
        """
        Execute workflow session from current state to completion.

        Runs session through workflow phases using state machine, executing appropriate
        agent tasks at each phase. Continues until completion, error, or awaiting feedback
        state. Stores session state after each phase and triggers callbacks on transitions.

        Args:
            session_id (str): Session identifier to execute
            on_state_change (Optional[Callable]): Callback for state transitions (optional)

        Returns:
            WorkflowSession: Updated session with execution results

        Raises:
            Exception: If phase execution fails or session not found
        """
        session = await self._get_session(session_id)

        if on_state_change:
            self.session_callbacks[session_id] = on_state_change

        if session.state == WorkflowState.INITIAL:
            await self._update_session_state(session, WorkflowState.GENERATING)

        try:
            while session.state not in [WorkflowState.COMPLETED, WorkflowState.ERROR]:
                await self._execute_current_phase(session)
                await self.memory_manager.store_session(session)

                if session.state == WorkflowState.AWAITING_FEEDBACK:
                    logger.info(f"Session {session_id} is awaiting feedback")
                    break

            if session.state == WorkflowState.COMPLETED:
                session.completed_at = datetime.now()
                await self.memory_manager.store_session(session)
                logger.info(f"System: Session {session_id} completed successfully after {session.iterations_completed} iterations")

            return session

        except Exception as e:
            logger.error(f"Error running session {session_id}: {str(e)}")
            await self._update_session_state(session, WorkflowState.ERROR)
            await self.memory_manager.store_session(session)
            raise

    async def add_feedback(self,
                         session_id: str,
                         feedback: dict,
                         target_idea_ids: List[str] = None) -> str:
        """
        Add scientist feedback to workflow session.

        Incorporates external feedback into session history, optionally targeting specific
        ideas. If session is awaiting feedback, transitions to reflection phase. Stores
        updated session state with feedback entry including timestamp and iteration context.

        Args:
            session_id (str): Target session identifier
            feedback (dict): Feedback content and metadata
            target_idea_ids (List[str]): Specific ideas to address (optional)

        Returns:
            str: Confirmation message with session ID
        """
        session = await self._get_session(session_id)

        feedback_entry = {
            "text": feedback,
            "timestamp": datetime.now().isoformat(),
            "target_ideas": target_idea_ids,
            "iteration": session.iterations_completed
        }
        session.feedback_history.append(feedback_entry)

        if session.state == WorkflowState.AWAITING_FEEDBACK:
            await self._update_session_state(session, WorkflowState.REFLECTING)

        await self.memory_manager.store_session(session)
        return f"Feedback added to session {session_id}"

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve current session status and metadata.

        Returns comprehensive session information including current state, iteration progress,
        idea counts, timestamps, and top-ranked ideas with scores.

        Args:
            session_id (str): Session identifier to query

        Returns:
            Dict[str, Any]: Status dictionary with keys: id, task, state, iterations_completed,
                max_iterations, idea_count, started_at, age_hours, top_ideas (list of dicts)
        """
        session = await self._get_session(session_id)

        status = {
            "id": session.id,
            "task": session.task.description,
            "state": session.state.value,
            "iterations_completed": session.iterations_completed,
            "max_iterations": session.max_iterations,
            "idea_count": len(session.ideas),
            "started_at": session.started_at.isoformat(),
            "age_hours": (datetime.now() - session.started_at).total_seconds() / 3600,
            "top_ideas": []
        }

        if session.top_ideas:
            for idea_id in session.top_ideas:
                idea = next((i for i in session.ideas if i.id == idea_id), None)
                if idea:
                    status["top_ideas"].append({
                        "id": idea.id,
                        "text": idea.text,
                        "score": idea.score
                    })

        return status

    async def get_top_ideas(self, session_id: str, include_all: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve top-ranked ideas from session.

        Returns ideas marked as top performers by ranking agent. Optionally includes
        ideas from all iterations or only the latest iteration.

        Args:
            session_id (str): Session identifier to query
            include_all (bool): Include ideas from all iterations if True (default: False)

        Returns:
            List[Dict[str, Any]]: Top ideas as dictionaries with all idea attributes
        """
        session = await self._get_session(session_id)

        if include_all:
            ideas = session.ideas
        else:
            latest_iter = max(i.iteration for i in session.ideas) if session.ideas else 0
            ideas = [i for i in session.ideas if i.iteration == latest_iter]

        ideas = [i for i in ideas if i.id in session.top_ideas]
        return [i.to_dict() for i in ideas]

    async def get_ideas(self, session_id: str, limit: int = 10, include_all: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve ideas from session with optional filtering.

        Returns ideas sorted by score, optionally limited to top N and filtered by iteration.
        Useful for accessing all generated ideas beyond just top-ranked selections.

        Args:
            session_id (str): Session identifier to query
            limit (int): Maximum number of ideas to return (default: 10)
            include_all (bool): Include all iterations if True, else latest only (default: False)

        Returns:
            List[Dict[str, Any]]: Ideas as dictionaries sorted by score (highest first)
        """
        session = await self._get_session(session_id)

        if include_all:
            ideas = session.ideas
        else:
            latest_iter = max(i.iteration for i in session.ideas) if session.ideas else 0
            ideas = [i for i in session.ideas if i.iteration == latest_iter]

        ideas = sorted(ideas, key=lambda i: i.score, reverse=True)[:limit]
        return [i.to_dict() for i in ideas]

    # Private methods
    async def _get_session(self, session_id: str) -> WorkflowSession:
        """
        Retrieve session from active cache or memory storage.

        Checks active sessions first for performance, falls back to memory manager
        if not cached. Loads and caches session if found in storage.

        Args:
            session_id (str): Session identifier to retrieve

        Returns:
            WorkflowSession: Session object with current state

        Raises:
            ValueError: If session not found in active sessions or memory
        """
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        session = await self.memory_manager.load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        self.active_sessions[session_id] = session
        return session

    def _get_agent_info_for_state(self, state: WorkflowState) -> str:
        """
        Map workflow state to responsible agent name.

        Returns human-readable agent name for logging and display purposes.
        Maps workflow states to their corresponding agent handlers.

        Args:
            state (WorkflowState): Current workflow state

        Returns:
            str: Agent name or "Unknown Agent" if unmapped
        """
        agent_mapping = {
            WorkflowState.GENERATING: "Idea Innovation Agent",
            WorkflowState.EVOLVING: "Idea Innovation Agent",
            WorkflowState.REFLECTING: "Assessment Agent",
            WorkflowState.RANKING: "Assessment Agent",
            WorkflowState.METHOD_DEVELOPMENT: "Method Development Agent",
            WorkflowState.REFINING: "Method Development Agent",
            WorkflowState.EXTERNAL_DATA: "Survey Agent",
            WorkflowState.AWAITING_FEEDBACK: "System",
            WorkflowState.INITIAL: "System",
            WorkflowState.COMPLETED: "System",
            WorkflowState.ERROR: "System"
        }
        return agent_mapping.get(state, "Unknown Agent")

    async def _update_session_state(self, session: WorkflowSession, new_state: WorkflowState) -> None:
        """
        Transition session to new workflow state.

        Updates session state, sets method phase flag if entering method development,
        logs state transition with agent context, and triggers registered callbacks.

        Args:
            session (WorkflowSession): Session to update
            new_state (WorkflowState): Target workflow state
        """
        old_state = session.state
        session.state = new_state

        if new_state == WorkflowState.METHOD_DEVELOPMENT:
            session.method_phase = True

        # Log state transition with agent context
        old_agent_info = self._get_agent_info_for_state(old_state)
        new_agent_info = self._get_agent_info_for_state(new_state)
        logger.info(f"Session {session.id}: {old_agent_info} -> {new_agent_info}")

        if session.id in self.session_callbacks:
            try:
                callback = self.session_callbacks[session.id]
                await callback(session, old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {str(e)}")

    async def _execute_current_phase(self, session: WorkflowSession) -> None:
        """
        Route session to appropriate phase handler based on current state.

        Dispatches execution to specialized phase methods (generation, reflection, evolution,
        ranking, method development, refinement, literature, awaiting feedback). Transitions
        to error state if handler not found.

        Args:
            session (WorkflowSession): Session to execute
        """
        phase_handlers = {
            WorkflowState.GENERATING: self._run_generation_phase,
            WorkflowState.REFLECTING: self._run_reflection_phase,
            WorkflowState.EVOLVING: self._run_evolution_phase,
            WorkflowState.METHOD_DEVELOPMENT: self._run_method_development_phase,
            WorkflowState.REFINING: self._run_refinement_phase,
            WorkflowState.RANKING: self._run_ranking_phase,
            WorkflowState.EXTERNAL_DATA: self._run_external_data_phase,
            WorkflowState.AWAITING_FEEDBACK: self._run_awaiting_feedback_phase,
        }

        handler = phase_handlers.get(session.state)
        if handler:
            await handler(session)
        else:
            logger.error(f"Unknown state: {session.state}")
            await self._update_session_state(session, WorkflowState.ERROR)

    async def _run_generation_phase(self, session: WorkflowSession) -> None:
        """
        Execute idea generation phase.

        Invokes generation agent to create initial hypothesis candidates. Optionally runs
        survey agent for literature if configured. Creates idea objects from agent responses
        and adds to session. Transitions to reflection phase on success.

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Idea Innovation Agent: Starting idea generation for session {session.id}")

        generation_agent = self._get_agent("generation")
        if not generation_agent:
            raise ValueError("Generation agent initialization failed")

        paper_lst = None
        survey_report = None
        if generation_agent.config.get("do_survey", False):
            logger.info(f"Survey Agent: Conduct in-depth literature research on task {session.id}")
            survey_agent = self._get_agent("survey")
            if survey_agent:
                survey_outputs = await survey_agent.execute(session.task.to_dict(), {})
                if isinstance(survey_outputs, dict):
                    paper_lst = survey_outputs.get("papers", [])
                    search_history = survey_outputs.get("search_queries", [])
                else:
                    paper_lst = survey_outputs
                    search_history = []

                summary_agent = self._get_agent("literature_summary")
                if summary_agent and paper_lst:
                    task_dict = session.task.to_dict()
                    summary_context = {
                        "description": task_dict.get("description", ""),
                        "domain": task_dict.get("domain", ""),
                        "papers": paper_lst,
                        "search_queries": search_history,
                    }
                    try:
                        survey_report = await summary_agent.execute(summary_context, {})
                    except Exception as e:
                        logger.error(f"Literature summary agent failed: {e}")
                        survey_report = None
            else:
                logger.warning("Survey agent requested but not available")

        context = {
            "goal": session.task.to_dict(),
            "iteration": session.iterations_completed,
            "feedback": session.feedback_history,
            "paper_lst": paper_lst,
            "survey_report": survey_report
        }

        try:
            response = await generation_agent.execute(context, {})

            for idx, idea_data in enumerate(response.get("hypotheses", [])):
                idea = Idea(
                    id=f"idea_{int(time.time())}_{idx}",
                    text=idea_data.get("text", ""),
                    rationale=idea_data.get("rationale", ""),
                    baseline_summary=response.get("baseline_summary", ""),
                    iteration=session.iterations_completed
                )
                session.ideas.append(idea)

            logger.info(f"Idea Innovation Agent: Generated {len(response.get('hypotheses', []))} ideas for session {session.id}")
            await self._update_session_state(session, WorkflowState.REFLECTING)

        except Exception as e:
            logger.error(f"Error in generation phase: {str(e)}")
            await self._update_session_state(session, WorkflowState.ERROR)

    async def _run_reflection_phase(self, session: WorkflowSession) -> None:
        """
        Execute reflection and critique phase.

        Invokes reflection agent to critically evaluate current iteration ideas. Processes
        ideas concurrently, extracts feedback based on type (global/local), and attaches
        critiques to ideas. Transitions to literature gathering phase on success.

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Assessment Agent: Starting reflection and critique for session {session.id}")

        reflection_agent = self._get_agent("reflection")
        if not reflection_agent:
            raise ValueError("Reflection agent initialization failed")

        current_iter = session.iterations_completed
        ideas = self._get_current_ideas(session, current_iter)

        feedback_content = self._extract_feedback_content(session, ideas)

        tasks = []
        for idea in ideas:
            context = {
                "goal": session.task.to_dict(),
                "hypothesis": idea.to_dict(),
                "iteration": current_iter,
                "feedback": feedback_content if isinstance(feedback_content, str)
                          else feedback_content.get('comment', '') if feedback_content.get("id") == idea.id else ""
            }
            tasks.append(reflection_agent.execute(context, {}))

        try:
            results = await asyncio.gather(*tasks)

            for idx, idea in enumerate(ideas):
                critiques = results[idx].get("critiques", [])
                if idea.to_dict().get("method_details"):
                    idea.method_critiques = critiques
                else:
                    idea.critiques = critiques

            logger.info(f"Assessment Agent: Completed reflection and critique for {len(ideas)} ideas in session {session.id}")
            await self._update_session_state(session, WorkflowState.EXTERNAL_DATA)

        except Exception as e:
            logger.error(f"Error in reflection phase: {str(e)}")
            await self._update_session_state(session, WorkflowState.ERROR)

    async def _run_external_data_phase(self, session: WorkflowSession) -> None:
        """
        Execute paper gathering phase.

        Invokes scholar agent to retrieve supporting literature and evidence for current
        ideas. Uses semaphore for concurrency control. Attaches evidence and references
        to ideas. Transitions to refinement phase if in method phase, else evolution phase.

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Survey Agent: Starting literature gathering for session {session.id}")

        scholar_agent = self._get_agent("scholar")
        if not scholar_agent:
            raise ValueError("Scholar agent initialization failed")

        current_iter = session.iterations_completed
        ideas = self._get_current_ideas(session, current_iter)

        # Use semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        tasks = []

        async def execute_with_semaphore(idea):
            async with semaphore:
                context = {
                    "goal": session.task.to_dict(),
                    "hypothesis": idea.to_dict(),
                    "iteration": current_iter
                }
                return await scholar_agent.execute(context, {"method_phase": session.method_phase})

        for idea in ideas:
            tasks.append(execute_with_semaphore(idea))

        try:
            results = await asyncio.gather(*tasks)

            for idx, idea in enumerate(ideas):
                if not session.method_phase:
                    idea.evidence = results[idx].get("evidence", [])
                    idea.references = results[idx].get("references", [])
                else:
                    idea.refine_evidence = results[idx].get("evidence", [])

            next_state = WorkflowState.REFINING if session.method_phase else WorkflowState.EVOLVING
            logger.info(f"Survey Agent: Completed literature gathering for {len(ideas)} ideas in session {session.id}")
            await self._update_session_state(session, next_state)

        except Exception as e:
            logger.error(f"Error in literature survey phase: {str(e)}")
            await self._update_session_state(session, WorkflowState.ERROR)

    async def _run_evolution_phase(self, session: WorkflowSession) -> None:
        """
        Execute idea evolution phase.

        Invokes evolution agent to refine current iteration ideas by addressing critiques
        and incorporating evidence. Creates evolved idea variants with parent tracking,
        adds to session for next iteration. Transitions to ranking phase on success.

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Idea Innovation Agent: Starting idea evolution for session {session.id}")

        evolution_agent = self._get_agent("evolution")
        if not evolution_agent:
            raise ValueError("Evolution agent initialization failed")

        current_iter = session.iterations_completed
        ideas = self._get_current_ideas(session, current_iter)

        evolved_ideas = []
        for idea in ideas:
            context = {
                "goal": session.task.to_dict(),
                "hypothesis": idea.to_dict(),
                "critiques": idea.critiques,
                "evidence": idea.evidence,
                "feedback": session.feedback_history,
                "iteration": current_iter
            }

            try:
                response = await evolution_agent.execute(context, {})

                evolutions = response.get("evolved_hypotheses", [])
                for idx, evolution in enumerate(evolutions):
                    evolved_idea = Idea(
                        id=f"idea_{int(time.time())}_{idx}_{idea.id}",
                        text=evolution.get("text", ""),
                        rationale=evolution.get("rationale", ""),
                        baseline_summary=idea.baseline_summary,
                        iteration=current_iter + 1,
                        parent_id=idea.id
                    )
                    evolved_ideas.append(evolved_idea)

            except Exception as e:
                logger.error(f"Error evolving idea {idea.id}: {str(e)}")

        session.ideas.extend(evolved_ideas)
        logger.info(f"Idea Innovation Agent: Evolved {len(evolved_ideas)} ideas from {len(ideas)} parent ideas in session {session.id}")
        await self._update_session_state(session, WorkflowState.RANKING)

    async def _run_ranking_phase(self, session: WorkflowSession) -> None:
        """
        Execute idea ranking and scoring phase.

        Invokes ranking agent to evaluate and score ideas from current iteration. Updates
        idea scores and identifies top performers. Increments iteration counter. Transitions
        based on phase (method phase → awaiting feedback, max iterations → method development,
        else → awaiting feedback).

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Assessment Agent: Starting idea ranking and scoring for session {session.id}")

        ranking_agent = self._get_agent("ranking")
        if not ranking_agent:
            raise ValueError("Ranking agent initialization failed")

        current_iter = session.iterations_completed
        ideas = [i for i in session.ideas if i.iteration == (current_iter + 1)]

        if not ideas:
            logger.warning(f"No ideas found for iteration {current_iter}")
            await self._update_session_state(session, WorkflowState.ERROR)
            return

        context = {
            "goal": session.task.to_dict(),
            "hypotheses": [i.to_dict() for i in ideas],
            "iteration": current_iter + 1,
            "feedback": session.feedback_history
        }

        try:
            response = await ranking_agent.execute(context, {})

            # Update idea scores
            ranked_ideas = response.get("ranked_hypotheses", [])
            for ranked in ranked_ideas:
                idea_id = ranked.get("id")
                if idea_id:
                    idea = next((i for i in ideas if i.id == idea_id), None)
                    if idea:
                        idea.score = ranked.get("overall_score", 0.0)
                        idea.scores = ranked.get("criteria_scores", {})

            session.top_ideas = response.get("top_hypotheses", [])
            session.iterations_completed += 1

            logger.info(f"Assessment Agent: Completed ranking of {len(ideas)} ideas, selected top {len(session.top_ideas)} for session {session.id}")
            # Determine next state
            if session.method_phase:
                await self._update_session_state(session, WorkflowState.AWAITING_FEEDBACK)
            elif session.iterations_completed >= session.max_iterations:
                await self._update_session_state(session, WorkflowState.METHOD_DEVELOPMENT)
            else:
                await self._update_session_state(session, WorkflowState.AWAITING_FEEDBACK)

        except Exception as e:
            logger.error(f"Error in ranking phase: {str(e)}")
            await self._update_session_state(session, WorkflowState.ERROR)

    async def _run_method_development_phase(self, session: WorkflowSession) -> None:
        """
        Execute method development phase.

        Transforms top-ranked ideas into detailed implementable methods. Gathers additional
        evidence via scholar agent if needed. Invokes method development agent with concurrency
        control to create method specifications. Attaches method details to ideas with fallback
        on errors. Transitions to reflection phase for method critique.

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Method Development Agent: Starting method development for session {session.id}")

        method_dev_agent = self._get_agent("method_development")
        if not method_dev_agent:
            logger.warning("Method development agent not found, skipping to ranking phase")
            await self._update_session_state(session, WorkflowState.RANKING)
            return

        current_iter = session.iterations_completed
        ideas = self._get_current_ideas(session, current_iter)

        # Filter to only process top ideas (after ranking phase)
        if session.top_ideas:
            ideas = [i for i in ideas if i.id in session.top_ideas]
            logger.info(f"Method Development Agent: Processing {len(ideas)} top ideas for session {session.id}")

        # Gather evidence if needed
        scholar_agent = self._get_agent("scholar")
        if scholar_agent:
            await self._gather_evidence_for_ideas(ideas, scholar_agent, session)

        # Process method development with concurrency control
        semaphore = asyncio.Semaphore(3)
        tasks = []

        async def develop_method(idea):
            async with semaphore:
                related_evidence = self._get_idea_evidence(idea, session)
                paper_context = self._format_paper_context(related_evidence)

                context = {
                    "goal": session.task.to_dict(),
                    "hypothesis": idea.to_dict(),
                    "baseline_summary": idea.baseline_summary,
                    "paper_context": paper_context,
                    "feedback": session.feedback_history,
                    "iteration": session.iterations_completed,
                }

                return await method_dev_agent.execute(context, {})

        for idea in ideas:
            tasks.append((idea, develop_method(idea)))

        try:
            for idea, task in tasks:
                try:
                    result = await task
                    method_details = result.get("method_details", {})

                    idea.method_details = {
                        "name": method_details.get("name", idea.text[:20]),
                        "title": method_details.get("title", idea.text),
                        "description": method_details.get("description", ""),
                        "statement": method_details.get("statement", ""),
                        "method": method_details.get("method", ""),
                    }

                    logger.info(f"Method development completed for idea {idea.id} with method_details keys: {list(idea.method_details.keys())}")

                except Exception as e:
                    logger.error(f"Error in method development for idea {idea.id}: {str(e)}")
                    # Set fallback method details for failed method development
                    idea.method_details = {
                        "name": f"failed_{idea.text[:20] if idea.text else 'unnamed'}",
                        "title": idea.text if idea.text else "Failed Method Development",
                        "description": idea.text if idea.text else "Method development encountered an error",
                        "statement": f"Method development failed: {str(e)}",
                        "method": "Method development failed - see statement for details",
                    }
                    logger.info(f"Set fallback method_details for failed idea {idea.id}")

            logger.info(f"Method Development Agent: Developed methods for {len(ideas)} ideas in session {session.id}")
            await self._update_session_state(session, WorkflowState.REFLECTING)

        except Exception as e:
            logger.error(f"Error in method development phase: {str(e)}")
            await self._update_session_state(session, WorkflowState.ERROR)

    async def _run_refinement_phase(self, session: WorkflowSession):
        """
        Execute method refinement phase.

        Refines developed methods by addressing critiques and incorporating literature.
        Processes only top ideas with valid method details. Invokes refinement agent to
        produce improved method versions. Attaches refined methods to ideas. Transitions
        to completion state when done.

        Args:
            session (WorkflowSession): Session to process
        """
        logger.info(f"Method Development Agent: Starting method refinement for session {session.id}")

        current_iter = session.iterations_completed
        ideas = self._get_current_ideas(session, current_iter)

        # Filter to only process top ideas that went through method development
        if session.top_ideas:
            ideas = [i for i in ideas if i.id in session.top_ideas]
            logger.info(f"Method Development Agent: Processing {len(ideas)} top ideas for refinement in session {session.id}")

        if not ideas:
            logger.warning(f"No active ideas for refinement in session {session.id}")
            await self._update_session_state(session, WorkflowState.COMPLETED)
            return

        refinement_agent = self._get_agent("refinement")
        if not refinement_agent:
            logger.warning("Refinement agent not found, skipping to completion")
            await self._update_session_state(session, WorkflowState.COMPLETED)
            return

        for idea in ideas:
            try:
                idea_dict = idea.to_dict()
                method_details = idea_dict.get("method_details", {})

                # Skip ideas without proper method details
                if not method_details or not any(method_details.values()):
                    logger.warning(f"Refinement Agent: Skipping idea {idea.id} - missing or empty method_details")
                    continue

                logger.info(f"Refinement Agent: Processing idea {idea.id} with method_details keys: {list(method_details.keys())}")

                refinement_result = await refinement_agent.execute({
                    "goal": session.task.to_dict(),
                    "hypothesis": idea_dict,
                    "literature": idea.refine_evidence,
                }, {})

                refined_method = refinement_result.get("refined_method", {})
                if refined_method:
                    idea.refined_method_details = refined_method
                    logger.info(f"Updated idea {idea.id} with refined method")
                else:
                    logger.warning(f"No refined method produced for idea {idea.id}")

            except Exception as e:
                logger.error(f"Error in refinement phase for idea {idea.id}: {str(e)}")

        logger.info(f"Method Development Agent: Completed method refinement for {len(ideas)} ideas in session {session.id}")
        await self._update_session_state(session, WorkflowState.COMPLETED)

    async def _run_awaiting_feedback_phase(self, session: WorkflowSession) -> None:
        """
        Handle awaiting feedback state.

        Passive phase where session waits for external scientist feedback via add_feedback().
        Does not execute agent tasks. External systems detect this state and provide input.
        Session automatically transitions to reflection phase when feedback is added.

        Args:
            session (WorkflowSession): Session in waiting state
        """
        logger.info(f"System: Session {session.id} is awaiting external feedback")

        # This phase doesn't do anything - it just waits for external feedback
        # The external IdeaGenerator (stage.py) will detect this state and provide feedback
        # Once feedback is added via add_feedback(), the session will transition to REFLECTING

        # For safety, if we've been waiting too long or something goes wrong,
        # we should have a timeout or fallback mechanism
        pass

    # Helper methods
    def _get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """
        Retrieve agent from registry by type.

        Looks up specialized agent instance for given type. Logs warning if not found.

        Args:
            agent_type (str): Agent type identifier (e.g., "generation", "reflection")

        Returns:
            Optional[BaseAgent]: Agent instance or None if not registered
        """
        if agent_type not in self.agent_registry:
            logger.warning(f"Agent type {agent_type} initialization failed")
            return None
        return self.agent_registry[agent_type]

    def _get_current_ideas(self, session: WorkflowSession, current_iter: int) -> List[Idea]:
        """
        Retrieve ideas for current iteration with optional filtering.

        Returns ideas from specified iteration. If top_ideas_evo is enabled and not first
        iteration, filters to only top-ranked ideas for focused evolution.

        Args:
            session (WorkflowSession): Session containing ideas
            current_iter (int): Iteration number to filter by

        Returns:
            List[Idea]: Filtered idea list for current iteration
        """
        ideas = [i for i in session.ideas if i.iteration == current_iter]

        if current_iter > 0 and self.top_ideas_evo and session.top_ideas:
            ideas = [i for i in ideas if i.id in session.top_ideas]

        return ideas

    def _extract_feedback_content(self, session: WorkflowSession, ideas: List[Idea]):
        """
        Extract and format feedback content based on feedback type.

        Retrieves most recent feedback and processes based on type (global applies to all
        ideas, local targets specific ideas). Filters idea list for local feedback.

        Args:
            session (WorkflowSession): Session with feedback history
            ideas (List[Idea]): Ideas to filter (modified in place for local feedback)

        Returns:
            str or dict: Feedback content (str for global, dict for local) or empty string
        """
        if not session.feedback_history:
            logger.info("No feedback needed in the initial iteration")
            return ""

        feedback = sorted(
            session.feedback_history,
            key=lambda x: x.get("iteration", 0),
            reverse=True
        )[-1]

        fb_type = feedback['text'].get("type", "global")
        if fb_type == "global":
            return feedback['text'].get("content", "")
        elif fb_type == "local":
            feedback_content = feedback['text'].get("content", [])
            feedback_id_list = [fb_i.get("id", "") for fb_i in feedback_content]
            # Filter ideas based on feedback IDs
            ideas[:] = [i for i in ideas if i.id in feedback_id_list]
            return feedback_content
        else:
            logger.warning("Invalid feedback type, using empty string")
            return ""

    async def _gather_evidence_for_ideas(self, ideas: List[Idea], scholar_agent, session):
        """
        Gather supporting evidence for ideas lacking literature references.

        Invokes scholar agent concurrently for ideas without existing evidence. Attaches
        retrieved evidence and references to idea objects. Used during method development
        when evidence is needed but not yet collected.

        Args:
            ideas (List[Idea]): Ideas to gather evidence for
            scholar_agent: Scholar agent instance for evidence retrieval
            session: Session context for evidence gathering
        """
        tasks = []
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

        async def gather_evidence(idea):
            async with semaphore:
                context = {
                    "goal": session.task.to_dict(),
                    "hypothesis": idea.to_dict(),
                    "iteration": session.iterations_completed,
                }
                return await scholar_agent.execute(context, {})

        for idea in ideas:
            if not idea.evidence:
                tasks.append((idea, gather_evidence(idea)))

        if tasks:
            logger.info(f"Gathering evidence for {len(tasks)} ideas in method development phase")
            try:
                for idea, task in tasks:
                    try:
                        result = await task
                        idea.evidence = result.get("evidence", [])
                        idea.references = result.get("references", [])
                        logger.info(f"Evidence gathered for idea {idea.id}: {len(idea.evidence)} items")
                    except Exception as e:
                        logger.error(f"Error gathering evidence for idea {idea.id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error in evidence gathering: {str(e)}")

    def _get_idea_evidence(self, idea: Idea, session: WorkflowSession) -> List[Dict[str, Any]]:
        """
        Retrieve evidence for idea with parent fallback.

        Returns idea's direct evidence if available, otherwise inherits from parent idea
        if parent exists. Supports evidence propagation through idea evolution lineage.

        Args:
            idea (Idea): Idea to get evidence for
            session (WorkflowSession): Session containing parent ideas

        Returns:
            List[Dict[str, Any]]: Evidence items with title/content/relevance
        """
        related_evidence = idea.evidence

        if not related_evidence and idea.parent_id:
            parent_idea = next((i for i in session.ideas if i.id == idea.parent_id), None)
            if parent_idea and parent_idea.evidence:
                related_evidence = parent_idea.evidence

        return related_evidence

    def _format_paper_context(self, related_evidence: List[Dict[str, Any]]) -> str:
        """
        Format evidence items into structured context string.

        Converts evidence dictionaries into formatted text with title, content, and relevance
        sections. Used for providing literature context to method development agent.

        Args:
            related_evidence (List[Dict[str, Any]]): Evidence items with metadata

        Returns:
            str: Formatted context with double-newline separated entries
        """
        paper_summaries = []
        for evidence_item in related_evidence:
            if isinstance(evidence_item, dict):
                title = evidence_item.get('title', '')
                content = evidence_item.get('content', '')
                relevance = evidence_item.get('relevance', '')
                paper_summaries.append(f"Title: {title}\nContent: {content}\nRelevance: {relevance}")

        return "\n\n".join(paper_summaries)
