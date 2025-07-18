"""Demonstration of the Tomo plugin system.

This example shows how to create plugins that extend Tomo with new tools,
adapters, and other components.
"""

from tomo import BaseTool, tool, ToolRegistry, ToolRunner
from tomo.plugins import BasePlugin, PluginType, plugin, PluginRegistry, PluginLoader
from tomo.adapters.base import BaseAdapter
from typing import Dict, Any, List


# Example 1: Tool Collection Plugin
@plugin(PluginType.TOOL, "math_tools", "1.0.0")
class MathToolsPlugin(BasePlugin):
    """Plugin that provides mathematical tools."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def name(self) -> str:
        return "math_tools"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Mathematical computation tools including factorial, fibonacci, and prime checking"
    
    @property
    def author(self) -> str:
        return "Tomo Team"
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the plugin."""
        self.config = config or {}
        print(f"🔌 Initializing {self.name} plugin v{self.version}")
    
    def register_components(self, registry: PluginRegistry) -> None:
        """Register mathematical tools with the registry."""
        registry.tool_registry.register(FactorialTool)
        registry.tool_registry.register(FibonacciTool)
        registry.tool_registry.register(PrimeCheckerTool)


@tool
class FactorialTool(BaseTool):
    """Calculate factorial of a number."""
    
    n: int
    
    def run(self) -> int:
        """Calculate n!"""
        if self.n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        
        result = 1
        for i in range(1, self.n + 1):
            result *= i
        return result


@tool
class FibonacciTool(BaseTool):
    """Calculate nth Fibonacci number."""
    
    n: int
    
    def run(self) -> int:
        """Calculate nth Fibonacci number."""
        if self.n < 0:
            raise ValueError("Fibonacci is not defined for negative numbers")
        
        if self.n <= 1:
            return self.n
        
        a, b = 0, 1
        for _ in range(2, self.n + 1):
            a, b = b, a + b
        return b


@tool
class PrimeCheckerTool(BaseTool):
    """Check if a number is prime."""
    
    n: int
    
    def run(self) -> bool:
        """Check if n is prime."""
        if self.n < 2:
            return False
        
        for i in range(2, int(self.n ** 0.5) + 1):
            if self.n % i == 0:
                return False
        return True


# Example 2: Custom Adapter Plugin
@plugin(PluginType.ADAPTER, "custom_llm_adapter", "1.0.0")
class CustomLLMAdapterPlugin(BasePlugin):
    """Plugin that provides a custom LLM adapter."""
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.ADAPTER
    
    @property
    def name(self) -> str:
        return "custom_llm_adapter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Custom adapter for hypothetical LLM provider"
    
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the adapter plugin."""
        self.config = config or {}
        print(f"🔌 Initializing {self.name} plugin v{self.version}")
    
    def register_components(self, registry: PluginRegistry) -> None:
        """Register the custom adapter."""
        registry.adapter_registry["custom_llm"] = CustomLLMAdapter


class CustomLLMAdapter(BaseAdapter):
    """Example custom LLM adapter."""
    
    def export_tools(self, registry: ToolRegistry) -> List[Dict[str, Any]]:
        """Export tools in custom format."""
        tools = []
        for tool_name in registry.list():
            tool_class = registry.get(tool_name)
            if tool_class:
                tools.append(self.export_tool(tool_class))
        return tools
    
    def export_tool(self, tool_class) -> Dict[str, Any]:
        """Export single tool in custom format."""
        schema = tool_class.get_schema()
        return {
            "tool_name": schema.get("name"),
            "tool_description": schema.get("description"),
            "parameters": schema.get("parameters", {}),
            "custom_metadata": {
                "format": "custom_llm_v1",
                "exported_by": "Tomo"
            }
        }
    
    def convert_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Convert custom format to Tomo format."""
        return {
            "tool_name": tool_call.get("tool_name"),
            "inputs": tool_call.get("parameters", {})
        }
    
    def format_tool_result(self, result: Any, tool_call_id: str = None) -> Dict[str, Any]:
        """Format result for custom LLM."""
        return {
            "status": "success",
            "result": str(result),
            "call_id": tool_call_id,
            "format": "custom_llm_v1"
        }


def demo_plugin_system():
    """Demonstrate the plugin system functionality."""
    print("🧠 Tomo Plugin System Demo")
    print("=" * 50)
    
    # 1. Create plugin loader
    print("\n1. Creating plugin loader...")
    loader = PluginLoader()
    
    # 2. Manually register plugins (simulating auto-discovery)
    print("\n2. Registering plugins...")
    
    # Register math tools plugin
    math_plugin = MathToolsPlugin()
    loader.registry.register_plugin(math_plugin)
    
    # Register adapter plugin
    adapter_plugin = CustomLLMAdapterPlugin()
    loader.registry.register_plugin(adapter_plugin)
    
    print(f"   Registered {len(loader.registry.plugins)} plugins")
    
    # 3. List registered plugins
    print("\n3. Listing registered plugins...")
    for plugin_name in loader.registry.list_plugins():
        info = loader.registry.get_plugin_info(plugin_name)
        print(f"   📦 {info['name']} v{info['version']} ({info['type']})")
        print(f"      {info['description']}")
    
    # 4. Test tool execution using plugin-registered tools
    print("\n4. Testing plugin tools...")
    runner = ToolRunner(loader.registry.tool_registry)
    
    # Test factorial
    factorial_result = runner.run_tool("FactorialTool", {"n": 5})
    print(f"   Factorial(5) = {factorial_result}")
    
    # Test fibonacci
    fib_result = runner.run_tool("FibonacciTool", {"n": 10})
    print(f"   Fibonacci(10) = {fib_result}")
    
    # Test prime check
    prime_result = runner.run_tool("PrimeCheckerTool", {"n": 17})
    print(f"   Is 17 prime? {prime_result}")
    
    # 5. Test custom adapter
    print("\n5. Testing custom adapter...")
    custom_adapter = loader.registry.adapter_registry["custom_llm"]()
    
    # Export tools using custom adapter
    exported_tools = custom_adapter.export_tools(loader.registry.tool_registry)
    print(f"   Exported {len(exported_tools)} tools in custom format")
    
    # Show example tool export
    if exported_tools:
        example_tool = exported_tools[0]
        print(f"   Example tool export: {example_tool['tool_name']}")
        print(f"   Custom metadata: {example_tool['custom_metadata']}")
    
    # 6. Plugin validation
    print("\n6. Validating plugins...")
    validation_results = loader.registry.validate_all_plugins()
    for plugin_name, errors in validation_results.items():
        if errors:
            print(f"   ❌ {plugin_name}: {errors}")
        else:
            print(f"   ✅ {plugin_name}: Valid")
    
    print("\n✨ Plugin system demo completed!")


def demo_plugin_config():
    """Demonstrate plugin configuration loading."""
    print("\n🔧 Plugin Configuration Demo")
    print("=" * 30)
    
    # Create a sample configuration
    loader = PluginLoader()
    config_file = "sample_plugins.json"
    
    print(f"\n1. Creating sample configuration: {config_file}")
    loader.create_sample_config(config_file)
    
    print(f"   ✅ Created {config_file}")
    print("   📝 Edit this file to configure your plugins")
    
    # Validate the configuration
    print(f"\n2. Validating configuration...")
    errors = loader.validate_config_file(config_file)
    
    if not errors:
        print("   ✅ Configuration is valid")
    else:
        print("   ❌ Configuration has errors:")
        for error in errors:
            print(f"      • {error}")
    
    print(f"\n💡 To load plugins from config: tomo plugin load-config --config {config_file}")


def demo_example_plugins():
    """Demonstrate loading and using the example plugins."""
    print("\n🔌 Example Plugins Demo")
    print("=" * 30)
    
    # Load plugins from the examples directory
    loader = PluginLoader()
    
    print("\n1. Loading plugins from examples/plugins directory...")
    try:
        discovered = loader.load_from_directory("./examples/plugins")
        print(f"   ✅ Loaded {discovered} plugins from examples directory")
    except Exception as e:
        print(f"   ❌ Failed to load plugins: {e}")
        return
    
    # List the loaded plugins
    print("\n2. Loaded plugins:")
    for plugin_name in loader.registry.list_plugins():
        info = loader.registry.get_plugin_info(plugin_name)
        print(f"   📦 {info['name']} v{info['version']} ({info['type']})")
        print(f"      {info['description']}")
    
    # Test some plugin tools
    print("\n3. Testing plugin tools...")
    runner = ToolRunner(loader.registry.tool_registry)
    
    # Test URL validation
    if "URLValidator" in loader.registry.tool_registry:
        url_result = runner.run_tool("URLValidator", {
            "url": "https://github.com/tomo-framework/tomo"
        })
        print(f"   🌐 URL Validation: {url_result.get('is_valid')} for {url_result.get('domain')}")
    
    # Test JSON parsing
    if "JSONParser" in loader.registry.tool_registry:
        json_result = runner.run_tool("JSONParser", {
            "json_string": '{"user": {"name": "Alice", "age": 30}}',
            "key_path": "user.name"
        })
        print(f"   📊 JSON Parsing: Extracted '{json_result}' from nested JSON")
    
    # Test text analysis
    if "TextAnalyzer" in loader.registry.tool_registry:
        text_result = runner.run_tool("TextAnalyzer", {
            "text": "The quick brown fox jumps over the lazy dog."
        })
        word_count = text_result.get('word_count', 0)
        unique_words = text_result.get('unique_words', 0)
        print(f"   📝 Text Analysis: {word_count} words, {unique_words} unique")
    
    # Test custom adapter
    print("\n4. Testing custom adapter...")
    if "llama_local" in loader.registry.adapter_registry:
        adapter_class = loader.registry.adapter_registry["llama_local"]
        adapter = adapter_class()
        
        # Export tools using the custom adapter
        exported_tools = adapter.export_tools(loader.registry.tool_registry)
        print(f"   🦙 Custom Adapter: Exported {len(exported_tools)} tools in Llama format")
        
        if exported_tools:
            example_tool = exported_tools[0]
            print(f"      Example: {example_tool.get('function_name')} - {example_tool.get('description', '')[:50]}...")
    
    print("\n✨ Example plugins demo completed!")


if __name__ == "__main__":
    demo_plugin_system()
    demo_plugin_config()
    demo_example_plugins() 