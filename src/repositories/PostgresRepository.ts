/**
 * PostgreSQL Repository implementation
 * 
 * Base repository implementation for PostgreSQL database operations
 * with common CRUD operations and transaction support.
 */

import { PoolClient } from 'pg';
import { DatabaseException } from '../utils/exceptions';
import { createComponentLogger } from '../utils/logger';
import { PostgresConnection } from '../database/PostgresConnection';
import { ConditionOperator, PostgresQueryBuilder } from '../database/PostgresQueryBuilder';

/**
 * Type for entity identifiers
 */
export type EntityId = string | number;

/**
 * Transaction callback type
 */
export type TransactionCallback<T extends Record<string, any>, R> = (repository: PostgresRepository<T>) => Promise<R>;

/**
 * Base PostgreSQL repository with generic CRUD operations
 */
export abstract class PostgresRepository<T extends Record<string, any>> {
  /**
   * Logger for this repository
   */
  protected logger;
  
  /**
   * Current client for transaction support
   */
  protected client: PoolClient | null = null;

  /**
   * Creates a new repository
   * 
   * @param connection PostgreSQL connection
   * @param tableName Database table name
   * @param schemaName Database schema name (defaults to 'public')
   */
  constructor(
    protected connection: PostgresConnection,
    protected tableName: string,
    protected schemaName: string = 'public'
  ) {
    this.logger = createComponentLogger(`PostgresRepository:${tableName}`);
  }

  /**
   * Initialize the repository
   */
  async initialize(): Promise<void> {
    // Default implementation does nothing
    return Promise.resolve();
  }

  /**
   * Maps a database row to an entity
   * 
   * @param row Database row
   * @returns Entity instance
   */
  protected abstract mapToEntity(row: Record<string, any>): T;

  /**
   * Maps an entity to a database row
   * 
   * @param entity Entity to map
   * @returns Database row representation
   */
  protected abstract mapToRow(entity: T): Record<string, any>;

  /**
   * Creates a new entity
   * 
   * @param entity Entity to create
   * @returns Created entity with generated ID
   */
  async create(entity: T): Promise<T> {
    const row = this.mapToRow(entity);
    
    const columns = Object.keys(row);
    const values = Object.values(row);
    const placeholders = columns.map((_, i) => `$${i + 1}`).join(', ');
    
    const query = `
      INSERT INTO ${this.schemaName}.${this.tableName} 
      (${columns.join(', ')}) 
      VALUES (${placeholders})
      RETURNING *
    `;
    
    const result = await this.executeQuery(query, values);
    return this.mapToEntity(result.rows[0]);
  }

  /**
   * Finds all entities with optional limit/offset
   * 
   * @param limit Maximum number of entities to return
   * @param offset Number of entities to skip
   * @returns Array of entities
   */
  async findAll(limit: number = 100, offset: number = 0): Promise<T[]> {
    const queryBuilder = new PostgresQueryBuilder()
      .select(['*'])
      .from(`${this.schemaName}.${this.tableName}`)
      .limit(limit)
      .offset(offset);
    
    const query = queryBuilder.buildQuery();
    const params = queryBuilder.getParameters();
    
    const result = await this.executeQuery(query, params);
    return result.rows.map((row: Record<string, any>) => this.mapToEntity(row));
  }

  /**
   * Finds an entity by its ID
   * 
   * @param id Entity ID
   * @returns Entity or null if not found
   */
  async findById(id: EntityId): Promise<T | null> {
    const queryBuilder = new PostgresQueryBuilder()
      .select(['*'])
      .from(`${this.schemaName}.${this.tableName}`)
      .where('id', ConditionOperator.EQUALS, id);
    
    const query = queryBuilder.buildQuery();
    const params = queryBuilder.getParameters();
    
    const result = await this.executeQuery(query, params);
    
    if (result.rows.length === 0) {
      return null;
    }
    
    return this.mapToEntity(result.rows[0]);
  }

  /**
   * Updates an entity by ID
   * 
   * @param id Entity ID
   * @param updates Partial entity with fields to update
   * @returns Updated entity
   */
  async update(id: EntityId, updates: Partial<T>): Promise<T> {
    const row = this.mapToRow(updates as T);
    
    // Don't update ID field
    delete row.id;
    
    if (Object.keys(row).length === 0) {
      throw new DatabaseException('No fields to update');
    }
    
    const sets = Object.entries(row).map(([column, _], i) => `${column} = $${i + 1}`);
    const values = Object.values(row);
    
    // Add ID as the last parameter
    const query = `
      UPDATE ${this.schemaName}.${this.tableName}
      SET ${sets.join(', ')}
      WHERE id = $${values.length + 1}
      RETURNING *
    `;
    
    values.push(id);
    
    const result = await this.executeQuery(query, values);
    
    if (result.rows.length === 0) {
      throw new DatabaseException(`Entity with ID ${id} not found`);
    }
    
    return this.mapToEntity(result.rows[0]);
  }

  /**
   * Deletes an entity by ID
   * 
   * @param id Entity ID
   * @returns True if entity was deleted, false if not found
   */
  async delete(id: EntityId): Promise<boolean> {
    const query = `
      DELETE FROM ${this.schemaName}.${this.tableName}
      WHERE id = $1
      RETURNING id
    `;
    
    const result = await this.executeQuery(query, [id]);
    return result.rows.length > 0;
  }

  /**
   * Counts entities with optional filter
   * 
   * @param filter Optional filter condition
   * @returns Number of entities
   */
  async count(filter?: Record<string, any>): Promise<number> {
    const queryBuilder = new PostgresQueryBuilder()
      .select(['COUNT(*) as count'])
      .from(`${this.schemaName}.${this.tableName}`);
    
    if (filter) {
      Object.entries(filter).forEach(([column, value]) => {
        queryBuilder.where(column, ConditionOperator.EQUALS, value);
      });
    }
    
    const query = queryBuilder.buildQuery();
    const params = queryBuilder.getParameters();
    
    const result = await this.executeQuery(query, params);
    return parseInt(result.rows[0].count, 10);
  }

  /**
   * Helper method to execute queries through the connection
   * 
   * @param text SQL query text
   * @param params Query parameters
   * @returns Query result
   */
  private async executeQuery(text: string, params?: any[]): Promise<any> {
    if (this.client) {
      return this.client.query(text, params);
    }
    return this.connection.query(text, params);
  }

  /**
   * Executes operations in a transaction
   * 
   * @param callback Callback to execute within transaction
   * @returns Result of the transaction callback
   */
  async withTransaction<R>(callback: TransactionCallback<T, R>): Promise<R> {
    const client = await this.connection.getClient();
    
    try {
      await client.query('BEGIN');
      
      // Create a new transactional repository
      const transactionalRepo = Object.create(this);
      transactionalRepo.client = client;
      
      const result = await callback(transactionalRepo);
      
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }
} 