"""Tool registry for managing and discovering tools."""

from typing import Dict, List, Type, Any, Optional, Iterator
from .tool import BaseTool


class ToolRegistry:
    """Registry for managing and discovering tools.

    The registry allows tools to be registered by name and provides
    methods for discovery, retrieval, and schema export.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Type[BaseTool]] = {}

    def register(self, tool_class: Type[BaseTool], name: Optional[str] = None) -> None:
        """Register a tool class with the registry.

        Args:
            tool_class: The tool class to register.
            name: Optional name to register the tool under (defaults to class name).

        Raises:
            TypeError: If the tool_class is not a subclass of BaseTool.
            ValueError: If a tool with the same name is already registered.
        """
        if not issubclass(tool_class, BaseTool):
            raise TypeError(f"Tool {tool_class.__name__} must inherit from BaseTool")

        tool_name = name or tool_class.get_name()

        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        self._tools[tool_name] = tool_class

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name.

        Args:
            name: The name of the tool to unregister.

        Returns:
            True if the tool was found and removed, False otherwise.
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> Optional[Type[BaseTool]]:
        """Get a tool class by name.

        Args:
            name: The name of the tool to retrieve.

        Returns:
            The tool class if found, None otherwise.
        """
        return self._tools.get(name)

    def list(self) -> List[str]:
        """List all registered tool names.

        Returns:
            A list of all registered tool names.
        """
        return list(self._tools.keys())

    def list_tools(self) -> Dict[str, Type[BaseTool]]:
        """Get all registered tools.

        Returns:
            A dictionary mapping tool names to tool classes.
        """
        return self._tools.copy()

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()

    def size(self) -> int:
        """Get the number of registered tools.

        Returns:
            The number of registered tools.
        """
        return len(self._tools)

    def contains(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: The name of the tool to check.

        Returns:
            True if the tool is registered, False otherwise.
        """
        return name in self._tools

    def export_schemas(self) -> List[Dict[str, Any]]:
        """Export all tool schemas for LLM consumption.

        Returns:
            A list of tool schemas in OpenAI function calling format.
        """
        return [tool_class.get_schema() for tool_class in self._tools.values()]

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a specific tool.

        Args:
            name: The name of the tool.

        Returns:
            The tool schema if found, None otherwise.
        """
        tool_class = self.get(name)
        return tool_class.get_schema() if tool_class else None

    def auto_discover(self, module: Any) -> int:
        """Auto-discover and register tools from a module.

        This method scans a module for classes that inherit from BaseTool
        and have the _is_tomo_tool attribute set to True.

        Args:
            module: The module to scan for tools.

        Returns:
            The number of tools discovered and registered.
        """
        discovered = 0

        for name in dir(module):
            obj = getattr(module, name)

            # Check if it's a class that inherits from BaseTool and is marked as a tool
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseTool)
                and obj is not BaseTool
                and getattr(obj, "_is_tomo_tool", False)
            ):

                try:
                    self.register(obj)
                    discovered += 1
                except ValueError:
                    # Tool already registered, skip
                    pass

        return discovered

    def __len__(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered using 'in' operator."""
        return name in self._tools

    def __iter__(self) -> Iterator[str]:
        """Iterate over tool names."""
        return iter(self._tools)

    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"ToolRegistry({len(self._tools)} tools: {list(self._tools.keys())})"
