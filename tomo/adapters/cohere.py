"""Cohere adapter for Tomo tools."""

from typing import List, Dict, Any, Optional
from .base import BaseAdapter
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class CohereAdapter(BaseAdapter):
    """Adapter for converting Tomo tools to Cohere Command R+ tool format."""

    def __init__(self) -> None:
        """Initialize the Cohere adapter."""
        pass

    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as Cohere tool schemas.

        Args:
            registry: The tool registry to export from.

        Returns:
            A list of Cohere tool schemas.
        """
        tools = []
        for tool_name in registry.list():
            tool_class = registry.get(tool_name)
            if tool_class:
                tools.append(self.export_tool(tool_class))
        return tools

    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as Cohere tool schema.

        Args:
            tool_class: The tool class to export.

        Returns:
            Cohere tool schema for the tool.
        """
        openai_schema = tool_class.get_schema()

        # Convert OpenAI format to Cohere format
        cohere_schema = {
            "name": openai_schema.get("name"),
            "description": openai_schema.get("description", ""),
            "parameter_definitions": openai_schema.get("parameters", {}),
        }

        return cohere_schema

    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Cohere tool call to Tomo format.

        Args:
            tool_call: Cohere tool call object.

        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        tool_name = tool_call.get("name")
        parameters = tool_call.get("parameters", {})

        return {"tool_name": tool_name, "inputs": parameters}

    def format_tool_result(
        self, result: Any, tool_call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a tool result for Cohere response.

        Args:
            result: The tool execution result.
            tool_call_id: Optional tool call ID for response matching.

        Returns:
            Formatted tool result for Cohere.
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

        response = {"type": "tool_result", "content": content}

        if tool_call_id:
            response["tool_call_id"] = tool_call_id

        return response
