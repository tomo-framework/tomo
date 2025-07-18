# MCP Protocol Guide

The Model Context Protocol (MCP) allows dynamic discovery and execution of Tomo tools in AI applications.

## 📖 MCP Overview

MCP is a WebSocket-based JSON-RPC protocol for:
- Tool discovery
- Schema export
- Remote execution
- Real-time updates

## 🛠️ Implementation

### Client Implementation
Use `@modelcontextprotocol/sdk` or custom WebSocket client.

```typescript
// Custom MCP Client Example
class CustomMCPClient {
  private ws: WebSocket;

  constructor(url: string) {
    this.ws = new WebSocket(url);
  }

  async initialize() {
    return new Promise((resolve, reject) => {
      this.ws.onopen = () => {
        this.ws.send(JSON.stringify({
          jsonrpc: '2.0',
          method: 'initialize',
          params: { protocolVersion: '2024-11-05' },
          id: 1
        }));
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.id === 1) resolve(data);
      };
    });
  }

  // Additional methods...
}
```

### Protocol Methods

- **initialize**: Establish connection
- **tools/list**: Get tool schemas
- **tools/call**: Execute tool
- **ping**: Health check

## 🔒 Security

- Use wss:// for secure connections
- Implement authentication
- Validate all inputs

## 🔍 Debugging

- Use WebSocket inspectors
- Enable verbose logging
- Test with MCP playground tools

See [Troubleshooting](./troubleshooting.md#mcp-issues) for common problems. 