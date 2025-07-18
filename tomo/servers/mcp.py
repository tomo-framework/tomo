"""Model Context Protocol (MCP) server for Tomo tools.

This module provides an MCP-compliant server that exposes Tomo tools
using the Model Context Protocol, allowing AI agents to discover and execute tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
import websockets
from websockets.server import serve, WebSocketServerProtocol

from ..core.registry import ToolRegistry
from ..core.runner import ToolRunner, ToolNotFoundError, ToolValidationError, ToolExecutionError


logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base class for MCP-specific errors."""
    
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class MCPServer:
    """Model Context Protocol server for Tomo tools.
    
    Implements the MCP specification using JSON-RPC 2.0 over WebSockets,
    allowing AI agents to discover and execute tools remotely.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        server_name: str = "tomo-mcp-server",
        server_version: str = "0.1.0",
    ) -> None:
        """Initialize the MCP server.
        
        Args:
            registry: Tool registry containing available tools
            server_name: Name of the MCP server
            server_version: Version of the MCP server
        """
        self.registry = registry
        self.runner = ToolRunner(registry)
        self.server_name = server_name
        self.server_version = server_version
        
        # MCP protocol information
        self.protocol_version = "2024-11-05"
        self.capabilities = {
            "tools": {"listChanged": True},
            "resources": {},
            "prompts": {},
        }

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle a new client connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        logger.info(f"New MCP client connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    # Parse JSON-RPC message
                    data = json.loads(message)
                    response = await self._handle_message(data)
                    
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    error_response = self._create_error_response(
                        None, -32700, "Parse error"
                    )
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    error_response = self._create_error_response(
                        None, -32603, "Internal error"
                    )
                    await websocket.send(json.dumps(error_response))
        except websockets.exceptions.ConnectionClosed:
            logger.info("MCP client disconnected")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")

    async def _handle_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a JSON-RPC message.
        
        Args:
            data: Parsed JSON-RPC message
            
        Returns:
            Response message or None for notifications
        """
        # Validate JSON-RPC structure
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return self._create_error_response(
                data.get("id"), -32600, "Invalid Request"
            )
        
        method = data.get("method")
        params = data.get("params", {})
        message_id = data.get("id")
        
        # Handle different MCP methods
        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "ping":
                result = {}
            else:
                return self._create_error_response(
                    message_id, -32601, f"Method not found: {method}"
                )
            
            # Return success response for requests (not notifications)
            if message_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result
                }
            
        except MCPError as e:
            return self._create_error_response(message_id, e.code, e.message, e.data)
        except Exception as e:
            logger.error(f"Error handling method {method}: {e}")
            return self._create_error_response(
                message_id, -32603, "Internal error", str(e)
            )
        
        return None

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request.
        
        Args:
            params: Initialize parameters
            
        Returns:
            Initialize response
        """
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion")
        
        logger.info(f"Initializing MCP session with client: {client_info}")
        
        # Validate protocol version
        if protocol_version != self.protocol_version:
            logger.warning(f"Protocol version mismatch: {protocol_version} vs {self.protocol_version}")
        
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
            },
        }

    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request.
        
        Args:
            params: List parameters
            
        Returns:
            List of available tools
        """
        tools = []
        
        for tool_name in self.registry.list():
            tool_class = self.registry.get(tool_name)
            if tool_class:
                # Convert Tomo tool to MCP tool format
                schema = tool_class.get_schema()
                
                mcp_tool = {
                    "name": tool_name,
                    "description": tool_class.get_description(),
                    "inputSchema": schema.get("function", {}).get("parameters", {}),
                }
                
                tools.append(mcp_tool)
        
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request.
        
        Args:
            params: Tool call parameters
            
        Returns:
            Tool execution result
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise MCPError(-32602, "Missing tool name")
        
        try:
            # Execute the tool
            result = self.runner.run_tool(tool_name, arguments)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result) if not isinstance(result, str) else result
                    }
                ]
            }
            
        except ToolNotFoundError as e:
            raise MCPError(-32602, f"Tool not found: {tool_name}")
        except ToolValidationError as e:
            raise MCPError(-32602, f"Invalid arguments: {str(e)}")
        except ToolExecutionError as e:
            raise MCPError(-32603, f"Tool execution failed: {str(e)}")

    def _create_error_response(
        self,
        message_id: Optional[Union[str, int]],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Create a JSON-RPC error response.
        
        Args:
            message_id: Request ID
            code: Error code
            message: Error message
            data: Optional error data
            
        Returns:
            JSON-RPC error response
        """
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": error,
        }

    def run(
        self,
        host: str = "localhost",
        port: int = 8001,
        log_level: str = "info",
    ) -> None:
        """Run the MCP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            log_level: Logging level
        """
        logging.basicConfig(level=getattr(logging, log_level.upper()))
        
        logger.info(f"Starting MCP server on {host}:{port}")
        logger.info(f"Registered tools: {self.registry.list()}")
        
        async def start_server():
            async with serve(
                self.handle_client,
                host,
                port,
                ping_interval=30,
                ping_timeout=10,
            ):
                logger.info(f"MCP server listening on ws://{host}:{port}")
                await asyncio.Future()  # Run forever
        
        asyncio.run(start_server())

    async def start_async(
        self,
        host: str = "localhost",
        port: int = 8001,
    ) -> None:
        """Start the server asynchronously.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        logger.info(f"Starting MCP server on {host}:{port}")
        logger.info(f"Registered tools: {self.registry.list()}")
        
        async with serve(
            self.handle_client,
            host,
            port,
            ping_interval=30,
            ping_timeout=10,
        ):
            logger.info(f"MCP server listening on ws://{host}:{port}")
            await asyncio.Future()  # Run forever 