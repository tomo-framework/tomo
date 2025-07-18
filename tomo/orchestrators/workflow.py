"""Workflow engine for declarative multi-step process orchestration."""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Set
from pydantic import BaseModel


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status of individual step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class WorkflowContext:
    """Shared context and data between workflow steps."""
    
    data: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context data."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the context data."""
        self.data[key] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a workflow variable."""
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a workflow variable."""
        self.variables[name] = value
    
    def update(self, data: Dict[str, Any]) -> None:
        """Update context with new data."""
        self.data.update(data)


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    
    step_id: str
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success(self) -> bool:
        """Check if step completed successfully."""
        return self.status == StepStatus.COMPLETED


@dataclass
class WorkflowState:
    """Current state of workflow execution."""
    
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    completed_steps: Set[str] = field(default_factory=set)
    failed_steps: Set[str] = field(default_factory=set)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    context: WorkflowContext = field(default_factory=WorkflowContext)
    
    @property
    def duration(self) -> Optional[float]:
        """Get workflow execution duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == WorkflowStatus.COMPLETED
    
    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """Get result for a specific step."""
        return self.step_results.get(step_id)
    
    def is_step_completed(self, step_id: str) -> bool:
        """Check if a step has completed successfully."""
        return step_id in self.completed_steps
    
    def is_step_failed(self, step_id: str) -> bool:
        """Check if a step has failed."""
        return step_id in self.failed_steps


class WorkflowStep(ABC):
    """Abstract base class for workflow steps."""
    
    def __init__(
        self,
        step_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        condition: Optional[Callable[[WorkflowContext], bool]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize workflow step.
        
        Args:
            step_id: Unique identifier for the step
            name: Human-readable name for the step
            description: Description of what the step does
            depends_on: List of step IDs this step depends on
            condition: Optional condition function to determine if step should run
            retry_config: Configuration for retry behavior
        """
        self.step_id = step_id
        self.name = name or step_id
        self.description = description or ""
        self.depends_on = depends_on or []
        self.condition = condition
        self.retry_config = retry_config or {}
    
    @abstractmethod
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute the workflow step.
        
        Args:
            context: Current workflow context
            
        Returns:
            Result of step execution
        """
        pass
    
    def should_execute(self, context: WorkflowContext) -> bool:
        """Check if this step should be executed based on its condition.
        
        Args:
            context: Current workflow context
            
        Returns:
            True if step should execute, False otherwise
        """
        if self.condition is None:
            return True
        return self.condition(context)
    
    def get_dependencies(self) -> List[str]:
        """Get list of step IDs this step depends on."""
        return self.depends_on.copy()


class Workflow:
    """A declarative workflow definition with steps and execution logic."""
    
    def __init__(
        self,
        workflow_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "1.0.0",
        steps: Optional[List[WorkflowStep]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            name: Human-readable name for the workflow
            description: Description of what the workflow does
            version: Version of the workflow
            steps: List of workflow steps
            metadata: Additional metadata for the workflow
        """
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.name = name or self.workflow_id
        self.description = description or ""
        self.version = version
        self.steps: Dict[str, WorkflowStep] = {}
        self.metadata = metadata or {}
        
        # Add steps if provided
        if steps:
            for step in steps:
                self.add_step(step)
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow.
        
        Args:
            step: Workflow step to add
        """
        if step.step_id in self.steps:
            raise ValueError(f"Step with ID '{step.step_id}' already exists in workflow")
        
        # Validate dependencies
        for dep_id in step.get_dependencies():
            if dep_id not in self.steps:
                raise ValueError(f"Step '{step.step_id}' depends on unknown step '{dep_id}'")
        
        self.steps[step.step_id] = step
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID.
        
        Args:
            step_id: ID of the step to retrieve
            
        Returns:
            WorkflowStep if found, None otherwise
        """
        return self.steps.get(step_id)
    
    def list_steps(self) -> List[str]:
        """Get list of all step IDs in the workflow."""
        return list(self.steps.keys())
    
    def get_execution_order(self) -> List[str]:
        """Get steps in topological order based on dependencies.
        
        Returns:
            List of step IDs in execution order
            
        Raises:
            ValueError: If circular dependencies are detected
        """
        # Topological sort implementation
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(step_id: str) -> None:
            if step_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving step '{step_id}'")
            
            if step_id not in visited:
                temp_visited.add(step_id)
                
                # Visit dependencies first
                step = self.steps.get(step_id)
                if step:
                    for dep_id in step.get_dependencies():
                        visit(dep_id)
                
                temp_visited.remove(step_id)
                visited.add(step_id)
                result.append(step_id)
        
        # Visit all steps
        for step_id in self.steps:
            if step_id not in visited:
                visit(step_id)
        
        return result
    
    def validate(self) -> List[str]:
        """Validate the workflow definition.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for empty workflow
        if not self.steps:
            errors.append("Workflow has no steps")
            return errors
        
        # Check dependencies
        for step_id, step in self.steps.items():
            for dep_id in step.get_dependencies():
                if dep_id not in self.steps:
                    errors.append(f"Step '{step_id}' depends on unknown step '{dep_id}'")
        
        # Check for circular dependencies
        try:
            self.get_execution_order()
        except ValueError as e:
            errors.append(str(e))
        
        return errors
    
    def create_state(self) -> WorkflowState:
        """Create initial workflow state for execution.
        
        Returns:
            New WorkflowState instance
        """
        return WorkflowState(workflow_id=self.workflow_id)
    
    def __repr__(self) -> str:
        return f"Workflow(id='{self.workflow_id}', name='{self.name}', steps={len(self.steps)})" 