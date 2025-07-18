"""Plugin system for Tomo framework.

This module provides the infrastructure for extending Tomo with plugins that can
add new tools, adapters, workflow steps, servers, and other components.
"""

from .base import BasePlugin, PluginType, plugin
from .registry import PluginRegistry, PluginRegistryError
from .loader import PluginLoader, PluginLoaderError

__all__ = [
    "BasePlugin",
    "PluginType", 
    "plugin",
    "PluginRegistry",
    "PluginRegistryError",
    "PluginLoader",
    "PluginLoaderError",
] 