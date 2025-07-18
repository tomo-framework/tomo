# Quick Start Guide

Get Tomo integrated with TypeScript in 5 minutes or less. This guide focuses on MCP integration with Vercel AI SDK for a complete AI tool-calling example.

## ⚡ 5-Minute Setup

### Step 1: Install Tomo
```bash
git clone https://github.com/tomo-framework/tomo.git
cd tomo
uv sync --extra all
uv shell
```

### Step 2: Create TypeScript Project
```bash
mkdir tomo-ts-quickstart
cd tomo-ts-quickstart
npm init -y
npm install ai typescript ts-node @types/node @modelcontextprotocol/sdk
npx tsc --init
```

### Step 3: Create Tomo MCP Client
Create `tomo-mcp-client.ts` (copy from previous responses or documentation).

### Step 4: Create Quickstart Script
```typescript
// quickstart.ts
import { createAI } from 'ai';
import { TomoMCPClient } from './tomo-mcp-client';

const tomoClient = new TomoMCPClient();

async function main() {
  await tomoClient.connect();
  
  const tools = await tomoClient.getToolSchemas();
  
  const ai = createAI({
    actions: {
      async executeTomoTool(toolName: string, inputs: any) {
        return await tomoClient.executeTool(toolName, inputs);
      }
    }
  });
  
  console.log('Available Tomo Tools:', tools.map(t => t.function.name));
  
  // Example: Execute a tool if available
  if (tools.some(t => t.function.name === 'Calculator')) {
    const result = await tomoClient.executeTool('Calculator', {
      operation: 'add',
      a: 5,
      b: 3
    });
    console.log('Calculation Result:', result);
  }
  
  tomoClient.disconnect();
}

main().catch(console.error);
```

### Step 5: Start Tomo MCP Server
In a separate terminal:
```bash
cd ../tomo  # Go to Tomo directory
tomo serve-mcp --module examples.basic_tools --port 8001
```

### Step 6: Run the Quickstart
```bash
ts-node quickstart.ts
```

Expected Output:
```
Available Tomo Tools: [ 'Calculator', 'Weather', ... ]
Calculation Result: 8
```

## 🎯 Next Steps After Quickstart

1. **Add Vercel AI SDK Chat**: Extend to a full chat interface.
2. **Deploy to Vercel**: Add Next.js and deploy.
3. **Custom Tools**: Create your own tools in Python and expose them.

See [Vercel AI SDK Integration](./vercel-ai-sdk.md) for full chat implementation. 