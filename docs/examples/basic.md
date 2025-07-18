# Basic Examples

Complete integration examples showing both Python and TypeScript sides.

## 🐍 Python Side: Creating Tomo Tools

First, create your tools in Python using Tomo:

```python
# example_tools.py
from tomo import BaseTool, tool

@tool
class Calculator(BaseTool):
    """Perform basic mathematical calculations."""
    
    operation: str  # add, subtract, multiply, divide
    a: float
    b: float
    
    def run(self) -> float:
        if self.operation == "add":
            return self.a + self.b
        elif self.operation == "subtract":
            return self.a - self.b
        elif self.operation == "multiply":
            return self.a * self.b
        elif self.operation == "divide":
            if self.b == 0:
                raise ValueError("Cannot divide by zero")
            return self.a / self.b
        else:
            raise ValueError(f"Unknown operation: {self.operation}")

@tool
class WeatherChecker(BaseTool):
    """Get weather information for a city."""
    
    city: str
    country: Optional[str] = None
    
    def run(self) -> Dict[str, Any]:
        # Mock implementation - replace with real API
        return {
            "city": self.city,
            "country": self.country or "Unknown",
            "temperature": 22,
            "condition": "sunny"
        }

# Register tools and start server
if __name__ == "__main__":
    from tomo import ToolRegistry
    
    registry = ToolRegistry()
    registry.register(Calculator)
    registry.register(WeatherChecker)
    
    print("Tools registered:", registry.list())
```

Start the MCP server:
```bash
tomo serve-mcp --module example_tools --port 8001
```

## 📱 TypeScript Side: Using Tomo Tools

### MCP Client Integration
```typescript
import { TomoMCPClient } from './tomo-mcp-client';

async function basicExample() {
  const client = new TomoMCPClient('ws://localhost:8001');
  
  try {
    // Connect to Tomo server
    await client.connect();
    
    // List available tools
    const tools = await client.listTools();
    console.log('Available tools:', tools.map(t => t.name));
    
    // Execute Calculator tool
    const calcResult = await client.executeTool('Calculator', {
      operation: 'add',
      a: 15,
      b: 25
    });
    console.log('Calculator result:', calcResult); // 40
    
    // Execute Weather tool
    const weatherResult = await client.executeTool('WeatherChecker', {
      city: 'Tokyo',
      country: 'Japan'
    });
    console.log('Weather result:', weatherResult);
    
  } finally {
    client.disconnect();
  }
}

basicExample().catch(console.error);
```

### REST API Alternative
```typescript
// Simple HTTP client for Tomo REST API
async function runTomoTool(toolName: string, inputs: any) {
  const response = await fetch(`http://localhost:8000/tools/${toolName}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inputs)
  });
  
  if (!response.ok) {
    throw new Error(`Tool execution failed: ${response.statusText}`);
  }
  
  return response.json();
}

// Usage
const result = await runTomoTool('Calculator', { 
  operation: 'multiply', 
  a: 6, 
  b: 7 
});
console.log(result); // 42
```

### Tool Schema Export for AI Integration
```typescript
async function getToolsForAI() {
  const client = new TomoMCPClient();
  await client.connect();
  
  // Get schemas in OpenAI format
  const schemas = await client.getToolSchemas();
  console.log('Tool schemas for AI:', schemas);
  
  client.disconnect();
  return schemas;
}

// Use with OpenAI
import OpenAI from 'openai';

const openai = new OpenAI();
const toolSchemas = await getToolsForAI();

const completion = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Calculate 25 * 4' }],
  tools: toolSchemas,
  tool_choice: 'auto'
});
```

## 🏃 Running the Examples

### Step 1: Python Setup
```bash
# In Tomo directory
python example_tools.py  # Test tools
tomo serve-mcp --module example_tools --port 8001  # Start server
```

### Step 2: TypeScript Setup
```bash
npm install ws @types/ws typescript ts-node
npx ts-node basic-example.ts
```

## 📁 Complete Examples

For full working examples with error handling, see:
- **[Complete Code Examples](./code/)** - Python tools + TypeScript integration
- **[Advanced Examples](./advanced.md)** - Complex patterns and use cases 