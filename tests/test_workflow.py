"""Tests for the workflow engine."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from tomo import BaseTool, tool, ToolRegistry, ToolRunner
from tomo.orchestrators.workflow import (
    Workflow, 
    WorkflowStep, 
    WorkflowState, 
    WorkflowContext, 
    WorkflowStatus, 
    StepStatus,
    StepResult
)
from tomo.orchestrators.workflow_engine import WorkflowEngine, WorkflowEngineError
from tomo.orchestrators.workflow_steps import (
    ToolStep, 
    ConditionStep, 
    ParallelStep, 
    DataTransformStep,
    LoopStep, 
    DelayStep, 
    ScriptStep,
    create_tool_step
)


# Test tools
@tool
class TestCalculator(BaseTool):
    """Test calculator tool."""
    
    operation: str
    a: float
    b: float
    
    def run(self) -> float:
        if self.operation == "add":
            return self.a + self.b
        elif self.operation == "multiply":
            return self.a * self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class TestValidator(BaseTool):
    """Test validation tool."""
    
    value: float
    min_value: float = 0
    max_value: float = 100
    
    def run(self) -> dict:
        is_valid = self.min_value <= self.value <= self.max_value
        return {"value": self.value, "is_valid": is_valid}


@tool
class FailingTool(BaseTool):
    """Tool that always fails for testing."""
    
    should_fail: bool = True
    
    def run(self) -> str:
        if self.should_fail:
            raise RuntimeError("Tool intentionally failed")
        return "Success"


# Test fixtures
@pytest.fixture
def registry():
    """Create a test tool registry."""
    registry = ToolRegistry()
    registry.register(TestCalculator)
    registry.register(TestValidator)
    registry.register(FailingTool)
    return registry


@pytest.fixture
def runner(registry):
    """Create a test tool runner."""
    return ToolRunner(registry)


@pytest.fixture
def workflow_engine(registry):
    """Create a test workflow engine."""
    from tomo.adapters import OpenAIAdapter
    return WorkflowEngine(
        registry=registry,
        adapter=OpenAIAdapter(),
        max_parallel_steps=3,
        step_timeout=5.0,
        enable_retries=True
    )


# Test workflow context
class TestWorkflowContext:
    """Test workflow context functionality."""
    
    def test_context_creation(self):
        """Test creating a workflow context."""
        context = WorkflowContext()
        assert isinstance(context.data, dict)
        assert isinstance(context.variables, dict)
        assert isinstance(context.metadata, dict)
    
    def test_context_data_operations(self):
        """Test context data operations."""
        context = WorkflowContext()
        
        # Test set and get
        context.set("key1", "value1")
        assert context.get("key1") == "value1"
        assert context.get("nonexistent") is None
        assert context.get("nonexistent", "default") == "default"
        
        # Test update
        context.update({"key2": "value2", "key3": "value3"})
        assert context.get("key2") == "value2"
        assert context.get("key3") == "value3"
    
    def test_context_variables(self):
        """Test context variable operations."""
        context = WorkflowContext()
        
        context.set_variable("var1", 42)
        assert context.get_variable("var1") == 42
        assert context.get_variable("nonexistent") is None
        assert context.get_variable("nonexistent", "default") == "default"


# Test workflow step results
class TestStepResult:
    """Test step result functionality."""
    
    def test_step_result_creation(self):
        """Test creating a step result."""
        result = StepResult(
            step_id="test_step",
            status=StepStatus.COMPLETED,
            result="success"
        )
        
        assert result.step_id == "test_step"
        assert result.status == StepStatus.COMPLETED
        assert result.result == "success"
        assert result.success is True
    
    def test_step_result_duration(self):
        """Test step result duration calculation."""
        start_time = datetime.now()
        result = StepResult(
            step_id="test_step",
            status=StepStatus.COMPLETED,
            start_time=start_time
        )
        
        # Duration should be None without end time
        assert result.duration is None
        
        # Set end time and check duration
        import time
        time.sleep(0.1)
        result.end_time = datetime.now()
        duration = result.duration
        assert duration is not None
        assert duration > 0.05  # Should be at least 50ms


# Test workflow state
class TestWorkflowState:
    """Test workflow state functionality."""
    
    def test_workflow_state_creation(self):
        """Test creating a workflow state."""
        state = WorkflowState(workflow_id="test_workflow")
        
        assert state.workflow_id == "test_workflow"
        assert state.status == WorkflowStatus.PENDING
        assert len(state.completed_steps) == 0
        assert len(state.failed_steps) == 0
        assert isinstance(state.context, WorkflowContext)
    
    def test_workflow_state_step_tracking(self):
        """Test workflow state step tracking."""
        state = WorkflowState(workflow_id="test_workflow")
        
        # Add completed step
        result = StepResult(
            step_id="step1",
            status=StepStatus.COMPLETED,
            result="success"
        )
        state.completed_steps.add("step1")
        state.step_results["step1"] = result
        
        assert state.is_step_completed("step1")
        assert not state.is_step_failed("step1")
        assert state.get_step_result("step1") == result
        
        # Add failed step
        failed_result = StepResult(
            step_id="step2",
            status=StepStatus.FAILED,
            error="test error"
        )
        state.failed_steps.add("step2")
        state.step_results["step2"] = failed_result
        
        assert not state.is_step_completed("step2")
        assert state.is_step_failed("step2")


# Test workflow definition
class TestWorkflow:
    """Test workflow definition functionality."""
    
    def test_workflow_creation(self):
        """Test creating a workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow"
        )
        
        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert len(workflow.steps) == 0
    
    def test_workflow_add_step(self, runner):
        """Test adding steps to a workflow."""
        workflow = Workflow(name="Test Workflow")
        
        step1 = create_tool_step(
            step_id="step1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        
        workflow.add_step(step1)
        assert len(workflow.steps) == 1
        assert workflow.get_step("step1") == step1
    
    def test_workflow_add_duplicate_step(self, runner):
        """Test adding duplicate step IDs."""
        workflow = Workflow(name="Test Workflow")
        
        step1 = create_tool_step(
            step_id="step1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        
        workflow.add_step(step1)
        
        # Adding same step ID should raise error
        step2 = create_tool_step(
            step_id="step1",  # Same ID
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": 3, "b": 4},
            runner=runner
        )
        
        with pytest.raises(ValueError, match="already exists"):
            workflow.add_step(step2)
    
    def test_workflow_execution_order(self, runner):
        """Test workflow execution order calculation."""
        workflow = Workflow(name="Test Workflow")
        
        # Create steps with dependencies
        step1 = create_tool_step(
            step_id="step1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        
        step2 = create_tool_step(
            step_id="step2",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": "$step1", "b": 3},
            runner=runner,
            depends_on=["step1"]
        )
        
        step3 = create_tool_step(
            step_id="step3",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": "$step2", "b": 1},
            runner=runner,
            depends_on=["step2"]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        execution_order = workflow.get_execution_order()
        assert execution_order == ["step1", "step2", "step3"]
    
    def test_workflow_circular_dependency(self, runner):
        """Test detection of circular dependencies."""
        workflow = Workflow(name="Test Workflow")
        
        step1 = create_tool_step(
            step_id="step1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner,
            depends_on=["step2"]
        )
        
        step2 = create_tool_step(
            step_id="step2",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": 3, "b": 4},
            runner=runner,
            depends_on=["step1"]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        with pytest.raises(ValueError, match="Circular dependency"):
            workflow.get_execution_order()
    
    def test_workflow_validation(self, runner):
        """Test workflow validation."""
        workflow = Workflow(name="Test Workflow")
        
        # Empty workflow should have errors
        errors = workflow.validate()
        assert "no steps" in errors[0].lower()
        
        # Add valid step
        step1 = create_tool_step(
            step_id="step1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        workflow.add_step(step1)
        
        # Should be valid now
        errors = workflow.validate()
        assert len(errors) == 0


# Test workflow steps
class TestWorkflowSteps:
    """Test different workflow step types."""
    
    @pytest.mark.asyncio
    async def test_tool_step(self, runner):
        """Test tool step execution."""
        step = create_tool_step(
            step_id="calc_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 5, "b": 3},
            runner=runner
        )
        
        context = WorkflowContext()
        result = await step.execute(context)
        
        assert result == 8
        assert context.get("calc_step") == 8
    
    @pytest.mark.asyncio
    async def test_tool_step_with_context_variables(self, runner):
        """Test tool step with context variable resolution."""
        step = create_tool_step(
            step_id="calc_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": "$input_a", "b": "$input_b"},
            runner=runner
        )
        
        context = WorkflowContext()
        context.set("input_a", 6)
        context.set("input_b", 7)
        
        result = await step.execute(context)
        
        assert result == 42
        assert context.get("calc_step") == 42
    
    @pytest.mark.asyncio
    async def test_condition_step(self, runner):
        """Test conditional step execution."""
        # Create condition function
        def is_positive(context: WorkflowContext) -> bool:
            value = context.get("test_value", 0)
            return value > 0
        
        # Create true and false steps
        true_step = create_tool_step(
            step_id="positive_calc",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": "$test_value", "b": 2},
            runner=runner
        )
        
        false_step = ScriptStep(
            step_id="negative_handler",
            script='result = "Value is not positive"'
        )
        
        condition_step = ConditionStep(
            step_id="condition_test",
            condition_func=is_positive,
            true_step=true_step,
            false_step=false_step
        )
        
        # Test with positive value
        context = WorkflowContext()
        context.set("test_value", 5)
        
        result = await condition_step.execute(context)
        assert result == 10  # 5 * 2
        
        # Test with negative value
        context.set("test_value", -3)
        result = await condition_step.execute(context)
        assert result == "Value is not positive"
    
    @pytest.mark.asyncio
    async def test_parallel_step(self, runner):
        """Test parallel step execution."""
        # Create parallel steps
        step1 = create_tool_step(
            step_id="calc1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        
        step2 = create_tool_step(
            step_id="calc2",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": 3, "b": 4},
            runner=runner
        )
        
        step3 = ScriptStep(
            step_id="script1",
            script='result = "Hello World"'
        )
        
        parallel_step = ParallelStep(
            step_id="parallel_test",
            parallel_steps=[step1, step2, step3],
            wait_for_all=True
        )
        
        context = WorkflowContext()
        result = await parallel_step.execute(context)
        
        # Check that all steps completed
        assert "calc1" in result
        assert "calc2" in result
        assert "script1" in result
        
        assert result["calc1"]["success"] is True
        assert result["calc1"]["result"] == 3
        
        assert result["calc2"]["success"] is True
        assert result["calc2"]["result"] == 12
        
        assert result["script1"]["success"] is True
        assert result["script1"]["result"] == "Hello World"
    
    @pytest.mark.asyncio
    async def test_data_transform_step(self):
        """Test data transformation step."""
        def uppercase_transform(data):
            return str(data).upper()
        
        step = DataTransformStep(
            step_id="transform_test",
            transform_func=uppercase_transform,
            input_key="input_text",
            output_key="output_text"
        )
        
        context = WorkflowContext()
        context.set("input_text", "hello world")
        
        result = await step.execute(context)
        
        assert result == "HELLO WORLD"
        assert context.get("output_text") == "HELLO WORLD"
    
    @pytest.mark.asyncio
    async def test_loop_step(self, runner):
        """Test loop step execution."""
        # Create step to execute in loop
        loop_step = create_tool_step(
            step_id="square_number",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": "$loop_test_current_item", "b": "$loop_test_current_item"},
            runner=runner
        )
        
        step = LoopStep(
            step_id="loop_test",
            loop_step=loop_step,
            iteration_data_key="numbers",
            max_iterations=5
        )
        
        context = WorkflowContext()
        context.set("numbers", [2, 3, 4])
        
        result = await step.execute(context)
        
        assert len(result) == 3
        assert result[0]["result"] == 4  # 2^2
        assert result[1]["result"] == 9  # 3^2
        assert result[2]["result"] == 16  # 4^2
    
    @pytest.mark.asyncio
    async def test_delay_step(self):
        """Test delay step execution."""
        step = DelayStep(
            step_id="delay_test",
            delay_seconds=0.1
        )
        
        context = WorkflowContext()
        start_time = datetime.now()
        
        result = await step.execute(context)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        assert duration >= 0.09  # Allow some timing variance
        assert "Delayed for 0.1 seconds" in result
    
    @pytest.mark.asyncio
    async def test_script_step(self):
        """Test script step execution."""
        step = ScriptStep(
            step_id="script_test",
            script="""
import math
x = 5
y = math.sqrt(x * x)
result = f"Square root of {x}^2 is {y}"
"""
        )
        
        context = WorkflowContext()
        result = await step.execute(context)
        
        assert result == "Square root of 5^2 is 5.0"
        assert context.get("script_test") == result


# Test workflow engine
class TestWorkflowEngine:
    """Test workflow engine functionality."""
    
    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self, workflow_engine, runner):
        """Test executing a simple workflow."""
        workflow = Workflow(name="Simple Test")
        
        step1 = create_tool_step(
            step_id="add_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 10, "b": 5},
            runner=runner
        )
        
        step2 = create_tool_step(
            step_id="multiply_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": "$add_step", "b": 2},
            runner=runner,
            depends_on=["add_step"]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        state = await workflow_engine.execute_workflow(workflow)
        
        assert state.status == WorkflowStatus.COMPLETED
        assert len(state.completed_steps) == 2
        assert len(state.failed_steps) == 0
        
        # Check results
        assert state.context.get("add_step") == 15
        assert state.context.get("multiply_step") == 30
    
    @pytest.mark.asyncio
    async def test_workflow_with_failure(self, workflow_engine, runner):
        """Test workflow execution with a failing step."""
        workflow = Workflow(name="Failing Test")
        
        step1 = create_tool_step(
            step_id="success_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        
        step2 = create_tool_step(
            step_id="fail_step",
            tool_name="FailingTool",
            tool_inputs={"should_fail": True},
            runner=runner,
            depends_on=["success_step"]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        with pytest.raises(WorkflowEngineError):
            await workflow_engine.execute_workflow(workflow)
    
    @pytest.mark.asyncio
    async def test_workflow_validation_error(self, workflow_engine):
        """Test workflow validation errors."""
        # Create workflow with invalid dependencies
        workflow = Workflow(name="Invalid Test")
        
        # This will fail validation because of missing dependency
        step = ToolStep(
            step_id="test_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            depends_on=["nonexistent_step"]
        )
        
        # We need to bypass add_step validation for this test
        workflow.steps["test_step"] = step
        
        with pytest.raises(WorkflowEngineError, match="validation failed"):
            await workflow_engine.execute_workflow(workflow)
    
    def test_create_execution_plan(self, workflow_engine, runner):
        """Test workflow execution plan creation."""
        workflow = Workflow(name="Plan Test")
        
        # Create a workflow with multiple dependency levels
        step1 = create_tool_step(
            step_id="step1",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        
        step2 = create_tool_step(
            step_id="step2",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 3, "b": 4},
            runner=runner
        )
        
        step3 = create_tool_step(
            step_id="step3",
            tool_name="TestCalculator",
            tool_inputs={"operation": "multiply", "a": "$step1", "b": "$step2"},
            runner=runner,
            depends_on=["step1", "step2"]
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        plan = workflow_engine.create_execution_plan(workflow)
        
        assert plan["total_steps"] == 3
        assert plan["estimated_parallel_stages"] == 2  # step1&2 can run in parallel, then step3
        assert "step1" in plan["parallel_groups"][0]
        assert "step2" in plan["parallel_groups"][0]
        assert "step3" in plan["parallel_groups"][1]
    
    @pytest.mark.asyncio
    async def test_workflow_event_handlers(self, workflow_engine, runner):
        """Test workflow event handlers."""
        events = []
        
        def on_workflow_start(workflow, state):
            events.append(("workflow_start", workflow.name))
        
        def on_step_start(step, state):
            events.append(("step_start", step.step_id))
        
        def on_step_complete(step, result, state):
            events.append(("step_complete", step.step_id, result.success))
        
        def on_workflow_complete(workflow, state):
            events.append(("workflow_complete", workflow.name, state.success))
        
        # Set event handlers
        workflow_engine.on_workflow_start = on_workflow_start
        workflow_engine.on_step_start = on_step_start
        workflow_engine.on_step_complete = on_step_complete
        workflow_engine.on_workflow_complete = on_workflow_complete
        
        # Create simple workflow
        workflow = Workflow(name="Event Test")
        step = create_tool_step(
            step_id="test_step",
            tool_name="TestCalculator",
            tool_inputs={"operation": "add", "a": 1, "b": 2},
            runner=runner
        )
        workflow.add_step(step)
        
        # Execute workflow
        await workflow_engine.execute_workflow(workflow)
        
        # Check events
        assert ("workflow_start", "Event Test") in events
        assert ("step_start", "test_step") in events
        assert ("step_complete", "test_step", True) in events
        assert ("workflow_complete", "Event Test", True) in events


# Integration tests
class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios."""
    
    @pytest.mark.asyncio
    async def test_complex_workflow_scenario(self, workflow_engine, runner):
        """Test a complex workflow with multiple patterns."""
        workflow = Workflow(
            name="Complex Integration Test",
            description="A workflow combining multiple patterns"
        )
        
        # Initialize data
        init_step = ScriptStep(
            step_id="init",
            script="""
data = [10, 25, 35, 50, 75]
context.set("input_data", data)
context.set("threshold", 30)
result = f"Initialized {len(data)} values"
"""
        )
        
        # Validate each value in parallel
        validation_steps = []
        for i in range(3):  # Just test first 3 values
            val_step = ToolStep(
                step_id=f"validate_{i}",
                tool_name="TestValidator",
                tool_inputs={
                    "value": {"$context": f"input_data[{i}]"},
                    "min_value": 0,
                    "max_value": 100
                },
                runner=runner
            )
            validation_steps.append(val_step)
        
        parallel_validation = ParallelStep(
            step_id="parallel_validation",
            parallel_steps=validation_steps,
            depends_on=["init"]
        )
        
        # Process results conditionally
        def has_valid_data(context: WorkflowContext) -> bool:
            validation_results = context.get("parallel_validation_results", {})
            valid_count = sum(
                1 for result in validation_results.values()
                if result.get("success") and result.get("result", {}).get("is_valid")
            )
            return valid_count >= 2
        
        # Success branch: Calculate statistics
        stats_step = ScriptStep(
            step_id="calculate_stats",
            script="""
input_data = context.get("input_data", [])
stats = {
    "count": len(input_data),
    "sum": sum(input_data),
    "average": sum(input_data) / len(input_data) if input_data else 0
}
context.set("statistics", stats)
result = stats
"""
        )
        
        # Failure branch: Handle insufficient data
        failure_step = ScriptStep(
            step_id="handle_failure",
            script='result = "Insufficient valid data"'
        )
        
        conditional_step = ConditionStep(
            step_id="conditional_processing",
            condition_func=has_valid_data,
            true_step=stats_step,
            false_step=failure_step,
            depends_on=["parallel_validation"]
        )
        
        # Final step: Generate report
        final_step = ScriptStep(
            step_id="generate_report",
            script="""
import json
processing_result = context.get("conditional_processing_result")
report = {
    "processing_result": processing_result,
    "workflow_completed": True
}
result = json.dumps(report, indent=2)
"""
        )
        final_step.depends_on = ["conditional_processing"]
        
        # Add all steps
        workflow.add_step(init_step)
        workflow.add_step(parallel_validation)
        workflow.add_step(conditional_step)
        workflow.add_step(final_step)
        
        # Execute workflow
        state = await workflow_engine.execute_workflow(workflow)
        
        # Verify results
        assert state.status == WorkflowStatus.COMPLETED
        assert len(state.completed_steps) == 4
        assert len(state.failed_steps) == 0
        
        # Check that final report contains expected data
        final_result = state.context.get("generate_report")
        assert "processing_result" in final_result
        assert "workflow_completed" in final_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 