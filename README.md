# 🧠 Tomo – Tool-Oriented Micro Orchestrator

## Overview

**Tomo** is a lightweight, language-model-agnostic framework that allows developers to define, register, and execute **typed tools**. These tools can be invoked programmatically, by an LLM through function calling, or through intelligent orchestration. Tomo is built for speed, simplicity, and developer ergonomics — not complexity.

---

## ✨ Core Value Proposition

> **Define once, use anywhere.**  
> Tomo empowers developers to define structured tools (functions, APIs, actions) that can be executed by any LLM or used directly in Python. It offers composability without lock-in, and intelligent orchestration without bloated chains or graphs.

---

## 🎯 Goals

- ✅ Provide a minimal API for defining and registering tools
- ✅ Support **LLM-agnostic** tool invocation (OpenAI, Claude, Gemini, Cohere, Mistral, etc.)
- ✅ Allow tools to be called programmatically (Python) or by agents
- ✅ Enable introspection and metadata export for all major LLM providers
- ✅ Intelligent orchestration via LLM-based decision making
- ✅ Multi-step workflow support with conversation memory

---

## 🧱 Core Concepts

### 🔧 Tool

A reusable unit of logic with typed input and output (e.g., function, class). Can be called by LLMs or directly.

```python
@tool
class Translate(BaseTool):
    text: str
    to_lang: str

    def run(self):
        return f"Translated to {self.to_lang}: {self.text}"
```

### 🧭 Registry

A container to register, discover, and retrieve tools.

```python
registry = ToolRegistry()
registry.register(Translate)
```

### 🚀 Runner

Executes tools from:
- Direct Python calls
- LLM tool-calling schema
- External sources (e.g., API, MCP)

```python
runner.run_tool("Translate", {"text": "Hello", "to_lang": "es"})
```

### 🧩 Adapters

Convert tools to match different LLM provider schemas:

```python
OpenAIAdapter().export_tools(registry)
AnthropicAdapter().export_tools(registry)
GeminiAdapter().export_tools(registry)
```

### 🤖 Orchestrator

An intelligent LLM-based control loop that:
- Analyzes user intent using LLM
- Selects appropriate tools automatically
- Executes tools with proper parameters
- Handles multi-step workflows
- Maintains conversation context

```python
orchestrator = LLMOrchestrator(
    llm_client=openai_client,
    registry=registry,
    adapter=OpenAIAdapter(),
    config=OrchestrationConfig(max_iterations=5)
)
response = await orchestrator.run("Calculate the weather in Tokyo and convert to Fahrenheit")
```

---

## 📦 Project Scope

### ✅ Completed Features

**Core System:**
- Tool decorator and schema (based on Pydantic)
- ToolRegistry for discovery and management
- ToolRunner for local execution with validation
- Comprehensive test suite and documentation

**LLM Adapters:**
- **OpenAI** - GPT-4, GPT-3.5-turbo function calling
- **Anthropic** - Claude models with tool use
- **Google Gemini** - Gemini Pro and Advanced tool calling
- **Azure OpenAI** - Azure-hosted OpenAI models
- **Cohere** - Command R+ tool integration
- **Mistral AI** - Mistral models with function calling

**Orchestration:**
- LLM-based intelligent tool selection
- Multi-step workflow support
- Conversation memory and context management
- Configurable execution parameters
- Error handling and retry logic

**CLI Interface:**
- `tomo list` - List available tools
- `tomo run` - Execute tools directly
- `tomo schema` - Export schemas for LLM providers
- `tomo orchestrate` - Run LLM-based orchestration

### 🔄 In Development

- **Workflow Engine** - Complex multi-step process orchestration
- **API Server** - RESTful interface for external integrations
- **Plugin System** - Extensible architecture for custom extensions
- **Web Dashboard** - Visual tool inspection and monitoring interface

### 📋 Planned Features

- **Security Layer** - Access control and authentication
- **Monitoring & Analytics** - Execution metrics and performance tracking
- **Persistent Storage** - State management and workflow persistence
- **Advanced Patterns** - Conditional workflows and error recovery

---

## 🧪 Example Use Cases

### Basic Tool Usage

```python
@tool
class Weather(BaseTool):
    city: str

    def run(self):
        return f"Weather in {self.city}: Sunny"

registry = ToolRegistry()
registry.register(Weather)

# Direct execution
runner = ToolRunner(registry)
result = runner.run_tool("Weather", {"city": "Tokyo"})
```

### LLM Orchestration

```python
from tomo import LLMOrchestrator, OrchestrationConfig
from tomo.adapters import OpenAIAdapter

# Set up orchestrator
orchestrator = LLMOrchestrator(
    llm_client=openai_client,
    registry=registry,
    adapter=OpenAIAdapter(),
    config=OrchestrationConfig(max_iterations=5)
)

# Run intelligent orchestration
response = await orchestrator.run("What's the weather in Tokyo and convert the temperature to Fahrenheit?")
```

### Multi-Provider Support

```python
# Export for different LLM providers
openai_schemas = OpenAIAdapter().export_tools(registry)
anthropic_schemas = AnthropicAdapter().export_tools(registry)
gemini_schemas = GeminiAdapter().export_tools(registry)
```

---

## 🧰 Tech Stack

- **Python 3.10+**
- **Pydantic** – for schema validation and type safety
- **Typer** – for CLI interface
- **Rich** – for beautiful terminal output
- **OpenAI SDK** – for OpenAI integration
- **Anthropic SDK** – for Claude integration
- **AsyncIO** – for concurrent tool execution

---

## 🔮 Roadmap

### Phase 2: Advanced Features
- 🧠 Workflow engine for complex multi-step processes
- 🌐 API server for external integrations
- 🔌 Plugin system for custom extensions
- 📊 Web dashboard for tool inspection and monitoring

### Phase 3: Enterprise Features
- 🔐 Security and access control
- 📈 Monitoring and analytics
- 🗄️ Persistent storage and state management
- 🔄 Advanced workflow patterns

---

## 👤 Target Audience

- Developers building LLM apps with custom tools
- Engineers who want clean, composable primitives
- AI teams avoiding LangChain bloat but want structured execution
- Infra hackers building custom agents or copilots

---

## 🗣 Why "Tomo"?

"Tomo" means "friend" in Japanese, and "I take" in Spanish.
It's short, friendly, and reflects what the framework does: help LLMs and devs "take" and use tools easily.

---

## 📍 Repository Structure

```
tomo/
├── tomo/
│   ├── core/           # tool, registry, runner
│   ├── adapters/       # LLM provider adapters
│   ├── orchestrators/  # LLM orchestrator components
│   └── cli/            # Command-line interface
├── examples/           # Example tools and usage
├── tests/              # Test suite
├── docs/               # Documentation
└── ADAPTERS.md         # Adapter documentation
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.10 or higher
- For LLM orchestration: API keys for your chosen LLM provider(s)

### Quick Install

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/tomo-framework/tomo.git
cd tomo

# Install with uv
uv sync

# Install with optional dependencies
uv sync --extra cli --extra openai --extra anthropic --extra orchestrator

# Or install everything
uv sync --extra all

# Activate the environment
uv shell
```

### Using pip

```bash
pip install -e .

# With optional dependencies
pip install -e .[cli,openai,anthropic,orchestrator]
```

### Environment Setup

For LLM orchestration, set your API keys:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google Gemini
export GOOGLE_API_KEY="your-google-api-key"
```

## 🎯 Quick Start

### 1. Define Tools

```python
from tomo import BaseTool, tool

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
        # ... more operations
```

### 2. Register and Run Tools

```python
from tomo import ToolRegistry, ToolRunner

# Create registry and register tools
registry = ToolRegistry()
registry.register(Calculator)

# Create runner and execute tools
runner = ToolRunner(registry)
result = runner.run_tool("Calculator", {
    "operation": "add",
    "a": 5,
    "b": 3
})
print(result)  # 8
```

### 3. Use the CLI

```bash
# List available tools
tomo list --module examples.basic_tools

# Run a tool
tomo run Calculator --module examples.basic_tools --inputs '{"operation": "add", "a": 5, "b": 3}'

# Export tool schemas for LLM use
tomo schema --module examples.basic_tools --format openai --output tools.json

# Run LLM orchestration
tomo orchestrate "Calculate 15 + 25" --module examples.basic_tools --provider openai
```

### 4. LLM Integration

```python
from tomo.adapters import OpenAIAdapter

adapter = OpenAIAdapter()
schemas = adapter.export_tools(registry)

# Use with OpenAI client
import openai
client = openai.OpenAI()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Calculate 15 + 25"}],
    tools=schemas
)
```

### 5. Advanced Orchestration

```python
from tomo import LLMOrchestrator, OrchestrationConfig

# Configure orchestrator
config = OrchestrationConfig(
    max_iterations=5,
    temperature=0.1,
    enable_memory=True
)

orchestrator = LLMOrchestrator(
    llm_client=openai_client,
    registry=registry,
    adapter=OpenAIAdapter(),
    config=config
)

# Run complex workflows
response = await orchestrator.run(
    "Get the weather in Tokyo, convert the temperature to Fahrenheit, "
    "and calculate how many degrees warmer it is than 20°F"
)
```

## 🧪 Development

### Running the Orchestrator Demo

```bash
# Run the orchestrator component demo (works without LLM)
python examples/orchestrator_demo.py

# Run the full orchestrator demo (requires LLM client setup)
# python examples/orchestrator_demo.py --full
```

### Running Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=tomo
```

### Code Formatting

```bash
# Format code
uv run black .
uv run ruff check . --fix

# Type checking
uv run mypy tomo/
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository** and clone it locally
2. **Set up the development environment**:
   ```bash
   git clone https://github.com/your-username/tomo.git
   cd tomo
   uv sync --extra dev
   uv shell
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Guidelines

- **Code Style**: Follow PEP 8 and use Black for formatting
- **Type Hints**: Include type annotations for all functions and methods
- **Tests**: Add tests for new features and ensure all tests pass
- **Documentation**: Update docstrings and README as needed
- **Commits**: Use conventional commit messages

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=tomo --cov-report=html

# Run specific test file
uv run pytest tests/test_core.py
```

### Submitting Changes

1. **Test your changes** thoroughly
2. **Update documentation** if needed
3. **Create a pull request** with a clear description
4. **Link any related issues** in the PR description

### Areas for Contribution

- **New LLM Adapters**: Support for additional LLM providers
- **Tool Examples**: More example tools and use cases
- **Documentation**: Improvements to docs and tutorials
- **Performance**: Optimizations and performance improvements
- **Testing**: Additional test coverage and edge cases

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that allows you to:
- Use the software for any purpose
- Modify the software
- Distribute the software
- Distribute modified versions
- Use it commercially

The only requirement is that the original license and copyright notice be included in any substantial portions of the software.

---

## 📦 Project Status

✅ **Phase 1: Core Orchestration (Complete)**
- ✅ Core tool system with `@tool` decorator and Pydantic validation
- ✅ `ToolRegistry` for tool discovery and management
- ✅ `ToolRunner` for execution with error handling
- ✅ **6 LLM Adapters**: OpenAI, Anthropic, Gemini, Azure OpenAI, Cohere, Mistral
- ✅ **LLM Orchestrator** with intelligent tool selection and multi-step workflows
- ✅ **Conversation Manager** with memory and context management
- ✅ **Execution Engine** with retry logic and parallel execution
- ✅ **CLI Interface** with `tomo list`, `tomo run`, `tomo schema`, `tomo orchestrate`
- ✅ Comprehensive test suite and documentation
- ✅ Example tools and orchestrator demos

🔄 **Phase 2: Advanced Features (In Development)**
- 🔄 Workflow engine for complex multi-step processes
- 🔄 API server for external integrations
- 🔄 Plugin system for custom extensions
- 🔄 Web dashboard for tool inspection and monitoring

📋 **Phase 3: Enterprise Features (Planned)**
- 📋 Security and access control
- 📋 Monitoring and analytics
- 📋 Persistent storage and state management
- 📋 Advanced workflow patterns