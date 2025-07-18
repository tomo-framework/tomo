/**
 * Basic Tomo Integration Example
 * 
 * This example shows how to:
 * 1. Connect to Tomo's MCP server
 * 2. List available tools
 * 3. Execute tools with proper error handling
 * 4. Use the TypeScript client effectively
 */

import { TomoMCPClient, TomoToolManager } from './tomo-mcp-client';

async function basicExample() {
  console.log('🚀 Starting Basic Tomo Integration Example\n');

  // Create client instance
  const client = new TomoMCPClient('ws://localhost:8001');
  
  try {
    // Step 1: Connect to the server
    console.log('📡 Connecting to Tomo MCP server...');
    await client.connect();
    console.log('✅ Connected successfully!\n');

    // Step 2: List available tools
    console.log('🔍 Listing available tools...');
    const tools = await client.listTools();
    console.log('Available tools:');
    tools.forEach(tool => {
      console.log(`  - ${tool.name}: ${tool.description}`);
    });
    console.log();

    // Step 3: Execute Calculator tool
    console.log('🧮 Testing Calculator tool...');
    const calcResult = await client.executeTool('Calculator', {
      operation: 'add',
      a: 15,
      b: 25
    });
    console.log(`Calculator result: 15 + 25 = ${calcResult}\n`);

    // Step 4: Execute Weather tool
    console.log('🌤️  Testing Weather tool...');
    const weatherResult = await client.executeTool('WeatherChecker', {
      city: 'Tokyo',
      country: 'Japan',
      units: 'celsius'
    });
    console.log('Weather result:', JSON.stringify(weatherResult, null, 2));
    console.log();

    // Step 5: Execute Text Processor
    console.log('📝 Testing Text Processor...');
    const textResult = await client.executeTool('TextProcessor', {
      text: 'Hello, Tomo!',
      operation: 'uppercase'
    });
    console.log('Text processing result:', JSON.stringify(textResult, null, 2));
    console.log();

    // Step 6: Test error handling
    console.log('❌ Testing error handling...');
    try {
      await client.executeTool('Calculator', {
        operation: 'divide',
        a: 10,
        b: 0  // This should cause an error
      });
    } catch (error) {
      console.log('Caught expected error:', error.message);
    }
    console.log();

  } catch (error) {
    console.error('❌ Error in basic example:', error);
  } finally {
    // Step 7: Clean up
    console.log('🧹 Cleaning up...');
    client.disconnect();
    console.log('✅ Example completed!\n');
  }
}

async function advancedToolManagerExample() {
  console.log('🚀 Starting Advanced Tool Manager Example\n');

  const client = new TomoMCPClient('ws://localhost:8001');
  const manager = new TomoToolManager(client);

  try {
    // Initialize the tool manager
    console.log('🔧 Initializing tool manager...');
    await manager.initialize();
    console.log('✅ Tool manager initialized!\n');

    // Get OpenAI-compatible schemas
    console.log('📋 Getting tool schemas for AI integration...');
    const schemas = manager.getSchemas();
    console.log(`Found ${schemas.length} tools with schemas:\n`);
    
    schemas.forEach(schema => {
      console.log(`Tool: ${schema.function.name}`);
      console.log(`Description: ${schema.function.description}`);
      console.log(`Parameters:`, JSON.stringify(schema.function.parameters, null, 2));
      console.log('---');
    });

    // Validate inputs before execution
    console.log('✅ Testing input validation...');
    const validation = manager.validateInputs('Calculator', {
      operation: 'add',
      a: 10,
      b: 20
    });
    console.log('Validation result:', validation);
    console.log();

    // Execute with retry logic
    console.log('🔄 Testing retry logic...');
    const retryResult = await manager.executeToolWithRetry('Calculator', {
      operation: 'multiply',
      a: 6,
      b: 7
    }, 3, 500);
    console.log(`Retry result: 6 × 7 = ${retryResult}\n`);

    // Execute multiple tools in parallel
    console.log('⚡ Testing parallel execution...');
    const parallelResults = await manager.executeTools([
      {
        name: 'Calculator',
        inputs: { operation: 'add', a: 1, b: 2 }
      },
      {
        name: 'Calculator', 
        inputs: { operation: 'multiply', a: 3, b: 4 }
      },
      {
        name: 'NumberSequence',
        inputs: { sequence_type: 'fibonacci', count: 5 }
      }
    ]);
    
    console.log('Parallel execution results:');
    parallelResults.forEach((result, index) => {
      console.log(`  Result ${index + 1}:`, result);
    });
    console.log();

  } catch (error) {
    console.error('❌ Error in advanced example:', error);
  } finally {
    console.log('🧹 Cleaning up...');
    client.disconnect();
    console.log('✅ Advanced example completed!\n');
  }
}

// Run examples
async function main() {
  console.log('='.repeat(60));
  console.log('  TOMO TYPESCRIPT INTEGRATION EXAMPLES');
  console.log('='.repeat(60));
  console.log();

  console.log('⚠️  Make sure to start the Tomo MCP server first:');
  console.log('   cd /path/to/tomo');
  console.log('   tomo serve-mcp --module docs.examples.code.python.example_tools --port 8001');
  console.log();

  // Wait a moment for user to read
  await new Promise(resolve => setTimeout(resolve, 2000));

  await basicExample();
  
  console.log('🔄 Waiting 3 seconds before advanced example...\n');
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  await advancedToolManagerExample();

  console.log('🎉 All examples completed successfully!');
}

// Export for use in other files
export { basicExample, advancedToolManagerExample };

// Run if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
} 