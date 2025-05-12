/**
 * PostgreSQL Connection Manager
 * 
 * This class manages multiple PostgreSQL connections, providing a central point
 * for creating, retrieving, and closing database connections.
 */

import { createComponentLogger } from '../utils/logger';
import { InternalException } from '../utils/exceptions';
import { PostgresConnection } from './PostgresConnection';
import { PostgresConnectionConfig, PostgresConfigBuilder } from './PostgresConfig';
import { MCPConfig } from '../core/MCPConfig';

/**
 * Class to manage multiple PostgreSQL connections
 */
export class PostgresConnectionManager {
  private connections: Map<string, PostgresConnection> = new Map();
  private logger = createComponentLogger('PostgresConnectionManager');
  private defaultConnectionId: string | null = null;

  /**
   * Creates a new connection manager
   */
  constructor() {
    this.logger.debug('PostgreSQL connection manager initialized');
  }

  /**
   * Creates a new PostgreSQL connection
   * 
   * @param config PostgreSQL connection configuration
   * @param connectionId Optional connection identifier (defaults to 'default')
   * @returns The created connection
   */
  async createConnection(
    config: PostgresConnectionConfig,
    connectionId: string = 'default'
  ): Promise<PostgresConnection> {
    if (this.connections.has(connectionId)) {
      throw new InternalException(`Connection with ID '${connectionId}' already exists`);
    }

    this.logger.info(`Creating new PostgreSQL connection: ${connectionId}`);
    
    const connection = new PostgresConnection(config);
    
    try {
      await connection.initialize();
      this.connections.set(connectionId, connection);
      
      // Set as default connection if it's the first one or explicitly named 'default'
      if (this.defaultConnectionId === null || connectionId === 'default') {
        this.defaultConnectionId = connectionId;
      }
      
      return connection;
    } catch (error: any) {
      this.logger.error(`Failed to create connection: ${connectionId}`, error);
      // Close the connection to free resources
      await connection.close().catch(() => {});
      throw error;
    }
  }

  /**
   * Creates a connection from MCP configuration
   * 
   * @param config MCP configuration
   * @param connectionId Optional connection identifier (defaults to 'default')
   * @returns The created connection
   */
  async createConnectionFromMCPConfig(
    config: MCPConfig,
    connectionId: string = 'default'
  ): Promise<PostgresConnection> {
    // Create PostgreSQL config from MCP config
    const pgConfig = new PostgresConfigBuilder()
      .fromMCPConfig(config)
      .build();
    
    return this.createConnection(pgConfig, connectionId);
  }

  /**
   * Gets an existing connection by ID
   * 
   * @param connectionId Connection identifier (defaults to the default connection)
   * @returns The requested connection
   * @throws InternalException if connection does not exist
   */
  getConnection(connectionId?: string): PostgresConnection {
    const id = connectionId || this.defaultConnectionId;
    
    if (!id) {
      throw new InternalException('No default connection has been established');
    }
    
    const connection = this.connections.get(id);
    
    if (!connection) {
      throw new InternalException(`Connection with ID '${id}' does not exist`);
    }
    
    return connection;
  }

  /**
   * Checks if a connection with the given ID exists
   * 
   * @param connectionId Connection identifier
   * @returns True if the connection exists
   */
  hasConnection(connectionId: string): boolean {
    return this.connections.has(connectionId);
  }

  /**
   * Gets the default connection ID
   * 
   * @returns The default connection ID or null if none exists
   */
  getDefaultConnectionId(): string | null {
    return this.defaultConnectionId;
  }

  /**
   * Sets the default connection ID
   * 
   * @param connectionId Connection identifier to set as default
   * @throws InternalException if connection does not exist
   */
  setDefaultConnectionId(connectionId: string): void {
    if (!this.connections.has(connectionId)) {
      throw new InternalException(`Cannot set default: Connection with ID '${connectionId}' does not exist`);
    }
    
    this.defaultConnectionId = connectionId;
    this.logger.info(`Default connection set to: ${connectionId}`);
  }

  /**
   * Closes a specific connection
   * 
   * @param connectionId Connection identifier
   */
  async closeConnection(connectionId: string): Promise<void> {
    const connection = this.connections.get(connectionId);
    
    if (connection) {
      this.logger.info(`Closing PostgreSQL connection: ${connectionId}`);
      await connection.close();
      this.connections.delete(connectionId);
      
      // Update default connection if needed
      if (this.defaultConnectionId === connectionId) {
        this.defaultConnectionId = this.connections.size > 0 ? 
          Array.from(this.connections.keys())[0] : null;
      }
    }
  }

  /**
   * Closes all connections
   */
  async closeAllConnections(): Promise<void> {
    this.logger.info('Closing all PostgreSQL connections');
    
    const closePromises = Array.from(this.connections.entries()).map(
      async ([id, connection]) => {
        try {
          await connection.close();
          this.logger.debug(`Connection closed: ${id}`);
        } catch (error: any) {
          this.logger.error(`Error closing connection ${id}:`, error);
        }
      }
    );
    
    await Promise.all(closePromises);
    this.connections.clear();
    this.defaultConnectionId = null;
  }

  /**
   * Gets the number of active connections
   */
  getConnectionCount(): number {
    return this.connections.size;
  }

  /**
   * Gets all connection IDs
   */
  getConnectionIds(): string[] {
    return Array.from(this.connections.keys());
  }
} 