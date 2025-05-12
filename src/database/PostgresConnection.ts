/**
 * PostgreSQL Connection Manager
 * 
 * This class is responsible for managing connections to PostgreSQL databases,
 * providing connection pooling, error handling, and connection lifecycle management.
 */

import { Pool, PoolClient, types } from 'pg';
import fs from 'fs';
import { createComponentLogger } from '../utils/logger';
import { 
  DatabaseException, 
  TransactionException, 
  InternalException, 
  transformDbError 
} from '../utils/exceptions';
import { PostgresConnectionConfig } from './PostgresConfig';

/**
 * Transaction isolation levels supported by PostgreSQL
 */
export enum TransactionIsolationLevel {
  READ_UNCOMMITTED = 'READ UNCOMMITTED',
  READ_COMMITTED = 'READ COMMITTED',
  REPEATABLE_READ = 'REPEATABLE READ',
  SERIALIZABLE = 'SERIALIZABLE'
}

/**
 * Options for starting a transaction
 */
export interface TransactionOptions {
  /** 
   * Isolation level for the transaction 
   * @default TransactionIsolationLevel.READ_COMMITTED
   */
  isolationLevel?: TransactionIsolationLevel;

  /** 
   * Whether the transaction is read-only 
   * @default false
   */
  readOnly?: boolean;

  /** 
   * Transaction timeout in milliseconds 
   * @default 300000 (5 minutes)
   */
  timeoutMillis?: number;
}

/**
 * Class to manage PostgreSQL connections
 */
export class PostgresConnection {
  private pool: Pool;
  private logger: ReturnType<typeof createComponentLogger>;
  private config: PostgresConnectionConfig;
  private initialized: boolean = false;

  /**
   * Creates a new PostgreSQL connection manager
   * 
   * @param config PostgreSQL connection configuration
   */
  constructor(config: PostgresConnectionConfig) {
    this.config = config;
    this.logger = createComponentLogger('PostgresConnection');
    this.pool = this.createPool(config);
  }

  /**
   * Initializes the connection manager
   * This should be called before using any other methods
   */
  async initialize(): Promise<void> {
    if (this.initialized) {
      this.logger.warn('PostgreSQL connection already initialized');
      return;
    }

    // Configure PostgreSQL type parsers for better data handling
    this.configureTypeParsers();

    // Test the connection to ensure everything is working
    await this.testConnection();

    this.initialized = true;
    this.logger.info('PostgreSQL connection initialized successfully');
  }

  /**
   * Creates a connection pool based on configuration
   */
  private createPool(config: PostgresConnectionConfig): Pool {
    // Configure SSL if enabled
    const ssl = this.configureSsl(config);

    const poolConfig: any = {
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      min: config.poolMin,
      max: config.poolMax,
      connectionTimeoutMillis: config.connectionTimeoutMillis,
      idleTimeoutMillis: config.idleTimeoutMillis,
      ssl: ssl
    };

    // Add statement timeout if configured
    if (config.statementTimeout) {
      poolConfig.statement_timeout = config.statementTimeout;
    }

    this.logger.debug('Creating PostgreSQL connection pool', {
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      poolMin: config.poolMin,
      poolMax: config.poolMax,
      sslMode: config.sslMode
    });

    return new Pool(poolConfig);
  }

  /**
   * Configures SSL options based on configuration
   */
  private configureSsl(config: PostgresConnectionConfig): boolean | {[key: string]: any} {
    // Disable SSL completely
    if (config.sslMode === 'disable') {
      return false;
    }

    const sslConfig: {[key: string]: any} = {
      rejectUnauthorized: config.sslMode === 'verify-ca' || config.sslMode === 'verify-full'
    };

    // Add certificate files if provided and required
    if (config.sslCert && fs.existsSync(config.sslCert)) {
      sslConfig.cert = fs.readFileSync(config.sslCert).toString();
    }

    if (config.sslKey && fs.existsSync(config.sslKey)) {
      sslConfig.key = fs.readFileSync(config.sslKey).toString();
    }

    if (config.sslRootCert && fs.existsSync(config.sslRootCert)) {
      sslConfig.ca = fs.readFileSync(config.sslRootCert).toString();
    }

    return sslConfig;
  }

  /**
   * Configures custom type parsers for better data handling
   */
  private configureTypeParsers(): void {
    // Parse TIMESTAMP and TIMESTAMPTZ as ISO strings instead of Date objects
    types.setTypeParser(types.builtins.TIMESTAMP, (val) => val);
    types.setTypeParser(types.builtins.TIMESTAMPTZ, (val) => val);
    
    // Parse JSON and JSONB as objects
    types.setTypeParser(types.builtins.JSON, JSON.parse);
    types.setTypeParser(types.builtins.JSONB, JSON.parse);
  }

  /**
   * Tests the database connection
   */
  private async testConnection(): Promise<void> {
    let client: PoolClient;
    
    try {
      client = await this.pool.connect();
      
      const result = await client.query('SELECT current_database() as db, current_user as user, version() as version');
      
      this.logger.info(`Connected to PostgreSQL ${result.rows[0].version.split(' ')[1]}: ${result.rows[0].db} as ${result.rows[0].user}`);
      
      client.release();
    } catch (error: any) {
      if (client!) {
        client!.release(error);
      }
      
      this.logger.error('Failed to connect to PostgreSQL database', error);
      throw new DatabaseException(`Failed to connect to PostgreSQL: ${error.message}`, error);
    }
  }

  /**
   * Gets a client from the pool for running queries
   * The client must be released after use
   * 
   * @returns Client from the connection pool
   */
  async getClient(): Promise<PoolClient> {
    if (!this.initialized) {
      throw new InternalException('PostgreSQL connection not initialized');
    }
    
    try {
      return await this.pool.connect();
    } catch (error: any) {
      this.logger.error('Failed to get PostgreSQL client from pool', error);
      throw transformDbError(error);
    }
  }

  /**
   * Releases a client back to the pool
   * 
   * @param client Client to release
   * @param error Error to attach to client (if query failed)
   */
  releaseClient(client: PoolClient, error?: Error): void {
    client.release(error);
  }

  /**
   * Executes a query using the connection pool
   * 
   * @param text SQL query text
   * @param params Query parameters
   * @returns Query result
   */
  async query(text: string, params?: any[]): Promise<any> {
    if (!this.initialized) {
      throw new InternalException('PostgreSQL connection not initialized');
    }
    
    if (this.config.queryLogEnabled) {
      this.logger.debug('Executing SQL query', { query: text, params });
    }
    
    try {
      return await this.pool.query(text, params);
    } catch (error: any) {
      this.logger.error('Query failed', { query: text, params, error });
      throw transformDbError(error);
    }
  }

  /**
   * Begins a transaction and returns a transaction client
   * 
   * @param options Transaction options
   * @returns Client with active transaction
   */
  async beginTransaction(options: TransactionOptions = {}): Promise<PoolClient> {
    if (!this.initialized) {
      throw new InternalException('PostgreSQL connection not initialized');
    }
    
    // Set default options
    const isolationLevel = options.isolationLevel || TransactionIsolationLevel.READ_COMMITTED;
    const readOnly = options.readOnly || false;
    const timeoutMillis = options.timeoutMillis || 300000; // 5 minutes default
    
    const client = await this.getClient();
    
    try {
      // Set transaction timeout
      await client.query(`SET LOCAL statement_timeout = ${timeoutMillis}`);
      
      // Construct transaction start command with options
      let startCmd = 'BEGIN';
      
      if (isolationLevel || readOnly) {
        startCmd += ' TRANSACTION';
        
        if (isolationLevel) {
          startCmd += ` ISOLATION LEVEL ${isolationLevel}`;
        }
        
        if (readOnly) {
          startCmd += ' READ ONLY';
        }
      }
      
      await client.query(startCmd);
      
      this.logger.debug('Transaction started', { isolationLevel, readOnly });
      
      return client;
    } catch (error: any) {
      // Release client back to pool in case of error
      client.release(error);
      
      this.logger.error('Failed to begin transaction', error);
      throw new TransactionException(`Failed to begin transaction: ${error.message}`, error);
    }
  }

  /**
   * Commits an active transaction
   * 
   * @param client Client with active transaction
   */
  async commitTransaction(client: PoolClient): Promise<void> {
    try {
      await client.query('COMMIT');
      this.logger.debug('Transaction committed');
    } catch (error: any) {
      this.logger.error('Failed to commit transaction', error);
      throw new TransactionException(`Failed to commit transaction: ${error.message}`, error);
    } finally {
      client.release();
    }
  }

  /**
   * Rolls back an active transaction
   * 
   * @param client Client with active transaction
   */
  async rollbackTransaction(client: PoolClient): Promise<void> {
    try {
      await client.query('ROLLBACK');
      this.logger.debug('Transaction rolled back');
    } catch (error: any) {
      this.logger.error('Failed to rollback transaction', error);
      throw new TransactionException(`Failed to rollback transaction: ${error.message}`, error);
    } finally {
      client.release();
    }
  }

  /**
   * Creates a savepoint within a transaction
   * 
   * @param client Client with active transaction
   * @param name Savepoint name
   */
  async createSavepoint(client: PoolClient, name: string): Promise<void> {
    try {
      await client.query(`SAVEPOINT ${name}`);
      this.logger.debug(`Savepoint created: ${name}`);
    } catch (error: any) {
      this.logger.error(`Failed to create savepoint: ${name}`, error);
      throw new TransactionException(`Failed to create savepoint: ${error.message}`, error);
    }
  }

  /**
   * Rolls back to a savepoint within a transaction
   * 
   * @param client Client with active transaction
   * @param name Savepoint name
   */
  async rollbackToSavepoint(client: PoolClient, name: string): Promise<void> {
    try {
      await client.query(`ROLLBACK TO SAVEPOINT ${name}`);
      this.logger.debug(`Rolled back to savepoint: ${name}`);
    } catch (error: any) {
      this.logger.error(`Failed to rollback to savepoint: ${name}`, error);
      throw new TransactionException(`Failed to rollback to savepoint: ${error.message}`, error);
    }
  }

  /**
   * Releases a savepoint within a transaction
   * 
   * @param client Client with active transaction
   * @param name Savepoint name
   */
  async releaseSavepoint(client: PoolClient, name: string): Promise<void> {
    try {
      await client.query(`RELEASE SAVEPOINT ${name}`);
      this.logger.debug(`Savepoint released: ${name}`);
    } catch (error: any) {
      this.logger.error(`Failed to release savepoint: ${name}`, error);
      throw new TransactionException(`Failed to release savepoint: ${error.message}`, error);
    }
  }

  /**
   * Closes all connections in the pool
   */
  async close(): Promise<void> {
    if (this.pool) {
      this.logger.info('Closing PostgreSQL connection pool');
      await this.pool.end();
      this.initialized = false;
    }
  }

  /**
   * Gets the underlying pool instance
   */
  getPool(): Pool {
    return this.pool;
  }
} 