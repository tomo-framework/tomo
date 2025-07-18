"""Tomo - Tool-Oriented Micro Orchestrator

A lightweight, language-model-agnostic framework for defining, registering,
and executing typed tools.
"""

from tomo.core.tool import BaseTool, tool
from tomo.core.registry import ToolRegistry
from tomo.core.runner import ToolRunner

# Import orchestrators if available
try:
    from tomo.orchestrators import (
        LLMOrchestrator, 
        ConversationManager, 
        ExecutionEngine,
        # Workflow engine components
        Workflow,
        WorkflowEngine,
        WorkflowStep,
        WorkflowState,
        WorkflowContext,
        ToolStep,
        ConditionStep,
        ParallelStep,
        create_tool_step,
    )
    orchestrator_available = True
except ImportError:
    orchestrator_available = False

# Import servers if available
try:
    from tomo.servers import APIServer, MCPServer
    server_available = True
except ImportError:
    server_available = False

# Import plugins if available
try:
    from tomo.plugins import (
        BasePlugin,
        PluginType,
        plugin,
        PluginRegistry,
        PluginRegistryError,
        PluginLoader,
        PluginLoaderError,
    )
    plugin_available = True
except ImportError:
    plugin_available = False

# Build __all__ list based on available components
__all__ = ["BaseTool", "tool", "ToolRegistry", "ToolRunner"]

if orchestrator_available:
    __all__.extend([
        "LLMOrchestrator", 
        "ConversationManager", 
        "ExecutionEngine",
        # Workflow engine
        "Workflow",
        "WorkflowEngine", 
        "WorkflowStep",
        "WorkflowState",
        "WorkflowContext",
        "ToolStep",
        "ConditionStep", 
        "ParallelStep",
        "create_tool_step",
    ])

if server_available:
    __all__.extend(["APIServer", "MCPServer"])

if plugin_available:
    __all__.extend([
        "BasePlugin",
        "PluginType", 
        "plugin",
        "PluginRegistry",
        "PluginRegistryError",
        "PluginLoader",
        "PluginLoaderError",
    ])

__version__ = "0.1.0"
