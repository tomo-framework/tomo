"""Concrete workflow step implementations."""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from ..core.runner import ToolRunner
from .workflow import WorkflowStep, WorkflowContext, WorkflowStatus


class ToolStep(WorkflowStep):
    """A workflow step that executes a Tomo tool."""
    
    def __init__(
        self,
        step_id: str,
        tool_name: str,
        tool_inputs: Dict[str, Any],
        output_key: Optional[str] = None,
        runner: Optional[ToolRunner] = None,
        **kwargs
    ):
        """Initialize tool step.
        
        Args:
            step_id: Unique identifier for the step
            tool_name: Name of the tool to execute
            tool_inputs: Inputs to pass to the tool
            output_key: Key to store the tool result in context (defaults to step_id)
            runner: Tool runner instance
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.tool_name = tool_name
        self.tool_inputs = tool_inputs
        self.output_key = output_key or step_id
        self.runner = runner
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute the tool."""
        if not self.runner:
            raise ValueError("ToolStep requires a ToolRunner instance")
        
        # Resolve input values from context
        resolved_inputs = self._resolve_inputs(context)
        
        # Execute tool
        result = self.runner.run_tool(self.tool_name, resolved_inputs)
        
        # Store result in context
        context.set(self.output_key, result)
        
        return result
    
    def _resolve_inputs(self, context: WorkflowContext) -> Dict[str, Any]:
        """Resolve input values from context variables.
        
        Args:
            context: Current workflow context
            
        Returns:
            Resolved input dictionary
        """
        resolved = {}
        
        for key, value in self.tool_inputs.items():
            resolved[key] = self._resolve_value(value, context)
        
        return resolved
    
    def _resolve_value(self, value: Any, context: WorkflowContext) -> Any:
        """Recursively resolve a value from context.
        
        Args:
            value: Value to resolve
            context: Current workflow context
            
        Returns:
            Resolved value
        """
        if isinstance(value, str) and value.startswith("$"):
            # Variable reference - handle nested properties and array access
            var_path = value[1:]
            return self._resolve_path(var_path, context)
        elif isinstance(value, dict) and value.get("$context"):
            # Context reference
            context_key = value["$context"]
            return self._resolve_path(context_key, context)
        elif isinstance(value, dict):
            # Recursively resolve dictionary values
            return {k: self._resolve_value(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            # Recursively resolve list values
            return [self._resolve_value(item, context) for item in value]
        else:
            # Literal value
            return value
    
    def _resolve_path(self, path: str, context: WorkflowContext) -> Any:
        """Resolve a dot-notation or bracket-notation path from context.
        
        Args:
            path: Path to resolve (e.g., "user.name" or "items[0]" or "data.values[1]")
            context: Current workflow context
            
        Returns:
            Resolved value or None if path not found
        """
        try:
            # Start with the full context data
            current = context.data
            
            # Handle bracket notation for arrays first
            import re
            
            # Split path by dots, but preserve bracket notation
            parts = []
            current_part = ""
            bracket_depth = 0
            
            for char in path:
                if char == '[':
                    bracket_depth += 1
                    current_part += char
                elif char == ']':
                    bracket_depth -= 1
                    current_part += char
                elif char == '.' and bracket_depth == 0:
                    if current_part:
                        parts.append(current_part)
                        current_part = ""
                else:
                    current_part += char
            
            if current_part:
                parts.append(current_part)
            
            # Navigate through the path
            for part in parts:
                if '[' in part and ']' in part:
                    # Handle array/dict access like "items[0]" or "data[key]"
                    key_match = re.match(r'([^[]+)\[([^\]]+)\]', part)
                    if key_match:
                        base_key = key_match.group(1)
                        index_or_key = key_match.group(2)
                        
                        # Get the base object
                        if base_key:
                            current = current.get(base_key) if isinstance(current, dict) else None
                        
                        if current is not None:
                            # Try to parse index as integer for list access
                            try:
                                index = int(index_or_key)
                                if isinstance(current, (list, tuple)) and 0 <= index < len(current):
                                    current = current[index]
                                else:
                                    return None
                            except ValueError:
                                # Not an integer, try as string key for dict access
                                if isinstance(current, dict):
                                    current = current.get(index_or_key)
                                else:
                                    return None
                        else:
                            return None
                    else:
                        return None
                else:
                    # Regular key access
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        return None
                
                if current is None:
                    break
            
            return current
            
        except Exception:
            # If any error occurs during path resolution, return None
            return None


class ConditionStep(WorkflowStep):
    """A workflow step that executes based on a condition."""
    
    def __init__(
        self,
        step_id: str,
        condition_func: Callable[[WorkflowContext], bool],
        true_step: Optional[WorkflowStep] = None,
        false_step: Optional[WorkflowStep] = None,
        **kwargs
    ):
        """Initialize condition step.
        
        Args:
            step_id: Unique identifier for the step
            condition_func: Function that evaluates the condition
            true_step: Step to execute if condition is true
            false_step: Step to execute if condition is false
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.condition_func = condition_func
        self.true_step = true_step
        self.false_step = false_step
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute conditional logic."""
        condition_result = self.condition_func(context)
        
        # Store condition result
        context.set(f"{self.step_id}_condition", condition_result)
        
        # Execute appropriate step
        if condition_result and self.true_step:
            result = await self.true_step.execute(context)
            context.set(f"{self.step_id}_result", result)
            return result
        elif not condition_result and self.false_step:
            result = await self.false_step.execute(context)
            context.set(f"{self.step_id}_result", result)
            return result
        
        return condition_result


class ParallelStep(WorkflowStep):
    """A workflow step that executes multiple steps in parallel."""
    
    def __init__(
        self,
        step_id: str,
        parallel_steps: List[WorkflowStep],
        wait_for_all: bool = True,
        **kwargs
    ):
        """Initialize parallel step.
        
        Args:
            step_id: Unique identifier for the step
            parallel_steps: List of steps to execute in parallel
            wait_for_all: Whether to wait for all steps to complete
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.parallel_steps = parallel_steps
        self.wait_for_all = wait_for_all
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute steps in parallel."""
        # Create tasks for all parallel steps
        tasks = []
        for step in self.parallel_steps:
            task = asyncio.create_task(step.execute(context))
            tasks.append((step.step_id, task))
        
        results = {}
        
        if self.wait_for_all:
            # Wait for all tasks to complete
            for step_id, task in tasks:
                try:
                    result = await task
                    results[step_id] = {"success": True, "result": result}
                except Exception as e:
                    results[step_id] = {"success": False, "error": str(e)}
        else:
            # Wait for first completion
            task_dict = {task: step_id for step_id, task in tasks}
            done, pending = await asyncio.wait(
                [task for _, task in tasks], 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get result from first completed task
            for task in done:
                step_id = task_dict[task]
                try:
                    result = await task
                    results[step_id] = {"success": True, "result": result}
                except Exception as e:
                    results[step_id] = {"success": False, "error": str(e)}
        
        # Store results in context
        context.set(f"{self.step_id}_results", results)
        
        return results


class DataTransformStep(WorkflowStep):
    """A workflow step that transforms data using a function."""
    
    def __init__(
        self,
        step_id: str,
        transform_func: Callable[[Any], Any],
        input_key: str,
        output_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize data transform step.
        
        Args:
            step_id: Unique identifier for the step
            transform_func: Function to transform the data
            input_key: Key to get input data from context
            output_key: Key to store output data (defaults to step_id)
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.transform_func = transform_func
        self.input_key = input_key
        self.output_key = output_key or step_id
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute data transformation."""
        # Get input data
        input_data = context.get(self.input_key)
        
        # Transform data
        if asyncio.iscoroutinefunction(self.transform_func):
            result = await self.transform_func(input_data)
        else:
            result = self.transform_func(input_data)
        
        # Store result
        context.set(self.output_key, result)
        
        return result


class LoopStep(WorkflowStep):
    """A workflow step that executes a step in a loop."""
    
    def __init__(
        self,
        step_id: str,
        loop_step: WorkflowStep,
        iteration_data_key: str,
        max_iterations: Optional[int] = None,
        break_condition: Optional[Callable[[WorkflowContext, int], bool]] = None,
        **kwargs
    ):
        """Initialize loop step.
        
        Args:
            step_id: Unique identifier for the step
            loop_step: Step to execute in each iteration
            iteration_data_key: Key for data to iterate over
            max_iterations: Maximum number of iterations
            break_condition: Function to check if loop should break
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.loop_step = loop_step
        self.iteration_data_key = iteration_data_key
        self.max_iterations = max_iterations
        self.break_condition = break_condition
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute loop."""
        iteration_data = context.get(self.iteration_data_key, [])
        results = []
        
        for i, item in enumerate(iteration_data):
            # Check max iterations
            if self.max_iterations and i >= self.max_iterations:
                break
            
            # Check break condition
            if self.break_condition and self.break_condition(context, i):
                break
            
            # Set current iteration data
            context.set(f"{self.step_id}_current_item", item)
            context.set(f"{self.step_id}_iteration", i)
            
            # Execute loop step
            try:
                result = await self.loop_step.execute(context)
                results.append({"iteration": i, "success": True, "result": result})
            except Exception as e:
                results.append({"iteration": i, "success": False, "error": str(e)})
        
        # Store results
        context.set(f"{self.step_id}_results", results)
        
        return results


class DelayStep(WorkflowStep):
    """A workflow step that introduces a delay."""
    
    def __init__(
        self,
        step_id: str,
        delay_seconds: float,
        **kwargs
    ):
        """Initialize delay step.
        
        Args:
            step_id: Unique identifier for the step
            delay_seconds: Number of seconds to delay
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.delay_seconds = delay_seconds
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute delay."""
        await asyncio.sleep(self.delay_seconds)
        return f"Delayed for {self.delay_seconds} seconds"


class ScriptStep(WorkflowStep):
    """A workflow step that executes Python code."""
    
    def __init__(
        self,
        step_id: str,
        script: str,
        output_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize script step.
        
        Args:
            step_id: Unique identifier for the step
            script: Python code to execute
            output_key: Key to store script result
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.script = script
        self.output_key = output_key or step_id
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute Python script."""
        # Create execution environment
        env = {
            "context": context,
            "asyncio": asyncio,
        }
        
        # Execute script
        try:
            exec(self.script, env)
            result = env.get("result", "Script executed successfully")
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {str(e)}") from e
        
        # Store result
        context.set(self.output_key, result)
        
        return result


class WebhookStep(WorkflowStep):
    """A workflow step that makes HTTP requests."""
    
    def __init__(
        self,
        step_id: str,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        output_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize webhook step.
        
        Args:
            step_id: Unique identifier for the step
            url: URL to make request to
            method: HTTP method
            headers: Request headers
            data: Request data
            output_key: Key to store response
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.data = data
        self.output_key = output_key or step_id
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute HTTP request."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for WebhookStep")
        
        # Resolve dynamic values
        url = self._resolve_value(self.url, context)
        headers = {k: self._resolve_value(v, context) for k, v in self.headers.items()}
        data = self._resolve_value(self.data, context) if self.data else None
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=self.method,
                url=url,
                headers=headers,
                json=data if self.method in ["POST", "PUT", "PATCH"] else None
            ) as response:
                result = {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "data": await response.text()
                }
                
                # Try to parse JSON if possible
                try:
                    result["json"] = await response.json()
                except:
                    pass
        
        # Store result
        context.set(self.output_key, result)
        
        return result
    
    def _resolve_value(self, value: Any, context: WorkflowContext) -> Any:
        """Resolve dynamic values from context."""
        if isinstance(value, str) and value.startswith("$"):
            return context.get(value[1:])
        elif isinstance(value, dict):
            return {k: self._resolve_value(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(item, context) for item in value]
        return value


class EmailStep(WorkflowStep):
    """A workflow step that sends emails."""
    
    def __init__(
        self,
        step_id: str,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        smtp_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize email step.
        
        Args:
            step_id: Unique identifier for the step
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email address
            smtp_config: SMTP server configuration
            **kwargs: Additional step configuration
        """
        super().__init__(step_id, **kwargs)
        self.to_email = to_email
        self.subject = subject
        self.body = body
        self.from_email = from_email
        self.smtp_config = smtp_config or {}
    
    async def execute(self, context: WorkflowContext) -> Any:
        """Send email."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Resolve dynamic values
        to_email = self._resolve_value(self.to_email, context)
        subject = self._resolve_value(self.subject, context)
        body = self._resolve_value(self.body, context)
        from_email = self._resolve_value(self.from_email, context)
        
        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        smtp_server = self.smtp_config.get("server", "localhost")
        smtp_port = self.smtp_config.get("port", 587)
        username = self.smtp_config.get("username")
        password = self.smtp_config.get("password")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if username and password:
                server.starttls()
                server.login(username, password)
            
            server.send_message(msg)
        
        result = f"Email sent to {to_email}"
        context.set(f"{self.step_id}_result", result)
        
        return result
    
    def _resolve_value(self, value: Any, context: WorkflowContext) -> Any:
        """Resolve dynamic values from context."""
        if isinstance(value, str) and "$" in value:
            # Simple template substitution
            for key, val in context.data.items():
                value = value.replace(f"${key}", str(val))
        return value


# Utility functions for creating common step patterns

def create_tool_step(
    step_id: str,
    tool_name: str,
    tool_inputs: Dict[str, Any],
    runner: ToolRunner,
    **kwargs
) -> ToolStep:
    """Create a tool step with convenient defaults."""
    return ToolStep(
        step_id=step_id,
        tool_name=tool_name,
        tool_inputs=tool_inputs,
        runner=runner,
        **kwargs
    )


def create_condition_step(
    step_id: str,
    condition: Union[str, Callable[[WorkflowContext], bool]],
    true_step: Optional[WorkflowStep] = None,
    false_step: Optional[WorkflowStep] = None,
    **kwargs
) -> ConditionStep:
    """Create a condition step with string condition support."""
    if isinstance(condition, str):
        # Simple string condition evaluation
        def condition_func(context: WorkflowContext) -> bool:
            # Basic evaluation - can be enhanced
            return bool(context.get(condition))
        condition = condition_func
    
    return ConditionStep(
        step_id=step_id,
        condition_func=condition,
        true_step=true_step,
        false_step=false_step,
        **kwargs
    )


def create_transform_step(
    step_id: str,
    transform: Union[str, Callable[[Any], Any]],
    input_key: str,
    output_key: Optional[str] = None,
    **kwargs
) -> DataTransformStep:
    """Create a data transform step with string transform support."""
    if isinstance(transform, str):
        # Simple string-based transformation
        def transform_func(data: Any) -> Any:
            if transform == "upper":
                return str(data).upper()
            elif transform == "lower":
                return str(data).lower()
            elif transform == "length":
                return len(data) if hasattr(data, "__len__") else 0
            elif transform == "json":
                import json
                return json.loads(str(data))
            else:
                return data
        transform = transform_func
    
    return DataTransformStep(
        step_id=step_id,
        transform_func=transform,
        input_key=input_key,
        output_key=output_key,
        **kwargs
    ) 