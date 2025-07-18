"""Base plugin infrastructure for Tomo."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .registry import PluginRegistry


class PluginType(Enum):
    """Types of plugins supported by Tomo."""
    TOOL = "tool"
    ADAPTER = "adapter"
    WORKFLOW_STEP = "workflow_step"
    SERVER = "server"
    ORCHESTRATOR = "orchestrator"
    TRANSFORMER = "transformer"


class BasePlugin(ABC):
    """Base class for all Tomo plugins.
    
    Plugins extend Tomo with new functionality by registering components
    like tools, adapters, workflow steps, servers, etc.
    """
    
    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Type of plugin."""
        pass
    
    @property
    @abstractmethod  
    def name(self) -> str:
        """Unique name for the plugin."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
        
    @property
    def description(self) -> str:
        """Plugin description."""
        return ""
        
    @property
    def dependencies(self) -> List[str]:
        """List of required dependencies."""
        return []
    
    @property
    def author(self) -> str:
        """Plugin author."""
        return ""
    
    @property
    def homepage(self) -> str:
        """Plugin homepage URL."""
        return ""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        pass
    
    @abstractmethod
    def register_components(self, registry: 'PluginRegistry') -> None:
        """Register plugin components with appropriate registries.
        
        Args:
            registry: Plugin registry to register components with
        """
        pass
    
    def validate_dependencies(self) -> List[str]:
        """Validate that all plugin dependencies are available.
        
        Returns:
            List of missing dependencies (empty if all satisfied)
        """
        missing_deps = []
        
        for dep in self.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        return missing_deps
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information as a dictionary.
        
        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "type": self.plugin_type.value,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "dependencies": self.dependencies,
        }
    
    def __repr__(self) -> str:
        """String representation of the plugin."""
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}', type='{self.plugin_type.value}')"


def plugin(plugin_type: PluginType, name: str, version: str = "1.0.0"):
    """Decorator to mark classes as Tomo plugins.
    
    Args:
        plugin_type: Type of plugin (from PluginType enum)
        name: Unique name for the plugin
        version: Plugin version (defaults to "1.0.0")
    
    Returns:
        Decorated class with plugin metadata
    
    Example:
        @plugin(PluginType.TOOL, "my_tools", "1.0.0")
        class MyToolsPlugin(BasePlugin):
            # Plugin implementation
            pass
    """
    def decorator(cls: Type[BasePlugin]) -> Type[BasePlugin]:
        if not issubclass(cls, BasePlugin):
            raise TypeError(f"Plugin class {cls.__name__} must inherit from BasePlugin")
        
        # Add plugin metadata as class attributes
        cls._is_tomo_plugin = True
        cls._plugin_type = plugin_type
        cls._plugin_name = name  
        cls._plugin_version = version
        
        return cls
    
    return decorator 