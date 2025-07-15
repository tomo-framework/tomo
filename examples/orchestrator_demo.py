"""Demo of the LLM orchestrator functionality."""

import asyncio
from tomo import BaseTool, tool, ToolRegistry
from tomo.core.runner import ToolRunner
from tomo.orchestrators import LLMOrchestrator, OrchestrationConfig
from tomo.adapters import OpenAIAdapter


# Example tools for the orchestrator
@tool
class Calculator(BaseTool):
    """Perform basic mathematical calculations."""

    operation: str  # add, subtract, multiply, divide
    a: float
    b: float

    def run(self) -> float:
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


@tool
class Weather(BaseTool):
    """Get weather information for a city (mock implementation)."""

    city: str
    units: str = "celsius"  # celsius, fahrenheit

    def run(self) -> dict:
        # Mock weather data
        temp_c = 22

        if self.units == "fahrenheit":
            temp = temp_c * 9 / 5 + 32
            unit = "°F"
        else:
            temp = temp_c
            unit = "°C"

        return {
            "city": self.city,
            "temperature": f"{temp}{unit}",
            "condition": "Sunny",
            "humidity": "65%",
            "wind": "10 km/h",
        }


async def demo_orchestrator():
    """Demonstrate the LLM orchestrator."""
    print("🧠 Tomo LLM Orchestrator Demo")
    print("=" * 50)

    # 1. Set up tools and registry
    print("\n1. Setting up tools and registry...")
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(TextProcessor)
    registry.register(Weather)

    print(f"   Registered tools: {registry.list()}")

    # 2. Set up LLM client (mock for demo)
    print("\n2. Setting up LLM client...")

    # Mock LLM client for demonstration
    class MockLLMClient:
        def __init__(self):
            self.model = "gpt-4"

        async def chat(self):
            return self

        async def completions(self):
            return self

        async def create(self, **kwargs):
            # Mock response that would use the Calculator tool
            return MockResponse()

    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice()]

    class MockChoice:
        def __init__(self):
            self.message = MockMessage()

    class MockMessage:
        def __init__(self):
            self.content = "I'll help you calculate that."
            self.tool_calls = [
                {
                    "function": {
                        "name": "Calculator",
                        "arguments": '{"operation": "add", "a": 15, "b": 25}',
                    }
                }
            ]

    llm_client = MockLLMClient()

    # 3. Set up orchestrator
    print("\n3. Setting up orchestrator...")
    adapter = OpenAIAdapter()
    config = OrchestrationConfig(max_iterations=3, temperature=0.1, enable_memory=True)

    orchestrator = LLMOrchestrator(
        llm_client=llm_client, registry=registry, adapter=adapter, config=config
    )

    print("   Orchestrator configured successfully")

    # 4. Run orchestration
    print("\n4. Running orchestration...")

    # Example user requests
    requests = [
        "Calculate 15 + 25",
        "What's the weather in Tokyo?",
        "Convert 'Hello World' to uppercase",
    ]

    for i, request in enumerate(requests, 1):
        print(f"\n   Request {i}: {request}")
        try:
            response = await orchestrator.run(request)
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")

    # 5. Show conversation history
    print("\n5. Conversation history:")
    history = orchestrator.get_conversation_history()
    for msg in history:
        print(f"   {msg['role']}: {msg['content'][:100]}...")

    print("\n✅ Orchestrator demo completed!")


def demo_without_llm():
    """Demo orchestrator components without LLM."""
    print("🧠 Tomo Orchestrator Components Demo")
    print("=" * 50)

    # Set up tools
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(TextProcessor)

    # Test execution engine
    from tomo.orchestrators.execution import ExecutionEngine
    from tomo.adapters import OpenAIAdapter

    runner = ToolRunner(registry)
    adapter = OpenAIAdapter()
    engine = ExecutionEngine(runner, adapter)

    # Test tool execution
    tool_call = {
        "function": {
            "name": "Calculator",
            "arguments": '{"operation": "add", "a": 10, "b": 20}',
        }
    }

    print("\nTesting execution engine...")
    try:
        result = asyncio.run(engine.execute_tool(tool_call))
        print(f"Tool execution result: {result}")
    except Exception as e:
        print(f"Execution error: {e}")

    # Test conversation manager
    from tomo.orchestrators.conversation import ConversationManager

    print("\nTesting conversation manager...")
    conversation = ConversationManager()
    conversation.add_message("user", "Calculate 5 + 3")
    conversation.add_message("assistant", "I'll use the calculator tool for you.")
    conversation.add_tool_result("Calculator", 8, success=True)

    messages = conversation.get_messages()
    print(f"Conversation has {len(messages)} messages")

    summary = conversation.get_summary()
    print(f"Conversation summary: {summary}")


if __name__ == "__main__":
    # Run component demo (works without LLM)
    demo_without_llm()

    # Uncomment to run full orchestrator demo (requires LLM client)
    # asyncio.run(demo_orchestrator())
