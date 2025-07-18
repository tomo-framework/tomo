# Tomo TypeScript Integration - Code Examples

This directory contains complete, working examples for integrating Tomo (Python) with TypeScript applications.

## 📁 Directory Structure

```
code/
├── python/
│   └── example_tools.py        # Complete Tomo tools in Python
├── typescript/
│   ├── package.json           # TypeScript dependencies
│   ├── tsconfig.json          # TypeScript configuration
│   ├── tomo-mcp-client.ts     # Complete MCP client
│   ├── basic-example.ts       # Basic integration example
│   └── nextjs-example.tsx.example  # Full Next.js chat app
└── README.md                  # This file
```

## 🚀 Quick Start

### Step 1: Set Up Python Side (Tomo Tools)

```bash
# From the main tomo directory
cd /path/to/tomo

# Make sure Tomo is installed
uv sync --extra all
uv shell

# Test the example tools
python docs/examples/code/python/example_tools.py

# Start MCP server with our example tools
tomo serve-mcp --module docs.examples.code.python.example_tools --port 8001
```

### Step 2: Set Up TypeScript Side

```bash
# Navigate to TypeScript examples
cd docs/examples/code/typescript

# Install dependencies
npm install

# Run basic example
npm run dev
```

## 🐍 Python Tools (example_tools.py)

The Python side includes these example tools:

### Calculator
Performs mathematical operations (add, subtract, multiply, divide, power).

```python
@tool
class Calculator(BaseTool):
    operation: str  # add, subtract, multiply, divide, power
    a: float
    b: float
```

### WeatherChecker
Mock weather API (replace with real API in production).

```python
@tool
class WeatherChecker(BaseTool):
    city: str
    country: Optional[str] = None
    units: str = "celsius"
```

### TextProcessor
Text manipulation operations.

```python
@tool
class TextProcessor(BaseTool):
    text: str
    operation: str  # uppercase, lowercase, reverse, word_count, char_count
```

### DataValidator
Validates different data formats.

```python
@tool
class DataValidator(BaseTool):
    value: Any
    validation_type: str  # email, url, positive_number, non_empty_string
```

### NumberSequence
Generates mathematical sequences.

```python
@tool
class NumberSequence(BaseTool):
    sequence_type: str  # fibonacci, prime, even, odd, squares
    count: int
```

### DateTimeUtility
Date and time operations.

```python
@tool
class DateTimeUtility(BaseTool):
    operation: str  # current_time, format_date, add_days
    # ... other optional parameters
```

## 📱 TypeScript Integration

### MCP Client (tomo-mcp-client.ts)

Complete WebSocket-based MCP client with features:

- **Automatic reconnection** with exponential backoff
- **Request timeout handling** (30 seconds)
- **Tool schema export** in OpenAI format
- **Input validation** against schemas
- **Parallel tool execution**
- **Retry logic** with configurable attempts

```typescript
const client = new TomoMCPClient('ws://localhost:8001');
await client.connect();

// List tools
const tools = await client.listTools();

// Execute tool
const result = await client.executeTool('Calculator', {
  operation: 'add',
  a: 5,
  b: 3
});
```

### Tool Manager (TomoToolManager)

Higher-level utility for managing tool interactions:

```typescript
const manager = new TomoToolManager(client);
await manager.initialize();

// Get OpenAI-compatible schemas
const schemas = manager.getSchemas();

// Execute with retry
const result = await manager.executeToolWithRetry('Calculator', inputs, 3);

// Execute multiple tools in parallel
const results = await manager.executeTools([
  { name: 'Calculator', inputs: { operation: 'add', a: 1, b: 2 } },
  { name: 'TextProcessor', inputs: { text: 'hello', operation: 'uppercase' } }
]);
```

## 🖥️ Running the Examples

### Basic Example

```bash
# Terminal 1: Start Tomo MCP server
cd /path/to/tomo
tomo serve-mcp --module docs.examples.code.python.example_tools --port 8001

# Terminal 2: Run TypeScript example
cd docs/examples/code/typescript
npm run dev  # Runs basic-example.ts
```

**Expected Output:**
```
🚀 Starting Basic Tomo Integration Example

📡 Connecting to Tomo MCP server...
✅ Connected successfully!

🔍 Listing available tools...
Available tools:
  - Calculator: Perform basic mathematical calculations.
  - WeatherChecker: Get weather information for a city (mock implementation).
  - TextProcessor: Process text with various operations.
  - DataValidator: Validate data against various criteria.
  - NumberSequence: Generate number sequences.
  - DateTimeUtility: Utility for date and time operations.

🧮 Testing Calculator tool...
Calculator result: 15 + 25 = 40

🌤️  Testing Weather tool...
Weather result: {
  "city": "Tokyo",
  "country": "Japan",
  "temperature": 23,
  "units": "celsius",
  "condition": "sunny",
  "humidity": 65,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Next.js Example Setup

For the full Next.js chat application:

```bash
# Create new Next.js project
npx create-next-app@latest tomo-chat --typescript --tailwind --app

# Copy the example files
cp nextjs-example.tsx.example tomo-chat/app/page.tsx
cp tomo-mcp-client.ts tomo-chat/lib/

# Install additional dependencies
cd tomo-chat
npm install ai ws openai
npm install --save-dev @types/ws

# Set environment variables
echo "OPENAI_API_KEY=your_key_here" >> .env.local
echo "TOMO_MCP_URL=ws://localhost:8001" >> .env.local

# Create API routes (see nextjs-example.tsx.example for code)
mkdir -p app/api/chat app/api/tomo/tools
# ... copy API route code from example

# Run the app
npm run dev
```

## 🔧 Configuration

### Environment Variables

Create `.env` or `.env.local`:

```
# Required for LLM integration
OPENAI_API_KEY=sk-your-openai-key

# Tomo server URLs
TOMO_MCP_URL=ws://localhost:8001
TOMO_REST_URL=http://localhost:8000

# Optional: Debug mode
DEBUG_TOMO=true
```

### TypeScript Configuration

The `tsconfig.json` is configured for:
- **ES2020** target with CommonJS modules
- **Strict mode** enabled
- **Node.js types** included
- **Source maps** for debugging

## 🚨 Troubleshooting

### Connection Issues

**Problem**: `Connection refused` error
**Solutions**:
1. Ensure Tomo MCP server is running:
   ```bash
   tomo serve-mcp --module docs.examples.code.python.example_tools --port 8001
   ```
2. Check the port in your TypeScript code matches the server port
3. Verify firewall settings

**Problem**: `WebSocket disconnects frequently`
**Solutions**:
1. Check network stability
2. Increase timeout in `TomoMCPClient` constructor
3. Implement connection monitoring

### Tool Execution Issues

**Problem**: `Tool not found` error
**Solutions**:
1. Verify tool registration in Python:
   ```python
   registry.register(YourTool)
   ```
2. Check tool name spelling in TypeScript calls
3. Restart MCP server after tool changes

**Problem**: `Input validation failed`
**Solutions**:
1. Check tool parameter types match schema
2. Ensure required fields are provided
3. Use `TomoToolManager.validateInputs()` before execution

### Performance Issues

**Problem**: High latency
**Solutions**:
1. Use tool manager's caching features
2. Implement connection pooling
3. Consider REST API for simple cases

## 📊 Example Use Cases

### 1. Mathematical Assistant
```typescript
const result1 = await client.executeTool('Calculator', {
  operation: 'power',
  a: 2,
  b: 10
});

const result2 = await client.executeTool('NumberSequence', {
  sequence_type: 'fibonacci',
  count: 10
});
```

### 2. Data Processing Pipeline
```typescript
// Validate email
const validation = await client.executeTool('DataValidator', {
  value: 'user@example.com',
  validation_type: 'email'
});

// Process text if email is valid
if (validation.is_valid) {
  const processed = await client.executeTool('TextProcessor', {
    text: 'Welcome to our service!',
    operation: 'uppercase'
  });
}
```

### 3. Report Generation
```typescript
const data = [
  { name: 'John', age: 30, city: 'New York' },
  { name: 'Jane', age: 25, city: 'San Francisco' }
];

const report = await client.executeTool('FileGenerator', {
  filename: 'users.csv',
  content_type: 'csv',
  data: data
});
```

## 🔗 Integration with AI SDKs

### OpenAI Integration

```typescript
import OpenAI from 'openai';

const openai = new OpenAI();
const manager = new TomoToolManager(client);
await manager.initialize();

const completion = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Calculate 25 + 17' }],
  tools: manager.getSchemas(),
  tool_choice: 'auto'
});

// Handle tool calls in response
for (const toolCall of completion.choices[0].message.tool_calls || []) {
  const result = await client.executeTool(
    toolCall.function.name,
    JSON.parse(toolCall.function.arguments)
  );
  console.log(`Tool ${toolCall.function.name} result:`, result);
}
```

### Vercel AI SDK Integration

```typescript
import { useChat } from 'ai/react';

const { messages, input, handleInputChange, handleSubmit } = useChat({
  api: '/api/chat',  // API route handles Tomo integration
  onFinish: (message) => {
    console.log('Chat completed:', message);
  }
});
```

## 📚 Additional Resources

- **[TypeScript Integration Guide](../typescript-integration.md)** - Detailed integration options
- **[Vercel AI SDK Guide](../vercel-ai-sdk.md)** - AI SDK specific integration
- **[Troubleshooting Guide](../troubleshooting.md)** - Common issues and solutions
- **[API Reference](../api-reference.md)** - Complete API documentation

## 🤝 Contributing

Found an issue or want to add more examples?

1. **Test your changes** with both Python and TypeScript sides
2. **Update documentation** if you add new features
3. **Follow the existing code style** and patterns
4. **Add error handling** and proper types

See the main [Contributing Guide](../../../CONTRIBUTING.md) for more details. 