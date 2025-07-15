"""Mistral AI adapter for Tomo tools."""

from typing import List, Dict, Any, Optional
from .base import BaseAdapter
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class MistralAdapter(BaseAdapter):
    """Adapter for converting Tomo tools to Mistral AI tool format."""

    def __init__(self) -> None:
        """Initialize the Mistral adapter."""
        pass

    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as Mistral tool schemas.

        Args:
            registry: The tool registry to export from.

        Returns:
            A list of Mistral tool schemas.
        """
        tools = []
        for tool_name in registry.list():
            tool_class = registry.get(tool_name)
            if tool_class:
                tools.append(self.export_tool(tool_class))
        return tools

    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as Mistral tool schema.

        Args:
            tool_class: The tool class to export.

        Returns:
            Mistral tool schema for the tool.
        """
        openai_schema = tool_class.get_schema()

        # Convert OpenAI format to Mistral format
        mistral_schema = {
            "type": "function",
            "function": {
                "name": openai_schema.get("name"),
                "description": openai_schema.get("description", ""),
                "parameters": openai_schema.get("parameters", {}),
            },
        }

        return mistral_schema

    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Mistral tool call to Tomo format.

        Args:
            tool_call: Mistral tool call object.

        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        arguments = function.get("arguments", {})

        # Parse arguments from JSON string if needed
        if isinstance(arguments, str):
            import json

            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        return {"tool_name": tool_name, "inputs": arguments}

    def format_tool_result(
        self, result: Any, tool_call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a tool result for Mistral response.

        Args:
            result: The tool execution result.
            tool_call_id: Optional tool call ID for response matching.

        Returns:
            Formatted tool result for Mistral.
        """
        # Convert result to string if it's not already
        if not isinstance(result, str):
            import json

            try:
                content = json.dumps(result, default=str)
            except (TypeError, ValueError):
                content = str(result)
        else:
            content = result

        response = {"role": "tool", "content": content}

        if tool_call_id:
            response["tool_call_id"] = tool_call_id

        return response
