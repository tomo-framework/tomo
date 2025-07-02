"""Main CLI application for Tomo."""

import json
import sys
from pathlib import Path
from typing import Optional, List
try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.json import JSON
except ImportError:
    print("CLI dependencies not installed. Install with: uv add tomo[cli]")
    sys.exit(1)

from ..core.registry import ToolRegistry
from ..core.runner import ToolRunner, ToolNotFoundError, ToolValidationError, ToolExecutionError
from ..adapters.openai import OpenAIAdapter

app = typer.Typer(
    name="tomo",
    help="Tomo - Tool-Oriented Micro Orchestrator",
    add_completion=False
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
        if module_path.endswith('.py'):
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
        console.print(f"[green]Discovered {discovered} tools from {module_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error loading tools from {module_path}: {e}[/red]")
    
    return registry


@app.command("list")
def list_tools(
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Python module to load tools from"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information")
):
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


@app.command("run")
def run_tool(
    tool_name: str = typer.Argument(..., help="Name of the tool to run"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Python module to load tools from"),
    inputs: Optional[str] = typer.Option(None, "--inputs", "-i", help="JSON string of tool inputs"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="JSON file containing tool inputs"),
    safe: bool = typer.Option(False, "--safe", help="Use safe execution (structured error handling)")
):
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


@app.command("schema")
def export_schema(
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Python module to load tools from"),
    tool: Optional[str] = typer.Option(None, "--tool", "-t", help="Specific tool to export schema for"),
    format: str = typer.Option("openai", "--format", "-f", help="Schema format: openai"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Export tool schemas for LLM consumption."""
    registry = load_tools_from_module(module) if module else ToolRegistry()
    
    if not registry.list():
        console.print("[yellow]No tools found[/yellow]")
        return
    
    adapter = OpenAIAdapter()
    
    if tool:
        # Export single tool schema
        if tool not in registry:
            console.print(f"[red]Tool '{tool}' not found[/red]")
            raise typer.Exit(1)
        
        schema = registry.get_schema(tool)
        schema_data = [schema] if schema else []
    else:
        # Export all tools
        schema_data = adapter.export_tools(registry)
    
    if output:
        with open(output, 'w') as f:
            json.dump(schema_data, f, indent=2)
        console.print(f"[green]Schema exported to {output}[/green]")
    else:
        console.print(JSON.from_data(schema_data))


@app.command("validate")
def validate_tool(
    tool_name: str = typer.Argument(..., help="Name of the tool to validate"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Python module to load tools from"),
    inputs: Optional[str] = typer.Option(None, "--inputs", "-i", help="JSON string of tool inputs to validate"),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="JSON file containing tool inputs to validate")
):
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


if __name__ == "__main__":
    app() 