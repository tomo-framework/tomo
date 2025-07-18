"""Comprehensive workflow engine demonstration."""

import asyncio
from datetime import datetime
from tomo import BaseTool, tool, ToolRegistry, ToolRunner
from tomo.orchestrators.workflow import Workflow, WorkflowContext
from tomo.orchestrators.workflow_engine import WorkflowEngine
from tomo.orchestrators.workflow_steps import (
    ToolStep, ConditionStep, ParallelStep, DataTransformStep, 
    LoopStep, DelayStep, ScriptStep, create_tool_step, 
    create_condition_step, create_transform_step
)


# Example tools for workflows
@tool
class Calculator(BaseTool):
    """Perform basic mathematical calculations."""
    
    operation: str  # add, subtract, multiply, divide
    a: float
    b: float
    
    def run(self) -> float:
        if self.operation == "add":
            return self.a + self.b
        elif self.operation == "subtract":
            return self.a - self.b
        elif self.operation == "multiply":
            return self.a * self.b
        elif self.operation == "divide":
            if self.b == 0:
                raise ValueError("Cannot divide by zero")
            return self.a / self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class TextProcessor(BaseTool):
    """Process text in various ways."""
    
    text: str
    operation: str  # upper, lower, reverse, length
    
    def run(self) -> str:
        if self.operation == "upper":
            return self.text.upper()
        elif self.operation == "lower":
            return self.text.lower()
        elif self.operation == "reverse":
            return self.text[::-1]
        elif self.operation == "length":
            return str(len(self.text))
        else:
            return self.text


@tool
class DataValidator(BaseTool):
    """Validate data against criteria."""
    
    value: float
    min_value: float = 0
    max_value: float = 100
    
    def run(self) -> dict:
        is_valid = self.min_value <= self.value <= self.max_value
        return {
            "value": self.value,
            "is_valid": is_valid,
            "min_value": self.min_value,
            "max_value": self.max_value
        }


@tool
class ReportGenerator(BaseTool):
    """Generate a simple report."""
    
    title: str
    data: dict
    format: str = "text"
    
    def run(self) -> str:
        if self.format == "text":
            lines = [f"Report: {self.title}", "=" * 40]
            for key, value in self.data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif self.format == "json":
            import json
            return json.dumps({"title": self.title, "data": self.data}, indent=2)
        else:
            return f"Report '{self.title}' with data: {self.data}"


def setup_tools() -> tuple[ToolRegistry, ToolRunner]:
    """Set up tools and registry for workflows."""
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(TextProcessor)
    registry.register(DataValidator)
    registry.register(ReportGenerator)
    
    runner = ToolRunner(registry)
    return registry, runner


def create_simple_workflow(runner: ToolRunner) -> Workflow:
    """Create a simple sequential workflow."""
    workflow = Workflow(
        name="Simple Calculation Workflow",
        description="Perform a series of calculations"
    )
    
    # Step 1: Add two numbers
    step1 = create_tool_step(
        step_id="add_numbers",
        tool_name="Calculator",
        tool_inputs={"operation": "add", "a": 10, "b": 5},
        runner=runner,
        name="Add 10 + 5"
    )
    
    # Step 2: Multiply result by 2
    step2 = create_tool_step(
        step_id="multiply_result",
        tool_name="Calculator",
        tool_inputs={"operation": "multiply", "a": "$add_numbers", "b": 2},
        runner=runner,
        name="Multiply by 2",
        depends_on=["add_numbers"]
    )
    
    # Step 3: Generate report
    step3 = create_tool_step(
        step_id="generate_report",
        tool_name="ReportGenerator",
        tool_inputs={
            "title": "Calculation Results",
            "data": {"final_result": "$multiply_result"},
            "format": "text"
        },
        runner=runner,
        name="Generate Report",
        depends_on=["multiply_result"]
    )
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    return workflow


def create_conditional_workflow(runner: ToolRunner) -> Workflow:
    """Create a workflow with conditional execution."""
    workflow = Workflow(
        name="Conditional Processing Workflow",
        description="Process data conditionally based on validation"
    )
    
    # Step 1: Validate input data
    step1 = create_tool_step(
        step_id="validate_data",
        tool_name="DataValidator",
        tool_inputs={"value": 75, "min_value": 0, "max_value": 100},
        runner=runner,
        name="Validate Input"
    )
    
    # Step 2: Conditional processing based on validation
    def is_valid_condition(context: WorkflowContext) -> bool:
        validation_result = context.get("validate_data")
        return validation_result and validation_result.get("is_valid", False)
    
    # Success step: Process valid data
    success_step = ScriptStep(
        step_id="process_valid_data",
        script="""
validation_result = context.get("validate_data")
if validation_result and validation_result.get("value"):
    processed_value = validation_result["value"] * 1.1
else:
    processed_value = 0
result = processed_value
""",
        name="Process Valid Data"
    )
    
    # Failure step: Handle invalid data
    failure_step = create_tool_step(
        step_id="handle_invalid_data",
        tool_name="TextProcessor",
        tool_inputs={"text": "Data validation failed", "operation": "upper"},
        runner=runner,
        name="Handle Invalid Data"
    )
    
    step2 = ConditionStep(
        step_id="conditional_process",
        condition_func=is_valid_condition,
        true_step=success_step,
        false_step=failure_step,
        depends_on=["validate_data"],
        name="Conditional Processing"
    )
    
    # Step 3: Generate final report
    step3 = create_tool_step(
        step_id="final_report",
        tool_name="ReportGenerator",
        tool_inputs={
            "title": "Processing Results",
            "data": {"processing_result": "$conditional_process_result"},
            "format": "json"
        },
        runner=runner,
        name="Generate Final Report",
        depends_on=["conditional_process"]
    )
    
    workflow.add_step(step1)
    workflow.add_step(step2)
    workflow.add_step(step3)
    
    return workflow


def create_parallel_workflow(runner: ToolRunner) -> Workflow:
    """Create a workflow with parallel execution."""
    workflow = Workflow(
        name="Parallel Processing Workflow",
        description="Process multiple operations in parallel"
    )
    
    # Step 1: Set up initial data
    setup_step = ScriptStep(
        step_id="setup_data",
        script="""
context.set("numbers", [10, 20, 30])
context.set("text", "Hello World")
result = "Data initialized"
""",
        name="Initialize Data"
    )
    
    # Parallel steps
    calc_step1 = create_tool_step(
        step_id="calc1",
        tool_name="Calculator",
        tool_inputs={"operation": "add", "a": 10, "b": 20},
        runner=runner,
        name="Calculate Sum"
    )
    
    calc_step2 = create_tool_step(
        step_id="calc2",
        tool_name="Calculator",
        tool_inputs={"operation": "multiply", "a": 5, "b": 6},
        runner=runner,
        name="Calculate Product"
    )
    
    text_step = create_tool_step(
        step_id="text_proc",
        tool_name="TextProcessor",
        tool_inputs={"text": "$text", "operation": "upper"},
        runner=runner,
        name="Process Text"
    )
    
    # Parallel execution step
    parallel_step = ParallelStep(
        step_id="parallel_processing",
        parallel_steps=[calc_step1, calc_step2, text_step],
        wait_for_all=True,
        depends_on=["setup_data"],
        name="Parallel Operations"
    )
    
    # Combine results
    combine_step = ScriptStep(
        step_id="combine_results",
        script="""
parallel_results = context.get("parallel_processing_results")
combined = {
    "calculations": {
        "sum": parallel_results.get("calc1", {}).get("result"),
        "product": parallel_results.get("calc2", {}).get("result")
    },
    "text_result": parallel_results.get("text_proc", {}).get("result")
}
context.set("combined_data", combined)
result = combined
""",
        depends_on=["parallel_processing"],
        name="Combine Results"
    )
    
    workflow.add_step(setup_step)
    workflow.add_step(parallel_step)
    workflow.add_step(combine_step)
    
    return workflow


def create_loop_workflow(runner: ToolRunner) -> Workflow:
    """Create a workflow with loop processing."""
    workflow = Workflow(
        name="Data Processing Loop Workflow",
        description="Process a list of numbers in a loop"
    )
    
    # Step 1: Initialize data
    init_step = ScriptStep(
        step_id="init_data",
        script="""
numbers = [1, 2, 3, 4, 5]
context.set("number_list", numbers)
context.set("results", [])
result = f"Initialized {len(numbers)} numbers"
""",
        name="Initialize Numbers"
    )
    
    # Loop step: Square each number
    square_step = create_tool_step(
        step_id="square_number",
        tool_name="Calculator",
        tool_inputs={"operation": "multiply", "a": "$loop_process_current_item", "b": "$loop_process_current_item"},
        runner=runner,
        name="Square Number"
    )
    
    loop_step = LoopStep(
        step_id="loop_process",
        loop_step=square_step,
        iteration_data_key="number_list",
        max_iterations=10,
        depends_on=["init_data"],
        name="Process Numbers in Loop"
    )
    
    # Step 3: Summarize results
    summary_step = ScriptStep(
        step_id="summarize",
        script="""
loop_results = context.get("loop_process_results")
successful_results = [r["result"] for r in loop_results if r["success"]]
summary = {
    "total_processed": len(loop_results),
    "successful": len(successful_results),
    "results": successful_results,
    "sum_of_squares": sum(successful_results) if successful_results else 0
}
context.set("summary", summary)
result = summary
""",
        depends_on=["loop_process"],
        name="Summarize Results"
    )
    
    workflow.add_step(init_step)
    workflow.add_step(loop_step)
    workflow.add_step(summary_step)
    
    return workflow


def create_complex_workflow(runner: ToolRunner) -> Workflow:
    """Create a complex workflow combining multiple patterns."""
    workflow = Workflow(
        name="Complex Data Processing Pipeline",
        description="A comprehensive workflow demonstrating multiple patterns"
    )
    
    # Step 1: Initialize and validate input
    init_step = ScriptStep(
        step_id="initialize",
        script="""
import random
data = {
    "input_numbers": [random.randint(1, 100) for _ in range(5)],
    "text_data": "Process This Text",
    "threshold": 50
}
context.update(data)
result = "Pipeline initialized"
""",
        name="Initialize Pipeline"
    )
    
    # Step 2: Validate numbers using a script step for simplicity
    validation_step = ScriptStep(
        step_id="parallel_validation",
        script="""
input_numbers = context.get("input_numbers", [])
validation_results = {}

for i, number in enumerate(input_numbers):
    is_valid = 1 <= number <= 100
    validation_results[f"validate_{i}"] = {
        "success": True,
        "result": {
            "value": number,
            "is_valid": is_valid,
            "min_value": 1,
            "max_value": 100
        }
    }

context.set("parallel_validation_results", validation_results)
result = f"Validated {len(input_numbers)} numbers"
""",
        depends_on=["initialize"],
        name="Validate All Numbers"
    )
    
    # Step 3: Process valid numbers
    process_valid_step = ScriptStep(
        step_id="process_valid",
        script="""
validation_results = context.get("parallel_validation_results")
valid_numbers = []
for step_id, result in validation_results.items():
    if result["success"] and result["result"]["is_valid"]:
        valid_numbers.append(result["result"]["value"])

context.set("valid_numbers", valid_numbers)
result = f"Found {len(valid_numbers)} valid numbers"
""",
        depends_on=["parallel_validation"],
        name="Extract Valid Numbers"
    )
    
    # Step 4: Conditional processing based on count
    def has_enough_numbers(context: WorkflowContext) -> bool:
        valid_numbers = context.get("valid_numbers", [])
        return len(valid_numbers) >= 3
    
    # Success branch: Calculate statistics
    stats_step = ScriptStep(
        step_id="calculate_stats",
        script="""
import statistics
valid_numbers = context.get("valid_numbers", [])
stats = {
    "count": len(valid_numbers),
    "mean": statistics.mean(valid_numbers),
    "median": statistics.median(valid_numbers),
    "sum": sum(valid_numbers)
}
context.set("statistics", stats)
result = stats
""",
        name="Calculate Statistics"
    )
    
    # Failure branch: Handle insufficient data
    insufficient_step = create_tool_step(
        step_id="handle_insufficient",
        tool_name="TextProcessor",
        tool_inputs={"text": "Insufficient valid data for processing", "operation": "upper"},
        runner=runner,
        name="Handle Insufficient Data"
    )
    
    conditional_step = ConditionStep(
        step_id="conditional_processing",
        condition_func=has_enough_numbers,
        true_step=stats_step,
        false_step=insufficient_step,
        depends_on=["process_valid"],
        name="Conditional Statistics"
    )
    
    # Step 5: Generate comprehensive report
    final_report_step = ScriptStep(
        step_id="final_report",
        script="""
import json
from datetime import datetime

processing_result = context.get("conditional_processing_result")
report_data = {
    "title": "Data Processing Pipeline Results",
    "data": {
        "processing_result": processing_result,
        "timestamp": str(datetime.now())
    }
}
result = json.dumps(report_data, indent=2)
""",
        name="Generate Final Report",
        depends_on=["conditional_processing"]
    )
    
    # Add delay before completion
    delay_step = DelayStep(
        step_id="final_delay",
        delay_seconds=1.0,
        depends_on=["final_report"],
        name="Final Delay"
    )
    
    # Add all steps to workflow
    workflow.add_step(init_step)
    workflow.add_step(validation_step)
    workflow.add_step(process_valid_step)
    workflow.add_step(conditional_step)
    workflow.add_step(final_report_step)
    workflow.add_step(delay_step)
    
    return workflow


async def run_workflow_demo(workflow: Workflow, engine: WorkflowEngine, name: str) -> None:
    """Run a single workflow demonstration."""
    print(f"\n{'='*60}")
    print(f"🔄 Running {name}")
    print(f"{'='*60}")
    
    # Show workflow details
    print(f"Workflow: {workflow.name}")
    print(f"Description: {workflow.description}")
    print(f"Steps: {len(workflow.steps)}")
    
    # Show execution plan
    plan = engine.create_execution_plan(workflow)
    print(f"Execution plan: {plan['estimated_parallel_stages']} parallel stages")
    
    # Validate workflow
    errors = workflow.validate()
    if errors:
        print(f"❌ Validation errors: {errors}")
        return
    
    print("✅ Workflow validation passed")
    
    # Execute workflow
    start_time = datetime.now()
    try:
        state = await engine.execute_workflow(workflow)
        end_time = datetime.now()
        
        print(f"\n📊 Execution Results:")
        print(f"Status: {state.status.value}")
        print(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")
        print(f"Completed steps: {len(state.completed_steps)}")
        print(f"Failed steps: {len(state.failed_steps)}")
        
        # Show step results
        print(f"\n📋 Step Results:")
        for step_id, result in state.step_results.items():
            status_emoji = "✅" if result.success else "❌"
            print(f"  {status_emoji} {step_id}: {result.status.value}")
            if result.error:
                print(f"    Error: {result.error}")
        
        # Show final context data
        print(f"\n💾 Final Context Data:")
        for key, value in state.context.data.items():
            if not key.startswith("task_"):  # Skip internal task references
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")


async def main():
    """Run comprehensive workflow demonstrations."""
    print("🧠 Tomo Workflow Engine Demonstration")
    print("=" * 60)
    
    # Set up tools
    registry, runner = setup_tools()
    
    # Create workflow engine
    engine = WorkflowEngine(
        registry=registry,
        max_parallel_steps=3,
        step_timeout=30.0,
        enable_retries=True
    )
    
    # Set up event handlers for demonstration
    def on_workflow_start(workflow: Workflow, state) -> None:
        print(f"🚀 Starting workflow: {workflow.name}")
    
    def on_step_start(step, state) -> None:
        print(f"   ▶️  Executing step: {step.name or step.step_id}")
    
    def on_step_complete(step, result, state) -> None:
        status_emoji = "✅" if result.success else "❌"
        print(f"   {status_emoji} Completed step: {step.name or step.step_id}")
    
    engine.on_workflow_start = on_workflow_start
    engine.on_step_start = on_step_start
    engine.on_step_complete = on_step_complete
    
    # Create and run different workflow patterns
    workflows = [
        (create_simple_workflow(runner), "Simple Sequential Workflow"),
        (create_conditional_workflow(runner), "Conditional Workflow"),
        (create_parallel_workflow(runner), "Parallel Processing Workflow"),
        (create_loop_workflow(runner), "Loop Processing Workflow"),
        (create_complex_workflow(runner), "Complex Multi-Pattern Workflow"),
    ]
    
    for workflow, name in workflows:
        await run_workflow_demo(workflow, engine, name)
    
    print(f"\n{'='*60}")
    print("🎉 All workflow demonstrations completed!")
    print("='*60")


if __name__ == "__main__":
    asyncio.run(main()) 