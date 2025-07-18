# Setup Guide

This guide walks you through setting up Tomo for integration with TypeScript, Next.js, and Vercel AI SDK. We'll cover prerequisites, installation, configuration, and basic testing.

## 📋 Prerequisites

### Software Requirements
- **Python 3.10+** (for Tomo)
- **Node.js 18+** (for TypeScript/Next.js)
- **npm/yarn/pnpm** package manager
- **Git** for cloning repositories

### API Keys
- **LLM Provider Keys** (e.g., OPENAI_API_KEY)
- **Optional**: Vercel account for deployment

### Knowledge
- Basic Python and TypeScript
- Familiarity with Next.js (for advanced integration)

## 🛠️ Installation

### 1. Install Tomo (Python)
```bash
# Clone Tomo repository
git clone https://github.com/tomo-framework/tomo.git
cd tomo

# Install with uv (recommended)
uv sync --extra all
uv shell

# Or with pip
pip install -e .[all]
```

### 2. Install TypeScript Dependencies
```bash
# Create TypeScript project (if not existing)
mkdir tomo-ts-integration
cd tomo-ts-integration
npm init -y

# Install core dependencies
npm install typescript ts-node @types/node
npm install --save-dev @types/ws @types/node-fetch

# For Next.js (optional)
npx create-next-app@latest . --typescript

# For Vercel AI SDK (optional)
npm install ai
```

### 3. Install MCP Client (for MCP integration)
```bash
npm install @modelcontextprotocol/sdk
```

## ⚙️ Configuration

### Environment Variables
Create `.env` file in your TypeScript project:
```
# LLM Keys
OPENAI_API_KEY=sk-...

# Tomo Server URLs
TOMO_REST_URL=http://localhost:8000
TOMO_MCP_URL=ws://localhost:8001
```

Load them in TypeScript:
```typescript
import dotenv from 'dotenv';
dotenv.config();
```

### Tomo Configuration
In Tomo directory, configure tools in your module (e.g., `my_tools.py`):
```python
from tomo import tool, BaseTool

@tool
class Calculator(BaseTool):
    # ...
```

## 🏃 Starting Servers

### Start Tomo REST API Server
```bash
tomo serve-api --module my_tools --port 8000
```

### Start Tomo MCP Server
```bash
tomo serve-mcp --module my_tools --port 8001
```

## 🔌 Basic Integration Test

### REST API Test
```typescript
// test-rest.ts
import fetch from 'node-fetch';

async function testRest() {
  const response = await fetch(`${process.env.TOMO_REST_URL}/tools`);
  const tools = await response.json();
  console.log('Available tools:', tools);
}

testRest();
```
Run: `ts-node test-rest.ts`

### MCP Test
```typescript
// test-mcp.ts
import { TomoMCPClient } from './tomo-mcp-client';  // From previous examples

async function testMCP() {
  const client = new TomoMCPClient();
  await client.connect();
  const tools = await client.listTools();
  console.log('Available tools:', tools);
  client.disconnect();
}

testMCP();
```
Run: `ts-node test-mcp.ts`

## 🛡️ Security Configuration

- **API Authentication**: Add to Tomo config (future feature)
- **HTTPS**: Use nginx reverse proxy for production
- **CORS**: Configure in Next.js

## 📦 Production Setup

### Docker
```dockerfile
# Dockerfile for Tomo
FROM python:3.10
COPY . /app
RUN pip install -e .[all]
CMD ["tomo", "serve-mcp", "--module", "my_tools", "--port", "8001"]
```

### Vercel Deployment
1. Deploy Next.js app to Vercel
2. Deploy Tomo as a separate service (e.g., on Render/EC2)
3. Configure environment variables in Vercel dashboard

## 🔍 Troubleshooting

- **Connection refused**: Check if Tomo servers are running
- **Module not found**: Verify --module flag
- **API Key errors**: Check environment variables
- See [Troubleshooting Guide](./troubleshooting.md) for more

## 🔗 Next Steps

- [Quick Start](./quickstart.md)
- [Next.js Integration](./nextjs-integration.md) 