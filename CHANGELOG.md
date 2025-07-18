# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-17

### 🚀 Added

**Workflow Engine**
- Complete declarative workflow system for multi-step process orchestration
- Multiple workflow step types: Tool, Condition, Parallel, Loop, DataTransform, Delay, Script, Webhook, Email
- Dependency management with topological sorting
- Event-driven execution with hooks and callbacks
- Retry logic and error recovery
- Context sharing between steps with variable interpolation
- `WorkflowEngine`, `Workflow`, `WorkflowStep`, `WorkflowState`, and `WorkflowContext` classes
- Comprehensive workflow demonstrations in `examples/workflow_demo.py`

**Plugin System**
- Extensible architecture for custom tools, adapters, workflow steps, and servers
- Auto-discovery of plugins from packages and directories
- Configuration-based plugin loading with JSON configs (`sample_plugins.json`)
- Plugin validation and dependency checking
- `BasePlugin`, `PluginRegistry`, `PluginLoader` with comprehensive error handling
- Plugin management through CLI commands

**Server Infrastructure**
- RESTful API server (`APIServer`) with FastAPI and automatic OpenAPI documentation
- Model Context Protocol (MCP) server (`MCPServer`) for AI agent integration
- WebSocket support for real-time tool execution
- CORS support and security middleware
- Health check endpoints and monitoring capabilities

**CLI Enhancements**
- `tomo workflow` - Execute declarative workflows from files
- `tomo workflow-demo` - Run workflow engine demonstrations
- `tomo serve-api` - Start RESTful API server with auto-reload
- `tomo serve-mcp` - Start MCP server for AI agents
- `tomo plugin` - Comprehensive plugin management (list, load, validate, configure)
- Enhanced existing commands with better error handling and formatting

**Documentation System**
- Complete TypeScript integration guides in `docs/` directory
- Next.js integration examples with Vercel AI SDK
- MCP protocol implementation guide
- Setup, quickstart, and troubleshooting documentation
- Configuration reference and API documentation
- Production-ready code examples with error handling

**Examples and Demonstrations**
- `examples/plugin_demo.py` - Plugin system demonstration
- `examples/server_demo.py` - Server infrastructure examples
- `examples/workflow_demo.py` - Comprehensive workflow patterns
- `examples/plugins/` - Sample custom plugins (data tools, web tools, custom adapters)
- Python tool examples with calculator, weather, text processing, and validation

**Testing and Quality**
- Comprehensive test suite for workflow engine (`tests/test_workflow.py`)
- 855 lines of workflow tests covering all step types and error scenarios
- Enhanced development tooling with Black, Ruff, MyPy configuration
- Pre-commit hooks and code quality checks

### 🔧 Changed

**Package Configuration**
- **BREAKING**: Package name changed from `tomo` to `tomo-framework` for PyPI publication
- Import name remains `tomo` (install: `pip install tomo-framework`, import: `import tomo`)
- Updated project URLs with changelog, bug reports, and source code links
- Enhanced optional dependencies for different feature sets (cli, orchestrator, server, mcp, all)
- Added development dependencies for building and publishing

**Core API Enhancements**
- Enhanced `tomo/__init__.py` with conditional imports for optional components
- Improved error handling in `ToolRunner` with safe execution modes
- Extended `ToolRegistry` with auto-discovery capabilities
- Better type hints and documentation throughout codebase

**CLI Interface**
- Redesigned command structure with clearer help text and examples
- Enhanced output formatting with Rich tables and JSON
- Improved error messages and user feedback
- Added verbose modes for detailed debugging

### 🏗️ Infrastructure

**Development Setup**
- `CONTRIBUTING.md` with comprehensive development guidelines
- `MANIFEST.in` for controlling package file inclusion
- Enhanced `.cursorrules` with documentation exclusions
- Improved linting configuration excluding docs from TypeScript validation

**Build and Release**
- PyPI-ready package configuration with proper metadata
- Automated dependency management with uv
- Build tools integration (build, twine) for package distribution
- Version management and release workflow

### 📚 Documentation

**Comprehensive Guides**
- TypeScript integration with multiple patterns (REST, MCP, subprocess, serverless)
- Next.js chat application examples with streaming responses
- MCP client implementation with automatic reconnection and timeout handling
- Setup and installation guides for different environments
- API reference and configuration documentation

**Code Examples**
- Production-ready TypeScript integration code
- Complete Python tool implementations
- Workflow pattern demonstrations
- Plugin development examples

### 🔧 Technical Details

**Workflow Engine Features**
- Supports sequential, parallel, and conditional execution
- Loop processing with item iteration and condition checking
- Data transformation with built-in and custom transformers
- Webhook integration for external system notifications
- Email step for automated notifications
- Script execution step for custom logic
- Delay step for timing control

**Plugin Architecture**
- Support for tool plugins, adapter plugins, workflow step plugins, and server plugins
- Package-based and directory-based plugin discovery
- Configuration validation and error reporting
- Dependency management and conflict resolution

**Server Capabilities**
- FastAPI-based REST API with automatic documentation
- WebSocket-based MCP server following the Model Context Protocol standard
- Tool schema export for different LLM providers
- Request validation and response formatting
- Health monitoring and status endpoints

### 🎯 Impact

This release transforms Tomo from a simple tool execution framework into a comprehensive orchestration platform supporting:

- **Enterprise Workflows**: Declarative multi-step processes with full lifecycle management
- **External Integration**: REST APIs and MCP servers for seamless system integration  
- **Extensibility**: Plugin system enabling custom components and third-party extensions
- **Developer Experience**: Enhanced CLI, comprehensive documentation, and production-ready examples
- **TypeScript Ecosystem**: First-class support for TypeScript and Next.js applications
- **AI Agent Integration**: MCP protocol support for modern AI development workflows

The package is now PyPI-ready as `tomo-framework` with proper semantic versioning and comprehensive optional dependencies for different use cases. 