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
      const query = `
        SELECT
          nspname AS schema_name,
          nspname LIKE 'pg_%' OR nspname = 'information_schema' AS is_system,
          pg_catalog.pg_get_userbyid(nspowner) AS owner
        FROM pg_catalog.pg_namespace
        WHERE ${includeSystem ? 'TRUE' : "nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'"}
        ORDER BY schema_name;
      `;

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

      const query = `
        SELECT
          n.nspname AS schema_name,
          c.relname AS table_name,
          CASE
            WHEN c.relkind = 'r' THEN 'TABLE'
            WHEN c.relkind = 'v' THEN 'VIEW'
            WHEN c.relkind = 'm' THEN 'MATERIALIZED_VIEW'
            WHEN c.relkind = 'f' THEN 'FOREIGN_TABLE'
            ELSE 'OTHER'
          END AS table_type,
          pg_catalog.pg_get_userbyid(c.relowner) AS owner,
          COALESCE(pg_catalog.obj_description(c.oid, 'pg_class'), '') AS description,
          c.reltuples::bigint AS estimated_row_count
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE ${tableTypeFilter}
          AND n.nspname = $1
          AND c.relpersistence != 't'  -- exclude temporary tables
        ORDER BY table_name;
      `;

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
      const query = `
        SELECT
          n.nspname AS schema_name,
          c.relname AS table_name,
          CASE
            WHEN c.relkind = 'r' THEN 'TABLE'
            WHEN c.relkind = 'v' THEN 'VIEW'
            WHEN c.relkind = 'm' THEN 'MATERIALIZED_VIEW'
            WHEN c.relkind = 'f' THEN 'FOREIGN_TABLE'
            ELSE 'OTHER'
          END AS table_type,
          pg_catalog.pg_get_userbyid(c.relowner) AS owner,
          COALESCE(pg_catalog.obj_description(c.oid, 'pg_class'), '') AS description,
          c.reltuples::bigint AS estimated_row_count
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = $1 AND c.relname = $2
        LIMIT 1;
      `;

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
      const query = `
        SELECT
          a.attnum AS position,
          a.attname AS column_name,
          pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
          t.typname AS udt_name,
          a.attnotnull = false AS is_nullable,
          COALESCE(pg_catalog.pg_get_expr(ad.adbin, ad.adrelid), '') AS column_default,
          CASE 
            WHEN a.atttypid = ANY ('{int,int8,int2}'::regtype[]) AND EXISTS (
              SELECT 1 FROM pg_catalog.pg_attribute_identity ai WHERE ai.attrelid = a.attrelid AND ai.attnum = a.attnum
            ) THEN true
            ELSE false
          END AS is_identity,
          COALESCE(
            (SELECT pg_catalog.pg_get_serial_sequence(quote_ident(n.nspname) || '.' || quote_ident(c.relname), a.attname)),
            ''
          ) AS identity_generation,
          a.attgenerated <> '' AS is_generated,
          COALESCE(pg_catalog.col_description(a.attrelid, a.attnum), '') AS description,
          CASE 
            WHEN t.typname IN ('varchar', 'char', 'text', 'bpchar') THEN a.atttypmod - 4
            ELSE NULL
          END AS character_max_length,
          CASE 
            WHEN t.typname IN ('numeric', 'decimal') THEN (a.atttypmod - 4) >> 16
            ELSE NULL
          END AS numeric_precision,
          CASE 
            WHEN t.typname IN ('numeric', 'decimal') THEN (a.atttypmod - 4) & 65535
            ELSE NULL
          END AS numeric_scale
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
        LEFT JOIN pg_catalog.pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
        WHERE n.nspname = $1 
          AND c.relname = $2
          AND a.attnum > 0 
          AND NOT a.attisdropped
        ORDER BY a.attnum;
      `;

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
      const query = `
        SELECT a.attname AS column_name
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_catalog.pg_constraint con ON con.conrelid = c.oid
        WHERE n.nspname = $1
          AND c.relname = $2
          AND con.contype = 'p'
          AND a.attnum = ANY(con.conkey)
        ORDER BY array_position(con.conkey, a.attnum);
      `;

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
      const query = `
        SELECT
          con.conname AS constraint_name,
          CASE
            WHEN con.contype = 'p' THEN 'PRIMARY KEY'
            WHEN con.contype = 'f' THEN 'FOREIGN KEY'
            WHEN con.contype = 'u' THEN 'UNIQUE'
            WHEN con.contype = 'c' THEN 'CHECK'
            WHEN con.contype = 'x' THEN 'EXCLUSION'
            ELSE NULL
          END AS constraint_type,
          n.nspname AS table_schema,
          cl.relname AS table_name,
          ARRAY(
            SELECT attname 
            FROM pg_catalog.pg_attribute 
            WHERE attrelid = con.conrelid AND attnum = ANY(con.conkey)
            ORDER BY array_position(con.conkey, attnum)
          ) AS column_names,
          fn.nspname AS foreign_schema,
          fcl.relname AS foreign_table,
          ARRAY(
            SELECT attname 
            FROM pg_catalog.pg_attribute 
            WHERE attrelid = con.confrelid AND attnum = ANY(con.confkey)
            ORDER BY array_position(con.confkey, attnum)
          ) AS foreign_columns,
          CASE con.confupdtype
            WHEN 'a' THEN 'NO ACTION'
            WHEN 'r' THEN 'RESTRICT'
            WHEN 'c' THEN 'CASCADE'
            WHEN 'n' THEN 'SET NULL'
            WHEN 'd' THEN 'SET DEFAULT'
            ELSE NULL
          END AS update_rule,
          CASE con.confdeltype
            WHEN 'a' THEN 'NO ACTION'
            WHEN 'r' THEN 'RESTRICT'
            WHEN 'c' THEN 'CASCADE'
            WHEN 'n' THEN 'SET NULL'
            WHEN 'd' THEN 'SET DEFAULT'
            ELSE NULL
          END AS delete_rule,
          pg_catalog.pg_get_constraintdef(con.oid, true) AS definition,
          COALESCE(pg_catalog.obj_description(con.oid, 'pg_constraint'), '') AS description
        FROM pg_catalog.pg_constraint con
        JOIN pg_catalog.pg_class cl ON cl.oid = con.conrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = cl.relnamespace
        LEFT JOIN pg_catalog.pg_class fcl ON fcl.oid = con.confrelid
        LEFT JOIN pg_catalog.pg_namespace fn ON fn.oid = fcl.relnamespace
        WHERE n.nspname = $1 AND cl.relname = $2
        ORDER BY con.conname;
      `;

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
      const query = `
        SELECT
          i.relname AS index_name,
          n.nspname AS table_schema,
          t.relname AS table_name,
          ix.indisunique AS is_unique,
          ix.indisprimary AS is_primary,
          array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) AS column_names,
          pg_catalog.pg_get_indexdef(ix.indexrelid, 0, true) AS index_def
        FROM pg_catalog.pg_index ix
        JOIN pg_catalog.pg_class i ON i.oid = ix.indexrelid
        JOIN pg_catalog.pg_class t ON t.oid = ix.indrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
        JOIN pg_catalog.pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE n.nspname = $1 AND t.relname = $2
        GROUP BY i.relname, n.nspname, t.relname, ix.indisunique, ix.indisprimary, ix.indexrelid
        ORDER BY i.relname;
      `;

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
      const query = `
        SELECT
          n.nspname AS schema_name,
          p.proname AS function_name,
          pg_catalog.pg_get_function_result(p.oid) AS return_type,
          pg_catalog.pg_get_function_arguments(p.oid) AS argument_string,
          CASE 
            WHEN p.prokind = 'f' THEN 'FUNCTION'
            WHEN p.prokind = 'p' THEN 'PROCEDURE'
            ELSE p.prokind::text
          END AS function_type,
          l.lanname AS language,
          CASE
            WHEN p.provolatile = 'i' THEN 'IMMUTABLE'
            WHEN p.provolatile = 's' THEN 'STABLE'
            WHEN p.provolatile = 'v' THEN 'VOLATILE'
            ELSE NULL
          END AS volatility,
          COALESCE(pg_catalog.obj_description(p.oid, 'pg_proc'), '') AS description
        FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        JOIN pg_catalog.pg_language l ON l.oid = p.prolang
        LEFT JOIN pg_catalog.pg_description d ON p.oid = d.objoid
        WHERE n.nspname = $1
          AND p.prokind IN ('f', 'p')
        ORDER BY function_name;
      `;

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
      const query = `
        SELECT
          current_database() AS database_name,
          pg_database_size(current_database()) AS size_bytes,
          pg_size_pretty(pg_database_size(current_database())) AS pretty_size;
      `;

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
      const query = `
        SELECT
          pg_table_size($1) AS size_bytes,
          pg_size_pretty(pg_table_size($1)) AS pretty_size,
          pg_total_relation_size($1) AS total_size_bytes,
          pg_size_pretty(pg_total_relation_size($1)) AS total_pretty_size
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = $2 AND c.relname = $3
        LIMIT 1;
      `;

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