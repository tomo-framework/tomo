"""Custom Adapter Plugin - Example plugin providing a custom LLM adapter."""

from typing import Dict, Any, List, Optional

from tomo import ToolRegistry
from tomo.adapters.base import BaseAdapter
from tomo.plugins import BasePlugin, PluginType, plugin


@plugin(PluginType.ADAPTER, "llama_local_adapter", "1.0.0")
class LlamaLocalAdapterPlugin(BasePlugin):
    """Plugin providing an adapter for local Llama models."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.ADAPTER
    
    @property
    def name(self) -> str:
        return "llama_local_adapter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Adapter for local Llama models via llama.cpp or similar backends"
    
    @property
    def author(self) -> str:
        return "Tomo Community"
    
    @property
    def homepage(self) -> str:
        return "https://github.com/tomo-framework/tomo/tree/main/examples/plugins"
    
    @property
    def dependencies(self) -> List[str]:
        return []  # In a real implementation, this might include llama-cpp-python
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the adapter plugin."""
        self.config = config or {}
        print(f"🦙 Initializing {self.name} plugin v{self.version}")
        
        # Configuration for the local model
        self.model_path = self.config.get("model_path", "./models/llama-model.gguf")
        self.context_length = self.config.get("context_length", 2048)
        self.temperature = self.config.get("temperature", 0.7)
    
    def register_components(self, registry) -> None:
        """Register the Llama adapter with the registry."""
        registry.adapter_registry["llama_local"] = LlamaLocalAdapter


class LlamaLocalAdapter(BaseAdapter):
    """Adapter for local Llama models.
    
    This is a simplified example showing the adapter interface.
    A real implementation would integrate with llama.cpp or similar.
    """
    
    def __init__(self, model_path: str = None, context_length: int = 2048):
        self.model_path = model_path or "./models/llama-model.gguf"
        self.context_length = context_length
    
    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export all tools from registry as Llama-compatible schemas."""
        tools = []
        for tool_name in registry.list():
            tool_class = registry.get(tool_name)
            if tool_class:
                tools.append(self.export_tool(tool_class))
        return tools
    
    def export_tool(self, tool_class) -> Dict[str, Any]:
        """Export a single tool as Llama-compatible schema."""
        base_schema = tool_class.get_schema()
        
        # Convert to a simplified format suitable for local models
        llama_schema = {
            "function_name": base_schema.get("name"),
            "description": base_schema.get("description", ""),
            "parameters": self._convert_parameters(base_schema.get("parameters", {})),
            "format": "llama_local_v1",
            "context_requirements": {
                "min_context_length": 512,
                "recommended_context_length": 1024
            }
        }
        
        return llama_schema
    
    def _convert_parameters(self, openai_params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAI parameter format to local model format."""
        if "properties" not in openai_params:
            return {}
        
        converted = {}
        properties = openai_params["properties"]
        required = openai_params.get("required", [])
        
        for param_name, param_info in properties.items():
            converted[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
                "required": param_name in required,
                "example": self._generate_example(param_info.get("type", "string"))
            }
        
        return converted
    
    def _generate_example(self, param_type: str) -> Any:
        """Generate example values for parameters."""
        examples = {
            "string": "example_value",
            "integer": 42,
            "number": 3.14,
            "boolean": True,
            "array": ["item1", "item2"],
            "object": {"key": "value"}
        }
        return examples.get(param_type, "example")
    
    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Llama tool call to Tomo format."""
        # Expect format: {"function_name": "tool_name", "arguments": {...}}
        function_name = tool_call.get("function_name")
        arguments = tool_call.get("arguments", {})
        
        # Handle different possible argument formats
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        
        return {
            "tool_name": function_name,
            "inputs": arguments
        }
    
    def format_tool_result(self, result: Any, tool_call_id: Optional[str] = None) -> Dict[str, Any]:
        """Format a tool result for Llama response."""
        # Convert result to a format suitable for local models
        if not isinstance(result, str):
            import json
            try:
                result_str = json.dumps(result, default=str, indent=2)
            except (TypeError, ValueError):
                result_str = str(result)
        else:
            result_str = result
        
        return {
            "type": "function_result",
            "content": result_str,
            "call_id": tool_call_id,
            "status": "success",
            "format": "llama_local_v1",
            "tokens_used": len(result_str.split()),  # Rough estimate
        }
    
    def create_system_prompt(
        self, 
        registry: ToolRegistry, 
        custom_instructions: Optional[str] = None
    ) -> str:
        """Create a system prompt optimized for local Llama models."""
        tools = registry.list_tools()
        
        prompt_parts = []
        
        # Add custom instructions
        if custom_instructions:
            prompt_parts.append(custom_instructions)
            prompt_parts.append("")
        
        # Add tool information in a format optimized for local models
        if tools:
            prompt_parts.append("You have access to the following tools. Call them using the specified format:")
            prompt_parts.append("")
            
            for tool_name, tool_class in tools.items():
                description = tool_class.get_description()
                schema = tool_class.get_schema()
                
                prompt_parts.append(f"Tool: {tool_name}")
                prompt_parts.append(f"Description: {description}")
                
                # Add parameter information
                params = schema.get("parameters", {}).get("properties", {})
                if params:
                    prompt_parts.append("Parameters:")
                    for param_name, param_info in params.items():
                        param_type = param_info.get("type", "string")
                        param_desc = param_info.get("description", "")
                        prompt_parts.append(f"  - {param_name} ({param_type}): {param_desc}")
                
                prompt_parts.append("")
            
            prompt_parts.append("To call a tool, use this exact format:")
            prompt_parts.append('{"function_name": "tool_name", "arguments": {"param1": "value1", "param2": "value2"}}')
            prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    def validate_tool_call(
        self, 
        tool_call: Dict[str, Any], 
        registry: ToolRegistry
    ) -> bool:
        """Validate that a tool call is valid for the given registry."""
        try:
            converted = self.convert_tool_call(tool_call)
            tool_name = converted.get("tool_name")
            
            if not tool_name or tool_name not in registry:
                return False
            
            # Basic validation - in a real implementation, you might do more
            return True
            
        except Exception:
            return False 