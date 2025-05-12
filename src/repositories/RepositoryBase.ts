/**
 * Base interfaces for all repository classes
 * 
 * The repository layer is responsible for data access operations and abstraction
 * of database interactions. Each repository typically handles operations for a
 * specific entity or domain area.
 */

import { Pool, PoolClient } from 'pg';

/**
 * Base interface for repositories
 */
export interface RepositoryBase {
  /**
   * Initialize the repository
   */
  initialize(): Promise<void>;
}

/**
 * Options for database operations
 */
export interface DbOperationOptions {
  /**
   * Client to use for the operation (for transaction support)
   */
  client?: PoolClient;
  
  /**
   * Whether to use a transaction for the operation
   */
  useTransaction?: boolean;
}

/**
 * Base abstract class for repositories
 */
export abstract class AbstractRepository implements RepositoryBase {
  /**
   * Database connection pool
   */
  protected pool: Pool;

  /**
   * Creates a new repository instance
   * 
   * @param pool Database connection pool
   */
  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Initialize the repository
   * Default implementation is a no-op
   */
  async initialize(): Promise<void> {
    // Default implementation does nothing
    return Promise.resolve();
  }

  /**
   * Executes a database operation with appropriate error handling
   * 
   * @param operation Async function that performs the database operation
   * @param options Operation options, including transaction support
   * @returns Result of the operation
   */
  protected async executeDbOperation<T>(
    operation: (client: Pool | PoolClient) => Promise<T>,
    options: DbOperationOptions = {}
  ): Promise<T> {
    // Use the provided client (usually from transaction) or the pool
    const client = options.client || this.pool;
    
    // If a transaction is requested and we're using the pool directly,
    // we need to handle the transaction ourselves
    if (options.useTransaction && !options.client) {
      const transactionClient = await this.pool.connect();
      try {
        await transactionClient.query('BEGIN');
        const result = await operation(transactionClient);
        await transactionClient.query('COMMIT');
        return result;
      } catch (error) {
        await transactionClient.query('ROLLBACK');
        throw error;
      } finally {
        transactionClient.release();
      }
    }
    
    // Otherwise, just run the operation with the client/pool
    return operation(client);
  }
} 