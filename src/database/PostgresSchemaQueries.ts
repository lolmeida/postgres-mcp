/**
 * PostgreSQL Schema Queries
 * 
 * This file contains all SQL queries used by the PostgresSchemaManager.
 * Separating the queries from the manager implementation improves code organization
 * and maintainability.
 */

/**
 * Queries for schema operations
 */
export const schemaQueries = {
  /**
   * Query to list all schemas in the database
   */
  listSchemas: `
    SELECT
      nspname AS schema_name,
      nspname LIKE 'pg_%' OR nspname = 'information_schema' AS is_system,
      pg_catalog.pg_get_userbyid(nspowner) AS owner
    FROM pg_catalog.pg_namespace
    WHERE \${includeSystem ? 'TRUE' : "nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'"}
    ORDER BY schema_name;
  `,

  /**
   * Query to list all tables in a schema
   */
  listTables: `
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
    WHERE \${tableTypeFilter}
      AND n.nspname = $1
      AND c.relpersistence != 't'  -- exclude temporary tables
    ORDER BY table_name;
  `,

  /**
   * Query to get detailed information about a table
   */
  getTableInfo: `
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
  `,

  /**
   * Query to get column information for a table
   */
  getTableColumns: `
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
  `,

  /**
   * Query to get primary key columns for a table
   */
  getPrimaryKeyColumns: `
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
  `,

  /**
   * Query to get constraints for a table
   */
  getTableConstraints: `
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
  `,

  /**
   * Query to get indexes for a table
   */
  getTableIndexes: `
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
  `,

  /**
   * Query to list functions in a schema
   */
  listFunctions: `
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
  `,

  /**
   * Query to get database size information
   */
  getDatabaseSize: `
    SELECT
      current_database() AS database_name,
      pg_database_size(current_database()) AS size_bytes,
      pg_size_pretty(pg_database_size(current_database())) AS pretty_size;
  `,

  /**
   * Query to get the size of a table
   */
  getTableSize: `
    SELECT
      pg_table_size($1) AS size_bytes,
      pg_size_pretty(pg_table_size($1)) AS pretty_size,
      pg_total_relation_size($1) AS total_size_bytes,
      pg_size_pretty(pg_total_relation_size($1)) AS total_pretty_size
    FROM pg_catalog.pg_class c
    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = $2 AND c.relname = $3
    LIMIT 1;
  `
}; 