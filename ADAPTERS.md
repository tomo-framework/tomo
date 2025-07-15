# LLM Adapters

Tomo provides adapters for popular LLM providers to seamlessly integrate your tools with different AI models. Each adapter converts Tomo tools to the specific format required by the LLM provider.

## Supported Providers

- **OpenAI** - GPT-4, GPT-3.5-turbo with function calling
- **Anthropic** - Claude models with tool use
- **Google Gemini** - Gemini models with function calling
- **Azure OpenAI** - Azure-hosted OpenAI models
- **Cohere** - Command R+ models with tool use
- **Mistral AI** - Mistral models with function calling

## Usage

### Basic Usage

```python
from tomo.core.registry import ToolRegistry
from tomo.adapters import OpenAIAdapter, AnthropicAdapter

# Create a registry and register tools
registry = ToolRegistry()
# ... register your tools ...

# Export tools for different providers
openai_adapter = OpenAIAdapter()
anthropic_adapter = AnthropicAdapter()

# Export all tools
openai_schemas = openai_adapter.export_tools(registry)
anthropic_schemas = anthropic_adapter.export_tools(registry)

# Export a single tool
tool_schema = openai_adapter.export_tool(MyTool)
```

### Converting Tool Calls

```python
# OpenAI tool call format
openai_tool_call = {
    "function": {
        "name": "calculator",
        "arguments": '{"operation": "add", "a": 5, "b": 3}'
    }
}

# Convert to Tomo format
converted = openai_adapter.convert_tool_call(openai_tool_call)
# Result: {"tool_name": "calculator", "inputs": {"operation": "add", "a": 5, "b": 3}}
```

### Formatting Tool Results

```python
# Execute your tool
result = my_tool.execute(operation="add", a=5, b=3)

# Format for LLM response
formatted = openai_adapter.format_tool_result(result, tool_call_id="call_123")
```

### Creating System Prompts

```python
system_prompt = openai_adapter.create_system_prompt(
    registry,
    custom_instructions="You are a helpful assistant with access to tools."
)
```

## CLI Usage

Export tool schemas for different providers:

```bash
# Export for OpenAI
tomo schema --format openai --module my_tools.py

# Export for Anthropic Claude
tomo schema --format anthropic --module my_tools.py

# Export for Google Gemini
tomo schema --format gemini --module my_tools.py

# Export for Azure OpenAI
tomo schema --format azure --module my_tools.py

# Export for Cohere
tomo schema --format cohere --module my_tools.py

# Export for Mistral
tomo schema --format mistral --module my_tools.py
```

## Provider-Specific Details

### OpenAI
- Uses OpenAI function calling format
- Compatible with GPT-4 and GPT-3.5-turbo
- Standard JSON schema format

### Anthropic
- Uses Claude tool use format
- Compatible with Claude 3 models
- Simplified schema structure

### Google Gemini
- Uses Gemini function calling format
- Compatible with Gemini Pro and Gemini Flash
- Similar to OpenAI format with minor differences

### Azure OpenAI
- Extends OpenAI adapter
- Supports Azure deployment names
- Same format as OpenAI

### Cohere
- Uses Command R+ tool format
- Compatible with Command R+ models
- Parameter definitions format

### Mistral
- Uses Mistral function calling format
- Compatible with Mistral 7B and larger models
- Wrapped function format

## Creating Custom Adapters

You can create custom adapters by inheriting from `BaseAdapter`:

```python
from tomo.adapters.base import BaseAdapter

class CustomAdapter(BaseAdapter):
    def export_tools(self, registry):
        # Convert tools to your format
        pass
    
    def export_tool(self, tool_class):
        # Convert single tool to your format
        pass
    
    def convert_tool_call(self, tool_call):
        # Convert tool call to Tomo format
        pass
    
    def format_tool_result(self, result, tool_call_id=None):
        # Format result for your LLM
        pass
```

## Example Integration

See `examples/llm_adapters.py` for a complete demonstration of using all adapters with a sample calculator tool. 