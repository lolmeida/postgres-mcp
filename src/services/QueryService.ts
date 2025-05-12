/**
 * Query Service Implementation
 * 
 * This service handles custom SQL query execution with security checks,
 * parameter validation, and result processing.
 */

import Joi from 'joi';
import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { createComponentLogger } from '../utils/logger';
import { QueryException } from '../utils/exceptions';

/**
 * Options for query execution
 */
export interface QueryExecutionOptions {
  /**
   * Parameters for the query (for parameterized queries)
   */
  parameters?: any[];
  
  /**
   * Maximum rows to return (for pagination)
   */
  maxRows?: number;
  
  /**
   * Number of rows to skip (for pagination)
   */
  offset?: number;
  
  /**
   * Whether this query is read-only
   */
  readOnly?: boolean;
  
  /**
   * Transaction ID if part of a transaction
   */
  transactionId?: string;
}

/**
 * Result of a query execution
 */
export interface QueryResult {
  /**
   * Rows returned by the query
   */
  rows: Record<string, any>[];
  
  /**
   * Total count of rows (may be estimated for large result sets)
   */
  count: number;
  
  /**
   * Command executed (SELECT, INSERT, etc)
   */
  command?: string;
  
  /**
   * Number of rows affected by command (for INSERT, UPDATE, DELETE)
   */
  rowCount?: number;
  
  /**
   * Time taken to execute the query (in milliseconds)
   */
  executionTime?: number;
  
  /**
   * Is there more data available beyond the maxRows limit
   */
  hasMore?: boolean;
}

/**
 * Service for executing SQL queries
 */
export class QueryService extends AbstractService {
  private logger;
  
  /**
   * List of dangerous SQL operations that are restricted
   */
  private readonly RESTRICTED_OPERATIONS = [
    /DROP\s+(TABLE|DATABASE|SCHEMA)/i,
    /TRUNCATE\s+TABLE/i,
    /ALTER\s+(DATABASE|ROLE|USER|SYSTEM)/i,
    /GRANT\s+/i,
    /REVOKE\s+/i,
    /CREATE\s+(DATABASE|ROLE|USER)/i,
    /REASSIGN\s+OWNED/i,
    /SECURITY\s+LABEL/i,
    /REINDEX/i
  ];

  /**
   * Constructor for QueryService
   * 
   * @param connection PostgreSQL connection
   * @param securityEnabled Whether to enable security restrictions
   */
  constructor(
    private connection: PostgresConnection,
    private securityEnabled: boolean = true
  ) {
    super();
    this.logger = createComponentLogger('QueryService');
  }

  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing QueryService');
    return Promise.resolve();
  }

  /**
   * Executes a SQL query with security validation
   * 
   * @param sql SQL query to execute
   * @param options Query execution options
   * @returns Query execution result
   * @throws QueryException if the query fails or is not allowed
   */
  async executeQuery(sql: string, options: QueryExecutionOptions = {}): Promise<QueryResult> {
    this.validateQuery(sql, options);
    
    const parameters = options.parameters || [];
    const maxRows = options.maxRows || 1000;
    const offset = options.offset || 0;
    const startTime = Date.now();
    
    try {
      // Add limit/offset if not already in the query and it's a SELECT
      if (
        sql.trim().toUpperCase().startsWith('SELECT') && 
        !sql.toUpperCase().includes('LIMIT') && 
        !sql.toUpperCase().includes(' FOR ')
      ) {
        sql = `${sql} LIMIT ${maxRows} OFFSET ${offset}`;
      }
      
      this.logger.debug(`Executing query: ${sql}`, { parameters });
      
      // Execute the query
      const result = await this.connection.query(sql, parameters);
      const executionTime = Date.now() - startTime;
      
      // For SELECT queries, try to get total count if rows were limited
      let totalCount = result.rows?.length || 0;
      let hasMore = false;
      
      if (
        sql.trim().toUpperCase().startsWith('SELECT') && 
        result.rows?.length === maxRows
      ) {
        // There might be more rows, set hasMore flag
        hasMore = true;
        
        // Try to get an estimate of total rows for large tables
        // This is a simple approach; a more accurate count would require
        // query rewriting or separate count query which can be expensive
        try {
          // Check if we're close to the real end
          const peekResult = await this.connection.query(
            `${sql.replace(/LIMIT\s+\d+/i, `LIMIT 1`)} OFFSET ${offset + maxRows}`,
            parameters
          );
          
          if (peekResult.rows?.length === 0) {
            // No more rows
            hasMore = false;
            totalCount = offset + result.rows.length;
          }
        } catch (error) {
          // Ignore errors in count estimation
          this.logger.warn('Error estimating total count', error);
        }
      }
      
      return {
        rows: result.rows || [],
        count: totalCount,
        command: result.command,
        rowCount: result.rowCount,
        executionTime,
        hasMore
      };
    } catch (error: any) {
      this.logger.error(`Query execution failed: ${error.message}`, error);
      throw new QueryException(
        `Query execution failed: ${error.message}`,
        { sql, parameters }
      );
    }
  }

  /**
   * Validates a SQL query for security and syntax
   * 
   * @param sql SQL query to validate
   * @param options Query execution options
   * @throws Error if the query is not allowed
   */
  private validateQuery(sql: string, options: QueryExecutionOptions): void {
    if (!sql) {
      throw this.createError('SQL query is required', 'validation_error');
    }
    
    // Validate with Joi
    const schema = Joi.string().required().min(3);
    const { error } = schema.validate(sql);
    
    if (error) {
      throw this.createError(`Invalid SQL query: ${error.message}`, 'validation_error');
    }
    
    // Security check for dangerous operations
    if (this.securityEnabled) {
      // Read-only check
      if (options.readOnly === true) {
        if (!sql.trim().toUpperCase().startsWith('SELECT')) {
          throw this.createError(
            'Only SELECT queries are allowed in read-only mode',
            'security_error'
          );
        }
      }
      
      // Check for restricted operations
      for (const pattern of this.RESTRICTED_OPERATIONS) {
        if (pattern.test(sql)) {
          throw this.createError(
            'This query contains restricted operations',
            'security_error',
            { operation: pattern.toString() }
          );
        }
      }
    }
  }
} 