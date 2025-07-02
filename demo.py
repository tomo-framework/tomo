#!/usr/bin/env python3
"""Demo script showcasing Tomo framework capabilities."""

import json
from tomo import BaseTool, tool, ToolRegistry, ToolRunner
from tomo.adapters.openai import OpenAIAdapter


# Define some example tools
@tool
class Calculator(BaseTool):
    """Perform basic mathematical calculations."""
    
    operation: str  # add, subtract, multiply, divide
    a: float
    b: float
    
    def run(self) -> float:
        """Execute the calculation."""
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


@tool
class TextProcessor(BaseTool):
    """Process text with various operations."""
    
    text: str
    operation: str  # uppercase, lowercase, reverse, word_count
    
    def run(self) -> str:
        """Process the text."""
        if self.operation == "uppercase":
            return self.text.upper()
        elif self.operation == "lowercase":
            return self.text.lower()
        elif self.operation == "reverse":
            return self.text[::-1]
        elif self.operation == "word_count":
            word_count = len(self.text.split())
            return f"Word count: {word_count}"
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


def main():
    """Run the demo."""
    print("🧠 Tomo Framework Demo")
    print("=" * 40)
    
    # 1. Create registry and register tools
    print("\n1. Creating registry and registering tools...")
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(TextProcessor)
    
    print(f"   Registered tools: {registry.list()}")
    
    # 2. Create runner and execute tools
    print("\n2. Executing tools...")
    runner = ToolRunner(registry)
    
    # Execute calculator
    calc_result = runner.run_tool("Calculator", {
        "operation": "add",
        "a": 15,
        "b": 25
    })
    print(f"   Calculator (15 + 25): {calc_result}")
    
    # Execute text processor
    text_result = runner.run_tool("TextProcessor", {
        "text": "Hello Tomo Framework!",
        "operation": "uppercase"
    })
    print(f"   Text Processor (uppercase): {text_result}")
    
    # 3. Test error handling with safe execution
    print("\n3. Testing error handling...")
    safe_result = runner.run_tool_safe("Calculator", {
        "operation": "divide",
        "a": 10,
        "b": 0
    })
    print(f"   Safe execution result: {safe_result}")
    
    # 4. Export schemas for LLM use
    print("\n4. Exporting schemas for LLM use...")
    adapter = OpenAIAdapter()
    schemas = adapter.export_tools(registry)
    
    print("   OpenAI Function Schemas:")
    for schema in schemas:
        tool_info = schema["function"]
        print(f"   - {tool_info['name']}: {tool_info['description']}")
    
    # 5. Show full schema for one tool
    print("\n5. Full schema example (Calculator):")
    calc_schema = registry.get_schema("Calculator")
    print(json.dumps(calc_schema, indent=2))
    
    # 6. Demonstrate validation
    print("\n6. Input validation...")
    
    # Valid inputs
    is_valid = runner.validate_tool_inputs("Calculator", {
        "operation": "multiply",
        "a": 5,
        "b": 4
    })
    print(f"   Valid inputs: {is_valid}")
    
    # Invalid inputs
    is_valid = runner.validate_tool_inputs("Calculator", {
        "operation": "invalid_op",
        "a": "not_a_number",
        "b": 4
    })
    print(f"   Invalid inputs: {is_valid}")
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("- Try the CLI: `tomo list --module examples.basic_tools`")
    print("- Run tools: `tomo run Calculator --inputs '{\"operation\": \"add\", \"a\": 5, \"b\": 3}'`")
    print("- Export schemas: `tomo schema --output tools.json`")


if __name__ == "__main__":
    main() 