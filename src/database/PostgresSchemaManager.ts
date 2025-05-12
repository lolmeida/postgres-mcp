/**
 * PostgreSQL Schema Manager
 * 
 * This class handles schema-related operations such as retrieving table information,
 * column details, and other database metadata.
 */

import { PoolClient } from 'pg';
import { createComponentLogger } from '../utils/logger';
import { DatabaseException, QueryException, transformDbError } from '../utils/exceptions';
import { PostgresConnection } from './PostgresConnection';
import { schemaQueries } from './PostgresSchemaQueries';

/**
 * Database schema information
 */
export interface SchemaInfo {
  schemaName: string;
  isSystem: boolean;
  owner: string;
}

/**
 * Table information
 */
export interface TableInfo {
  schemaName: string;
  tableName: string;
  tableType: 'TABLE' | 'VIEW' | 'MATERIALIZED_VIEW' | 'FOREIGN_TABLE' | 'OTHER';
  owner: string;
  estimatedRowCount: number;
  description?: string;
}

/**
 * Column information
 */
export interface ColumnInfo {
  columnName: string;
  position: number;
  dataType: string;
  udtName: string;
  isNullable: boolean;
  columnDefault?: string;
  characterMaxLength?: number;
  numericPrecision?: number;
  numericScale?: number;
  isIdentity: boolean;
  identityGeneration?: string;
  isGenerated: boolean;
  generationExpression?: string;
  description?: string;
}

/**
 * Constraint information
 */
export interface ConstraintInfo {
  constraintName: string;
  constraintType: 'PRIMARY KEY' | 'FOREIGN KEY' | 'UNIQUE' | 'CHECK' | 'EXCLUSION';
  tableSchema: string;
  tableName: string;
  columnNames?: string[];
  foreignSchema?: string;
  foreignTable?: string;
  foreignColumns?: string[];
  updateRule?: string;
  deleteRule?: string;
  checkClause?: string;
  description?: string;
}

/**
 * Index information
 */
export interface IndexInfo {
  indexName: string;
  tableSchema: string;
  tableName: string;
  isUnique: boolean;
  isPrimary: boolean;
  columnNames: string[];
  indexDef: string;
}

/**
 * Function information
 */
export interface FunctionInfo {
  schemaName: string;
  functionName: string;
  returnType: string;
  argumentTypes: string[];
  argumentNames: string[];
  argumentDefaults: string[];
  language: string;
  functionType: 'FUNCTION' | 'PROCEDURE';
  volatility: 'IMMUTABLE' | 'STABLE' | 'VOLATILE';
  description?: string;
}

/**
 * PostgreSQL row types for internal use
 */
interface SchemaRow {
  schema_name: string;
  is_system: boolean;
  owner: string;
}

interface TableRow {
  schema_name: string;
  table_name: string;
  table_type: string;
  owner: string;
  estimated_row_count: number;
  description: string;
}

interface ColumnRow {
  position: number;
  column_name: string;
  data_type: string;
  udt_name: string;
  is_nullable: boolean;
  column_default: string;
  character_max_length: number | null;
  numeric_precision: number | null;
  numeric_scale: number | null;
  is_identity: boolean;
  identity_generation: string;
  is_generated: boolean;
  description: string;
}

interface ConstraintRow {
  constraint_name: string;
  constraint_type: string;
  table_schema: string;
  table_name: string;
  column_names: string[];
  foreign_schema: string | null;
  foreign_table: string | null;
  foreign_columns: string[] | null;
  update_rule: string | null;
  delete_rule: string | null;
  definition: string;
  description: string;
}

interface IndexRow {
  index_name: string;
  table_schema: string;
  table_name: string;
  is_unique: boolean;
  is_primary: boolean;
  column_names: string[];
  index_def: string;
}

interface FunctionRow {
  schema_name: string;
  function_name: string;
  return_type: string;
  argument_string: string;
  function_type: string;
  language: string;
  volatility: string | null;
  description: string;
}

/**
 * Class to manage PostgreSQL schema operations
 */
export class PostgresSchemaManager {
  private connection: PostgresConnection;
  private logger = createComponentLogger('PostgresSchemaManager');

  /**
   * Creates a new PostgreSQL schema manager
   * 
   * @param connection PostgreSQL connection
   */
  constructor(connection: PostgresConnection) {
    this.connection = connection;
    this.logger.debug('PostgreSQL schema manager initialized');
  }

  /**
   * Lists all schemas in the database
   * 
   * @param includeSystem Whether to include system schemas
   * @returns List of schemas
   */
  async listSchemas(includeSystem: boolean = false): Promise<SchemaInfo[]> {
    try {
      const query = schemaQueries.listSchemas.replace('${includeSystem ? \'TRUE\' : "nspname NOT LIKE \'pg_%\' AND nspname != \'information_schema\'"}', 
                                                     includeSystem ? 'TRUE' : "nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'");

      const result = await this.connection.query(query);

      return result.rows.map((row: SchemaRow) => ({
        schemaName: row.schema_name,
        isSystem: row.is_system,
        owner: row.owner
      }));
    } catch (error: any) {
      this.logger.error('Failed to list schemas', error);
      throw transformDbError(error);
    }
  }

  /**
   * Lists all tables in a schema
   * 
   * @param schemaName Schema name (default: 'public')
   * @param includeViews Whether to include views in the results
   * @returns List of tables
   */
  async listTables(schemaName: string = 'public', includeViews: boolean = false): Promise<TableInfo[]> {
    try {
      let tableTypeFilter = "c.relkind = 'r'"; // Regular tables
      
      if (includeViews) {
        tableTypeFilter = "(c.relkind = 'r' OR c.relkind = 'v' OR c.relkind = 'm' OR c.relkind = 'f')";
      }

      const query = schemaQueries.listTables.replace('${tableTypeFilter}', tableTypeFilter);

      const result = await this.connection.query(query, [schemaName]);

      return result.rows.map((row: TableRow) => ({
        schemaName: row.schema_name,
        tableName: row.table_name,
        tableType: row.table_type as TableInfo['tableType'],
        owner: row.owner,
        estimatedRowCount: row.estimated_row_count,
        description: row.description || undefined
      }));
    } catch (error: any) {
      this.logger.error(`Failed to list tables in schema: ${schemaName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Gets detailed information about a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name (default: 'public')
   * @returns Table information
   */
  async getTableInfo(tableName: string, schemaName: string = 'public'): Promise<TableInfo | null> {
    try {
      const query = schemaQueries.getTableInfo;

      const result = await this.connection.query(query, [schemaName, tableName]);

      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0] as TableRow;
      return {
        schemaName: row.schema_name,
        tableName: row.table_name,
        tableType: row.table_type as TableInfo['tableType'],
        owner: row.owner,
        estimatedRowCount: row.estimated_row_count,
        description: row.description || undefined
      };
    } catch (error: any) {
      this.logger.error(`Failed to get table info: ${schemaName}.${tableName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Gets column information for a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name (default: 'public')
   * @returns List of columns
   */
  async getTableColumns(tableName: string, schemaName: string = 'public'): Promise<ColumnInfo[]> {
    try {
      const query = schemaQueries.getTableColumns;

      const result = await this.connection.query(query, [schemaName, tableName]);

      return result.rows.map((row: ColumnRow) => ({
        position: row.position,
        columnName: row.column_name,
        dataType: row.data_type,
        udtName: row.udt_name,
        isNullable: row.is_nullable,
        columnDefault: row.column_default || undefined,
        characterMaxLength: row.character_max_length,
        numericPrecision: row.numeric_precision,
        numericScale: row.numeric_scale,
        isIdentity: row.is_identity,
        identityGeneration: row.identity_generation || undefined,
        isGenerated: row.is_generated,
        generationExpression: undefined, // This requires a separate query
        description: row.description || undefined
      }));
    } catch (error: any) {
      this.logger.error(`Failed to get columns for table: ${schemaName}.${tableName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Gets primary key columns for a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name (default: 'public')
   * @returns List of primary key column names
   */
  async getPrimaryKeyColumns(tableName: string, schemaName: string = 'public'): Promise<string[]> {
    try {
      const query = schemaQueries.getPrimaryKeyColumns;

      const result = await this.connection.query(query, [schemaName, tableName]);
      return result.rows.map((row: { column_name: string }) => row.column_name);
    } catch (error: any) {
      this.logger.error(`Failed to get primary key columns for table: ${schemaName}.${tableName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Gets constraints for a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name (default: 'public')
   * @returns List of constraints
   */
  async getTableConstraints(tableName: string, schemaName: string = 'public'): Promise<ConstraintInfo[]> {
    try {
      const query = schemaQueries.getTableConstraints;

      const result = await this.connection.query(query, [schemaName, tableName]);

      return result.rows.map((row: ConstraintRow) => ({
        constraintName: row.constraint_name,
        constraintType: row.constraint_type as ConstraintInfo['constraintType'],
        tableSchema: row.table_schema,
        tableName: row.table_name,
        columnNames: row.column_names,
        foreignSchema: row.foreign_schema || undefined,
        foreignTable: row.foreign_table || undefined,
        foreignColumns: row.foreign_columns || undefined,
        updateRule: row.update_rule || undefined,
        deleteRule: row.delete_rule || undefined,
        checkClause: row.constraint_type === 'CHECK' ? row.definition : undefined,
        description: row.description || undefined
      }));
    } catch (error: any) {
      this.logger.error(`Failed to get constraints for table: ${schemaName}.${tableName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Gets indexes for a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name (default: 'public')
   * @returns List of indexes
   */
  async getTableIndexes(tableName: string, schemaName: string = 'public'): Promise<IndexInfo[]> {
    try {
      const query = schemaQueries.getTableIndexes;

      const result = await this.connection.query(query, [schemaName, tableName]);

      return result.rows.map((row: IndexRow) => ({
        indexName: row.index_name,
        tableSchema: row.table_schema,
        tableName: row.table_name,
        isUnique: row.is_unique,
        isPrimary: row.is_primary,
        columnNames: row.column_names,
        indexDef: row.index_def
      }));
    } catch (error: any) {
      this.logger.error(`Failed to get indexes for table: ${schemaName}.${tableName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Lists functions in a schema
   * 
   * @param schemaName Schema name (default: 'public')
   * @returns List of functions
   */
  async listFunctions(schemaName: string = 'public'): Promise<FunctionInfo[]> {
    try {
      const query = schemaQueries.listFunctions;

      const result = await this.connection.query(query, [schemaName]);

      return await Promise.all(result.rows.map(async (row: FunctionRow) => {
        // Parse the function arguments to get their details
        const argDetails = await this.parseFunctionArguments(row.argument_string);
        
        return {
          schemaName: row.schema_name,
          functionName: row.function_name,
          returnType: row.return_type,
          argumentTypes: argDetails.types,
          argumentNames: argDetails.names,
          argumentDefaults: argDetails.defaults,
          language: row.language,
          functionType: row.function_type as FunctionInfo['functionType'],
          volatility: row.volatility as FunctionInfo['volatility'],
          description: row.description || undefined
        };
      }));
    } catch (error: any) {
      this.logger.error(`Failed to list functions in schema: ${schemaName}`, error);
      throw transformDbError(error);
    }
  }

  /**
   * Helper method to parse function arguments string
   * 
   * @param argumentString Argument string from pg_get_function_arguments
   * @returns Parsed argument details
   */
  private async parseFunctionArguments(argumentString: string): Promise<{
    names: string[];
    types: string[];
    defaults: string[];
  }> {
    // If empty string, return empty arrays
    if (!argumentString.trim()) {
      return { names: [], types: [], defaults: [] };
    }

    const names: string[] = [];
    const types: string[] = [];
    const defaults: string[] = [];

    // Split by commas, but respect parentheses (for complex types)
    const args = this.splitArguments(argumentString);

    args.forEach(arg => {
      // Format is typically: "argname argtype DEFAULT expression" or "argname argtype"
      const defaultMatch = arg.match(/DEFAULT\s+(.+)$/i);
      const defaultValue = defaultMatch ? defaultMatch[1].trim() : '';
      const withoutDefault = defaultMatch ? arg.substring(0, arg.indexOf('DEFAULT')).trim() : arg.trim();

      // The first word is the parameter name, the rest is the type
      const parts = withoutDefault.trim().split(/\s+/);
      const name = parts[0];
      const type = parts.slice(1).join(' ');

      names.push(name);
      types.push(type);
      defaults.push(defaultValue);
    });

    return { names, types, defaults };
  }

  /**
   * Helper method to split a comma-separated argument string while respecting parentheses
   * 
   * @param str The string to split
   * @returns Array of split arguments
   */
  private splitArguments(str: string): string[] {
    const result: string[] = [];
    let currentChunk = '';
    let parenCount = 0;

    for (let i = 0; i < str.length; i++) {
      const char = str[i];
      
      if (char === ',' && parenCount === 0) {
        result.push(currentChunk.trim());
        currentChunk = '';
      } else {
        currentChunk += char;
        if (char === '(') parenCount++;
        else if (char === ')') parenCount--;
      }
    }

    if (currentChunk.trim()) {
      result.push(currentChunk.trim());
    }

    return result;
  }

  /**
   * Gets database size information
   * 
   * @returns Database size information
   */
  async getDatabaseSize(): Promise<{
    databaseName: string;
    sizeBytes: number;
    prettySize: string;
  }> {
    try {
      const query = schemaQueries.getDatabaseSize;

      const result = await this.connection.query(query);
      
      return {
        databaseName: result.rows[0].database_name,
        sizeBytes: parseInt(result.rows[0].size_bytes, 10),
        prettySize: result.rows[0].pretty_size
      };
    } catch (error: any) {
      this.logger.error('Failed to get database size', error);
      throw transformDbError(error);
    }
  }

  /**
   * Gets the size of a table
   * 
   * @param tableName Table name
   * @param schemaName Schema name (default: 'public')
   * @returns Table size information
   */
  async getTableSize(tableName: string, schemaName: string = 'public'): Promise<{
    tableName: string;
    schemaName: string;
    sizeBytes: number;
    prettySize: string;
    totalSizeBytes: number;
    totalPrettySize: string;
  }> {
    try {
      const query = schemaQueries.getTableSize;

      const fullTableName = `${schemaName}.${tableName}`;
      const result = await this.connection.query(query, [fullTableName, schemaName, tableName]);
      
      if (result.rows.length === 0) {
        throw new QueryException(`Table not found: ${fullTableName}`);
      }
      
      return {
        tableName,
        schemaName,
        sizeBytes: parseInt(result.rows[0].size_bytes, 10),
        prettySize: result.rows[0].pretty_size,
        totalSizeBytes: parseInt(result.rows[0].total_size_bytes, 10),
        totalPrettySize: result.rows[0].total_pretty_size
      };
    } catch (error: any) {
      this.logger.error(`Failed to get table size: ${schemaName}.${tableName}`, error);
      throw transformDbError(error);
    }
  }
} 