# 🧠 Tomo – Tool-Oriented Micro Orchestrator

## Overview

**Tomo** is a lightweight, language-model-agnostic framework that allows developers to define, register, and execute **typed tools**. These tools can be invoked programmatically, by an LLM through function calling, or remotely via orchestration interfaces like agents or MCPs. Tomo is built for speed, simplicity, and developer ergonomics — not complexity.

---

## ✨ Core Value Proposition

> **Define once, use anywhere.**  
> Tomo empowers developers to define structured tools (functions, APIs, actions) that can be executed by any LLM or used directly in Python. It offers composability without lock-in, and orchestration without bloated chains or graphs.

---

## 🎯 Goals

- ✅ Provide a minimal API for defining and registering tools
- ✅ Support **LLM-agnostic** tool invocation (OpenAI, Claude, Grok, local LLMs, etc.)
- ✅ Allow tools to be called programmatically (Python) or by agents (via MCP)
- ✅ Enable introspection and metadata export (e.g., OpenAI tool schema, Anthropic tool format)
- ✅ Optional orchestration via a simple LLM-based agent runner

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
ClaudeAdapter().export_tools(registry)
```

### 🤖 Orchestrator (Optional Agent Mode)

An LLM-based control loop that:
- Takes user input
- Chooses the right tool via LLM
- Executes it and returns output

```python
agent = LLMOrchestrator(llm=Claude(), tools=registry.list())
agent.run("Translate 'dog' to French")
```

---

## 📦 MVP Scope

### ✅ Features (Phase 1)

- Tool decorator and schema (based on Pydantic)
- ToolRegistry for discovery
- ToolRunner for local execution
- Adapter for OpenAI function-calling schema
- Basic orchestrator using OpenAI or Claude
- CLI with `tomo run` and `tomo list`
- Export to JSON schema for external tools

### ❌ Not in MVP

- Multi-step workflows or graph-based execution
- Web UI or dashboard
- Built-in vector search or memory
- Fine-grained auth or persistence

---

## 🧪 Example Use Case

```python
@tool
class Weather(BaseTool):
    city: str

    def run(self):
        return f"Weather in {self.city}: Sunny"

registry = ToolRegistry()
registry.register(Weather)

agent = LLMOrchestrator(llm=OpenAI(), tools=registry.list())
agent.run("What's the weather in Tokyo?")
```

---

## 🧰 Tech Stack

- **Python 3.10+**
- **Pydantic** – for schema validation
- **Typer** – for CLI (optional)
- **OpenAI SDK / Anthropic SDK** – for orchestrator
- **Optional Rust (via PyO3)** – for performance-critical tool extensions

---

## 🔮 Future Ideas

- 🧠 Fine-grained state handling (LangGraph-style)
- 🕸️ Workflow engine / tool chaining
- 🌐 Web dashboard for tool inspection
- 🐍 SDK generation from tools
- ⚙️ Plugin system for adapters
- 🧪 LLM-based tool testing suite

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

## 📍 Repo Structure (Proposal)

```
tomo/
├── core/           # tool, registry, runner
├── adapters/       # openai.py, anthropic.py, mistral.py
├── orchestrators/  # llm_runner.py
├── cli/            # tomo CLI with Typer
├── examples/       # example tools and agent usage
├── tests/
```

---

## 🚀 Installation & Setup

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/tomo-framework/tomo.git
cd tomo

# Install with uv
uv sync

# Install with optional dependencies
uv sync --extra cli --extra openai --extra anthropic

# Or install everything
uv sync --extra all

# Activate the environment
uv shell
```

### Using pip

```bash
pip install -e .

# With optional dependencies
pip install -e .[cli,openai,anthropic]
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
tomo schema --module examples.basic_tools --output tools.json
```

### 4. Export for OpenAI

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

## 🧪 Development

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

## 📦 Project Status

✅ **Completed (MVP)**
- ✅ Core tool system with `@tool` decorator
- ✅ `ToolRegistry` for tool management
- ✅ `ToolRunner` for execution
- ✅ OpenAI adapter for function calling
- ✅ CLI with `tomo list`, `tomo run`, `tomo schema`
- ✅ Comprehensive test suite
- ✅ Example tools and documentation

🔄 **In Progress**
- 🔄 Anthropic adapter
- 🔄 LLM orchestrator
- 🔄 Additional adapters (Mistral, local LLMs)

📋 **Planned**
- 📋 Plugin system
- 📋 Workflow engine
- 📋 Web dashboard
- 📋 SDK generation