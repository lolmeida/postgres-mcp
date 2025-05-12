/**
 * Base interface for all MCP handlers
 * 
 * This interface defines the contract that all MCP handlers must implement.
 * Each handler is responsible for processing a specific MCP tool request and
 * returning a standardized response.
 */

import { MCPRequest, MCPResponse } from '../core/types';

/**
 * Interface for all MCP handlers
 */
export interface HandlerBase<T = any> {
  /**
   * Handles the MCP request and returns a response
   * 
   * @param request The MCP request to handle
   * @returns Promise resolving to an MCPResponse with the result
   */
  handle(request: MCPRequest): Promise<MCPResponse<T>>;
  
  /**
   * Returns the tool name that this handler processes
   */
  getToolName(): string;
  
  /**
   * Validates the parameters in an MCP request
   * 
   * @param parameters The parameters to validate
   * @returns Validated parameters or throws validation error
   */
  validateParameters(parameters: Record<string, any>): Record<string, any>;
}

/**
 * Abstract base class that implements basic handler functionality
 */
export abstract class AbstractHandler<T = any> implements HandlerBase<T> {
  /**
   * The tool name that this handler processes
   */
  protected abstract readonly toolName: string;

  /**
   * Handles an MCP request
   * 
   * @param request The MCP request to handle
   * @returns Promise resolving to an MCPResponse
   */
  async handle(request: MCPRequest): Promise<MCPResponse<T>> {
    try {
      // Validate the parameters
      const validatedParams = this.validateParameters(request.parameters || {});
      
      // Process the request (to be implemented by subclasses)
      return await this.processRequest(validatedParams);
    } catch (error: any) {
      // Convert errors to the appropriate MCP error format
      return {
        success: false,
        error: {
          message: error.message || 'An unknown error occurred',
          type: error.errorType || 'internal_error',
          details: error.details || undefined
        }
      };
    }
  }

  /**
   * Returns the tool name that this handler processes
   */
  getToolName(): string {
    return this.toolName;
  }

  /**
   * Abstract method to validate request parameters
   * Must be implemented by subclasses
   * 
   * @param parameters The parameters to validate
   * @returns Validated parameters or throws validation error
   */
  abstract validateParameters(parameters: Record<string, any>): Record<string, any>;

  /**
   * Abstract method to process the validated request
   * Must be implemented by subclasses
   * 
   * @param parameters The validated parameters
   * @returns Promise resolving to an MCPResponse
   */
  protected abstract processRequest(parameters: Record<string, any>): Promise<MCPResponse<T>>;
} 