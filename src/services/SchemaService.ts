/**
 * Schema Service Implementation
 * 
 * This service manages PostgreSQL schema operations, providing a higher-level
 * interface to work with database schemas, tables, views, and other objects.
 */

import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { PostgresSchemaManager, SchemaInfo, TableInfo, ColumnInfo } from '../database/PostgresSchemaManager';
import { createComponentLogger } from '../utils/logger';

/**
 * Interface for schema listing options
 */
export interface SchemaListOptions {
  /**
   * Whether to include system schemas (pg_*, information_schema)
   */
  includeSystem?: boolean;
  
  /**
   * Limit the number of schemas returned
   */
  limit?: number;
  
  /**
   * Skip a number of schemas in the result
   */
  offset?: number;
}

/**
 * Interface for table listing options
 */
export interface TableListOptions {
  /**
   * Whether to include views in the results
   */
  includeViews?: boolean;
  
  /**
   * Limit the number of tables returned
   */
  limit?: number;
  
  /**
   * Skip a number of tables in the result
   */
  offset?: number;
}

/**
 * Interface for table details options
 */
export interface TableDetailOptions {
  /**
   * Whether to include relation information (foreign keys, etc)
   */
  includeRelations?: boolean;
  
  /**
   * Whether to include index information
   */
  includeIndexes?: boolean;
  
  /**
   * Whether to include comment/description information
   */
  includeComments?: boolean;
}

/**
 * Service for PostgreSQL schema management
 */
export class SchemaService extends AbstractService {
  private logger;
  private schemaManager: PostgresSchemaManager;
  
  /**
   * Creates a new SchemaService instance
   * 
   * @param connection PostgreSQL connection
   */
  constructor(private connection: PostgresConnection) {
    super();
    this.logger = createComponentLogger('SchemaService');
    this.schemaManager = new PostgresSchemaManager(connection);
  }
  
  /**
   * Initialize the service
   */
  async initialize(): Promise<void> {
    this.logger.debug('Initializing SchemaService');
    return Promise.resolve();
  }
  
  /**
   * Lists all schemas in the database
   * 
   * @param options Options for listing schemas
   * @returns List of schema information
   */
  async listSchemas(options: SchemaListOptions = {}): Promise<SchemaInfo[]> {
    try {
      const includeSystem = options.includeSystem || false;
      const limit = options.limit || 100;
      const offset = options.offset || 0;
      
      this.logger.debug('Listing schemas', options);
      const schemas = await this.schemaManager.listSchemas(includeSystem);
      
      // Apply pagination
      return schemas.slice(offset, offset + limit);
    } catch (error: any) {
      this.logger.error('Error listing schemas', error);
      throw this.createError(
        `Failed to list schemas: ${error.message}`,
        'database_error',
        error.details
      );
    }
  }
  
  /**
   * Lists tables in a schema
   * 
   * @param schemaName Schema name
   * @param options Options for listing tables
   * @returns List of tables
   */
  async listTables(
    schemaName: string = 'public',
    options: TableListOptions = {}
  ): Promise<TableInfo[]> {
    try {
      const includeViews = options.includeViews ?? true;
      const limit = options.limit || 100;
      const offset = options.offset || 0;
      
      this.logger.debug(`Listing tables in schema ${schemaName}`, options);
      
      // Validate schema exists
      const schemas = await this.schemaManager.listSchemas(true);
      const schemaExists = schemas.some(s => s.schemaName === schemaName);
      
      if (!schemaExists) {
        throw this.createError(
          `Schema "${schemaName}" does not exist`,
          'validation_error'
        );
      }
      
      const tables = await this.schemaManager.listTables(schemaName, includeViews);
      
      // Apply pagination
      return tables.slice(offset, offset + limit);
    } catch (error: any) {
      this.logger.error(`Error listing tables in schema ${schemaName}`, error);
      throw this.createError(
        `Failed to list tables: ${error.message}`,
        error.errorType || 'database_error',
        error.details
      );
    }
  }
  
  /**
   * Gets detailed information about a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @param options Table detail options
   * @returns Table information
   */
  async getTableDetails(
    tableName: string,
    schemaName: string = 'public',
    options: TableDetailOptions = {}
  ): Promise<TableInfo> {
    try {
      const includeRelations = options.includeRelations ?? true;
      const includeIndexes = options.includeIndexes ?? true;
      const includeComments = options.includeComments ?? true;
      
      this.logger.debug(`Getting details for table ${schemaName}.${tableName}`, options);
      
      // First check if table exists
      const tables = await this.schemaManager.listTables(schemaName, true);
      const table = tables.find(t => t.name === tableName);
      
      if (!table) {
        throw this.createError(
          `Table "${schemaName}.${tableName}" does not exist`,
          'validation_error'
        );
      }
      
      // Get columns
      const columns = await this.schemaManager.listTableColumns(tableName, schemaName);
      
      // Get primary key
      const primaryKey = await this.schemaManager.getPrimaryKey(tableName, schemaName);
      
      // Get foreign keys if requested
      let foreignKeys = undefined;
      if (includeRelations) {
        foreignKeys = await this.schemaManager.getForeignKeys(tableName, schemaName);
      }
      
      // Get indexes if requested
      let indexes = undefined;
      if (includeIndexes) {
        indexes = await this.schemaManager.getTableIndexes(tableName, schemaName);
      }
      
      // Get comments/descriptions if requested
      let description = table.description;
      if (includeComments && !description) {
        description = await this.schemaManager.getTableDescription(tableName, schemaName);
      }
      
      // Combine everything into a comprehensive table info object
      return {
        name: tableName,
        schema: schemaName,
        description,
        columns,
        primaryKey: primaryKey?.columnNames,
        foreignKeys,
        isView: table.isView
      };
    } catch (error: any) {
      this.logger.error(`Error getting details for table ${schemaName}.${tableName}`, error);
      throw this.createError(
        `Failed to get table details: ${error.message}`,
        error.errorType || 'database_error',
        error.details
      );
    }
  }
  
  /**
   * Checks if a table exists
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @returns True if the table exists
   */
  async tableExists(tableName: string, schemaName: string = 'public'): Promise<boolean> {
    try {
      this.logger.debug(`Checking if table ${schemaName}.${tableName} exists`);
      return await this.schemaManager.tableExists(tableName, schemaName);
    } catch (error: any) {
      this.logger.error(`Error checking if table ${schemaName}.${tableName} exists`, error);
      throw this.createError(
        `Failed to check if table exists: ${error.message}`,
        'database_error',
        error.details
      );
    }
  }
  
  /**
   * Gets column information for a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @returns List of column information
   */
  async getTableColumns(tableName: string, schemaName: string = 'public'): Promise<ColumnInfo[]> {
    try {
      this.logger.debug(`Getting columns for table ${schemaName}.${tableName}`);
      return await this.schemaManager.listTableColumns(tableName, schemaName);
    } catch (error: any) {
      this.logger.error(`Error getting columns for table ${schemaName}.${tableName}`, error);
      throw this.createError(
        `Failed to get table columns: ${error.message}`,
        'database_error',
        error.details
      );
    }
  }
} 