"""Conversation management for orchestrator."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """A conversation message."""

    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """Manages conversation history and context for the orchestrator."""

    def __init__(self, max_messages: int = 50):
        """Initialize conversation manager.

        Args:
            max_messages: Maximum number of messages to keep in history
        """
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.context: Dict[str, Any] = {}

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a message to the conversation.

        Args:
            role: Message role (user, assistant, system, tool)
            content: Message content
            metadata: Optional metadata for the message
        """
        message = Message(role=role, content=content, metadata=metadata or {})

        self.messages.append(message)

        # Maintain max message limit
        if len(self.messages) > self.max_messages:
            # Remove oldest non-system messages
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]

            # Keep all system messages and recent other messages
            keep_count = self.max_messages - len(system_messages)
            self.messages = system_messages + other_messages[-keep_count:]

    def get_messages(self, include_metadata: bool = False) -> List[Dict[str, str]]:
        """Get conversation messages in LLM format.

        Args:
            include_metadata: Whether to include metadata in output

        Returns:
            List of message dictionaries
        """
        result = []

        for message in self.messages:
            msg_dict = {"role": message.role, "content": message.content}

            if include_metadata and message.metadata:
                msg_dict["metadata"] = message.metadata

            result.append(msg_dict)

        return result

    def get_recent_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent messages.

        Args:
            count: Number of recent messages to return

        Returns:
            List of recent message dictionaries
        """
        recent_messages = (
            self.messages[-count:] if len(self.messages) > count else self.messages
        )
        return self.get_messages()[-count:]

    def add_tool_result(self, tool_name: str, result: Any, success: bool = True):
        """Add a tool execution result to conversation.

        Args:
            tool_name: Name of the tool that was executed
            result: Tool execution result
            success: Whether the tool execution was successful
        """
        content = f"Tool '{tool_name}' executed successfully: {result}"
        if not success:
            content = f"Tool '{tool_name}' failed: {result}"

        self.add_message(
            role="tool",
            content=content,
            metadata={"tool_name": tool_name, "success": success, "result": result},
        )

    def set_context(self, key: str, value: Any):
        """Set a context value.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value
        """
        return self.context.get(key, default)

    def clear_context(self):
        """Clear all context values."""
        self.context.clear()

    def clear(self):
        """Clear conversation history and context."""
        self.messages.clear()
        self.context.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary.

        Returns:
            Dictionary with conversation statistics
        """
        return {
            "total_messages": len(self.messages),
            "user_messages": len([m for m in self.messages if m.role == "user"]),
            "assistant_messages": len(
                [m for m in self.messages if m.role == "assistant"]
            ),
            "tool_messages": len([m for m in self.messages if m.role == "tool"]),
            "context_keys": list(self.context.keys()),
            "oldest_message": self.messages[0].timestamp if self.messages else None,
            "newest_message": self.messages[-1].timestamp if self.messages else None,
        }
