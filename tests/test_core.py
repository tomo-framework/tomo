"""Tests for core Tomo functionality."""

import pytest
from tomo import BaseTool, tool, ToolRegistry, ToolRunner
from tomo.core.runner import ToolNotFoundError, ToolValidationError, ToolExecutionError


@tool
class TestCalculator(BaseTool):
    """Test calculator tool."""
    
    a: int
    b: int
    
    def run(self) -> int:
        return self.a + self.b


@tool
class TestDivider(BaseTool):
    """Test divider tool that can raise errors."""
    
    a: float
    b: float
    
    def run(self) -> float:
        if self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self.a / self.b


class TestTool:
    """Test tool definition and decoration."""
    
    def test_tool_decorator(self):
        """Test the @tool decorator."""
        assert hasattr(TestCalculator, '_is_tomo_tool')
        assert TestCalculator._is_tomo_tool is True
    
    def test_tool_inheritance(self):
        """Test that tools inherit from BaseTool."""
        assert issubclass(TestCalculator, BaseTool)
    
    def test_tool_instantiation(self):
        """Test tool instantiation with validation."""
        calc = TestCalculator(a=5, b=3)
        assert calc.a == 5
        assert calc.b == 3
    
    def test_tool_execution(self):
        """Test tool execution."""
        calc = TestCalculator(a=5, b=3)
        result = calc.run()
        assert result == 8
    
    def test_invalid_tool_instantiation(self):
        """Test that invalid inputs raise ValidationError."""
        with pytest.raises(Exception):  # ValidationError from Pydantic
            TestCalculator(a="invalid", b=3)
    
    def test_tool_schema(self):
        """Test tool schema generation."""
        schema = TestCalculator.get_schema()
        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "TestCalculator"
        assert "parameters" in schema["function"]


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_registry_creation(self):
        """Test registry creation."""
        registry = ToolRegistry()
        assert len(registry) == 0
    
    def test_tool_registration(self):
        """Test tool registration."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        
        assert len(registry) == 1
        assert "TestCalculator" in registry
        assert registry.get("TestCalculator") is TestCalculator
    
    def test_duplicate_registration(self):
        """Test that duplicate registration raises error."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        
        with pytest.raises(ValueError):
            registry.register(TestCalculator)
    
    def test_tool_listing(self):
        """Test tool listing."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        registry.register(TestDivider)
        
        tools = registry.list()
        assert "TestCalculator" in tools
        assert "TestDivider" in tools
        assert len(tools) == 2
    
    def test_tool_unregistration(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        
        assert registry.unregister("TestCalculator") is True
        assert len(registry) == 0
        assert registry.unregister("NonExistent") is False
    
    def test_schema_export(self):
        """Test schema export."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        
        schemas = registry.export_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "TestCalculator"


class TestToolRunner:
    """Test tool runner functionality."""
    
    def test_runner_creation(self):
        """Test runner creation."""
        registry = ToolRegistry()
        runner = ToolRunner(registry)
        assert runner.registry is registry
    
    def test_tool_execution(self):
        """Test tool execution through runner."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        runner = ToolRunner(registry)
        
        result = runner.run_tool("TestCalculator", {"a": 10, "b": 5})
        assert result == 15
    
    def test_tool_not_found(self):
        """Test error when tool not found."""
        registry = ToolRegistry()
        runner = ToolRunner(registry)
        
        with pytest.raises(ToolNotFoundError):
            runner.run_tool("NonExistent", {})
    
    def test_invalid_inputs(self):
        """Test error with invalid inputs."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        runner = ToolRunner(registry)
        
        with pytest.raises(ToolValidationError):
            runner.run_tool("TestCalculator", {"a": "invalid", "b": 5})
    
    def test_tool_execution_error(self):
        """Test error during tool execution."""
        registry = ToolRegistry()
        registry.register(TestDivider)
        runner = ToolRunner(registry)
        
        with pytest.raises(ToolExecutionError):
            runner.run_tool("TestDivider", {"a": 10, "b": 0})
    
    def test_safe_execution(self):
        """Test safe execution mode."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        registry.register(TestDivider)
        runner = ToolRunner(registry)
        
        # Successful execution
        result = runner.run_tool_safe("TestCalculator", {"a": 10, "b": 5})
        assert result["success"] is True
        assert result["result"] == 15
        assert result["error"] is None
        
        # Failed execution
        result = runner.run_tool_safe("TestDivider", {"a": 10, "b": 0})
        assert result["success"] is False
        assert result["result"] is None
        assert "Cannot divide by zero" in result["error"]
    
    def test_input_validation(self):
        """Test input validation."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        runner = ToolRunner(registry)
        
        # Valid inputs
        assert runner.validate_tool_inputs("TestCalculator", {"a": 5, "b": 3}) is True
        
        # Invalid inputs
        assert runner.validate_tool_inputs("TestCalculator", {"a": "invalid", "b": 3}) is False
    
    def test_json_execution(self):
        """Test execution with JSON inputs."""
        registry = ToolRegistry()
        registry.register(TestCalculator)
        runner = ToolRunner(registry)
        
        result = runner.run_tool_from_json("TestCalculator", '{"a": 7, "b": 3}')
        assert result == 10
        
        with pytest.raises(ToolValidationError):
            runner.run_tool_from_json("TestCalculator", 'invalid json')


if __name__ == "__main__":
    pytest.main([__file__]) 