# TypeScript Integration Overview

Tomo is a Python-based framework, but it can be integrated with TypeScript applications through several methods. This guide provides an overview of the available integration options, their use cases, and trade-offs.

## 🎯 Integration Methods

### 1. REST API Integration
**Description**: Use Tomo's built-in RESTful API server to expose tools and orchestration endpoints.

**Key Features**:
- Simple HTTP calls from TypeScript
- Tool execution via POST requests
- Orchestration support
- Easy to implement

**Use Cases**:
- Basic tool execution
- Non-real-time applications
- Simple web apps

**Pros**:
- Easy setup
- No WebSocket complexity
- Works with any HTTP client

**Cons**:
- No automatic tool discovery
- Manual schema handling
- Latency from HTTP requests

**Implementation Complexity**: Low

### 2. MCP (Model Context Protocol) Integration
**Description**: Use Tomo's MCP server for dynamic tool discovery and execution via WebSockets.

**Key Features**:
- Automatic tool schema export
- Real-time communication
- JSON-RPC protocol
- Built for AI agent integration

**Use Cases**:
- AI applications with dynamic tools
- Vercel AI SDK integration
- Real-time tool execution

**Pros**:
- Dynamic tool discovery
- Standardized protocol
- Better for AI workflows

**Cons**:
- Requires WebSocket handling
- More complex client implementation
- Persistent connections needed

**Implementation Complexity**: Medium

### 3. Subprocess Integration
**Description**: Run Tomo as a Python subprocess from Node.js.

**Key Features**:
- Direct execution without network
- Stdio communication
- Full control over process

**Use Cases**:
- Desktop applications
- When network overhead is unacceptable
- Tight integration needed

**Pros**:
- Low latency
- No network dependencies
- Secure (no exposed ports)

**Cons**:
- Complex error handling
- Process management required
- Platform-specific issues

**Implementation Complexity**: High

### 4. Serverless Integration (Vercel Functions)
**Description**: Deploy Tomo in serverless environments with TypeScript wrappers.

**Key Features**:
- Scalable deployment
- Edge function support
- Easy Vercel integration

**Use Cases**:
- Cloud-native applications
- Scalable AI services
- Vercel-hosted apps

**Pros**:
- Automatic scaling
- Global distribution
- Easy deployment

**Cons**:
- Cold starts
- Execution limits
- More complex setup

**Implementation Complexity**: Medium-High

## 📊 Comparison Matrix

| Feature | REST API | MCP | Subprocess | Serverless |
|---------|----------|-----|------------|------------|
| **Latency** | Medium | Low | Lowest | Variable |
| **Complexity** | Low | Medium | High | Medium |
| **Scalability** | High | High | Low | Highest |
| **Real-time** | No | Yes | Yes | Partial |
| **Tool Discovery** | Manual | Automatic | Manual | Manual |
| **AI Integration** | Basic | Excellent | Good | Good |
| **Security** | HTTP Auth | WS Auth | High | Cloud-dependent |

## 🛤️ Choosing an Integration

- **Start with REST API** if you're new to Tomo or need simple integration.
- **Use MCP** for AI-focused applications, especially with Vercel AI SDK.
- **Choose Subprocess** for desktop/CLI tools where performance is critical.
- **Go Serverless** for production web applications on Vercel.

## ⚠️ Common Considerations

- **Cross-language Communication**: Always handle JSON serialization/deserialization carefully.
- **Error Handling**: Implement robust error catching for Python-Node.js interactions.
- **Performance**: Monitor and optimize for cross-process communication overhead.
- **Security**: Use authentication and validate inputs when exposing endpoints.
- **Dependencies**: Ensure Python environment is properly managed in production.

## 🔗 Next Steps

1. Review the [Setup Guide](./setup.md) for installation instructions.
2. Try the [Quick Start](./quickstart.md) for a hands-on introduction.
3. Explore specific integrations:
   - [Next.js Guide](./nextjs-integration.md)
   - [Vercel AI SDK Guide](./vercel-ai-sdk.md) 