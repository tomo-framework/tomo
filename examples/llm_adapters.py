"""Example demonstrating LLM adapters for different providers."""

import json
from tomo.core.registry import ToolRegistry
from tomo.core.runner import ToolRunner
from tomo.core.tool import BaseTool
from tomo.adapters import (
    OpenAIAdapter,
    AnthropicAdapter,
    GeminiAdapter,
    AzureOpenAIAdapter,
    CohereAdapter,
    MistralAdapter,
)


# Example tool class for demonstration
class CalculatorTool(BaseTool):
    """A simple calculator tool for demonstration."""

    operation: str
    a: float
    b: float

    def run(self) -> float:
        """Execute the calculator operation."""
        if self.operation == "add":
            return self.a + self.b
        elif self.operation == "subtract":
            return self.a - self.b
        elif self.operation == "multiply":
            return self.a * self.b
        elif self.operation == "divide":
            if self.b == 0:
                raise ValueError("Cannot divide by zero")
            return self.a / self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")

    @classmethod
    def get_name(cls) -> str:
        return "calculator"

    @classmethod
    def get_description(cls) -> str:
        return "Perform basic mathematical operations"

    @classmethod
    def get_schema(cls) -> dict:
        return {
            "name": "calculator",
            "description": "Perform basic mathematical operations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The mathematical operation to perform",
                    },
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["operation", "a", "b"],
            },
        }


def demonstrate_adapters():
    """Demonstrate how to use different LLM adapters."""

    # Create a registry and register our tool
    registry = ToolRegistry()
    registry.register(CalculatorTool)

    # Create adapters for different LLM providers
    adapters = {
        "OpenAI": OpenAIAdapter(),
        "Anthropic": AnthropicAdapter(),
        "Gemini": GeminiAdapter(),
        "Azure OpenAI": AzureOpenAIAdapter(deployment_name="gpt-4"),
        "Cohere": CohereAdapter(),
        "Mistral": MistralAdapter(),
    }

    # Example tool call (simulating what an LLM would send)
    example_tool_call = {
        "function": {
            "name": "calculator",
            "arguments": '{"operation": "add", "a": 5, "b": 3}',
        }
    }

    print("=== LLM Adapter Demonstration ===\n")

    # Demonstrate each adapter
    for provider_name, adapter in adapters.items():
        print(f"--- {provider_name} Adapter ---")

        # Export tools
        tools = adapter.export_tools(registry)
        print(f"Exported {len(tools)} tools")

        # Export single tool
        tool_schema = adapter.export_tool(CalculatorTool)
        print(f"Tool schema keys: {list(tool_schema.keys())}")

        # Convert tool call
        converted = adapter.convert_tool_call(example_tool_call)
        print(f"Converted tool call: {converted}")

        # Validate tool call
        is_valid = adapter.validate_tool_call(example_tool_call, registry)
        print(f"Tool call valid: {is_valid}")

        # Format tool result
        result = 8.0  # 5 + 3
        formatted_result = adapter.format_tool_result(result, "call_123")
        print(f"Formatted result keys: {list(formatted_result.keys())}")

        # Create system prompt
        system_prompt = adapter.create_system_prompt(
            registry,
            custom_instructions="You are a helpful assistant with access to tools.",
        )
        print(f"System prompt length: {len(system_prompt)} characters")
        print()


def demonstrate_provider_specific_formats():
    """Show the different schema formats for each provider."""

    registry = ToolRegistry()
    registry.register(CalculatorTool)

    adapters = {
        "OpenAI": OpenAIAdapter(),
        "Anthropic": AnthropicAdapter(),
        "Gemini": GeminiAdapter(),
        "Cohere": CohereAdapter(),
        "Mistral": MistralAdapter(),
    }

    print("=== Provider-Specific Schema Formats ===\n")

    for provider_name, adapter in adapters.items():
        print(f"--- {provider_name} Schema Format ---")
        schema = adapter.export_tool(CalculatorTool)
        print(json.dumps(schema, indent=2))
        print()


if __name__ == "__main__":
    demonstrate_adapters()
    demonstrate_provider_specific_formats()
