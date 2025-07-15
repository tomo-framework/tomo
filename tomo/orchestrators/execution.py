"""Execution engine for tool orchestration."""

import asyncio
from typing import Any, Dict, List, Optional
from ..core.runner import ToolRunner
from ..adapters.base import BaseAdapter


class ExecutionEngine:
    """Engine for executing tools with retry logic and error handling."""

    def __init__(self, runner: ToolRunner, adapter: BaseAdapter):
        """Initialize execution engine.

        Args:
            runner: Tool runner for executing tools
            adapter: Adapter for converting LLM formats
        """
        self.runner = runner
        self.adapter = adapter

    async def execute_tool(self, tool_call: Dict[str, Any]) -> Any:
        """Execute a single tool.

        Args:
            tool_call: Tool call from LLM

        Returns:
            Tool execution result
        """
        # Convert tool call to Tomo format
        converted = self.adapter.convert_tool_call(tool_call)
        tool_name = converted["tool_name"]
        inputs = converted["inputs"]

        # Execute tool
        try:
            result = self.runner.run_tool(tool_name, inputs)
            return result
        except Exception as e:
            raise ExecutionError(f"Tool '{tool_name}' execution failed: {str(e)}")

    async def execute_tools_parallel(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tools in parallel.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of execution results
        """
        tasks = []
        for tool_call in tool_calls:
            task = asyncio.create_task(self._execute_tool_with_retry(tool_call))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "tool": tool_calls[i].get("name", "unknown"),
                        "success": False,
                        "error": str(result),
                    }
                )
            else:
                processed_results.append(
                    {
                        "tool": tool_calls[i].get("name", "unknown"),
                        "success": True,
                        "result": result,
                    }
                )

        return processed_results

    async def execute_tools_sequential(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple tools sequentially.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of execution results
        """
        results = []

        for tool_call in tool_calls:
            try:
                result = await self._execute_tool_with_retry(tool_call)
                results.append(
                    {
                        "tool": tool_call.get("name", "unknown"),
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "tool": tool_call.get("name", "unknown"),
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    async def _execute_tool_with_retry(
        self, tool_call: Dict[str, Any], max_retries: int = 3
    ) -> Any:
        """Execute tool with retry logic.

        Args:
            tool_call: Tool call to execute
            max_retries: Maximum number of retry attempts

        Returns:
            Tool execution result
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await self.execute_tool(tool_call)
            except Exception as e:
                last_exception = e

                if attempt < max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    break

        raise last_exception

    def validate_tool_call(self, tool_call: Dict[str, Any]) -> bool:
        """Validate a tool call before execution.

        Args:
            tool_call: Tool call to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            converted = self.adapter.convert_tool_call(tool_call)
            tool_name = converted["tool_name"]
            inputs = converted["inputs"]

            return self.runner.validate_tool_inputs(tool_name, inputs)
        except Exception:
            return False


class ExecutionError(Exception):
    """Exception raised when tool execution fails."""

    pass
