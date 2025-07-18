# Vercel AI SDK Integration Guide

Integrate Tomo tools with Vercel AI SDK for powerful AI applications with tool calling capabilities.

## 🛠️ Setup

1. Install Vercel AI SDK:
```bash
npm install ai
```

2. Add Tomo MCP Client (from setup guide).

## 🔗 Integration

### AI Provider Configuration
```typescript
// lib/ai-provider.ts
import { createAI } from 'ai';
import { TomoMCPClient } from './tomo-mcp-client';

const tomoClient = new TomoMCPClient();

export const ai = createAI({
  actions: {
    async getTools() {
      'use server';
      await tomoClient.connect();
      return await tomoClient.getToolSchemas();
    },
    async callTool(toolName: string, inputs: any) {
      'use server';
      return await tomoClient.executeTool(toolName, inputs);
    }
  }
});
```

### Chat Component with Tool Calling
```typescript
// components/ai-chat.tsx
import { useAIState, useActions } from 'ai/rsc';
import { useEffect, useState } from 'react';

export function AIChat() {
  const [input, setInput] = useState('');
  const aiState = useAIState();
  const { getTools, callTool } = useActions();
  const [tools, setTools] = useState<any[]>([]);

  useEffect(() => {
    const loadTools = async () => {
      const tomoTools = await getTools();
      setTools(tomoTools);
    };
    loadTools();
  }, [getTools]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newMessage = { role: 'user', content: input };
    aiState.update([...aiState.get(), newMessage]);
    setInput('');

    // Simulate AI response with tool calling
    const response = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ messages: aiState.get(), tools })
    });

    const reader = response.body?.getReader();
    // Handle streaming response...
  };

  return (
    // Chat UI implementation...
  );
}
```

### API Route for Chat
Create `app/api/chat/route.ts` (from previous responses).

## 🎯 Best Practices

- Cache tool schemas to reduce latency.
- Implement retry logic for tool calls.
- Handle streaming responses properly.
- Monitor token usage.

See [Examples](./examples/advanced.md#ai-sdk-tool-calling) for advanced patterns. 