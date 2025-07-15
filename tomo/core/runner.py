"""Tool runner for executing registered tools."""

from typing import Any, Dict, Optional, Union
import json
from pydantic import ValidationError
from .tool import BaseTool
from .registry import ToolRegistry


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""

    pass


class ToolNotFoundError(Exception):
    """Exception raised when a requested tool is not found."""

    pass


class ToolValidationError(Exception):
    """Exception raised when tool input validation fails."""

    pass


class ToolRunner:
    """Runner for executing tools from a registry.

    The runner handles tool instantiation, validation, and execution
    with proper error handling and result formatting.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        """Initialize the tool runner with a registry.

        Args:
            registry: The tool registry to use for tool lookup.
        """
        self.registry = registry

    def run_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Any:
        """Run a tool by name with the given inputs.

        Args:
            tool_name: The name of the tool to run.
            inputs: Dictionary of input parameters for the tool.

        Returns:
            The result of the tool execution.

        Raises:
            ToolNotFoundError: If the tool is not found in the registry.
            ToolValidationError: If the input validation fails.
            ToolExecutionError: If the tool execution fails.
        """
        # Get the tool class
        tool_class = self.registry.get(tool_name)
        if tool_class is None:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in registry")

        try:
            # Instantiate the tool with input validation
            tool_instance = tool_class(**inputs)
        except ValidationError as e:
            raise ToolValidationError(
                f"Input validation failed for tool '{tool_name}': {e}"
            )
        except TypeError as e:
            raise ToolValidationError(f"Invalid inputs for tool '{tool_name}': {e}")

        try:
            # Execute the tool
            result = tool_instance.run()
            return result
        except Exception as e:
            raise ToolExecutionError(f"Tool '{tool_name}' execution failed: {e}")

    def run_tool_from_json(self, tool_name: str, inputs_json: str) -> Any:
        """Run a tool by name with JSON-encoded inputs.

        Args:
            tool_name: The name of the tool to run.
            inputs_json: JSON string containing input parameters.

        Returns:
            The result of the tool execution.

        Raises:
            ToolNotFoundError: If the tool is not found in the registry.
            ToolValidationError: If JSON parsing or input validation fails.
            ToolExecutionError: If the tool execution fails.
        """
        try:
            inputs = json.loads(inputs_json)
        except json.JSONDecodeError as e:
            raise ToolValidationError(f"Invalid JSON inputs: {e}")

        return self.run_tool(tool_name, inputs)

    def run_tool_safe(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run a tool safely, returning a structured result with error handling.

        Args:
            tool_name: The name of the tool to run.
            inputs: Dictionary of input parameters for the tool.

        Returns:
            A dictionary with 'success', 'result', and 'error' keys.
        """
        try:
            result = self.run_tool(tool_name, inputs)
            return {"success": True, "result": result, "error": None}
        except (ToolNotFoundError, ToolValidationError, ToolExecutionError) as e:
            return {"success": False, "result": None, "error": str(e)}

    def validate_tool_inputs(self, tool_name: str, inputs: Dict[str, Any]) -> bool:
        """Validate inputs for a tool without executing it.

        Args:
            tool_name: The name of the tool to validate inputs for.
            inputs: Dictionary of input parameters to validate.

        Returns:
            True if inputs are valid, False otherwise.

        Raises:
            ToolNotFoundError: If the tool is not found in the registry.
        """
        tool_class = self.registry.get(tool_name)
        if tool_class is None:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in registry")

        try:
            tool_class(**inputs)
            return True
        except (ValidationError, TypeError):
            return False

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a tool.

        Args:
            tool_name: The name of the tool.

        Returns:
            The tool schema if found, None otherwise.
        """
        return self.registry.get_schema(tool_name)

    def list_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools with their schemas.

        Returns:
            A dictionary mapping tool names to their schemas.
        """
        tools = {}
        for tool_name in self.registry.list():
            schema = self.get_tool_schema(tool_name)
            if schema:
                tools[tool_name] = schema
        return tools

    def create_tool_instance(self, tool_name: str, inputs: Dict[str, Any]) -> BaseTool:
        """Create a tool instance without running it.

        Args:
            tool_name: The name of the tool to create.
            inputs: Dictionary of input parameters for the tool.

        Returns:
            The instantiated tool.

        Raises:
            ToolNotFoundError: If the tool is not found in the registry.
            ToolValidationError: If the input validation fails.
        """
        tool_class = self.registry.get(tool_name)
        if tool_class is None:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found in registry")

        try:
            return tool_class(**inputs)
        except ValidationError as e:
            raise ToolValidationError(
                f"Input validation failed for tool '{tool_name}': {e}"
            )
        except TypeError as e:
            raise ToolValidationError(f"Invalid inputs for tool '{tool_name}': {e}")

    def __repr__(self) -> str:
        """String representation of the runner."""
        return f"ToolRunner(registry={self.registry})"
