/**
 * PostgreSQL Repository
 * 
 * Base repository implementation for PostgreSQL database access.
 * Provides common CRUD operations and transaction support.
 */

import { RepositoryBase } from './RepositoryBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { PostgresQueryBuilder, ConditionOperator, OrderDirection } from '../database/PostgresQueryBuilder';
import { QueryException, DatabaseException } from '../utils/exceptions';
import { createComponentLogger } from '../utils/logger';

/**
 * Options for find operations
 */
export interface FindOptions {
  limit?: number;
  offset?: number;
  orderBy?: { field: string; direction?: OrderDirection };
  relations?: string[];
}

/**
 * Base PostgreSQL repository implementation
 */
export abstract class PostgresRepository<T extends Record<string, any>> implements RepositoryBase<T> {
  protected connection: PostgresConnection;
  protected tableName: string;
  protected primaryKey: string;
  protected logger = createComponentLogger('PostgresRepository');

  /**
   * Creates a new PostgreSQL repository
   * 
   * @param connection PostgreSQL connection
   * @param tableName Table name
   * @param primaryKey Primary key field name (default: 'id')
   */
  constructor(connection: PostgresConnection, tableName: string, primaryKey: string = 'id') {
    this.connection = connection;
    this.tableName = tableName;
    this.primaryKey = primaryKey;
    this.logger.debug(`Repository initialized for table: ${tableName}`);
  }

  /**
   * Maps a database row to an entity
   * 
   * @param row Database row
   * @returns Entity object
   */
  protected abstract mapToEntity(row: Record<string, any>): T;

  /**
   * Maps an entity to a database row
   * 
   * @param entity Entity object
   * @returns Database row
   */
  protected abstract mapToRow(entity: T): Record<string, any>;

  /**
   * Finds all entities matching the given criteria
   * 
   * @param criteria Search criteria
   * @param options Find options
   * @returns Array of entities
   */
  async findAll(criteria: Partial<T> = {}, options: FindOptions = {}): Promise<T[]> {
    try {
      const queryBuilder = new PostgresQueryBuilder()
        .select()
        .from(this.tableName);

      // Apply search criteria as WHERE conditions
      Object.entries(criteria).forEach(([field, value]) => {
        if (value !== undefined) {
          if (value === null) {
            queryBuilder.where(field, ConditionOperator.IS_NULL);
          } else if (Array.isArray(value)) {
            queryBuilder.where(field, ConditionOperator.IN, value);
          } else {
            queryBuilder.where(field, ConditionOperator.EQUALS, value);
          }
        }
      });

      // Apply pagination
      if (options.limit !== undefined) {
        queryBuilder.limit(options.limit);
      }
      
      if (options.offset !== undefined) {
        queryBuilder.offset(options.offset);
      }

      // Apply ordering
      if (options.orderBy) {
        queryBuilder.orderBy(
          options.orderBy.field,
          options.orderBy.direction || OrderDirection.ASC
        );
      }

      // Execute the query
      const query = queryBuilder.buildQuery();
      const params = queryBuilder.getParameters();
      this.logger.debug(`Executing findAll query: ${query} with params: ${JSON.stringify(params)}`);
      
      const result = await this.connection.query(query, params);
      return result.rows.map(row => this.mapToEntity(row));
    } catch (error: any) {
      this.logger.error('Error in findAll', error);
      throw new DatabaseException(`Error in findAll: ${error.message}`, error);
    }
  }

  /**
   * Finds one entity matching the given criteria
   * 
   * @param criteria Search criteria
   * @returns Entity or null if not found
   */
  async findOne(criteria: Partial<T> = {}): Promise<T | null> {
    try {
      const results = await this.findAll(criteria, { limit: 1 });
      return results.length > 0 ? results[0] : null;
    } catch (error: any) {
      this.logger.error('Error in findOne', error);
      throw new DatabaseException(`Error in findOne: ${error.message}`, error);
    }
  }

  /**
   * Finds an entity by its primary key
   * 
   * @param id Primary key value
   * @returns Entity or null if not found
   */
  async findById(id: string | number): Promise<T | null> {
    try {
      const criteria = { [this.primaryKey]: id } as Partial<T>;
      return await this.findOne(criteria);
    } catch (error: any) {
      this.logger.error(`Error in findById: ${id}`, error);
      throw new DatabaseException(`Error in findById: ${error.message}`, error);
    }
  }

  /**
   * Creates a new entity
   * 
   * @param entity Entity to create
   * @returns Created entity with generated ID
   */
  async create(entity: T): Promise<T> {
    try {
      const row = this.mapToRow(entity);
      
      const queryBuilder = new PostgresQueryBuilder()
        .insert(this.tableName, row)
        .returning(['*']);
      
      const query = queryBuilder.buildQuery();
      const params = queryBuilder.getParameters();
      this.logger.debug(`Executing create query: ${query} with params: ${JSON.stringify(params)}`);
      
      const result = await this.connection.query(query, params);
      return this.mapToEntity(result.rows[0]);
    } catch (error: any) {
      this.logger.error('Error in create', error);
      throw new DatabaseException(`Error in create: ${error.message}`, error);
    }
  }

  /**
   * Updates an existing entity
   * 
   * @param id Primary key value
   * @param entity Entity data to update
   * @returns Updated entity
   */
  async update(id: string | number, entity: Partial<T>): Promise<T | null> {
    try {
      const row = this.mapToRow(entity as T);
      
      // Remove primary key from update data if present
      delete row[this.primaryKey];
      
      // If there's nothing to update, return the current entity
      if (Object.keys(row).length === 0) {
        return this.findById(id);
      }
      
      const queryBuilder = new PostgresQueryBuilder()
        .update(this.tableName, row)
        .where(this.primaryKey, ConditionOperator.EQUALS, id)
        .returning(['*']);
      
      const query = queryBuilder.buildQuery();
      const params = queryBuilder.getParameters();
      this.logger.debug(`Executing update query: ${query} with params: ${JSON.stringify(params)}`);
      
      const result = await this.connection.query(query, params);
      
      if (result.rowCount === 0) {
        return null;
      }
      
      return this.mapToEntity(result.rows[0]);
    } catch (error: any) {
      this.logger.error(`Error in update: ${id}`, error);
      throw new DatabaseException(`Error in update: ${error.message}`, error);
    }
  }

  /**
   * Deletes an entity by its primary key
   * 
   * @param id Primary key value
   * @returns true if deleted, false if not found
   */
  async delete(id: string | number): Promise<boolean> {
    try {
      const queryBuilder = new PostgresQueryBuilder()
        .delete(this.tableName)
        .where(this.primaryKey, ConditionOperator.EQUALS, id);
      
      const query = queryBuilder.buildQuery();
      const params = queryBuilder.getParameters();
      this.logger.debug(`Executing delete query: ${query} with params: ${JSON.stringify(params)}`);
      
      const result = await this.connection.query(query, params);
      return result.rowCount > 0;
    } catch (error: any) {
      this.logger.error(`Error in delete: ${id}`, error);
      throw new DatabaseException(`Error in delete: ${error.message}`, error);
    }
  }

  /**
   * Executes a raw SQL query
   * 
   * @param sql SQL query
   * @param params Query parameters
   * @returns Query result
   */
  async query(sql: string, params: any[] = []): Promise<any> {
    try {
      this.logger.debug(`Executing raw query: ${sql} with params: ${JSON.stringify(params)}`);
      return await this.connection.query(sql, params);
    } catch (error: any) {
      this.logger.error('Error in query execution', error);
      throw new DatabaseException(`Error in query execution: ${error.message}`, error);
    }
  }

  /**
   * Executes a function within a transaction
   * 
   * @param callback Function to execute within the transaction
   * @returns Result of the callback function
   */
  async withTransaction<R>(callback: (repository: this) => Promise<R>): Promise<R> {
    // Start a transaction
    const client = await this.connection.getClient();
    
    try {
      await client.query('BEGIN');
      
      // Create a temporary repository with the transaction client
      const transactionRepo = Object.create(this);
      transactionRepo.connection = {
        query: (sql: string, params: any[] = []) => client.query(sql, params),
        getClient: () => Promise.resolve(client)
      } as any;
      
      // Execute the callback with the transactional repository
      const result = await callback(transactionRepo);
      
      // Commit the transaction
      await client.query('COMMIT');
      
      return result;
    } catch (error: any) {
      // Rollback the transaction on error
      await client.query('ROLLBACK');
      this.logger.error('Transaction rolled back', error);
      throw new DatabaseException(`Transaction failed: ${error.message}`, error);
    } finally {
      // Release the client back to the pool
      client.release();
    }
  }

  /**
   * Counts entities matching the given criteria
   * 
   * @param criteria Search criteria
   * @returns Number of matching entities
   */
  async count(criteria: Partial<T> = {}): Promise<number> {
    try {
      const queryBuilder = new PostgresQueryBuilder()
        .select(['COUNT(*) as count'])
        .from(this.tableName);

      // Apply search criteria as WHERE conditions
      Object.entries(criteria).forEach(([field, value]) => {
        if (value !== undefined) {
          if (value === null) {
            queryBuilder.where(field, ConditionOperator.IS_NULL);
          } else if (Array.isArray(value)) {
            queryBuilder.where(field, ConditionOperator.IN, value);
          } else {
            queryBuilder.where(field, ConditionOperator.EQUALS, value);
          }
        }
      });

      const query = queryBuilder.buildQuery();
      const params = queryBuilder.getParameters();
      this.logger.debug(`Executing count query: ${query} with params: ${JSON.stringify(params)}`);
      
      const result = await this.connection.query(query, params);
      return parseInt(result.rows[0].count, 10);
    } catch (error: any) {
      this.logger.error('Error in count', error);
      throw new DatabaseException(`Error in count: ${error.message}`, error);
    }
  }

  /**
   * Checks if any entity matches the given criteria
   * 
   * @param criteria Search criteria
   * @returns True if at least one entity matches, false otherwise
   */
  async exists(criteria: Partial<T> = {}): Promise<boolean> {
    const count = await this.count(criteria);
    return count > 0;
  }
} 