# Example Plugins

This directory contains example plugins that demonstrate how to extend Tomo with custom functionality.

## Available Plugins

### 🌐 Web Tools Plugin (`web_tools_plugin.py`)
Provides web-related utilities:
- **URLValidator**: Validate URLs and extract components
- **DomainExtractor**: Extract domain names from URLs
- **HTMLCleaner**: Remove HTML tags from text
- **EmailExtractor**: Extract email addresses from text

### 📊 Data Tools Plugin (`data_tools_plugin.py`)
Provides data processing utilities:
- **JSONParser**: Parse JSON and extract values by key path
- **JSONValidator**: Validate JSON strings
- **CSVParser**: Parse CSV data into structured format
- **TextAnalyzer**: Analyze text for statistics and patterns
- **ListProcessor**: Process lists with various operations

### 🦙 Custom Adapter Plugin (`custom_adapter_plugin.py`)
Example custom LLM adapter:
- **LlamaLocalAdapter**: Adapter for local Llama models
- Shows how to create custom adapters for new LLM providers
- Demonstrates format conversion and system prompt optimization

## Using the Example Plugins

### 1. Load Plugins from Directory

```bash
# Load all plugins from this directory
tomo plugin load-directory ./examples/plugins --verbose

# List loaded plugins
tomo plugin list
```

### 2. Load Plugins via Configuration

```bash
# Create a sample configuration
tomo plugin create-sample-config --output my-plugins.json

# Edit the configuration file as needed
# Then load plugins from config
tomo plugin load-config --config my-plugins.json
```

### 3. Use Plugin Tools

After loading plugins, you can use the tools they provide:

```bash
# List all available tools (including plugin tools)
tomo list --module examples.basic_tools

# Run a web tool
tomo run URLValidator --inputs '{"url": "https://example.com"}'

# Run a data processing tool
tomo run JSONValidator --inputs '{"json_string": "{\"name\": \"test\"}"}'

# Run text analysis
tomo run TextAnalyzer --inputs '{"text": "This is a sample text for analysis."}'
```

### 4. Programmatic Usage

```python
from tomo.plugins import PluginLoader
from tomo import ToolRunner

# Load plugins
loader = PluginLoader()
loader.load_from_directory("./examples/plugins")

# Use plugin tools
runner = ToolRunner(loader.registry.tool_registry)

# Validate a URL
result = runner.run_tool("URLValidator", {
    "url": "https://github.com/tomo-framework/tomo"
})
print(result)

# Analyze text
analysis = runner.run_tool("TextAnalyzer", {
    "text": "The quick brown fox jumps over the lazy dog."
})
print(analysis)

# Parse JSON
data = runner.run_tool("JSONParser", {
    "json_string": '{"user": {"name": "Alice", "age": 30}}',
    "key_path": "user.name"
})
print(data)  # Output: "Alice"
```

## Creating Your Own Plugins

Use these examples as templates for creating your own plugins:

### 1. Tool Collection Plugin

```python
from tomo import BaseTool, tool
from tomo.plugins import BasePlugin, PluginType, plugin

@plugin(PluginType.TOOL, "my_tools", "1.0.0")
class MyToolsPlugin(BasePlugin):
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def name(self) -> str:
        return "my_tools"
    
    # ... other required properties
    
    def register_components(self, registry):
        registry.tool_registry.register(MyCustomTool)

@tool
class MyCustomTool(BaseTool):
    # Your tool implementation
    pass
```

### 2. Custom Adapter Plugin

```python
from tomo.adapters.base import BaseAdapter
from tomo.plugins import BasePlugin, PluginType, plugin

@plugin(PluginType.ADAPTER, "my_adapter", "1.0.0")
class MyAdapterPlugin(BasePlugin):
    def register_components(self, registry):
        registry.adapter_registry["my_provider"] = MyCustomAdapter

class MyCustomAdapter(BaseAdapter):
    # Implement the BaseAdapter interface
    pass
```

## Configuration

Plugins can be configured when loaded. The sample configuration shows examples:

```json
{
  "plugins": [
    {
      "source": {
        "directory": "./examples/plugins"
      },
      "enabled": true,
      "config": {
        "max_url_length": 2048,
        "model_path": "./models/llama-model.gguf"
      }
    }
  ]
}
```

Configuration values are passed to each plugin's `initialize()` method.

## Best Practices

1. **Plugin Structure**: Keep related tools in the same plugin
2. **Dependencies**: Declare external dependencies in the `dependencies` property
3. **Configuration**: Make plugins configurable through the config parameter
4. **Error Handling**: Handle errors gracefully in tool implementations
5. **Documentation**: Provide clear docstrings and type hints
6. **Testing**: Test your plugins before distribution

## Contributing

To contribute new example plugins:

1. Create a new `.py` file in this directory
2. Follow the existing plugin patterns
3. Add documentation about your plugin to this README
4. Test your plugin with the CLI and programmatic interfaces

These examples show the flexibility and power of the Tomo plugin system! 