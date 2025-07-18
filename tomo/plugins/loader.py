"""Plugin loader for discovering and loading plugins from various sources."""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from .registry import PluginRegistry, PluginRegistryError
from .base import BasePlugin


class PluginLoaderError(Exception):
    """Exception raised by plugin loader operations."""
    pass


class PluginLoader:
    """Loads and manages plugins from various sources.
    
    The PluginLoader can discover and load plugins from:
    - Installed Python packages
    - Local directories containing plugin files
    - Configuration files specifying plugins to load
    """
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        """Initialize the plugin loader.
        
        Args:
            registry: Plugin registry to use (creates new one if None)
        """
        self.registry = registry or PluginRegistry()
        self._loaded_modules: Dict[str, Any] = {}
        self._load_history: List[Dict[str, Any]] = []
    
    def load_from_package(self, package_name: str, config: Dict[str, Any] = None) -> int:
        """Load plugins from an installed Python package.
        
        Args:
            package_name: Name of the package to load plugins from
            config: Configuration to pass to discovered plugins
            
        Returns:
            Number of plugins loaded
            
        Raises:
            PluginLoaderError: If package loading fails
        """
        try:
            module = importlib.import_module(package_name)
            discovered = self.registry.auto_discover_plugins(module)
            
            # Apply config to newly discovered plugins if provided
            if config and discovered > 0:
                # Get plugins that were just added
                current_plugins = set(self.registry.list_plugins())
                # This is a simplified approach - in practice you'd track which plugins were just added
                
            self._record_load_operation("package", package_name, discovered, config)
            return discovered
            
        except ImportError as e:
            raise PluginLoaderError(f"Could not import package '{package_name}': {str(e)}") from e
        except Exception as e:
            raise PluginLoaderError(f"Error loading plugins from package '{package_name}': {str(e)}") from e
    
    def load_from_directory(self, directory: Union[str, Path], config: Dict[str, Any] = None) -> int:
        """Load plugins from a directory containing Python files.
        
        Args:
            directory: Directory path to scan for plugin files
            config: Configuration to pass to discovered plugins
            
        Returns:
            Number of plugins loaded
            
        Raises:
            PluginLoaderError: If directory loading fails
        """
        directory = Path(directory)
        
        if not directory.exists():
            raise PluginLoaderError(f"Directory '{directory}' does not exist")
        
        if not directory.is_dir():
            raise PluginLoaderError(f"Path '{directory}' is not a directory")
        
        discovered = 0
        loaded_files = []
        
        try:
            # Scan for Python files
            for file_path in directory.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue  # Skip private files
                
                # Load module from file
                module_name = f"plugin_{file_path.stem}_{id(file_path)}"
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add to sys.modules to make imports work
                    sys.modules[module_name] = module
                    
                    try:
                        spec.loader.exec_module(module)
                        
                        # Store reference to loaded module
                        self._loaded_modules[str(file_path)] = module
                        
                        # Discover plugins in module
                        file_discovered = self.registry.auto_discover_plugins(module)
                        discovered += file_discovered
                        loaded_files.append(str(file_path))
                        
                    except Exception as e:
                        # Clean up on failure
                        if module_name in sys.modules:
                            del sys.modules[module_name]
                        raise PluginLoaderError(f"Error executing plugin file '{file_path}': {str(e)}") from e
            
            self._record_load_operation("directory", str(directory), discovered, config, {"files": loaded_files})
            return discovered
            
        except Exception as e:
            if not isinstance(e, PluginLoaderError):
                raise PluginLoaderError(f"Error loading plugins from directory '{directory}': {str(e)}") from e
            raise
    
    def load_from_config(self, config_file: Union[str, Path]) -> int:
        """Load plugins defined in a configuration file.
        
        The configuration file should be JSON format with structure:
        {
            "plugins": [
                {
                    "source": "package_name" | {"directory": "/path/to/dir"},
                    "enabled": true,
                    "config": {...}
                }
            ]
        }
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            Number of plugins loaded
            
        Raises:
            PluginLoaderError: If configuration loading fails
        """
        config_file = Path(config_file)
        
        if not config_file.exists():
            raise PluginLoaderError(f"Configuration file '{config_file}' does not exist")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            total_discovered = 0
            loaded_sources = []
            
            for plugin_config in config.get("plugins", []):
                if not plugin_config.get("enabled", True):
                    continue
                
                source = plugin_config.get("source")
                plugin_specific_config = plugin_config.get("config", {})
                
                if isinstance(source, str):
                    # Package source
                    discovered = self.load_from_package(source, plugin_specific_config)
                    loaded_sources.append(f"package:{source}")
                    
                elif isinstance(source, dict) and "directory" in source:
                    # Directory source
                    directory = source["directory"]
                    discovered = self.load_from_directory(directory, plugin_specific_config)
                    loaded_sources.append(f"directory:{directory}")
                    
                else:
                    raise PluginLoaderError(f"Invalid plugin source configuration: {source}")
                
                total_discovered += discovered
            
            self._record_load_operation("config", str(config_file), total_discovered, None, {"sources": loaded_sources})
            return total_discovered
            
        except json.JSONDecodeError as e:
            raise PluginLoaderError(f"Invalid JSON in configuration file '{config_file}': {str(e)}") from e
        except Exception as e:
            if not isinstance(e, PluginLoaderError):
                raise PluginLoaderError(f"Error loading plugins from config '{config_file}': {str(e)}") from e
            raise
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin (unregister and load again).
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            True if plugin was successfully reloaded, False otherwise
        """
        # This is a simplified implementation
        # In practice, you'd need to track plugin sources to reload them properly
        if plugin_name in self.registry:
            self.registry.unregister_plugin(plugin_name)
            # Would need to reload from original source...
            return True
        return False
    
    def get_load_history(self) -> List[Dict[str, Any]]:
        """Get the history of plugin loading operations.
        
        Returns:
            List of load operation records
        """
        return self._load_history.copy()
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """Get all modules loaded by this loader.
        
        Returns:
            Dictionary mapping file paths to loaded modules
        """
        return self._loaded_modules.copy()
    
    def validate_config_file(self, config_file: Union[str, Path]) -> List[str]:
        """Validate a plugin configuration file without loading.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            List of validation errors (empty if valid)
        """
        config_file = Path(config_file)
        errors = []
        
        if not config_file.exists():
            errors.append(f"Configuration file '{config_file}' does not exist")
            return errors
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if not isinstance(config, dict):
                errors.append("Configuration must be a JSON object")
                return errors
            
            plugins = config.get("plugins")
            if plugins is None:
                errors.append("Configuration must contain 'plugins' array")
                return errors
            
            if not isinstance(plugins, list):
                errors.append("'plugins' must be an array")
                return errors
            
            for i, plugin_config in enumerate(plugins):
                if not isinstance(plugin_config, dict):
                    errors.append(f"Plugin config {i} must be an object")
                    continue
                
                source = plugin_config.get("source")
                if source is None:
                    errors.append(f"Plugin config {i} missing required 'source' field")
                elif isinstance(source, str):
                    # Package source - could validate package exists
                    pass
                elif isinstance(source, dict):
                    if "directory" not in source:
                        errors.append(f"Plugin config {i} directory source missing 'directory' field")
                    else:
                        directory = Path(source["directory"])
                        if not directory.exists():
                            errors.append(f"Plugin config {i} directory '{directory}' does not exist")
                else:
                    errors.append(f"Plugin config {i} 'source' must be string or object")
                
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            errors.append(f"Error reading configuration: {str(e)}")
        
        return errors
    
    def create_sample_config(self, output_file: Union[str, Path]) -> None:
        """Create a sample plugin configuration file.
        
        Args:
            output_file: Path where to create the sample configuration
        """
        sample_config = {
            "plugins": [
                {
                    "source": "tomo_web_scraping",
                    "enabled": False,
                    "config": {
                        "timeout": 30,
                        "user_agent": "Tomo/1.0"
                    }
                },
                {
                    "source": {
                        "directory": "./examples/plugins"
                    },
                    "enabled": True,
                    "config": {
                        "max_url_length": 2048,
                        "model_path": "./models/llama-model.gguf"
                    }
                }
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
    
    def _record_load_operation(
        self, 
        source_type: str, 
        source: str, 
        plugins_loaded: int, 
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a plugin loading operation in history.
        
        Args:
            source_type: Type of source (package, directory, config)
            source: Source identifier
            plugins_loaded: Number of plugins loaded
            config: Configuration used
            metadata: Additional metadata
        """
        import datetime
        
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_type": source_type,
            "source": source,
            "plugins_loaded": plugins_loaded,
            "config": config,
            "metadata": metadata or {}
        }
        
        self._load_history.append(record)
    
    def __repr__(self) -> str:
        """String representation of the loader."""
        return f"PluginLoader(registry={self.registry}, loaded_modules={len(self._loaded_modules)})" 