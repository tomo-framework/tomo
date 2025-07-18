# Next.js Integration Guide

This guide shows how to integrate Tomo with a Next.js application, including API routes, client components, and deployment to Vercel.

## 🏗️ Project Setup

### 1. Create Next.js App
```bash
npx create-next-app@latest tomo-next --typescript
cd tomo-next
```

### 2. Install Dependencies
```bash
npm install ai @modelcontextprotocol/sdk
npm install --save-dev @types/node-fetch
```

### 3. Add Tomo MCP Client
Create `lib/tomo-mcp-client.ts` (from previous docs).

## 🔌 Integration Implementation

### Server-Side (API Route)
Create `app/api/tomo/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { TomoMCPClient } from '@/lib/tomo-mcp-client';

const tomoClient = new TomoMCPClient(process.env.TOMO_MCP_URL);

export async function GET() {
  await tomoClient.connect();
  const tools = await tomoClient.listTools();
  tomoClient.disconnect();
  return NextResponse.json({ tools });
}

export async function POST(req: NextRequest) {
  const { toolName, inputs } = await req.json();
  await tomoClient.connect();
  const result = await tomoClient.executeTool(toolName, inputs);
  tomoClient.disconnect();
  return NextResponse.json({ result });
}
```

### Client-Side Component
Create `app/page.tsx`:
```typescript
import { useState } from 'react';

export default function Home() {
  const [tools, setTools] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);

  const loadTools = async () => {
    const res = await fetch('/api/tomo');
    const data = await res.json();
    setTools(data.tools);
  };

  const executeTool = async (toolName: string, inputs: any) => {
    const res = await fetch('/api/tomo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ toolName, inputs })
    });
    const data = await res.json();
    setResult(data.result);
  };

  return (
    <div>
      <button onClick={loadTools}>Load Tools</button>
      <ul>
        {tools.map(tool => (
          <li key={tool.name}>{tool.name}: {tool.description}</li>
        ))}
      </ul>
      <button onClick={() => executeTool('Calculator', { operation: 'add', a: 5, b: 3 })}>
        Run Calculator
      </button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

## 🚀 Deployment to Vercel

1. Commit changes and push to GitHub.
2. Create new Vercel project linked to your repo.
3. Add environment variables in Vercel dashboard.
4. Deploy Tomo server separately (e.g., on Render) and set TOMO_MCP_URL.

## 🔧 Advanced Configuration

- **Streaming Support**: Add streaming for real-time responses.
- **Authentication**: Implement JWT auth for API routes.
- **Error Handling**: Add global error boundaries.

See [Examples](./examples/applications.md#nextjs-chat-app) for full application code. 