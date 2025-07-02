"""OpenAI adapter for Tomo tools."""

from typing import List, Dict, Any, Optional, Union
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool


class OpenAIAdapter:
    """Adapter for converting Tomo tools to OpenAI function calling format."""
    
    def __init__(self) -> None:
        """Initialize the OpenAI adapter."""
        pass
    
    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as OpenAI function schemas.
        
        Args:
            registry: The tool registry to export from.
            
        Returns:
            A list of OpenAI function schemas.
        """
        return registry.export_schemas()
    
    def export_tool(self, tool_class: type[BaseTool]) -> Dict[str, Any]:
        """Export a single tool as OpenAI function schema.
        
        Args:
            tool_class: The tool class to export.
            
        Returns:
            OpenAI function schema for the tool.
        """
        return tool_class.get_schema()
    
    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an OpenAI tool call to Tomo format.
        
        Args:
            tool_call: OpenAI tool call object.
            
        Returns:
            Dictionary with 'tool_name' and 'inputs' keys.
        """
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        
        # Parse arguments from JSON string if needed
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        
        return {
            "tool_name": tool_name,
            "inputs": arguments
        }
    
    def format_tool_result(self, result: Any, tool_call_id: Optional[str] = None) -> Dict[str, Any]:
        """Format a tool result for OpenAI response.
        
        Args:
            result: The tool execution result.
            tool_call_id: Optional tool call ID for response matching.
            
        Returns:
            Formatted tool result for OpenAI.
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
            "role": "tool",
            "content": content
        }
        
        if tool_call_id:
            response["tool_call_id"] = tool_call_id
        
        return response
    
    def create_system_prompt(self, registry: ToolRegistry, 
                           custom_instructions: Optional[str] = None) -> str:
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
    
    def validate_tool_call(self, tool_call: Dict[str, Any], registry: ToolRegistry) -> bool:
        """Validate that a tool call is valid for the given registry.
        
        Args:
            tool_call: OpenAI tool call object.
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