/**
 * MCP Router - Routes MCP requests to the appropriate handlers
 * 
 * This class is responsible for registering handlers and routing
 * incoming MCP requests to the correct handler based on the tool name.
 */

import { MCPRequest, MCPResponse } from './types';
import { HandlerBase } from '../handlers/HandlerBase';
import { InternalException } from '../utils/exceptions';
import { createComponentLogger } from '../utils/logger';
import { MCPConfig } from './MCPConfig';

/**
 * Router for MCP requests
 */
export class MCPRouter {
  /**
   * Map of tool names to their handlers
   */
  private handlers: Map<string, HandlerBase> = new Map();
  
  /**
   * Logger for this component
   */
  private logger;

  /**
   * Creates a new MCP Router
   * 
   * @param config MCP configuration
   */
  constructor(private config: MCPConfig) {
    this.logger = createComponentLogger('MCPRouter', config);
  }

  /**
   * Registers a handler for a specific tool
   * 
   * @param handler The handler to register
   */
  registerHandler(handler: HandlerBase): void {
    const toolName = handler.getToolName();
    
    if (this.handlers.has(toolName)) {
      this.logger.warn(`Handler for tool ${toolName} is being overridden`);
    }
    
    this.handlers.set(toolName, handler);
    this.logger.debug(`Registered handler for tool: ${toolName}`);
  }

  /**
   * Registers multiple handlers at once
   * 
   * @param handlers Array of handlers to register
   */
  registerHandlers(handlers: HandlerBase[]): void {
    handlers.forEach(handler => this.registerHandler(handler));
  }

  /**
   * Routes an MCP request to the appropriate handler
   * 
   * @param request The MCP request to route
   * @returns Promise resolving to the handler's response
   */
  async route(request: MCPRequest): Promise<MCPResponse> {
    const { tool } = request;
    this.logger.debug(`Routing request for tool: ${tool}`);
    
    const handler = this.handlers.get(tool);
    
    if (!handler) {
      this.logger.warn(`No handler registered for tool: ${tool}`);
      return {
        success: false,
        error: {
          message: `Unknown tool: ${tool}`,
          type: 'internal_error'
        }
      };
    }
    
    try {
      return await handler.handle(request);
    } catch (error: any) {
      this.logger.error(`Error handling request for tool ${tool}:`, error);
      
      return {
        success: false,
        error: {
          message: error.message || 'An unknown error occurred',
          type: error.errorType || 'internal_error',
          details: error.details
        }
      };
    }
  }

  /**
   * Gets the list of registered tools
   * 
   * @returns Array of registered tool names
   */
  getRegisteredTools(): string[] {
    return Array.from(this.handlers.keys());
  }
} 