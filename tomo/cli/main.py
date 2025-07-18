"""Main CLI application for Tomo."""

import json
import sys
from pathlib import Path
from typing import Optional

try:
    import typer  # type: ignore
    from rich.console import Console  # type: ignore
    from rich.table import Table  # type: ignore
    from rich.panel import Panel  # type: ignore
    from rich.json import JSON  # type: ignore
except ImportError:
    print("CLI dependencies not installed. Install with: uv add tomo[cli]")
    sys.exit(1)

from ..core.registry import ToolRegistry
from ..core.runner import (
    ToolRunner,
    ToolNotFoundError,
    ToolValidationError,
    ToolExecutionError,
)
from ..adapters import (
    OpenAIAdapter,
    AnthropicAdapter,
    GeminiAdapter,
    AzureOpenAIAdapter,
    CohereAdapter,
    MistralAdapter,
)

app = typer.Typer(
    name="tomo", help="Tomo - Tool-Oriented Micro Orchestrator", add_completion=False
)
console = Console()


def load_tools_from_module(module_path: str) -> ToolRegistry:
    """Load tools from a Python module path."""
    import importlib.util
    import sys

    registry = ToolRegistry()

    if not module_path:
        return registry

    try:
        # Handle both file paths and module names
        if module_path.endswith(".py"):
            spec = importlib.util.spec_from_file_location("tools_module", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                console.print(f"[red]Could not load module from {module_path}[/red]")
                return registry
        else:
            module = importlib.import_module(module_path)

        # Auto-discover tools in the module
        discovered = registry.auto_discover(module)
        console.print(
            f"[green]Discovered {discovered} tools from {module_path}[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error loading tools from {module_path}: {e}[/red]")

    return registry


@app.command("list")  # type: ignore
def list_tools(
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
) -> None:
    """List all available tools."""
    registry = load_tools_from_module(module) if module else ToolRegistry()

    if not registry.list():
        console.print("[yellow]No tools found[/yellow]")
        return

    if format == "json":
        tools_data = {}
        for tool_name in registry.list():
            schema = registry.get_schema(tool_name)
            tools_data[tool_name] = schema
        console.print(JSON.from_data(tools_data))
        return

    # Table format
    table = Table(title="Available Tools")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    if verbose:
        table.add_column("Schema", style="dim")

    for tool_name in registry.list():
        tool_class = registry.get(tool_name)
        if tool_class:
            description = tool_class.get_description()
            row = [tool_name, description]

            if verbose:
                schema = registry.get_schema(tool_name)
                schema_str = json.dumps(schema, indent=2) if schema else "N/A"
                row.append(schema_str)

            table.add_row(*row)

    console.print(table)


@app.command("run")  # type: ignore
def run_tool(
    tool_name: str = typer.Argument(..., help="Name of the tool to run"),
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    inputs: Optional[str] = typer.Option(
        None, "--inputs", "-i", help="JSON string of tool inputs"
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="JSON file containing tool inputs"
    ),
    safe: bool = typer.Option(
        False, "--safe", help="Use safe execution (structured error handling)"
    ),
) -> None:
    """Run a specific tool with given inputs."""
    registry = load_tools_from_module(module) if module else ToolRegistry()
    runner = ToolRunner(registry)

    # Parse inputs
    tool_inputs = {}

    if file:
        try:
            with open(file) as f:
                tool_inputs = json.load(f)
        except Exception as e:
            console.print(f"[red]Error reading input file: {e}[/red]")
            raise typer.Exit(1)
    elif inputs:
        try:
            tool_inputs = json.loads(inputs)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON inputs: {e}[/red]")
            raise typer.Exit(1)

    # Run the tool
    try:
        if safe:
            result = runner.run_tool_safe(tool_name, tool_inputs)
            console.print(JSON.from_data(result))
        else:
            result = runner.run_tool(tool_name, tool_inputs)

            # Format output nicely
            if isinstance(result, (dict, list)):
                console.print(JSON.from_data(result))
            else:
                console.print(f"[green]Result:[/green] {result}")

    except ToolNotFoundError as e:
        console.print(f"[red]Tool not found: {e}[/red]")
        raise typer.Exit(1)
    except (ToolValidationError, ToolExecutionError) as e:
        console.print(f"[red]Tool execution failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("schema")  # type: ignore
def export_schema(
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    tool: Optional[str] = typer.Option(
        None, "--tool", "-t", help="Specific tool to export schema for"
    ),
    format: str = typer.Option(
        "openai",
        "--format",
        "-f",
        help="Schema format: openai, anthropic, gemini, azure, cohere, mistral",
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path"
    ),
) -> None:
    """Export tool schemas for LLM consumption."""
    registry = load_tools_from_module(module) if module else ToolRegistry()

    if not registry.list():
        console.print("[yellow]No tools found[/yellow]")
        return

    # Select adapter based on format
    adapters = {
        "openai": OpenAIAdapter(),
        "anthropic": AnthropicAdapter(),
        "gemini": GeminiAdapter(),
        "azure": AzureOpenAIAdapter(),
        "cohere": CohereAdapter(),
        "mistral": MistralAdapter(),
    }

    if format not in adapters:
        console.print(f"[red]Unsupported format: {format}[/red]")
        console.print(f"Supported formats: {', '.join(adapters.keys())}")
        raise typer.Exit(1)

    adapter = adapters[format]

    if tool:
        # Export single tool schema
        if tool not in registry:
            console.print(f"[red]Tool '{tool}' not found[/red]")
            raise typer.Exit(1)

        tool_class = registry.get(tool)
        schema_data = [adapter.export_tool(tool_class)] if tool_class else []
    else:
        # Export all tools
        schema_data = adapter.export_tools(registry)

    if output:
        with open(output, "w") as f:
            json.dump(schema_data, f, indent=2)
        console.print(f"[green]Schema exported to {output}[/green]")
    else:
        console.print(JSON.from_data(schema_data))


@app.command("validate")  # type: ignore
def validate_tool(
    tool_name: str = typer.Argument(..., help="Name of the tool to validate"),
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    inputs: Optional[str] = typer.Option(
        None, "--inputs", "-i", help="JSON string of tool inputs to validate"
    ),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="JSON file containing tool inputs to validate"
    ),
) -> None:
    """Validate tool inputs without running the tool."""
    registry = load_tools_from_module(module) if module else ToolRegistry()
    runner = ToolRunner(registry)

    if tool_name not in registry:
        console.print(f"[red]Tool '{tool_name}' not found[/red]")
        raise typer.Exit(1)

    # Parse inputs if provided
    tool_inputs = {}

    if file:
        try:
            with open(file) as f:
                tool_inputs = json.load(f)
        except Exception as e:
            console.print(f"[red]Error reading input file: {e}[/red]")
            raise typer.Exit(1)
    elif inputs:
        try:
            tool_inputs = json.loads(inputs)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON inputs: {e}[/red]")
            raise typer.Exit(1)

    # Validate inputs
    try:
        is_valid = runner.validate_tool_inputs(tool_name, tool_inputs)
        if is_valid:
            console.print(f"[green]✓ Inputs are valid for tool '{tool_name}'[/green]")
        else:
            console.print(f"[red]✗ Inputs are invalid for tool '{tool_name}'[/red]")
            raise typer.Exit(1)
    except ToolNotFoundError as e:
        console.print(f"[red]Tool not found: {e}[/red]")
        raise typer.Exit(1)


@app.command("orchestrate")  # type: ignore
def orchestrate(
    input_text: str = typer.Argument(..., help="User input to orchestrate"),
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    provider: str = typer.Option(
        "openai", "--provider", "-p", help="LLM provider: openai, anthropic, gemini"
    ),
    model: Optional[str] = typer.Option(None, "--model", help="LLM model name"),
    max_iterations: int = typer.Option(
        5, "--max-iterations", help="Maximum orchestration iterations"
    ),
    temperature: float = typer.Option(0.1, "--temperature", help="LLM temperature"),
    memory: bool = typer.Option(
        True, "--memory/--no-memory", help="Enable conversation memory"
    ),
) -> None:
    """Orchestrate tools using LLM-based decision making."""
    try:
        from ..orchestrators import LLMOrchestrator, OrchestrationConfig
    except ImportError:
        console.print(
            "[red]Orchestrator not available. Install with: uv add tomo[orchestrator][/red]"
        )
        raise typer.Exit(1)

    # Load tools
    registry = load_tools_from_module(module) if module else ToolRegistry()

    if not registry.list():
        console.print("[yellow]No tools found[/yellow]")
        return

    # Select adapter
    adapters = {
        "openai": OpenAIAdapter(),
        "anthropic": AnthropicAdapter(),
        "gemini": GeminiAdapter(),
        "azure": AzureOpenAIAdapter(),
        "cohere": CohereAdapter(),
        "mistral": MistralAdapter(),
    }

    if provider not in adapters:
        console.print(f"[red]Unsupported provider: {provider}[/red]")
        console.print(f"Supported providers: {', '.join(adapters.keys())}")
        raise typer.Exit(1)

    adapter = adapters[provider]

    # Create LLM client (this would need to be implemented based on the provider)
    console.print(f"[yellow]Note: LLM client setup not implemented in CLI yet[/yellow]")
    console.print(
        f"[yellow]Use the Python API for full orchestrator functionality[/yellow]"
    )

    # Show what would happen
    console.print(f"\n[green]Orchestration Plan:[/green]")
    console.print(f"Input: {input_text}")
    console.print(f"Provider: {provider}")
    console.print(f"Available tools: {registry.list()}")
    console.print(f"Max iterations: {max_iterations}")
    console.print(f"Temperature: {temperature}")
    console.print(f"Memory enabled: {memory}")

    # Show tool schemas
    console.print(f"\n[green]Available Tool Schemas:[/green]")
    schemas = adapter.export_tools(registry)
    for schema in schemas:
        if "function" in schema:
            func = schema["function"]
            console.print(f"- {func['name']}: {func['description']}")


@app.command("workflow")  # type: ignore
def workflow_command(
    workflow_file: str = typer.Argument(..., help="Path to workflow definition file"),
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    context_file: Optional[str] = typer.Option(
        None, "--context", "-c", help="JSON file with initial context data"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="File to write workflow results"
    ),
    max_parallel: int = typer.Option(5, "--max-parallel", help="Maximum parallel steps"),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Step timeout in seconds"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Execute a declarative workflow from a file."""
    try:
        from ..orchestrators import WorkflowEngine
    except ImportError:
        console.print(
            "[red]Workflow engine not available. Install with: uv sync --extra orchestrator[/red]"
        )
        raise typer.Exit(1)

    import asyncio
    from pathlib import Path

    # Load tools
    registry = load_tools_from_module(module) if module else ToolRegistry()
    
    if not registry.list() and module:
        console.print("[yellow]Warning: No tools found in module[/yellow]")

    # Load workflow definition
    workflow_path = Path(workflow_file)
    if not workflow_path.exists():
        console.print(f"[red]Workflow file not found: {workflow_file}[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]Note: Workflow file loading from Python modules not yet implemented[/yellow]")
    console.print(f"[yellow]Use the Python API with examples/workflow_demo.py for now[/yellow]")
    console.print(f"[green]Workflow engine is available and ready![/green]")


@app.command("workflow-demo")  # type: ignore
def workflow_demo(
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    pattern: Optional[str] = typer.Option(
        None, "--pattern", "-p", help="Workflow pattern to run: simple, conditional, parallel, loop, complex"
    ),
) -> None:
    """Run workflow engine demonstrations."""
    try:
        from ..orchestrators import WorkflowEngine, Workflow
    except ImportError:
        console.print(
            "[red]Workflow engine not available. Install with: uv sync --extra orchestrator[/red]"
        )
        raise typer.Exit(1)

    import asyncio

    # Load tools
    registry = load_tools_from_module(module) if module else ToolRegistry()

    console.print(f"[green]🧠 Tomo Workflow Engine Demo[/green]")
    console.print(f"Available tools: {registry.list()}")

    if pattern:
        console.print(f"[yellow]Running {pattern} workflow pattern...[/yellow]")
        console.print(f"[yellow]Use examples/workflow_demo.py for full demonstrations[/yellow]")
    else:
        console.print(f"[yellow]Use examples/workflow_demo.py for full demonstrations[/yellow]")

    # Create workflow engine
    from ..adapters import OpenAIAdapter
    engine = WorkflowEngine(
        registry=registry,
        adapter=OpenAIAdapter(),
        max_parallel_steps=3,
    )

    console.print(f"[green]✅ Workflow engine created successfully![/green]")
    console.print(f"[cyan]Example usage:[/cyan]")
    console.print(f"  python examples/workflow_demo.py")


@app.command("serve-api")  # type: ignore
def serve_api(
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(
        False, "--reload", help="Enable auto-reload for development"
    ),
    cors: bool = typer.Option(True, "--cors/--no-cors", help="Enable CORS"),
) -> None:
    """Start the RESTful API server for tool execution."""
    try:
        from ..servers import APIServer
    except ImportError:
        console.print(
            "[red]Server dependencies not available. Install with: uv sync --extra server[/red]"
        )
        raise typer.Exit(1)

    # Load tools
    registry = load_tools_from_module(module) if module else ToolRegistry()

    if not registry.list():
        console.print("[yellow]No tools found[/yellow]")
        return

    # Create and start API server
    console.print(f"[green]Starting API server on {host}:{port}[/green]")
    console.print(f"Available tools: {registry.list()}")
    console.print(f"API documentation: http://{host}:{port}/docs")

    server = APIServer(
        registry=registry,
        title="Tomo API Server",
        description="RESTful API for Tomo tool execution",
        enable_cors=cors,
    )

    server.run(host=host, port=port, reload=reload)


@app.command("serve-mcp")  # type: ignore
def serve_mcp(
    module: Optional[str] = typer.Option(
        None, "--module", "-m", help="Python module to load tools from"
    ),
    host: str = typer.Option("localhost", "--host", help="Host to bind to"),
    port: int = typer.Option(8001, "--port", help="Port to bind to"),
    name: str = typer.Option("tomo-mcp-server", "--name", help="Server name"),
    log_level: str = typer.Option("info", "--log-level", help="Logging level"),
) -> None:
    """Start the MCP server for AI agent tool execution."""
    try:
        from ..servers import MCPServer
    except ImportError:
        console.print(
            "[red]Server dependencies not available. Install with: uv sync --extra mcp[/red]"
        )
        raise typer.Exit(1)

    # Load tools
    registry = load_tools_from_module(module) if module else ToolRegistry()

    if not registry.list():
        console.print("[yellow]No tools found[/yellow]")
        return

    # Create and start MCP server
    console.print(f"[green]Starting MCP server on {host}:{port}[/green]")
    console.print(f"Available tools: {registry.list()}")
    console.print(f"WebSocket endpoint: ws://{host}:{port}")

    server = MCPServer(
        registry=registry,
        server_name=name,
        server_version="0.1.0",
    )

    server.run(host=host, port=port, log_level=log_level)


@app.command("plugin")  # type: ignore
def plugin_command(
    action: str = typer.Argument(
        ..., 
        help="Action: list, info, load-package, load-directory, load-config, validate-config, create-sample-config"
    ),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Plugin name (for info action)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Package name or directory path"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Plugin config file path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Manage Tomo plugins."""
    try:
        from ..plugins import PluginLoader, PluginLoaderError
    except ImportError:
        console.print("[red]Plugin system not available[/red]")
        raise typer.Exit(1)
    
    loader = PluginLoader()
    
    try:
        if action == "list":
            # List all registered plugins
            plugins = loader.registry.list_plugins()
            
            if not plugins:
                console.print("[yellow]No plugins registered[/yellow]")
                return
            
            table = Table(title="Registered Plugins")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="magenta")
            table.add_column("Type", style="green")
            table.add_column("Enabled", style="yellow")
            table.add_column("Description", style="white")
            
            for plugin_name in plugins:
                info = loader.registry.get_plugin_info(plugin_name)
                if info:
                    table.add_row(
                        info["name"],
                        info["version"],
                        info["type"],
                        "✅" if info["enabled"] else "❌",
                        info["description"][:50] + "..." if len(info["description"]) > 50 else info["description"]
                    )
            
            console.print(table)
            
        elif action == "info":
            # Show detailed info about a specific plugin
            if not name:
                console.print("[red]Plugin name required for info action[/red]")
                raise typer.Exit(1)
            
            info = loader.registry.get_plugin_info(name)
            if not info:
                console.print(f"[red]Plugin '{name}' not found[/red]")
                raise typer.Exit(1)
            
            console.print(Panel(JSON.from_data(info), title=f"Plugin: {name}"))
            
        elif action == "load-package":
            # Load plugins from a package
            if not source:
                console.print("[red]Package name required for load-package action[/red]")
                raise typer.Exit(1)
            
            discovered = loader.load_from_package(source)
            console.print(f"[green]✅ Loaded {discovered} plugins from package '{source}'[/green]")
            
            if verbose and discovered > 0:
                for plugin_name in loader.registry.list_plugins():
                    console.print(f"  📦 {plugin_name}")
                    
        elif action == "load-directory":
            # Load plugins from a directory
            if not source:
                console.print("[red]Directory path required for load-directory action[/red]")
                raise typer.Exit(1)
            
            discovered = loader.load_from_directory(source)
            console.print(f"[green]✅ Loaded {discovered} plugins from directory '{source}'[/green]")
            
            if verbose and discovered > 0:
                for plugin_name in loader.registry.list_plugins():
                    console.print(f"  📦 {plugin_name}")
                    
        elif action == "load-config":
            # Load plugins from configuration file
            if not config_file:
                console.print("[red]Config file path required for load-config action[/red]")
                raise typer.Exit(1)
            
            discovered = loader.load_from_config(config_file)
            console.print(f"[green]✅ Loaded {discovered} plugins from config '{config_file}'[/green]")
            
            if verbose and discovered > 0:
                for plugin_name in loader.registry.list_plugins():
                    console.print(f"  📦 {plugin_name}")
                    
        elif action == "validate-config":
            # Validate configuration file without loading
            if not config_file:
                console.print("[red]Config file path required for validate-config action[/red]")
                raise typer.Exit(1)
            
            errors = loader.validate_config_file(config_file)
            
            if not errors:
                console.print(f"[green]✅ Configuration file '{config_file}' is valid[/green]")
            else:
                console.print(f"[red]❌ Configuration file '{config_file}' has errors:[/red]")
                for error in errors:
                    console.print(f"  • {error}")
                raise typer.Exit(1)
                
        elif action == "create-sample-config":
            # Create a sample configuration file
            output_file = output or "plugins.json"
            
            loader.create_sample_config(output_file)
            console.print(f"[green]✅ Created sample plugin configuration: {output_file}[/green]")
            console.print(f"[yellow]Edit the file to configure your plugins, then use 'tomo plugin load-config --config {output_file}'[/yellow]")
            
        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available actions: list, info, load-package, load-directory, load-config, validate-config, create-sample-config")
            raise typer.Exit(1)
            
    except PluginLoaderError as e:
        console.print(f"[red]Plugin error: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
