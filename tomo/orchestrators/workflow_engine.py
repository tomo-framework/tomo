"""Workflow execution engine for Tomo."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
from ..core.registry import ToolRegistry
from ..core.runner import ToolRunner
from ..adapters.base import BaseAdapter
from .execution import ExecutionEngine
from .workflow import (
    Workflow, 
    WorkflowStep, 
    WorkflowState, 
    WorkflowStatus, 
    StepStatus, 
    StepResult, 
    WorkflowContext
)


class WorkflowEngineError(Exception):
    """Exception raised by workflow engine."""
    pass


class WorkflowEngine:
    """Engine for executing declarative workflows."""
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        adapter: Optional[BaseAdapter] = None,
        max_parallel_steps: int = 5,
        step_timeout: Optional[float] = None,
        enable_retries: bool = True,
    ):
        """Initialize workflow engine.
        
        Args:
            registry: Tool registry for tool steps
            adapter: Adapter for LLM format conversion
            max_parallel_steps: Maximum number of steps to run in parallel
            step_timeout: Timeout for individual steps in seconds
            enable_retries: Whether to enable step retries
        """
        self.registry = registry
        self.adapter = adapter
        self.max_parallel_steps = max_parallel_steps
        self.step_timeout = step_timeout
        self.enable_retries = enable_retries
        
        # Initialize execution components if registry/adapter provided
        if registry and adapter:
            self.runner = ToolRunner(registry)
            self.execution_engine = ExecutionEngine(self.runner, adapter)
        else:
            self.runner = None
            self.execution_engine = None
        
        # Event handlers
        self.on_workflow_start: Optional[Callable[[Workflow, WorkflowState], None]] = None
        self.on_workflow_complete: Optional[Callable[[Workflow, WorkflowState], None]] = None
        self.on_workflow_error: Optional[Callable[[Workflow, WorkflowState, Exception], None]] = None
        self.on_step_start: Optional[Callable[[WorkflowStep, WorkflowState], None]] = None
        self.on_step_complete: Optional[Callable[[WorkflowStep, StepResult, WorkflowState], None]] = None
        self.on_step_error: Optional[Callable[[WorkflowStep, Exception, WorkflowState], None]] = None
    
    async def execute_workflow(
        self, 
        workflow: Workflow, 
        initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """Execute a workflow from start to finish.
        
        Args:
            workflow: Workflow to execute
            initial_context: Initial context data for the workflow
            
        Returns:
            Final workflow state
            
        Raises:
            WorkflowEngineError: If workflow execution fails
        """
        # Validate workflow
        validation_errors = workflow.validate()
        if validation_errors:
            raise WorkflowEngineError(f"Workflow validation failed: {'; '.join(validation_errors)}")
        
        # Create initial state
        state = workflow.create_state()
        state.start_time = datetime.now()
        state.status = WorkflowStatus.RUNNING
        
        # Initialize context
        if initial_context:
            state.context.update(initial_context)
        
        # Fire start event
        if self.on_workflow_start:
            self.on_workflow_start(workflow, state)
        
        try:
            # Execute workflow steps
            await self._execute_workflow_steps(workflow, state)
            
            # Mark workflow as completed
            state.status = WorkflowStatus.COMPLETED
            state.end_time = datetime.now()
            
            # Fire completion event
            if self.on_workflow_complete:
                self.on_workflow_complete(workflow, state)
                
        except Exception as e:
            # Mark workflow as failed
            state.status = WorkflowStatus.FAILED
            state.error = str(e)
            state.end_time = datetime.now()
            
            # Fire error event
            if self.on_workflow_error:
                self.on_workflow_error(workflow, state, e)
            
            raise WorkflowEngineError(f"Workflow execution failed: {str(e)}") from e
        
        return state
    
    async def _execute_workflow_steps(self, workflow: Workflow, state: WorkflowState) -> None:
        """Execute all workflow steps in proper order.
        
        Args:
            workflow: Workflow being executed
            state: Current workflow state
        """
        # Get execution order
        execution_order = workflow.get_execution_order()
        
        # Track steps ready for execution
        ready_steps: Set[str] = set()
        running_steps: Set[str] = set()
        
        # Find initially ready steps (no dependencies)
        for step_id in execution_order:
            step = workflow.get_step(step_id)
            if step and not step.get_dependencies():
                ready_steps.add(step_id)
        
        # Execute steps until all are complete
        while ready_steps or running_steps:
            # Start new steps up to parallel limit
            while ready_steps and len(running_steps) < self.max_parallel_steps:
                step_id = ready_steps.pop()
                step = workflow.get_step(step_id)
                
                if step and step.should_execute(state.context):
                    # Start step execution
                    running_steps.add(step_id)
                    task = asyncio.create_task(
                        self._execute_step_with_timeout(step, state),
                        name=f"step_{step_id}"
                    )
                    # Store task for monitoring
                    state.context.metadata[f"task_{step_id}"] = task
                else:
                    # Skip step due to condition
                    self._mark_step_skipped(step_id, state)
                    self._check_for_ready_steps(workflow, state, step_id, ready_steps, running_steps)
            
            # Wait for at least one step to complete
            if running_steps:
                await self._wait_for_step_completion(workflow, state, ready_steps, running_steps)
        
        # Check if all required steps completed successfully
        for step_id in execution_order:
            step = workflow.get_step(step_id)
            if step and step.should_execute(state.context):
                if not state.is_step_completed(step_id):
                    if state.is_step_failed(step_id):
                        raise WorkflowEngineError(f"Required step '{step_id}' failed")
                    else:
                        raise WorkflowEngineError(f"Required step '{step_id}' did not complete")
    
    async def _execute_step_with_timeout(self, step: WorkflowStep, state: WorkflowState) -> StepResult:
        """Execute a single step with timeout handling.
        
        Args:
            step: Step to execute
            state: Current workflow state
            
        Returns:
            Step execution result
        """
        state.current_step = step.step_id
        
        # Fire step start event
        if self.on_step_start:
            self.on_step_start(step, state)
        
        # Create step result
        result = StepResult(
            step_id=step.step_id,
            status=StepStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            # Execute step with timeout
            if self.step_timeout:
                step_result = await asyncio.wait_for(
                    step.execute(state.context),
                    timeout=self.step_timeout
                )
            else:
                step_result = await step.execute(state.context)
            
            # Mark as completed
            result.result = step_result
            result.status = StepStatus.COMPLETED
            result.end_time = datetime.now()
            
            # Update state
            state.completed_steps.add(step.step_id)
            state.step_results[step.step_id] = result
            
            # Fire completion event
            if self.on_step_complete:
                self.on_step_complete(step, result, state)
                
        except asyncio.TimeoutError:
            result.status = StepStatus.FAILED
            result.error = f"Step timed out after {self.step_timeout} seconds"
            result.end_time = datetime.now()
            
            state.failed_steps.add(step.step_id)
            state.step_results[step.step_id] = result
            
            # Fire error event
            if self.on_step_error:
                self.on_step_error(step, TimeoutError(result.error), state)
            
            raise WorkflowEngineError(result.error)
            
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            
            state.failed_steps.add(step.step_id)
            state.step_results[step.step_id] = result
            
            # Fire error event
            if self.on_step_error:
                self.on_step_error(step, e, state)
            
            # Check if should retry
            if self.enable_retries and self._should_retry_step(step, result):
                return await self._retry_step(step, state, result)
            
            raise WorkflowEngineError(f"Step '{step.step_id}' failed: {str(e)}") from e
        
        return result
    
    def _should_retry_step(self, step: WorkflowStep, result: StepResult) -> bool:
        """Check if a step should be retried.
        
        Args:
            step: Step that failed
            result: Step result
            
        Returns:
            True if step should be retried
        """
        retry_config = step.retry_config
        if not retry_config:
            return False
        
        max_retries = retry_config.get("max_retries", 0)
        current_retries = result.metadata.get("retry_count", 0)
        
        return current_retries < max_retries
    
    async def _retry_step(self, step: WorkflowStep, state: WorkflowState, failed_result: StepResult) -> StepResult:
        """Retry a failed step.
        
        Args:
            step: Step to retry
            state: Current workflow state
            failed_result: Previous failed result
            
        Returns:
            New step result
        """
        retry_config = step.retry_config
        retry_count = failed_result.metadata.get("retry_count", 0) + 1
        
        # Wait before retry
        retry_delay = retry_config.get("retry_delay", 1.0)
        backoff_multiplier = retry_config.get("backoff_multiplier", 2.0)
        actual_delay = retry_delay * (backoff_multiplier ** (retry_count - 1))
        
        await asyncio.sleep(actual_delay)
        
        # Create new result with retry metadata
        result = StepResult(
            step_id=step.step_id,
            status=StepStatus.RUNNING,
            start_time=datetime.now(),
            metadata={"retry_count": retry_count, "previous_error": failed_result.error}
        )
        
        try:
            # Execute step again
            if self.step_timeout:
                step_result = await asyncio.wait_for(
                    step.execute(state.context),
                    timeout=self.step_timeout
                )
            else:
                step_result = await step.execute(state.context)
            
            # Mark as completed
            result.result = step_result
            result.status = StepStatus.COMPLETED
            result.end_time = datetime.now()
            
            # Update state (remove from failed, add to completed)
            state.failed_steps.discard(step.step_id)
            state.completed_steps.add(step.step_id)
            state.step_results[step.step_id] = result
            
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            
            state.step_results[step.step_id] = result
            
            # Check if should retry again
            if self._should_retry_step(step, result):
                return await self._retry_step(step, state, result)
            
            raise WorkflowEngineError(f"Step '{step.step_id}' failed after {retry_count} retries: {str(e)}") from e
        
        return result
    
    def _mark_step_skipped(self, step_id: str, state: WorkflowState) -> None:
        """Mark a step as skipped.
        
        Args:
            step_id: ID of the step to skip
            state: Current workflow state
        """
        result = StepResult(
            step_id=step_id,
            status=StepStatus.SKIPPED,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        state.step_results[step_id] = result
    
    def _check_for_ready_steps(
        self, 
        workflow: Workflow, 
        state: WorkflowState, 
        completed_step_id: str,
        ready_steps: Set[str],
        running_steps: Set[str]
    ) -> None:
        """Check if any new steps are ready to execute after a step completes.
        
        Args:
            workflow: Workflow being executed
            state: Current workflow state
            completed_step_id: ID of the step that just completed
            ready_steps: Set of steps ready to execute
            running_steps: Set of steps currently running
        """
        for step_id, step in workflow.steps.items():
            # Skip if already processed
            if (step_id in state.completed_steps or 
                step_id in state.failed_steps or 
                step_id in ready_steps or 
                step_id in running_steps):
                continue
            
            # Check if all dependencies are satisfied
            dependencies_satisfied = all(
                state.is_step_completed(dep_id) or 
                (state.step_results.get(dep_id) and state.step_results.get(dep_id).status == StepStatus.SKIPPED)
                for dep_id in step.get_dependencies()
            )
            
            if dependencies_satisfied:
                ready_steps.add(step_id)
    
    async def _wait_for_step_completion(
        self,
        workflow: Workflow,
        state: WorkflowState,
        ready_steps: Set[str],
        running_steps: Set[str]
    ) -> None:
        """Wait for at least one running step to complete.
        
        Args:
            workflow: Workflow being executed
            state: Current workflow state
            ready_steps: Set of steps ready to execute
            running_steps: Set of steps currently running
        """
        # Get all running tasks
        tasks = []
        step_id_map = {}
        
        for step_id in list(running_steps):
            task = state.context.metadata.get(f"task_{step_id}")
            if task:
                tasks.append(task)
                step_id_map[task] = step_id
        
        if not tasks:
            return
        
        # Wait for at least one task to complete
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Process completed tasks
        for task in done:
            step_id = step_id_map[task]
            running_steps.discard(step_id)
            
            # Clean up task reference
            state.context.metadata.pop(f"task_{step_id}", None)
            
            # Check for newly ready steps
            self._check_for_ready_steps(workflow, state, step_id, ready_steps, running_steps)
    
    def create_execution_plan(self, workflow: Workflow) -> Dict[str, Any]:
        """Create an execution plan for the workflow.
        
        Args:
            workflow: Workflow to create plan for
            
        Returns:
            Dictionary containing execution plan details
        """
        execution_order = workflow.get_execution_order()
        
        # Analyze dependencies and parallel opportunities
        dependency_levels = {}
        for step_id in execution_order:
            step = workflow.get_step(step_id)
            if not step or not step.get_dependencies():
                dependency_levels[step_id] = 0
            else:
                max_dep_level = max(
                    dependency_levels.get(dep_id, 0) for dep_id in step.get_dependencies()
                )
                dependency_levels[step_id] = max_dep_level + 1
        
        # Group steps by dependency level (can run in parallel)
        parallel_groups = {}
        for step_id, level in dependency_levels.items():
            if level not in parallel_groups:
                parallel_groups[level] = []
            parallel_groups[level].append(step_id)
        
        return {
            "workflow_id": workflow.workflow_id,
            "total_steps": len(workflow.steps),
            "execution_order": execution_order,
            "dependency_levels": dependency_levels,
            "parallel_groups": parallel_groups,
            "estimated_parallel_stages": len(parallel_groups),
        } 