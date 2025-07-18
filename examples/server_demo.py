"""Server demo for Tomo framework.

This demo shows how to use both the RESTful API server and MCP server
to expose Tomo tools remotely for external systems and AI agents.
"""

import asyncio
import json
import time
from typing import Dict, Any

from tomo import BaseTool, tool, ToolRegistry
from tomo.servers import APIServer, MCPServer


# Example tools for demonstration
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
                raise ValueError("Division by zero")
            return self.a / self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class TextProcessor(BaseTool):
    """Process text strings with various operations."""
    
    text: str
    operation: str  # uppercase, lowercase, reverse, length, word_count
    
    def run(self) -> Any:
        if self.operation == "uppercase":
            return self.text.upper()
        elif self.operation == "lowercase":
            return self.text.lower()
        elif self.operation == "reverse":
            return self.text[::-1]
        elif self.operation == "length":
            return len(self.text)
        elif self.operation == "word_count":
            return len(self.text.split())
        else:
            raise ValueError(f"Unknown operation: {self.operation}")


@tool
class Weather(BaseTool):
    """Get weather information for a city (mock implementation)."""
    
    city: str
    unit: str = "celsius"  # celsius or fahrenheit
    
    def run(self) -> Dict[str, Any]:
        # Mock weather data
        temp_celsius = 22
        temp_fahrenheit = 72
        
        return {
            "city": self.city,
            "temperature": temp_fahrenheit if self.unit == "fahrenheit" else temp_celsius,
            "unit": self.unit,
            "condition": "Sunny",
            "humidity": 65
        }


def setup_registry() -> ToolRegistry:
    """Set up a tool registry with example tools."""
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(TextProcessor)
    registry.register(Weather)
    return registry


def demo_api_server():
    """Demonstrate the RESTful API server."""
    print("🌐 RESTful API Server Demo")
    print("=" * 40)
    
    # Set up tools
    registry = setup_registry()
    print(f"Registered tools: {registry.list()}")
    
    # Create API server
    server = APIServer(
        registry=registry,
        title="Tomo Demo API",
        description="Demo API server for Tomo tools",
    )
    
    print("\nStarting API server...")
    print("Available endpoints:")
    print("- GET /health - Health check")
    print("- GET /tools - List all tools")
    print("- GET /tools/{tool_name} - Get tool info")
    print("- POST /tools/{tool_name}/execute - Execute tool")
    print("- POST /tools/{tool_name}/validate - Validate inputs")
    print("- GET /tools/{tool_name}/schema - Get tool schema")
    print("- GET /docs - API documentation")
    
    print("\nServer will start on http://0.0.0.0:8000")
    print("Visit http://0.0.0.0:8000/docs for interactive API documentation")
    
    # Start server (this will block)
    try:
        server.run(host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nAPI server stopped")


def demo_mcp_server():
    """Demonstrate the MCP server."""
    print("🔗 MCP Server Demo")
    print("=" * 40)
    
    # Set up tools
    registry = setup_registry()
    print(f"Registered tools: {registry.list()}")
    
    # Create MCP server
    server = MCPServer(
        registry=registry,
        server_name="tomo-demo-mcp",
        server_version="0.1.0",
    )
    
    print("\nStarting MCP server...")
    print("Protocol: Model Context Protocol (MCP)")
    print("Transport: JSON-RPC 2.0 over WebSockets")
    print("Available methods:")
    print("- initialize - Initialize MCP session")
    print("- tools/list - List available tools")
    print("- tools/call - Execute a tool")
    print("- ping - Health check")
    
    print("\nServer will start on ws://localhost:8001")
    print("Connect with an MCP-compatible client or AI agent")
    
    # Start server (this will block)
    try:
        server.run(host="localhost", port=8001)
    except KeyboardInterrupt:
        print("\nMCP server stopped")


async def demo_client_examples():
    """Show example client interactions with both servers."""
    print("📞 Client Examples")
    print("=" * 40)
    
    print("\n1. RESTful API Client Examples:")
    print("   # List tools")
    print("   curl http://localhost:8000/tools")
    print()
    print("   # Execute calculator")
    print('   curl -X POST http://localhost:8000/tools/Calculator/execute \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"inputs": {"operation": "add", "a": 5, "b": 3}}\'')
    print()
    print("   # Process text")
    print('   curl -X POST http://localhost:8000/tools/TextProcessor/execute \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"inputs": {"text": "Hello World", "operation": "uppercase"}}\'')
    
    print("\n2. MCP Client Examples:")
    print("   # Initialize connection")
    print('   {"jsonrpc": "2.0", "id": 1, "method": "initialize",')
    print('    "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "demo"}}}')
    print()
    print("   # List tools")
    print('   {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}')
    print()
    print("   # Call tool")
    print('   {"jsonrpc": "2.0", "id": 3, "method": "tools/call",')
    print('    "params": {"name": "Calculator", "arguments": {"operation": "multiply", "a": 6, "b": 7}}}')


def main():
    """Main demo function."""
    print("🧠 Tomo Server Demo")
    print("Choose a demo to run:")
    print("1. RESTful API Server")
    print("2. MCP Server") 
    print("3. Show Client Examples")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        demo_api_server()
    elif choice == "2":
        demo_mcp_server()
    elif choice == "3":
        asyncio.run(demo_client_examples())
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice. Please try again.")
        main()


if __name__ == "__main__":
    main() 