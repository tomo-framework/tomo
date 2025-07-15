"""Azure OpenAI adapter for Tomo tools."""

from typing import List, Dict, Any, Optional, Union
from .openai import OpenAIAdapter
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class AzureOpenAIAdapter(OpenAIAdapter):
    """Adapter for converting Tomo tools to Azure OpenAI function calling format.

    This adapter extends the OpenAI adapter to handle Azure-specific configurations
    and deployment names.
    """

    def __init__(self, deployment_name: Optional[str] = None) -> None:
        """Initialize the Azure OpenAI adapter.

        Args:
            deployment_name: Optional Azure deployment name for tool calls.
        """
        super().__init__()
        self.deployment_name = deployment_name

    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as Azure OpenAI function schemas.

        Args:
            registry: The tool registry to export from.

        Returns:
            A list of Azure OpenAI function schemas.
        """
        # Azure OpenAI uses the same format as OpenAI
        return super().export_tools(registry)

    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as Azure OpenAI function schema.

        Args:
            tool_class: The tool class to export.

        Returns:
            Azure OpenAI function schema for the tool.
        """
        # Azure OpenAI uses the same format as OpenAI
        return super().export_tool(tool_class)

    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an Azure OpenAI tool call to Tomo format.

        Args:
            tool_call: Azure OpenAI tool call object.

        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        # Azure OpenAI uses the same format as OpenAI
        return super().convert_tool_call(tool_call)

    def format_tool_result(
        self, result: Any, tool_call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a tool result for Azure OpenAI response.

        Args:
            result: The tool execution result.
            tool_call_id: Optional tool call ID for response matching.

        Returns:
            Formatted tool result for Azure OpenAI.
        """
        # Azure OpenAI uses the same format as OpenAI
        return super().format_tool_result(result, tool_call_id)

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
        # Azure OpenAI uses the same format as OpenAI
        return super().create_system_prompt(registry, custom_instructions)

    def validate_tool_call(
        self, tool_call: Dict[str, Any], registry: ToolRegistry
    ) -> bool:
        """Validate that a tool call is valid for the given registry.

        Args:
            tool_call: Azure OpenAI tool call object.
            registry: The tool registry to validate against.

        Returns:
            True if the tool call is valid, False otherwise.
        """
        # Azure OpenAI uses the same format as OpenAI
        return super().validate_tool_call(tool_call, registry)

    def get_deployment_config(self) -> Dict[str, Any]:
        """Get Azure deployment configuration.

        Returns:
            Dictionary with Azure-specific configuration.
        """
        config = {}
        if self.deployment_name:
            config["deployment_name"] = self.deployment_name
        return config
