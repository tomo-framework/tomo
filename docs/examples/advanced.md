# Advanced Examples

Complex integration patterns and use cases.

## AI SDK Tool Calling
```typescript
// Advanced tool calling with retries
import { retry } from 'ts-retry';

async function callToolWithRetry(toolName: string, inputs: any) {
  return retry(async () => {
    return await executeTomoTool(toolName, inputs);
  }, { maxRetries: 3, delay: 1000 });
}
```

## Streaming Response Handling
```typescript
// Handle streaming from API route
const stream = new ReadableStream({
  async start(controller) {
    // Streaming logic...
  }
});
```

## Custom Tool Integration
Create custom Python tool and expose via MCP.

For full apps, see [Applications](./applications.md). 