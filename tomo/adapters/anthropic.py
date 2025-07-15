"""Anthropic Claude adapter for Tomo tools."""

from typing import List, Dict, Any, Optional, Union
from .base import BaseAdapter
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class AnthropicAdapter(BaseAdapter):
    """Adapter for converting Tomo tools to Anthropic Claude tool format."""

    def __init__(self) -> None:
        """Initialize the Anthropic adapter."""
        pass

    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as Anthropic tool schemas.

        Args:
            registry: The tool registry to export from.

        Returns:
            A list of Anthropic tool schemas.
        """
        tools = []
        for tool_name in registry.list():
            tool_class = registry.get(tool_name)
            if tool_class:
                tools.append(self.export_tool(tool_class))
        return tools

    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as Anthropic tool schema.

        Args:
            tool_class: The tool class to export.

        Returns:
            Anthropic tool schema for the tool.
        """
        openai_schema = tool_class.get_schema()

        # Convert OpenAI format to Anthropic format
        anthropic_schema = {
            "name": openai_schema.get("name"),
            "description": openai_schema.get("description", ""),
            "input_schema": openai_schema.get("parameters", {}),
        }

        return anthropic_schema

    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an Anthropic tool call to Tomo format.

        Args:
            tool_call: Anthropic tool call object.

        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        tool_name = tool_call.get("name")
        inputs = tool_call.get("input", {})

        return {"tool_name": tool_name, "inputs": inputs}

    def format_tool_result(
        self, result: Any, tool_use_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a tool result for Anthropic response.

        Args:
            result: The tool execution result.
            tool_use_id: Optional tool use ID for response matching.

        Returns:
            Formatted tool result for Anthropic.
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

        if tool_use_id:
            response["tool_use_id"] = tool_use_id

        return response

    def create_system_prompt(
        self, registry: ToolRegistry, custom_instructions: Optional[str] = None
    ) -> str:
        """Create a system prompt that describes available tools.

        Args:
            registry: The tool registry containing available tools.
            custom_instructions: Optional custom instructions to include.

        Returns:
            System prompt string.
        """
        tools = registry.list_tools()

        prompt_parts = []

        if custom_instructions:
            prompt_parts.append(custom_instructions)
            prompt_parts.append("")

        if tools:
            prompt_parts.append("You have access to the following tools:")
            prompt_parts.append("")

            for tool_name, tool_class in tools.items():
                description = tool_class.get_description()
                prompt_parts.append(f"- {tool_name}: {description}")

            prompt_parts.append("")
            prompt_parts.append(
                "Use these tools when appropriate to help answer questions or complete tasks. "
                "Call tools with the correct parameters based on their schemas."
            )
        else:
            prompt_parts.append("No tools are currently available.")

        return "\n".join(prompt_parts)

    def validate_tool_call(
        self, tool_call: Dict[str, Any], registry: ToolRegistry
    ) -> bool:
        """Validate that a tool call is valid for the given registry.

        Args:
            tool_call: Anthropic tool call object.
            registry: The tool registry to validate against.

        Returns:
            True if the tool call is valid, False otherwise.
        """
        try:
            converted = self.convert_tool_call(tool_call)
            tool_name = converted["tool_name"]

            if not tool_name or tool_name not in registry:
                return False

            # Check if inputs can be validated
            from ..core.runner import ToolRunner

            runner = ToolRunner(registry)
            return runner.validate_tool_inputs(tool_name, converted["inputs"])

        except Exception:
            return False
