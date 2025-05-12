/**
 * Schema Service Implementation
 * 
 * This service manages PostgreSQL schema operations, providing a higher-level
 * interface to work with database schemas, tables, views, and other objects.
 */

import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { PostgresSchemaManager } from '../database/PostgresSchemaManager';
import { TableInfo, ColumnInfo } from '../core/types';
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
  constructor(connection: PostgresConnection) {
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
  async listSchemas(options: SchemaListOptions = {}): Promise<any[]> {
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
      
      // Map PostgresSchemaManager's TableInfo to our core TableInfo
      const pgTables = await this.schemaManager.listTables(schemaName, includeViews);
      const tables: TableInfo[] = [];
      
      for (const pgTable of pgTables) {
        const columns = await this.schemaManager.getTableColumns(pgTable.tableName, schemaName);
        const mappedColumns: ColumnInfo[] = columns.map(col => ({
          name: col.columnName,
          type: col.dataType,
          description: col.description,
          isNullable: col.isNullable,
          isPrimaryKey: false, // Will be set later if needed
          isForeignKey: false, // Will be set later if needed
          isUnique: false,     // Will be set later if needed
          defaultValue: col.columnDefault
        }));
        
        tables.push({
          name: pgTable.tableName,
          schema: pgTable.schemaName,
          description: pgTable.description,
          columns: mappedColumns,
          isView: pgTable.tableType === 'VIEW' || pgTable.tableType === 'MATERIALIZED_VIEW'
        });
      }
      
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
      
      this.logger.debug(`Getting details for table ${schemaName}.${tableName}`, options);
      
      // First check if table exists
      const pgTables = await this.schemaManager.listTables(schemaName, true);
      const pgTable = pgTables.find(t => t.tableName === tableName);
      
      if (!pgTable) {
        throw this.createError(
          `Table "${schemaName}.${tableName}" does not exist`,
          'validation_error'
        );
      }
      
      // Get columns
      const pgColumns = await this.schemaManager.getTableColumns(tableName, schemaName);
      
      // Get primary key
      const primaryKeyColumns = await this.schemaManager.getPrimaryKeyColumns(tableName, schemaName);
      
      // Get constraints for foreign keys
      interface ForeignKeyInfo {
        columns: string[];
        referencedTable: string;
        referencedSchema: string;
        referencedColumns: string[];
      }
      
      let foreignKeys: ForeignKeyInfo[] | undefined = undefined;
      if (includeRelations) {
        const constraints = await this.schemaManager.getTableConstraints(tableName, schemaName);
        foreignKeys = constraints
          .filter(c => c.constraintType === 'FOREIGN KEY')
          .map(fk => ({
            columns: fk.columnNames || [],
            referencedTable: fk.foreignTable || '',
            referencedSchema: fk.foreignSchema || '',
            referencedColumns: fk.foreignColumns || []
          }));
      }
      
      // Get indexes - already handled by PostgresSchemaManager
      if (includeIndexes) {
        await this.schemaManager.getTableIndexes(tableName, schemaName);
      }
      
      // Map columns
      const columns: ColumnInfo[] = pgColumns.map(col => {
        const isPrimaryKey = primaryKeyColumns.includes(col.columnName);
        // Check if column is part of any foreign key
        const isForeignKey = foreignKeys?.some(fk => 
          (fk.columns || []).includes(col.columnName)
        ) || false;
        
        return {
          name: col.columnName,
          type: col.dataType,
          description: col.description,
          isNullable: col.isNullable,
          isPrimaryKey,
          isForeignKey,
          isUnique: false, // Would need to check constraints/indexes
          defaultValue: col.columnDefault
        };
      });
      
      // Combine everything into a comprehensive table info object
      return {
        name: tableName,
        schema: schemaName,
        description: pgTable.description,
        columns,
        primaryKey: primaryKeyColumns,
        foreignKeys,
        isView: pgTable.tableType === 'VIEW' || pgTable.tableType === 'MATERIALIZED_VIEW'
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
      const pgTables = await this.schemaManager.listTables(schemaName, true);
      return pgTables.some(t => t.tableName === tableName);
    } catch (error: any) {
      this.logger.error(`Error checking if table exists: ${schemaName}.${tableName}`, error);
      throw this.createError(
        `Failed to check if table exists: ${error.message}`,
        error.errorType || 'database_error',
        error.details
      );
    }
  }
  
  /**
   * Gets columns for a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name
   * @returns List of columns
   */
  async getTableColumns(tableName: string, schemaName: string = 'public'): Promise<ColumnInfo[]> {
    try {
      const pgColumns = await this.schemaManager.getTableColumns(tableName, schemaName);
      
      // Convert from PostgresSchemaManager's ColumnInfo to our core ColumnInfo
      return pgColumns.map(col => ({
        name: col.columnName,
        type: col.dataType,
        description: col.description,
        isNullable: col.isNullable,
        isPrimaryKey: false, // Would need more info
        isForeignKey: false, // Would need more info
        isUnique: false,     // Would need more info
        defaultValue: col.columnDefault
      }));
    } catch (error: any) {
      this.logger.error(`Error getting columns for table: ${schemaName}.${tableName}`, error);
      throw this.createError(
        `Failed to get table columns: ${error.message}`,
        error.errorType || 'database_error',
        error.details
      );
    }
  }
} 