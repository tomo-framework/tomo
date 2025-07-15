"""Base adapter class for LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class BaseAdapter(ABC):
    """Base class for LLM adapters.

    This class defines the common interface that all LLM adapters must implement.
    Each adapter converts Tomo tools to the specific format required by its LLM provider.
    """

    @abstractmethod
    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as LLM-specific schemas.

        Args:
            registry: The tool registry to export from.

        Returns:
            A list of LLM-specific tool schemas.
        """
        pass

    @abstractmethod
    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as LLM-specific schema.

        Args:
            tool_class: The tool class to export.

        Returns:
            LLM-specific tool schema for the tool.
        """
        pass

    @abstractmethod
    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an LLM tool call to Tomo format.

        Args:
            tool_call: LLM-specific tool call object.

        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        pass

    @abstractmethod
    def format_tool_result(
        self, result: Any, tool_call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a tool result for LLM response.

        Args:
            result: The tool execution result.
            tool_call_id: Optional tool call ID for response matching.

        Returns:
            Formatted tool result for the LLM.
        """
        pass

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
            tool_call: LLM-specific tool call object.
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
