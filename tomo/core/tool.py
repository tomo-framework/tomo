"""Core tool definitions and decorators."""

from typing import Any, Dict, Type, TypeVar, Union, get_type_hints
from abc import ABC, abstractmethod
import inspect
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

T = TypeVar("T", bound="BaseTool")


class BaseTool(BaseModel, ABC):
    """Base class for all tools in Tomo.

    Tools are Pydantic models that define typed inputs and implement a run method
    to execute the tool's logic.
    """

    @abstractmethod
    def run(self) -> Any:
        """Execute the tool's logic.

        Returns:
            The result of the tool execution.
        """
        pass

    @classmethod
    def get_name(cls) -> str:
        """Get the tool name (class name by default)."""
        return cls.__name__

    @classmethod
    def get_description(cls) -> str:
        """Get the tool description from docstring."""
        return cls.__doc__ or f"Tool: {cls.get_name()}"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get the tool's JSON schema for LLM consumption."""
        schema = cls.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": cls.get_name(),
                "description": cls.get_description(),
                "parameters": schema,
            },
        }


def tool(cls: Type[T]) -> Type[T]:
    """Decorator to register a class as a Tomo tool.

    This decorator ensures the class inherits from BaseTool and adds
    any necessary tool metadata.

    Args:
        cls: The class to decorate as a tool.

    Returns:
        The decorated class.

    Raises:
        TypeError: If the class doesn't inherit from BaseTool.
    """
    if not issubclass(cls, BaseTool):
        raise TypeError(f"Tool {cls.__name__} must inherit from BaseTool")

    # Ensure the run method is implemented
    if not hasattr(cls, "run") or cls.run is BaseTool.run:
        raise TypeError(f"Tool {cls.__name__} must implement the run() method")

    # Add tool metadata
    cls._is_tomo_tool = True

    return cls


def create_tool_from_function(
    func: callable, name: str = None, description: str = None
) -> Type[BaseTool]:
    """Create a Tool class from a regular function.

    Args:
        func: The function to convert to a tool.
        name: Optional name for the tool (defaults to function name).
        description: Optional description (defaults to function docstring).

    Returns:
        A new Tool class that wraps the function.
    """
    tool_name = name or func.__name__
    tool_description = description or func.__doc__ or f"Tool: {tool_name}"

    # Get function signature and type hints
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    # Create fields for the Pydantic model
    fields = {}
    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name, Any)

        # Handle default values
        if param.default is not inspect.Parameter.empty:
            fields[param_name] = (param_type, param.default)
        else:
            fields[param_name] = (param_type, ...)

    # Create the tool class dynamically
    def run_method(self) -> Any:
        # Extract field values and call original function
        kwargs = {name: getattr(self, name) for name in fields.keys()}
        return func(**kwargs)

    # Create the class
    tool_class = create_model(tool_name, __base__=BaseTool, **fields)

    # Add the run method and metadata
    tool_class.run = run_method
    tool_class.__doc__ = tool_description
    tool_class._is_tomo_tool = True

    return tool_class
