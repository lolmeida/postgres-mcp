/**
 * Base interfaces for all service classes
 * 
 * The service layer is responsible for business logic and coordinates between
 * handlers (presentation) and repositories (data access). Services handle
 * complex operations, transactions, validations, and more.
 */

import { MCPError } from '../core/types';

/**
 * Base interface for all services
 */
export interface ServiceBase {
  /**
   * Initialize the service
   * This method should be called before the service is used
   */
  initialize(): Promise<void>;
}

/**
 * Base class for all services with common functionality
 */
export abstract class AbstractService implements ServiceBase {
  /**
   * Initialize the service
   * Default implementation is a no-op, subclasses can override if needed
   */
  async initialize(): Promise<void> {
    // Default implementation does nothing
    return Promise.resolve();
  }

  /**
   * Creates a standardized service error
   * 
   * @param message Error message
   * @param type Error type
   * @param details Additional error details (optional)
   * @returns Error object with standard properties
   */
  protected createError(
    message: string, 
    type: MCPError['type'] = 'internal_error', 
    details?: any
  ): Error & { errorType: MCPError['type'], details?: any } {
    const error = new Error(message) as Error & { 
      errorType: MCPError['type'],
      details?: any 
    };
    error.errorType = type;
    if (details) {
      error.details = details;
    }
    return error;
  }
} 