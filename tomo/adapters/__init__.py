"""Adapters for different LLM providers."""

from .openai import OpenAIAdapter

try:
    from .anthropic import AnthropicAdapter
    __all__ = ["OpenAIAdapter", "AnthropicAdapter"]
except ImportError:
    __all__ = ["OpenAIAdapter"] 