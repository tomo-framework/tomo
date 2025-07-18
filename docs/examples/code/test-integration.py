#!/usr/bin/env python3
"""
Test Integration Script

This script tests the complete Tomo → TypeScript integration by:
1. Loading the example tools
2. Starting a temporary MCP server
3. Running basic tool tests
4. Outputting instructions for TypeScript testing

Run this script to verify your setup before trying TypeScript integration.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the main tomo directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tomo import ToolRegistry, ToolRunner
from docs.examples.code.python.example_tools import (
    Calculator, WeatherChecker, TextProcessor, 
    DataValidator, NumberSequence, DateTimeUtility
)

def test_tools():
    """Test all tools to ensure they work correctly."""
    print("🧪 Testing Tomo Tools")
    print("=" * 50)
    
    # Create registry and register tools
    registry = ToolRegistry()
    tools = [Calculator, WeatherChecker, TextProcessor, DataValidator, NumberSequence, DateTimeUtility]
    
    for tool in tools:
        registry.register(tool)
    
    runner = ToolRunner(registry)
    
    # Test cases
    test_cases = [
        {
            "name": "Calculator",
            "inputs": {"operation": "add", "a": 15, "b": 25},
            "expected_type": (int, float)
        },
        {
            "name": "Calculator", 
            "inputs": {"operation": "multiply", "a": 6, "b": 7},
            "expected_type": (int, float)
        },
        {
            "name": "WeatherChecker",
            "inputs": {"city": "Tokyo", "country": "Japan"},
            "expected_type": dict
        },
        {
            "name": "TextProcessor",
            "inputs": {"text": "Hello, Tomo!", "operation": "uppercase"},
            "expected_type": dict
        },
        {
            "name": "DataValidator",
            "inputs": {"value": "test@example.com", "validation_type": "email"},
            "expected_type": dict
        },
        {
            "name": "NumberSequence",
            "inputs": {"sequence_type": "fibonacci", "count": 5},
            "expected_type": list
        },
        {
            "name": "DateTimeUtility",
            "inputs": {"operation": "current_time"},
            "expected_type": dict
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Testing {test_case['name']}...")
            print(f"   Inputs: {test_case['inputs']}")
            
            result = runner.run_tool(test_case['name'], test_case['inputs'])
            
            if isinstance(result, test_case['expected_type']):
                print(f"   ✅ PASSED")
                print(f"   Result: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
                passed += 1
            else:
                print(f"   ❌ FAILED - Expected {test_case['expected_type']}, got {type(result)}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ FAILED - Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some tests failed. Please check your tool implementations.")
        return False
    else:
        print("✅ All tests passed! Tools are working correctly.")
        return True

def print_mcp_instructions():
    """Print instructions for starting MCP server and testing with TypeScript."""
    print("\n🚀 Next Steps for TypeScript Integration")
    print("=" * 50)
    
    print("\n1. Start the Tomo MCP Server:")
    print("   tomo serve-mcp --module docs.examples.code.python.example_tools --port 8001")
    
    print("\n2. In another terminal, set up TypeScript:")
    print("   cd docs/examples/code/typescript")
    print("   npm install")
    print("   npm run dev")
    
    print("\n3. Expected TypeScript output should show:")
    print("   - Connected to MCP server")
    print("   - List of 6 available tools")
    print("   - Successful tool execution results")
    
    print("\n4. For Next.js integration:")
    print("   - Copy nextjs-example.tsx.example to your Next.js project")
    print("   - Follow the setup instructions in docs/examples/code/README.md")
    
    print("\n🔗 Documentation Links:")
    print("   - Complete setup: docs/setup.md")
    print("   - Basic examples: docs/examples/basic.md")
    print("   - Code examples: docs/examples/code/README.md")

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking Dependencies")
    print("=" * 50)
    
    try:
        import tomo
        print("✅ Tomo framework loaded successfully")
    except ImportError as e:
        print(f"❌ Tomo not found: {e}")
        return False
    
    try:
        from tomo.servers.mcp import MCPServer
        print("✅ MCP server available")
    except ImportError:
        print("❌ MCP server not available - install with: uv sync --extra mcp")
        return False
    
    try:
        from tomo.servers.api import APIServer
        print("✅ REST API server available") 
    except ImportError:
        print("⚠️  REST API server not available - install with: uv sync --extra server")
    
    return True

def main():
    """Main test function."""
    print("🧠 Tomo TypeScript Integration Test")
    print("🔗 Testing Python tools before TypeScript integration")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install required dependencies.")
        sys.exit(1)
    
    # Test tools
    if not test_tools():
        print("\n❌ Tool tests failed. Please fix the issues before proceeding.")
        sys.exit(1)
    
    # Print next steps
    print_mcp_instructions()
    
    print("\n🎉 Python side is ready! You can now proceed with TypeScript integration.")

if __name__ == "__main__":
    main() 