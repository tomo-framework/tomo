"""Tomo - Tool-Oriented Micro Orchestrator

A lightweight, language-model-agnostic framework for defining, registering,
and executing typed tools.
"""

from tomo.core.tool import BaseTool, tool
from tomo.core.registry import ToolRegistry
from tomo.core.runner import ToolRunner

__version__ = "0.1.0"
__all__ = [
    "BaseTool",
    "tool", 
    "ToolRegistry",
    "ToolRunner",
] 