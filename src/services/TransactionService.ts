/**
 * Transaction Service Implementation
 * 
 * This service manages PostgreSQL transactions, providing a higher-level
 * interface for transaction operations with proper error handling and cleanup.
 */

import { v4 as uuidv4 } from 'uuid';
import { PoolClient } from 'pg';
import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { createComponentLogger } from '../utils/logger';

/**
 * Isolation level for PostgreSQL transactions
 */
export enum IsolationLevel {
  READ_UNCOMMITTED = 'READ UNCOMMITTED',
  READ_COMMITTED = 'READ COMMITTED',
  REPEATABLE_READ = 'REPEATABLE READ',
  SERIALIZABLE = 'SERIALIZABLE'
}

/**
 * Status of a transaction
 */
export enum TransactionStatus {
  ACTIVE = 'active',
  COMMITTED = 'committed',
  ROLLED_BACK = 'rolled_back',
  ERROR = 'error'
}

/**
 * Information about a transaction
 */
export interface TransactionInfo {
  /**
   * Transaction ID
   */
  id: string;
  
  /**
   * Current status of the transaction
   */
  status: TransactionStatus;
  
  /**
   * Isolation level of the transaction
   */
  isolationLevel: IsolationLevel;
  
  /**
   * When the transaction was started
   */
  startedAt: Date;
  
  /**
   * When the transaction was completed (committed/rolled back)
   */
  completedAt?: Date;
  
  /**
   * Transaction timeout in milliseconds
   */
  timeout?: number;
  
  /**
   * Error information if the transaction failed
   */
  error?: string;
}

/**
 * Type for transaction callback functions
 */
export type TransactionCallback<T> = (client: PoolClient) => Promise<T>;

/**
 * Service for managing PostgreSQL transactions
 */
export class TransactionService extends AbstractService {
  private logger;
  
  /**
   * Map of active transaction clients by transaction ID
   */
  private activeTransactions: Map<string, { 
    client: PoolClient; 
    info: TransactionInfo; 
    timeoutId?: NodeJS.Timeout; 
  }> = new Map();
  
  /**
   * Default transaction timeout in milliseconds (5 minutes)
   */
  private defaultTimeout: number = 5 * 60 * 1000;
  
  /**
   * Creates a new TransactionService
   * 
   * @param connection PostgreSQL connection
   * @param defaultTimeout Default transaction timeout in milliseconds
   */
  constructor(
    private connection: PostgresConnection,
    defaultTimeout?: number
  ) {
    super();
    this.logger = createComponentLogger('TransactionService');
    
    if (defaultTimeout) {
      this.defaultTimeout = defaultTimeout;
    }
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing TransactionService');
    return Promise.resolve();
  }
  
  /**
   * Starts a new transaction
   * 
   * @param isolationLevel Transaction isolation level
   * @param timeout Transaction timeout in milliseconds
   * @returns Transaction information
   */
  async beginTransaction(
    isolationLevel: IsolationLevel = IsolationLevel.READ_COMMITTED,
    timeout: number = this.defaultTimeout
  ): Promise<TransactionInfo> {
    this.logger.debug(`Beginning transaction with isolation level: ${isolationLevel}`);
    
    try {
      // Get a dedicated client for this transaction
      const client = await this.connection.getClient();
      
      // Start the transaction
      await client.query('BEGIN');
      
      // Set isolation level if different from default
      if (isolationLevel !== IsolationLevel.READ_COMMITTED) {
        await client.query(`SET TRANSACTION ISOLATION LEVEL ${isolationLevel}`);
      }
      
      // Generate transaction ID and info
      const id = uuidv4();
      const transactionInfo: TransactionInfo = {
        id,
        status: TransactionStatus.ACTIVE,
        isolationLevel,
        startedAt: new Date(),
        timeout
      };
      
      // Set up transaction timeout
      let timeoutId: NodeJS.Timeout | undefined;
      if (timeout > 0) {
        timeoutId = setTimeout(() => this.handleTransactionTimeout(id), timeout);
      }
      
      // Store transaction in active transactions map
      this.activeTransactions.set(id, { client, info: transactionInfo, timeoutId });
      
      return transactionInfo;
    } catch (error: any) {
      this.logger.error(`Error beginning transaction: ${error.message}`, error);
      throw this.createError(
        `Failed to begin transaction: ${error.message}`,
        'transaction_error',
        error.details
      );
    }
  }
  
  /**
   * Commits an active transaction
   * 
   * @param transactionId Transaction ID
   * @returns Updated transaction information
   */
  async commitTransaction(transactionId: string): Promise<TransactionInfo> {
    this.logger.debug(`Committing transaction: ${transactionId}`);
    
    const transaction = this.getTransaction(transactionId);
    
    try {
      await transaction.client.query('COMMIT');
      
      // Update transaction info
      transaction.info.status = TransactionStatus.COMMITTED;
      transaction.info.completedAt = new Date();
      
      // Clean up transaction
      this.cleanupTransaction(transactionId);
      
      return { ...transaction.info };
    } catch (error: any) {
      this.logger.error(`Error committing transaction ${transactionId}: ${error.message}`, error);
      
      try {
        // Try to roll back on error
        await transaction.client.query('ROLLBACK');
        transaction.info.status = TransactionStatus.ERROR;
        transaction.info.error = `Commit failed: ${error.message}`;
      } catch (rollbackError: any) {
        this.logger.error(`Error rolling back transaction ${transactionId} after commit failure`, rollbackError);
      }
      
      // Clean up transaction
      this.cleanupTransaction(transactionId);
      
      throw this.createError(
        `Failed to commit transaction: ${error.message}`,
        'transaction_error',
        error.details
      );
    }
  }
  
  /**
   * Rolls back an active transaction
   * 
   * @param transactionId Transaction ID
   * @param savepoint Optional savepoint name to roll back to
   * @returns Updated transaction information
   */
  async rollbackTransaction(
    transactionId: string,
    savepoint?: string
  ): Promise<TransactionInfo> {
    this.logger.debug(`Rolling back transaction: ${transactionId}${savepoint ? ` to savepoint ${savepoint}` : ''}`);
    
    const transaction = this.getTransaction(transactionId);
    
    try {
      if (savepoint) {
        await transaction.client.query(`ROLLBACK TO SAVEPOINT ${savepoint}`);
        
        // Transaction is still active if rolling back to a savepoint
        return { ...transaction.info };
      } else {
        await transaction.client.query('ROLLBACK');
        
        // Update transaction info
        transaction.info.status = TransactionStatus.ROLLED_BACK;
        transaction.info.completedAt = new Date();
        
        // Clean up transaction
        this.cleanupTransaction(transactionId);
        
        return { ...transaction.info };
      }
    } catch (error: any) {
      this.logger.error(`Error rolling back transaction ${transactionId}: ${error.message}`, error);
      
      // Clean up transaction
      this.cleanupTransaction(transactionId);
      
      throw this.createError(
        `Failed to rollback transaction: ${error.message}`,
        'transaction_error',
        error.details
      );
    }
  }
  
  /**
   * Creates a savepoint in an active transaction
   * 
   * @param transactionId Transaction ID
   * @param savepointName Savepoint name
   * @returns Transaction information
   */
  async createSavepoint(
    transactionId: string,
    savepointName: string
  ): Promise<TransactionInfo> {
    this.logger.debug(`Creating savepoint ${savepointName} in transaction ${transactionId}`);
    
    const transaction = this.getTransaction(transactionId);
    
    try {
      await transaction.client.query(`SAVEPOINT ${savepointName}`);
      return { ...transaction.info };
    } catch (error: any) {
      this.logger.error(`Error creating savepoint ${savepointName} in transaction ${transactionId}: ${error.message}`, error);
      throw this.createError(
        `Failed to create savepoint: ${error.message}`,
        'transaction_error',
        error.details
      );
    }
  }
  
  /**
   * Executes a function within a transaction and automatically manages the transaction lifecycle
   * 
   * @param callback Function to execute within the transaction
   * @param isolationLevel Transaction isolation level
   * @returns Result of the callback function
   */
  async executeInTransaction<T>(
    callback: TransactionCallback<T>,
    isolationLevel: IsolationLevel = IsolationLevel.READ_COMMITTED
  ): Promise<T> {
    let transactionInfo: TransactionInfo | null = null;
    
    try {
      // Begin a new transaction
      transactionInfo = await this.beginTransaction(isolationLevel);
      const transaction = this.getTransaction(transactionInfo.id);
      
      // Execute the callback with the transaction client
      const result = await callback(transaction.client);
      
      // Commit the transaction
      await this.commitTransaction(transactionInfo.id);
      
      return result;
    } catch (error: any) {
      // Roll back the transaction on error
      if (transactionInfo) {
        try {
          await this.rollbackTransaction(transactionInfo.id);
        } catch (rollbackError) {
          // Just log the rollback error, but throw the original error
          this.logger.error('Error rolling back transaction', rollbackError);
        }
      }
      
      throw error;
    }
  }
  
  /**
   * Gets transaction information by ID
   * 
   * @param transactionId Transaction ID
   * @returns Transaction information
   */
  getTransactionInfo(transactionId: string): TransactionInfo {
    const transaction = this.activeTransactions.get(transactionId);
    
    if (!transaction) {
      throw this.createError(
        `Transaction not found: ${transactionId}`,
        'transaction_error'
      );
    }
    
    return { ...transaction.info };
  }
  
  /**
   * Gets the client for an active transaction
   * 
   * @param transactionId Transaction ID
   * @returns PostgreSQL client
   */
  getTransactionClient(transactionId: string): PoolClient {
    return this.getTransaction(transactionId).client;
  }
  
  /**
   * Lists all active transactions
   * 
   * @returns List of active transaction information
   */
  listActiveTransactions(): TransactionInfo[] {
    return Array.from(this.activeTransactions.values())
      .map(transaction => ({ ...transaction.info }));
  }
  
  /**
   * Cleans up all transactions when shutting down
   */
  async cleanup(): Promise<void> {
    this.logger.debug(`Cleaning up ${this.activeTransactions.size} active transactions`);
    
    const transactionIds = Array.from(this.activeTransactions.keys());
    
    for (const id of transactionIds) {
      try {
        await this.rollbackTransaction(id);
      } catch (error) {
        this.logger.error(`Error cleaning up transaction ${id}`, error);
      }
    }
  }
  
  /**
   * Helper method to get a transaction by ID
   * 
   * @param transactionId Transaction ID
   * @returns Transaction object
   * @throws Error if transaction not found
   */
  private getTransaction(transactionId: string): { 
    client: PoolClient; 
    info: TransactionInfo; 
    timeoutId?: NodeJS.Timeout; 
  } {
    const transaction = this.activeTransactions.get(transactionId);
    
    if (!transaction) {
      throw this.createError(
        `Transaction not found: ${transactionId}`,
        'transaction_error'
      );
    }
    
    if (transaction.info.status !== TransactionStatus.ACTIVE) {
      throw this.createError(
        `Transaction is not active: ${transactionId} (Status: ${transaction.info.status})`,
        'transaction_error'
      );
    }
    
    return transaction;
  }
  
  /**
   * Cleans up resources for a transaction
   * 
   * @param transactionId Transaction ID
   */
  private cleanupTransaction(transactionId: string): void {
    const transaction = this.activeTransactions.get(transactionId);
    
    if (transaction) {
      // Clear the timeout if it exists
      if (transaction.timeoutId) {
        clearTimeout(transaction.timeoutId);
      }
      
      // Release the client back to the pool
      transaction.client.release();
      
      // Remove from active transactions
      this.activeTransactions.delete(transactionId);
    }
  }
  
  /**
   * Handles transaction timeout
   * 
   * @param transactionId Transaction ID
   */
  private async handleTransactionTimeout(transactionId: string): Promise<void> {
    const transaction = this.activeTransactions.get(transactionId);
    
    if (transaction && transaction.info.status === TransactionStatus.ACTIVE) {
      this.logger.warn(`Transaction ${transactionId} timed out after ${transaction.info.timeout}ms`);
      
      try {
        await transaction.client.query('ROLLBACK');
        transaction.info.status = TransactionStatus.ROLLED_BACK;
        transaction.info.completedAt = new Date();
        transaction.info.error = 'Transaction timed out';
      } catch (error: any) {
        this.logger.error(`Error rolling back timed out transaction ${transactionId}`, error);
        transaction.info.status = TransactionStatus.ERROR;
        transaction.info.error = `Timeout rollback failed: ${error.message}`;
      }
      
      this.cleanupTransaction(transactionId);
    }
  }
} 