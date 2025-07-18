"""Plugin registry for managing and discovering plugins."""

from typing import Dict, List, Type, Any, Optional, Iterator
import importlib
from ..core.registry import ToolRegistry
from ..core.tool import BaseTool
from .base import BasePlugin, PluginType


class PluginRegistryError(Exception):
    """Exception raised by plugin registry operations."""
    pass


class PluginRegistry:
    """Central registry for all plugin types.
    
    The PluginRegistry manages plugins and their components, integrating with
    existing Tomo registries for tools, adapters, workflow steps, etc.
    """
    
    def __init__(self):
        """Initialize the plugin registry."""
        # Main plugin storage
        self.plugins: Dict[str, BasePlugin] = {}
        
        # Component registries
        self.tool_registry = ToolRegistry()
        self.adapter_registry: Dict[str, Type] = {}
        self.step_registry: Dict[str, Type] = {}
        self.server_registry: Dict[str, Type] = {}
        self.orchestrator_registry: Dict[str, Type] = {}
        self.transformer_registry: Dict[str, Type] = {}
        
        # Plugin metadata
        self._enabled_plugins: Dict[str, bool] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_plugin(self, plugin: BasePlugin, config: Dict[str, Any] = None) -> None:
        """Register a plugin and its components.
        
        Args:
            plugin: Plugin instance to register
            config: Configuration dictionary for the plugin
            
        Raises:
            PluginRegistryError: If plugin registration fails
        """
        if plugin.name in self.plugins:
            raise PluginRegistryError(f"Plugin '{plugin.name}' is already registered")
        
        # Validate dependencies
        missing_deps = plugin.validate_dependencies()
        if missing_deps:
            raise PluginRegistryError(
                f"Plugin '{plugin.name}' has missing dependencies: {', '.join(missing_deps)}"
            )
        
        try:
            # Initialize plugin
            plugin.initialize(config or {})
            
            # Register with main registry
            self.plugins[plugin.name] = plugin
            self._enabled_plugins[plugin.name] = True
            self._plugin_configs[plugin.name] = config or {}
            
            # Let plugin register its components
            plugin.register_components(self)
            
        except Exception as e:
            # Clean up on failure
            if plugin.name in self.plugins:
                del self.plugins[plugin.name]
            if plugin.name in self._enabled_plugins:
                del self._enabled_plugins[plugin.name]
            if plugin.name in self._plugin_configs:
                del self._plugin_configs[plugin.name]
            
            raise PluginRegistryError(f"Failed to register plugin '{plugin.name}': {str(e)}") from e
    
    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin by name.
        
        Args:
            name: Name of the plugin to unregister
            
        Returns:
            True if the plugin was found and removed, False otherwise
        """
        if name not in self.plugins:
            return False
        
        # TODO: Implement component cleanup (would need tracking of what each plugin registered)
        
        del self.plugins[name]
        if name in self._enabled_plugins:
            del self._enabled_plugins[name]
        if name in self._plugin_configs:
            del self._plugin_configs[name]
        
        return True
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name.
        
        Args:
            name: Name of the plugin to retrieve
            
        Returns:
            Plugin instance if found, None otherwise
        """
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names.
        
        Returns:
            List of all registered plugin names
        """
        return list(self.plugins.keys())
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """Get all plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugins of the specified type
        """
        return [p for p in self.plugins.values() if p.plugin_type == plugin_type]
    
    def is_plugin_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled.
        
        Args:
            name: Name of the plugin to check
            
        Returns:
            True if plugin is enabled, False otherwise
        """
        return self._enabled_plugins.get(name, False)
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin.
        
        Args:
            name: Name of the plugin to enable
            
        Returns:
            True if plugin was found and enabled, False otherwise
        """
        if name in self.plugins:
            self._enabled_plugins[name] = True
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin.
        
        Args:
            name: Name of the plugin to disable
            
        Returns:
            True if plugin was found and disabled, False otherwise
        """
        if name in self.plugins:
            self._enabled_plugins[name] = False
            return True
        return False
    
    def auto_discover_plugins(self, module: Any) -> int:
        """Auto-discover and register plugins from a module.
        
        This method scans a module for classes that inherit from BasePlugin
        and have the _is_tomo_plugin attribute set to True.
        
        Args:
            module: The module to scan for plugins
            
        Returns:
            The number of plugins discovered and registered
        """
        discovered = 0
        
        for name in dir(module):
            obj = getattr(module, name)
            
            # Check if it's a class that inherits from BasePlugin and is marked as a plugin
            if (
                isinstance(obj, type)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
                and getattr(obj, "_is_tomo_plugin", False)
            ):
                try:
                    # Create plugin instance
                    plugin = obj()
                    self.register_plugin(plugin)
                    discovered += 1
                except (PluginRegistryError, Exception):
                    # Plugin failed to register, skip
                    pass
        
        return discovered
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Dictionary with plugin information, None if not found
        """
        plugin = self.get_plugin(name)
        if not plugin:
            return None
        
        info = plugin.get_info()
        info.update({
            "enabled": self.is_plugin_enabled(name),
            "config": self._plugin_configs.get(name, {}),
        })
        
        return info
    
    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered plugins.
        
        Returns:
            Dictionary mapping plugin names to their information
        """
        return {name: self.get_plugin_info(name) for name in self.plugins.keys()}
    
    def validate_all_plugins(self) -> Dict[str, List[str]]:
        """Validate all registered plugins.
        
        Returns:
            Dictionary mapping plugin names to lists of validation errors
        """
        validation_results = {}
        
        for name, plugin in self.plugins.items():
            errors = []
            
            # Check dependencies
            missing_deps = plugin.validate_dependencies()
            if missing_deps:
                errors.extend([f"Missing dependency: {dep}" for dep in missing_deps])
            
            validation_results[name] = errors
        
        return validation_results
    
    def clear(self) -> None:
        """Clear all registered plugins and their components."""
        self.plugins.clear()
        self._enabled_plugins.clear()
        self._plugin_configs.clear()
        
        # Clear component registries
        self.tool_registry.clear()
        self.adapter_registry.clear()
        self.step_registry.clear()
        self.server_registry.clear()
        self.orchestrator_registry.clear()
        self.transformer_registry.clear()
    
    def size(self) -> int:
        """Get the number of registered plugins.
        
        Returns:
            Number of registered plugins
        """
        return len(self.plugins)
    
    def __len__(self) -> int:
        """Get the number of registered plugins."""
        return len(self.plugins)
    
    def __contains__(self, name: str) -> bool:
        """Check if a plugin is registered using 'in' operator."""
        return name in self.plugins
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over plugin names."""
        return iter(self.plugins)
    
    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"PluginRegistry({len(self.plugins)} plugins: {list(self.plugins.keys())})" 