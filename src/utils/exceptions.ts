/**
 * Custom exception classes for the PostgreSQL MCP
 * 
 * These exceptions provide a standardized way to handle different types
 * of errors throughout the application, with proper typing and context.
 */

import { MCPErrorType } from '../core/types';

/**
 * Base MCP exception class
 */
export class MCPException extends Error {
  /**
   * Type of the error
   */
  readonly errorType: MCPErrorType;
  
  /**
   * Additional error details (optional)
   */
  readonly details?: any;

  /**
   * Creates a new MCP exception
   * 
   * @param message Error message
   * @param errorType Type of the error
   * @param details Additional details about the error (optional)
   */
  constructor(message: string, errorType: MCPErrorType, details?: any) {
    super(message);
    this.name = this.constructor.name;
    this.errorType = errorType;
    this.details = details;
    
    // Maintains proper stack trace for where the error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

/**
 * Exception for validation errors
 */
export class ValidationException extends MCPException {
  constructor(message: string, details?: any) {
    super(message, 'validation_error', details);
  }
}

/**
 * Exception for database errors
 */
export class DatabaseException extends MCPException {
  constructor(message: string, details?: any) {
    super(message, 'database_error', details);
  }
}

/**
 * Exception for query errors
 */
export class QueryException extends MCPException {
  constructor(message: string, details?: any) {
    super(message, 'query_error', details);
  }
}

/**
 * Exception for security/permission errors
 */
export class SecurityException extends MCPException {
  constructor(message: string, details?: any) {
    super(message, 'security_error', details);
  }
}

/**
 * Exception for transaction errors
 */
export class TransactionException extends MCPException {
  constructor(message: string, details?: any) {
    super(message, 'transaction_error', details);
  }
}

/**
 * Exception for internal errors
 */
export class InternalException extends MCPException {
  constructor(message: string, details?: any) {
    super(message, 'internal_error', details);
  }
}

/**
 * Helper function to transform database errors into appropriate exceptions
 * 
 * @param error Original error from pg or other source
 * @returns Appropriately typed MCPException
 */
export function transformDbError(error: any): MCPException {
  // Check if it's already an MCPException
  if (error instanceof MCPException) {
    return error;
  }
  
  // If it's a database error with a code, map it to an appropriate exception
  if (error.code) {
    switch (error.code) {
      // Constraint violations
      case '23505': // unique_violation
        return new DatabaseException(`Unique constraint violation: ${error.detail || error.message}`, error);
      case '23503': // foreign_key_violation
        return new DatabaseException(`Foreign key constraint violation: ${error.detail || error.message}`, error);
      case '23502': // not_null_violation
        return new DatabaseException(`Not null constraint violation: ${error.detail || error.message}`, error);
      
      // Query syntax errors
      case '42601': // syntax_error
      case '42P01': // undefined_table
        return new QueryException(`Query syntax error: ${error.message}`, error);
      
      // Permission errors
      case '42501': // insufficient_privilege
        return new SecurityException(`Insufficient privileges: ${error.message}`, error);
      
      // Transaction errors
      case '25P02': // in_failed_sql_transaction
        return new TransactionException(`Transaction error: ${error.message}`, error);
      
      // Default to database error for other codes
      default:
        return new DatabaseException(`Database error: ${error.message}`, error);
    }
  }
  
  // Default to internal error for unknown cases
  return new InternalException(`Internal error: ${error.message || 'Unknown error'}`, error);
} 