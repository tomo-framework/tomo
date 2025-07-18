/**
 * Tomo MCP Client - TypeScript client for connecting to Tomo's MCP server
 * 
 * This client implements the Model Context Protocol (MCP) to communicate
 * with Tomo's Python tools via WebSocket/JSON-RPC.
 */

import WebSocket from 'ws';

interface MCPRequest {
  jsonrpc: '2.0';
  method: string;
  params?: any;
  id?: string | number;
}

interface MCPResponse {
  jsonrpc: '2.0';
  id?: string | number;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

interface ToolSchema {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
}

interface OpenAIToolSchema {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, any>;
      required?: string[];
    };
  };
}

export class TomoMCPClient {
  private ws: WebSocket | null = null;
  private serverUrl: string;
  private connected = false;
  private requestId = 1;
  private pendingRequests = new Map<string | number, { resolve: Function; reject: Function }>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(serverUrl: string = 'ws://localhost:8001') {
    this.serverUrl = serverUrl;
  }

  /**
   * Connect to the Tomo MCP server
   */
  async connect(): Promise<void> {
    if (this.connected) {
      return;
    }

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.serverUrl);

        this.ws.on('open', async () => {
          console.log('Connected to Tomo MCP server');
          
          try {
            // Initialize the MCP session
            await this.initialize();
            this.connected = true;
            this.reconnectAttempts = 0;
            resolve();
          } catch (error) {
            console.error('Failed to initialize MCP session:', error);
            reject(error);
          }
        });

        this.ws.on('message', (data: WebSocket.Data) => {
          try {
            const message: MCPResponse = JSON.parse(data.toString());
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        });

        this.ws.on('close', () => {
          console.log('Disconnected from Tomo MCP server');
          this.connected = false;
          this.handleDisconnect();
        });

        this.ws.on('error', (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Initialize the MCP session
   */
  private async initialize(): Promise<void> {
    const response = await this.sendRequest('initialize', {
      protocolVersion: '2024-11-05',
      clientInfo: {
        name: 'tomo-typescript-client',
        version: '1.0.0'
      }
    });

    console.log('MCP session initialized:', response);
  }

  /**
   * Handle incoming messages from the server
   */
  private handleMessage(message: MCPResponse): void {
    if (message.id !== undefined) {
      const pending = this.pendingRequests.get(message.id);
      if (pending) {
        this.pendingRequests.delete(message.id);
        
        if (message.error) {
          pending.reject(new Error(`MCP Error ${message.error.code}: ${message.error.message}`));
        } else {
          pending.resolve(message.result);
        }
      }
    }
  }

  /**
   * Handle disconnection and attempt reconnection
   */
  private handleDisconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  /**
   * Send a request to the server
   */
  private sendRequest(method: string, params?: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('Not connected to MCP server'));
        return;
      }

      const id = this.requestId++;
      const request: MCPRequest = {
        jsonrpc: '2.0',
        method,
        params,
        id
      };

      this.pendingRequests.set(id, { resolve, reject });

      try {
        this.ws.send(JSON.stringify(request));
      } catch (error) {
        this.pendingRequests.delete(id);
        reject(error);
      }

      // Add timeout
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Request timeout'));
        }
      }, 30000); // 30 second timeout
    });
  }

  /**
   * List all available tools
   */
  async listTools(): Promise<ToolSchema[]> {
    const response = await this.sendRequest('tools/list');
    return response.tools || [];
  }

  /**
   * Execute a tool with the given inputs
   */
  async executeTool(toolName: string, inputs: any): Promise<any> {
    const response = await this.sendRequest('tools/call', {
      name: toolName,
      arguments: inputs
    });
    
    // Handle different response formats
    if (response.content && Array.isArray(response.content)) {
      return response.content[0]?.text || response;
    }
    
    return response;
  }

  /**
   * Get tool schemas in OpenAI function calling format
   */
  async getToolSchemas(): Promise<OpenAIToolSchema[]> {
    const tools = await this.listTools();
    
    return tools.map(tool => ({
      type: 'function' as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.inputSchema
      }
    }));
  }

  /**
   * Get a specific tool's schema
   */
  async getToolSchema(toolName: string): Promise<ToolSchema | null> {
    const tools = await this.listTools();
    return tools.find(tool => tool.name === toolName) || null;
  }

  /**
   * Ping the server to check connectivity
   */
  async ping(): Promise<boolean> {
    try {
      await this.sendRequest('ping');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Disconnect from the server
   */
  disconnect(): void {
    if (this.ws) {
      this.connected = false;
      this.ws.close();
      this.ws = null;
    }
    this.pendingRequests.clear();
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }
}

/**
 * Utility class for managing multiple tool calls
 */
export class TomoToolManager {
  private client: TomoMCPClient;
  private toolSchemas: OpenAIToolSchema[] = [];

  constructor(client: TomoMCPClient) {
    this.client = client;
  }

  /**
   * Initialize and cache tool schemas
   */
  async initialize(): Promise<void> {
    if (!this.client.isConnected()) {
      await this.client.connect();
    }
    this.toolSchemas = await this.client.getToolSchemas();
  }

  /**
   * Get cached tool schemas
   */
  getSchemas(): OpenAIToolSchema[] {
    return this.toolSchemas;
  }

  /**
   * Execute multiple tools in parallel
   */
  async executeTools(toolCalls: Array<{ name: string; inputs: any }>): Promise<any[]> {
    const promises = toolCalls.map(call => 
      this.client.executeTool(call.name, call.inputs)
    );
    
    return Promise.all(promises);
  }

  /**
   * Execute tools with retry logic
   */
  async executeToolWithRetry(
    toolName: string, 
    inputs: any, 
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<any> {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.client.executeTool(toolName, inputs);
      } catch (error) {
        if (attempt === maxRetries) {
          throw error;
        }
        
        console.warn(`Tool execution failed (attempt ${attempt}/${maxRetries}):`, error);
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }
  }

  /**
   * Validate tool inputs against schema
   */
  validateInputs(toolName: string, inputs: any): { valid: boolean; errors: string[] } {
    const schema = this.toolSchemas.find(s => s.function.name === toolName);
    if (!schema) {
      return { valid: false, errors: [`Tool ${toolName} not found`] };
    }

    const errors: string[] = [];
    const required = schema.function.parameters.required || [];
    const properties = schema.function.parameters.properties || {};

    // Check required fields
    for (const field of required) {
      if (!(field in inputs)) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    // Basic type checking
    for (const [field, value] of Object.entries(inputs)) {
      const propSchema = properties[field];
      if (propSchema && propSchema.type) {
        const expectedType = propSchema.type;
        const actualType = typeof value;
        
        if (expectedType === 'number' && actualType !== 'number') {
          errors.push(`Field ${field} should be a number, got ${actualType}`);
        }
        if (expectedType === 'string' && actualType !== 'string') {
          errors.push(`Field ${field} should be a string, got ${actualType}`);
        }
        if (expectedType === 'boolean' && actualType !== 'boolean') {
          errors.push(`Field ${field} should be a boolean, got ${actualType}`);
        }
      }
    }

    return { valid: errors.length === 0, errors };
  }
}

export default TomoMCPClient; 