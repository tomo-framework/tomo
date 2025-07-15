"""Google Gemini adapter for Tomo tools."""

from typing import List, Dict, Any, Optional, Union
from .base import BaseAdapter
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class GeminiAdapter(BaseAdapter):
    """Adapter for converting Tomo tools to Google Gemini tool format."""

    def __init__(self) -> None:
        """Initialize the Gemini adapter."""
        pass

    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as Gemini tool schemas.

        Args:
            registry: The tool registry to export from.

        Returns:
            A list of Gemini tool schemas.
        """
        tools = []
        for tool_name in registry.list():
            tool_class = registry.get(tool_name)
            if tool_class:
                tools.append(self.export_tool(tool_class))
        return tools

    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as Gemini tool schema.

        Args:
            tool_class: The tool class to export.

        Returns:
            Gemini tool schema for the tool.
        """
        openai_schema = tool_class.get_schema()

        # Convert OpenAI format to Gemini format
        gemini_schema = {
            "name": openai_schema.get("name"),
            "description": openai_schema.get("description", ""),
            "parameters": openai_schema.get("parameters", {}),
        }

        return gemini_schema

    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Gemini tool call to Tomo format.

        Args:
            tool_call: Gemini tool call object.

        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        tool_name = tool_call.get("name")
        args = tool_call.get("args", {})

        return {"tool_name": tool_name, "inputs": args}

    def format_tool_result(
        self, result: Any, tool_call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a tool result for Gemini response.

        Args:
            result: The tool execution result.
            tool_call_id: Optional tool call ID for response matching.

        Returns:
            Formatted tool result for Gemini.
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

        response = {
            "role": "model",
            "parts": [
                {
                    "functionResponse": {
                        "name": tool_call_id or "unknown",
                        "response": {
                            "name": tool_call_id or "unknown",
                            "content": content,
                        },
                    }
                }
            ],
        }

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
            tool_call: Gemini tool call object.
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
