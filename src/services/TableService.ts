/**
 * Table Service Implementation
 * 
 * This service handles table operations, providing a higher-level abstraction
 * over the repository layer with additional business logic, validation, and error handling.
 */

import Joi from 'joi';
import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { PostgresRepository } from '../repositories/PostgresRepository';
import { createComponentLogger } from '../utils/logger';
import { TableInfo } from '../core/types';

/**
 * Represents a table operation result
 */
export interface TableOperationResult<T> {
  records: T[];
  count: number;
  metadata?: Record<string, any>;
}

/**
 * Filter options for table operations
 */
export interface TableFilterOptions {
  filter?: Record<string, any>;
  limit?: number;
  offset?: number;
  orderBy?: string | { column: string, direction: 'asc' | 'desc' }[];
}

/**
 * Generic repository factory function type
 */
type RepositoryFactory<T> = (connection: PostgresConnection, tableName: string, schemaName: string) => PostgresRepository<T>;

/**
 * Service for table operations
 */
export class TableService extends AbstractService {
  private logger;
  private repositories: Map<string, PostgresRepository<any>> = new Map();

  /**
   * Creates a new TableService instance
   * 
   * @param connection PostgreSQL connection
   */
  constructor(private connection: PostgresConnection) {
    super();
    this.logger = createComponentLogger('TableService');
  }

  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing TableService');
    return Promise.resolve();
  }

  /**
   * Gets or creates a repository for a specific table
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @param repositoryFactory Factory function to create a new repository instance
   * @returns Repository instance
   */
  getRepository<T extends Record<string, any>>(
    tableName: string,
    schemaName: string = 'public',
    repositoryFactory: RepositoryFactory<T>
  ): PostgresRepository<T> {
    const key = `${schemaName}.${tableName}`;
    
    if (!this.repositories.has(key)) {
      const repository = repositoryFactory(this.connection, tableName, schemaName);
      this.repositories.set(key, repository);
    }
    
    return this.repositories.get(key) as PostgresRepository<T>;
  }

  /**
   * Reads records from a table with filtering, pagination, and sorting
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @param options Filter options
   * @param repositoryFactory Factory function to create a repository instance
   * @returns Operation result with records and count
   */
  async readTable<T extends Record<string, any>>(
    tableName: string,
    schemaName: string = 'public',
    options: TableFilterOptions = {},
    repositoryFactory: RepositoryFactory<T>
  ): Promise<TableOperationResult<T>> {
    this.logger.debug(`Reading from table ${schemaName}.${tableName}`, options);
    
    // Validate inputs
    tableName = this.validateString('tableName', tableName);
    schemaName = this.validateString('schemaName', schemaName);
    
    const repository = this.getRepository<T>(tableName, schemaName, repositoryFactory);
    
    // For now we're just using findAll - this would be extended to support filters, ordering, etc.
    const records = await repository.findAll(options.limit || 100, options.offset || 0);
    const count = await repository.count(options.filter);
    
    return {
      records,
      count
    };
  }

  /**
   * Creates a new record in a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @param data Record data
   * @param repositoryFactory Factory function to create a repository instance
   * @returns Created record
   */
  async createRecord<T extends Record<string, any>>(
    tableName: string,
    schemaName: string = 'public',
    data: T,
    repositoryFactory: RepositoryFactory<T>
  ): Promise<T> {
    this.logger.debug(`Creating record in ${schemaName}.${tableName}`);
    
    // Validate inputs
    tableName = this.validateString('tableName', tableName);
    schemaName = this.validateString('schemaName', schemaName);
    
    if (!data || typeof data !== 'object') {
      throw this.createError('Data is required and must be an object', 'validation_error');
    }
    
    const repository = this.getRepository<T>(tableName, schemaName, repositoryFactory);
    return repository.create(data);
  }

  /**
   * Updates records in a table based on a filter
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @param id Record ID to update
   * @param data Update data
   * @param repositoryFactory Factory function to create a repository instance
   * @returns Updated record
   */
  async updateRecord<T extends Record<string, any>>(
    tableName: string,
    schemaName: string = 'public',
    id: string | number,
    data: Partial<T>,
    repositoryFactory: RepositoryFactory<T>
  ): Promise<T> {
    this.logger.debug(`Updating record ${id} in ${schemaName}.${tableName}`);
    
    // Validate inputs
    tableName = this.validateString('tableName', tableName);
    schemaName = this.validateString('schemaName', schemaName);
    
    if (!id) {
      throw this.createError('Record ID is required', 'validation_error');
    }
    
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
      throw this.createError('Update data is required and must be a non-empty object', 'validation_error');
    }
    
    const repository = this.getRepository<T>(tableName, schemaName, repositoryFactory);
    return repository.update(id, data);
  }

  /**
   * Deletes a record from a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @param id Record ID to delete
   * @param repositoryFactory Factory function to create a repository instance
   * @returns True if record was deleted, false otherwise
   */
  async deleteRecord<T extends Record<string, any>>(
    tableName: string,
    schemaName: string = 'public',
    id: string | number,
    repositoryFactory: RepositoryFactory<T>
  ): Promise<boolean> {
    this.logger.debug(`Deleting record ${id} from ${schemaName}.${tableName}`);
    
    // Validate inputs
    tableName = this.validateString('tableName', tableName);
    schemaName = this.validateString('schemaName', schemaName);
    
    if (!id) {
      throw this.createError('Record ID is required', 'validation_error');
    }
    
    const repository = this.getRepository<T>(tableName, schemaName, repositoryFactory);
    return repository.delete(id);
  }

  /**
   * Validates a string parameter
   * 
   * @param name Parameter name
   * @param value Parameter value
   * @returns Validated value
   */
  private validateString(name: string, value: any): string {
    const schema = Joi.string().required();
    const { error, value: validValue } = schema.validate(value);
    
    if (error) {
      throw this.createError(`Invalid ${name}: ${error.message}`, 'validation_error');
    }
    
    return validValue;
  }
} 