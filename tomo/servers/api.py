"""RESTful API server for Tomo tools.

This module provides a FastAPI-based HTTP server that exposes Tomo tools
as REST endpoints, allowing external systems to discover and execute tools.
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.registry import ToolRegistry
from ..core.runner import ToolRunner, ToolNotFoundError, ToolValidationError, ToolExecutionError


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    
    inputs: Dict[str, Any] = Field(description="Input parameters for the tool")


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    
    success: bool = Field(description="Whether the execution was successful")
    result: Optional[Any] = Field(default=None, description="The execution result")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class ToolInfo(BaseModel):
    """Information about a tool."""
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    schema: Dict[str, Any] = Field(description="Tool parameter schema")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(description="Server status")
    tools_count: int = Field(description="Number of registered tools")
    version: str = Field(description="Server version")


class APIServer:
    """RESTful API server for Tomo tools.
    
    Provides HTTP endpoints for tool discovery and execution using FastAPI.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        title: str = "Tomo API Server",
        description: str = "RESTful API for Tomo tool execution",
        version: str = "0.1.0",
        enable_cors: bool = True,
    ) -> None:
        """Initialize the API server.
        
        Args:
            registry: Tool registry containing available tools
            title: API title for documentation
            description: API description for documentation
            version: API version
            enable_cors: Whether to enable CORS middleware
        """
        self.registry = registry
        self.runner = ToolRunner(registry)
        
        # Create FastAPI app
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            docs_url="/docs",
            redoc_url="/redoc",
        )
        
        # Enable CORS if requested
        if enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Register endpoints
        self._register_endpoints()

    def _register_endpoints(self) -> None:
        """Register API endpoints."""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check() -> HealthResponse:
            """Health check endpoint."""
            return HealthResponse(
                status="healthy",
                tools_count=len(self.registry),
                version="0.1.0"
            )

        @self.app.get("/tools", response_model=List[ToolInfo])
        async def list_tools() -> List[ToolInfo]:
            """List all available tools."""
            tools = []
            for tool_name in self.registry.list():
                schema = self.registry.get_schema(tool_name)
                tool_class = self.registry.get(tool_name)
                
                if schema and tool_class:
                    tools.append(ToolInfo(
                        name=tool_name,
                        description=tool_class.get_description(),
                        schema=schema
                    ))
            
            return tools

        @self.app.get("/tools/{tool_name}", response_model=ToolInfo)
        async def get_tool(tool_name: str) -> ToolInfo:
            """Get information about a specific tool."""
            tool_class = self.registry.get(tool_name)
            schema = self.registry.get_schema(tool_name)
            
            if not tool_class or not schema:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            
            return ToolInfo(
                name=tool_name,
                description=tool_class.get_description(),
                schema=schema
            )

        @self.app.post("/tools/{tool_name}/execute", response_model=ToolExecutionResponse)
        async def execute_tool(
            tool_name: str, 
            request: ToolExecutionRequest
        ) -> ToolExecutionResponse:
            """Execute a tool with given inputs."""
            try:
                result = self.runner.run_tool(tool_name, request.inputs)
                return ToolExecutionResponse(
                    success=True,
                    result=result,
                    error=None
                )
            except ToolNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ToolValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except ToolExecutionError as e:
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        @self.app.post("/tools/{tool_name}/validate", response_model=Dict[str, Any])
        async def validate_tool_inputs(
            tool_name: str,
            request: ToolExecutionRequest
        ) -> Dict[str, Any]:
            """Validate tool inputs without executing."""
            try:
                is_valid = self.runner.validate_tool_inputs(tool_name, request.inputs)
                return {
                    "valid": is_valid,
                    "tool_name": tool_name,
                    "inputs": request.inputs
                }
            except ToolNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                return {
                    "valid": False,
                    "tool_name": tool_name,
                    "inputs": request.inputs,
                    "error": str(e)
                }

        @self.app.get("/tools/{tool_name}/schema")
        async def get_tool_schema(tool_name: str) -> Dict[str, Any]:
            """Get the JSON schema for a tool."""
            schema = self.registry.get_schema(tool_name)
            if not schema:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            return schema

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        log_level: str = "info",
        reload: bool = False,
    ) -> None:
        """Run the API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            log_level: Logging level
            reload: Enable auto-reload for development
        """
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=log_level,
            reload=reload,
        )

    async def start_async(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        log_level: str = "info",
    ) -> None:
        """Start the server asynchronously.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            log_level: Logging level
        """
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level=log_level,
        )
        server = uvicorn.Server(config)
        await server.serve()

    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app 