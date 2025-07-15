"""LLM orchestrator for intelligent tool execution."""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from ..core.registry import ToolRegistry
from ..core.runner import ToolRunner
from ..adapters.base import BaseAdapter
from .conversation import ConversationManager
from .execution import ExecutionEngine


@dataclass
class OrchestrationConfig:
    """Configuration for LLM orchestrator."""

    max_iterations: int = 5
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    custom_instructions: Optional[str] = None
    enable_memory: bool = True
    enable_retry: bool = True
    max_retries: int = 3


class LLMOrchestrator:
    """Intelligent orchestrator that uses LLM to select and execute tools."""

    def __init__(
        self,
        llm_client: Any,
        registry: ToolRegistry,
        adapter: BaseAdapter,
        config: Optional[OrchestrationConfig] = None,
    ):
        """Initialize the orchestrator.

        Args:
            llm_client: LLM client for making API calls
            registry: Tool registry containing available tools
            adapter: Adapter for converting between LLM formats
            config: Orchestration configuration
        """
        self.llm_client = llm_client
        self.registry = registry
        self.adapter = adapter
        self.config = config or OrchestrationConfig()

        # Initialize components
        self.runner = ToolRunner(registry)
        self.conversation = ConversationManager() if self.config.enable_memory else None
        self.execution_engine = ExecutionEngine(self.runner, self.adapter)

        # Create system prompt
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the orchestrator."""
        base_prompt = self.adapter.create_system_prompt(
            self.registry, custom_instructions=self.config.custom_instructions
        )

        orchestration_instructions = """
You are an intelligent tool orchestrator. Your job is to:

1. ANALYZE the user's request to understand their intent
2. SELECT the most appropriate tool(s) from the available options
3. EXECUTE tools with the correct parameters
4. HANDLE multi-step workflows when needed
5. PROVIDE clear, helpful responses

IMPORTANT RULES:
- Always use tools when they can help accomplish the user's goal
- If multiple tools are needed, execute them in logical order
- Provide context and explanations for your actions
- If a tool fails, try alternative approaches or explain the issue
- Keep responses concise but informative

Available tools are listed below:
"""

        return orchestration_instructions + "\n" + base_prompt

    async def run(self, user_input: str) -> str:
        """Run the orchestrator with user input.

        Args:
            user_input: The user's request or question

        Returns:
            The orchestrator's response
        """
        # Add user input to conversation history
        if self.conversation:
            self.conversation.add_message("user", user_input)

        # Initialize execution context
        context: Dict[str, Any] = {
            "user_input": user_input,
            "iteration": 0,
            "executed_tools": [],
            "results": [],
        }

        # Main orchestration loop
        while context["iteration"] < self.config.max_iterations:
            context["iteration"] += 1

            # Get LLM response with tool selection
            llm_response = await self._get_llm_response(context)

            # Check if LLM wants to use tools
            tool_calls = self._extract_tool_calls(llm_response)

            if not tool_calls:
                # No tools needed, return final response
                final_response = self._extract_final_response(llm_response)
                if self.conversation:
                    self.conversation.add_message("assistant", final_response)
                return final_response

            # Execute tools
            tool_results = await self._execute_tools(tool_calls, context)

            # Add results to context
            if isinstance(context["executed_tools"], list):
                context["executed_tools"].extend([call.get("name", "unknown") for call in tool_calls])
            if isinstance(context["results"], list):
                context["results"].extend(tool_results)

            # Check if we should continue or finish
            if self._should_continue(tool_results, context):
                continue
            else:
                break

        # Generate final response
        final_response = await self._generate_final_response(context)

        if self.conversation:
            self.conversation.add_message("assistant", final_response)

        return final_response

    async def _get_llm_response(self, context: Dict[str, Any]) -> str:
        """Get response from LLM with tool selection."""
        # Build messages for LLM
        messages = self._build_messages(context)

        # Get tool schemas
        tools = self.adapter.export_tools(self.registry)

        # Call LLM
        try:
            if hasattr(self.llm_client, "chat"):
                # OpenAI-style client
                response = await self.llm_client.chat.completions.create(
                    model=getattr(self.llm_client, "model", "gpt-4"),
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content or ""
            else:
                # Generic client - implement based on your LLM client
                raise NotImplementedError("LLM client not supported")

        except Exception as e:
            return f"Error getting LLM response: {str(e)}"

    def _build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build messages for LLM conversation."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history if available
        if self.conversation:
            conv_messages = self.conversation.get_messages()
            # Convert to the expected format
            for msg in conv_messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append({"role": str(msg["role"]), "content": str(msg["content"])})

        # Add current context
        if context["results"]:
            context_summary = self._summarize_context(context)
            messages.append(
                {
                    "role": "user",
                    "content": f"Context from previous steps: {context_summary}\n\nUser request: {context['user_input']}",
                }
            )
        else:
            messages.append({"role": "user", "content": context["user_input"]})

        return messages

    def _extract_tool_calls(self, llm_response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        # This is a simplified implementation
        # In practice, you'd parse the actual LLM response format
        tool_calls: List[Dict[str, Any]] = []

        # Look for tool call patterns in the response
        if "tool_call" in llm_response.lower() or "function" in llm_response.lower():
            # Parse tool calls from response
            # This would need to be implemented based on your LLM's response format
            pass

        return tool_calls

    def _extract_final_response(self, llm_response: str) -> str:
        """Extract final response from LLM output."""
        # Remove any tool call information and return the final response
        return llm_response.strip()

    async def _execute_tools(
        self, tool_calls: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tools and return results."""
        results = []

        for tool_call in tool_calls:
            try:
                result = await self.execution_engine.execute_tool(tool_call)
                results.append(
                    {"tool": tool_call.get("name", "unknown"), "success": True, "result": result}
                )
            except Exception as e:
                results.append(
                    {"tool": tool_call.get("name", "unknown"), "success": False, "error": str(e)}
                )

        return results

    def _should_continue(
        self, tool_results: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> bool:
        """Determine if orchestration should continue."""
        # Continue if there were successful tool executions and we haven't hit max iterations
        successful_tools = [r for r in tool_results if r["success"]]
        return (
            len(successful_tools) > 0
            and context["iteration"] < self.config.max_iterations
        )

    async def _generate_final_response(self, context: Dict[str, Any]) -> str:
        """Generate final response based on execution results."""
        if not context["results"]:
            return "I couldn't find any tools to help with your request."

        # Summarize what was accomplished
        successful_results = [r for r in context["results"] if r["success"]]
        failed_results = [r for r in context["results"] if not r["success"]]

        response_parts = []

        if successful_results:
            response_parts.append("I've completed the following actions:")
            for result in successful_results:
                response_parts.append(f"- {result['tool']}: {result['result']}")

        if failed_results:
            response_parts.append("\nSome actions couldn't be completed:")
            for result in failed_results:
                response_parts.append(f"- {result['tool']}: {result['error']}")

        return "\n".join(response_parts)

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Summarize execution context for LLM."""
        if not context["results"]:
            return "No previous actions taken."

        summary_parts = []
        for result in context["results"]:
            if result["success"]:
                summary_parts.append(f"{result['tool']}: {result['result']}")
            else:
                summary_parts.append(f"{result['tool']}: failed - {result['error']}")

        return "; ".join(summary_parts)

    def reset_conversation(self) -> None:
        """Reset conversation history."""
        if self.conversation:
            self.conversation.clear()

    def get_conversation_history(self) -> List[Dict[str, Union[str, Dict[str, Any]]]]:
        """Get conversation history."""
        if self.conversation:
            return self.conversation.get_messages()
        return []
