# API Reference

Documentation for TypeScript client APIs.

## TomoMCPClient

### Methods
- `connect(): Promise<void>` - Establish WebSocket connection
- `listTools(): Promise<any[]>` - Get available tools
- `executeTool(name: string, inputs: any): Promise<any>` - Run tool
- `getToolSchemas(): Promise<any[]>` - Get OpenAI-compatible schemas
- `disconnect(): void` - Close connection

### Example
```typescript
const client = new TomoMCPClient('ws://localhost:8001');
await client.connect();
const schemas = await client.getToolSchemas();
```

## REST API Endpoints

- `GET /tools` - List tools
- `POST /tools/:name/run` - Execute tool
- `POST /orchestrate` - Run orchestration

See OpenAPI spec at `http://localhost:8000/openapi.json`. 