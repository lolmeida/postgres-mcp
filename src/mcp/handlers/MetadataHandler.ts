/**
 * MCP MetadataHandler
 * 
 * Handler para obtenção de metadados sobre o banco de dados PostgreSQL
 * através do protocolo MCP.
 */

import { IMCPHandler } from '../router/MCPRouter';
import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { SchemaService } from '../../services/SchemaService';
import { PostgresConnection } from '../../database/PostgresConnection';
import { createComponentLogger } from '../../utils/logger';

/**
 * Handler para operações de metadados via MCP
 */
export class MetadataHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_metadata';
  private schemaService: SchemaService;
  private connection: PostgresConnection;
  private logger = createComponentLogger('MetadataHandler');

  /**
   * Cria uma nova instância do MetadataHandler
   * 
   * @param schemaService Serviço de schema a ser utilizado
   * @param connection Conexão com o banco de dados
   */
  constructor(schemaService: SchemaService, connection: PostgresConnection) {
    this.schemaService = schemaService;
    this.connection = connection;
  }

  /**
   * Processa requisições MCP para obtenção de metadados
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  async handle(request: MCPRequest): Promise<MCPResponse> {
    try {
      // Verifica qual operação deve ser executada com base na requisição
      const operation = request.parameters?.operation;

      if (!operation) {
        return MCPResponse.error(
          'Parâmetro obrigatório "operation" não fornecido',
          { 
            availableOperations: [
              'getDatabaseInfo', 'getServerInfo', 'getServerStats',
              'getTableStats', 'getColumnStats', 'listExtensions',
              'listDataTypes', 'getPostgresVersion', 'getSystemCatalogs'
            ] 
          },
          request.requestId
        );
      }

      switch (operation) {
        case 'getDatabaseInfo':
          return await this.handleGetDatabaseInfo(request);
        case 'getServerInfo':
          return await this.handleGetServerInfo(request);
        case 'getServerStats':
          return await this.handleGetServerStats(request);
        case 'getTableStats':
          return await this.handleGetTableStats(request);
        case 'getColumnStats':
          return await this.handleGetColumnStats(request);
        case 'listExtensions':
          return await this.handleListExtensions(request);
        case 'listDataTypes':
          return await this.handleListDataTypes(request);
        case 'getPostgresVersion':
          return await this.handleGetPostgresVersion(request);
        case 'getSystemCatalogs':
          return await this.handleGetSystemCatalogs(request);
        default:
          return MCPResponse.error(
            `Operação '${operation}' não suportada pelo handler de metadados`,
            { 
              availableOperations: [
                'getDatabaseInfo', 'getServerInfo', 'getServerStats',
                'getTableStats', 'getColumnStats', 'listExtensions',
                'listDataTypes', 'getPostgresVersion', 'getSystemCatalogs'
              ] 
            },
            request.requestId
          );
      }
    } catch (error) {
      this.logger.error(`Erro ao processar requisição de metadados: ${error.message}`, { 
        stack: error.stack,
        requestId: request.requestId
      });
      
      return MCPResponse.error(
        `Erro ao processar operação de metadados: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de obtenção de informações do banco de dados
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetDatabaseInfo(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo informações do banco de dados`, {
      requestId: request.requestId
    });

    // Executa a consulta para obter informações do banco de dados
    const result = await this.connection.query(`
      SELECT 
        d.datname AS database_name,
        pg_size_pretty(pg_database_size(d.datname)) AS database_size,
        u.usename AS owner,
        d.encoding,
        d.datcollate AS collation,
        d.datctype AS character_type,
        d.datistemplate AS is_template,
        d.datallowconn AS allows_connections,
        d.datconnlimit AS connection_limit,
        age(datfrozenxid) AS age,
        pg_tablespace_location(t.oid) AS tablespace_location
      FROM 
        pg_database d
        JOIN pg_user u ON d.datdba = u.usesysid
        JOIN pg_tablespace t ON d.dattablespace = t.oid
      WHERE 
        d.datname = current_database()
    `);

    if (result.records.length === 0) {
      return MCPResponse.error(
        'Não foi possível obter informações do banco de dados',
        null,
        request.requestId
      );
    }

    return MCPResponse.success(
      { database: result.records[0] },
      `Informações do banco de dados obtidas com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção de informações do servidor
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetServerInfo(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo informações do servidor`, {
      requestId: request.requestId
    });

    // Executa a consulta para obter informações do servidor
    const result = await this.connection.query(`
      SELECT 
        version() AS server_version,
        current_setting('max_connections') AS max_connections,
        current_setting('shared_buffers') AS shared_buffers,
        current_setting('effective_cache_size') AS effective_cache_size,
        current_setting('work_mem') AS work_mem,
        current_setting('maintenance_work_mem') AS maintenance_work_mem,
        current_setting('random_page_cost') AS random_page_cost,
        current_setting('seq_page_cost') AS seq_page_cost,
        current_setting('effective_io_concurrency') AS effective_io_concurrency,
        current_setting('max_worker_processes') AS max_worker_processes,
        current_setting('max_parallel_workers') AS max_parallel_workers,
        current_setting('max_parallel_workers_per_gather') AS max_parallel_workers_per_gather,
        current_setting('server_encoding') AS server_encoding,
        current_setting('datestyle') AS datestyle,
        current_setting('timezone') AS timezone
    `);

    return MCPResponse.success(
      { server: result.records[0] },
      `Informações do servidor obtidas com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção de estatísticas do servidor
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetServerStats(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo estatísticas do servidor`, {
      requestId: request.requestId
    });

    // Executa a consulta para obter estatísticas do servidor
    const connections = await this.connection.query(`
      SELECT 
        count(*) AS active_connections,
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') AS running_queries,
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') AS idle_connections,
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') AS idle_in_transaction
      FROM 
        pg_stat_activity
    `);

    const dbStats = await this.connection.query(`
      SELECT 
        pg_size_pretty(sum(pg_relation_size(pg_class.oid))::bigint) AS total_relation_size,
        (SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size),
        (SELECT COUNT(*) FROM pg_catalog.pg_namespace WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema') AS user_schema_count,
        (SELECT COUNT(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace 
         WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname != 'information_schema' AND c.relkind = 'r') AS table_count,
        (SELECT COUNT(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace 
         WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname != 'information_schema' AND c.relkind = 'v') AS view_count,
        (SELECT COUNT(*) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace 
         WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname != 'information_schema' AND c.relkind = 'i') AS index_count,
        (SELECT COUNT(*) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace 
         WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname != 'information_schema') AS function_count
      FROM 
        pg_catalog.pg_class
        JOIN pg_catalog.pg_namespace ON pg_namespace.oid = pg_class.relnamespace 
      WHERE 
        pg_namespace.nspname NOT LIKE 'pg_%' 
        AND pg_namespace.nspname != 'information_schema'
    `);

    // Listas alguns detalhes de desempenho
    const performance = await this.connection.query(`
      SELECT 
        (SELECT SUM(numbackends) FROM pg_stat_database) AS backends,
        (SELECT SUM(xact_commit) FROM pg_stat_database) AS commits,
        (SELECT SUM(xact_rollback) FROM pg_stat_database) AS rollbacks,
        (SELECT SUM(blks_read) FROM pg_stat_database) AS disk_blocks_read,
        (SELECT SUM(blks_hit) FROM pg_stat_database) AS buffer_blocks_hit,
        CASE WHEN (SELECT SUM(blks_read) FROM pg_stat_database) = 0 THEN 
          100
        ELSE
          round(100.0 * (SELECT SUM(blks_hit) FROM pg_stat_database) / ((SELECT SUM(blks_hit) FROM pg_stat_database) + (SELECT SUM(blks_read) FROM pg_stat_database)))
        END AS buffer_hit_ratio
    `);

    const stats = {
      connections: connections.records[0],
      database: dbStats.records[0],
      performance: performance.records[0],
      timestamp: new Date().toISOString()
    };

    return MCPResponse.success(
      { stats },
      `Estatísticas do servidor obtidas com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção de estatísticas de uma tabela
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetTableStats(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Obtendo estatísticas da tabela ${schemaName}.${tableName}`, {
      requestId: request.requestId
    });

    // Verifica se a tabela existe
    const tableExists = await this.connection.query(`
      SELECT EXISTS (
        SELECT 1 
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = $1 AND n.nspname = $2
      ) AS exists
    `, [tableName, schemaName]);

    if (!tableExists.records[0].exists) {
      return MCPResponse.error(
        `Tabela '${schemaName}.${tableName}' não encontrada`,
        null,
        request.requestId
      );
    }

    // Executa a consulta para obter estatísticas da tabela
    const basicStats = await this.connection.query(`
      SELECT
        c.relname AS table_name,
        n.nspname AS schema_name,
        c.reltuples::bigint AS row_estimate,
        pg_size_pretty(pg_relation_size(c.oid)) AS table_size,
        pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
        c.relhasindex AS has_indexes,
        c.relhaspkey AS has_primary_key,
        age(c.relfrozenxid) AS table_age,
        s.n_live_tup AS live_rows,
        s.n_dead_tup AS dead_rows,
        s.last_vacuum,
        s.last_autovacuum,
        s.last_analyze,
        s.last_autoanalyze,
        s.vacuum_count,
        s.autovacuum_count,
        s.analyze_count,
        s.autoanalyze_count
      FROM
        pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_catalog.pg_stat_user_tables s ON s.relname = c.relname AND s.schemaname = n.nspname
      WHERE
        c.relname = $1 AND n.nspname = $2
    `, [tableName, schemaName]);

    // Obter estatísticas de índices
    const indexStats = await this.connection.query(`
      SELECT
        i.relname AS index_name,
        a.attname AS column_name,
        idx.indisunique AS is_unique,
        idx.indisprimary AS is_primary,
        am.amname AS index_method,
        pg_size_pretty(pg_relation_size(i.oid)) AS index_size,
        s.idx_scan AS scans,
        s.idx_tup_read AS tuples_read,
        s.idx_tup_fetch AS tuples_fetched
      FROM
        pg_catalog.pg_index idx
        JOIN pg_catalog.pg_class c ON c.oid = idx.indrelid
        JOIN pg_catalog.pg_class i ON i.oid = idx.indexrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_catalog.pg_am am ON am.oid = i.relam
        JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(idx.indkey)
        LEFT JOIN pg_catalog.pg_stat_user_indexes s ON s.indexrelname = i.relname AND s.schemaname = n.nspname
      WHERE
        c.relname = $1 AND n.nspname = $2
      ORDER BY
        i.relname, a.attnum
    `, [tableName, schemaName]);

    // Obter informações sobre sequências associadas
    const sequences = await this.connection.query(`
      SELECT
        seq.relname AS sequence_name,
        a.attname AS column_name,
        pg_get_serial_sequence(quote_ident($2) || '.' || quote_ident($1), a.attname) AS sequence_definition
      FROM
        pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
        JOIN pg_catalog.pg_attrdef ad ON ad.adrelid = c.oid AND ad.adnum = a.attnum
        JOIN pg_catalog.pg_class seq ON seq.relname = regexp_replace(ad.adsrc, '^nextval\\(''([^'']+)''.*\\)$', '\\1')
      WHERE
        c.relname = $1 AND n.nspname = $2
        AND ad.adsrc LIKE 'nextval%'
    `, [tableName, schemaName]);

    const stats = {
      basic: basicStats.records[0],
      indexes: indexStats.records,
      sequences: sequences.records,
      timestamp: new Date().toISOString()
    };

    return MCPResponse.success(
      { stats },
      `Estatísticas da tabela '${schemaName}.${tableName}' obtidas com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção de estatísticas de uma coluna
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetColumnStats(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const columnName = request.parameters?.columnName;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    if (!columnName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "columnName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Obtendo estatísticas da coluna ${schemaName}.${tableName}.${columnName}`, {
      requestId: request.requestId
    });

    // Verifica se a coluna existe
    const columnExists = await this.connection.query(`
      SELECT EXISTS (
        SELECT 1 
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = $1 AND n.nspname = $2 AND a.attname = $3 AND a.attnum > 0 AND NOT a.attisdropped
      ) AS exists
    `, [tableName, schemaName, columnName]);

    if (!columnExists.records[0].exists) {
      return MCPResponse.error(
        `Coluna '${columnName}' não encontrada na tabela '${schemaName}.${tableName}'`,
        null,
        request.requestId
      );
    }

    // Obtém informações básicas da coluna
    const columnInfo = await this.connection.query(`
      SELECT
        a.attname AS column_name,
        format_type(a.atttypid, a.atttypmod) AS data_type,
        a.attnotnull AS not_null,
        a.atthasdef AS has_default,
        pg_get_expr(d.adbin, d.adrelid) AS default_value,
        c.coll_actual_version AS collation_version,
        cl.collname AS collation_name,
        co.contype AS constraint_type,
        attnum AS column_position
      FROM
        pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class rel ON rel.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = rel.relnamespace
        LEFT JOIN pg_catalog.pg_attrdef d ON (d.adrelid = a.attrelid AND d.adnum = a.attnum)
        LEFT JOIN pg_catalog.pg_collation cl ON a.attcollation = cl.oid
        LEFT JOIN pg_catalog.pg_constraint co ON (co.conrelid = a.attrelid AND a.attnum = ANY(co.conkey))
        LEFT JOIN pg_collation c ON a.attcollation = c.oid
      WHERE
        rel.relname = $1 AND n.nspname = $2 AND a.attname = $3
        AND a.attnum > 0 AND NOT a.attisdropped
    `, [tableName, schemaName, columnName]);

    // Obtém estatísticas da coluna usando pg_stats
    const columnStats = await this.connection.query(`
      SELECT
        null_frac AS null_fraction,
        avg_width AS average_width,
        n_distinct AS distinct_values,
        most_common_vals AS most_common_values,
        most_common_freqs AS most_common_frequencies,
        histogram_bounds,
        correlation,
        most_common_elems,
        most_common_elem_freqs,
        elem_count_histogram
      FROM
        pg_catalog.pg_stats
      WHERE
        tablename = $1 AND schemaname = $2 AND attname = $3
    `, [tableName, schemaName, columnName]);

    // Obtém amostra de valores distintos
    let sampleValues = [];
    try {
      const sampleQuery = await this.connection.query(`
        SELECT DISTINCT ${columnName} AS value
        FROM ${schemaName}.${tableName}
        ORDER BY ${columnName}
        LIMIT 10
      `);
      sampleValues = sampleQuery.records.map(r => r.value);
    } catch (error) {
      this.logger.warn(`Não foi possível obter amostra de valores para ${schemaName}.${tableName}.${columnName}: ${error.message}`);
      // Ignora erro ao obter amostra
    }

    const stats = {
      column: columnInfo.records[0],
      statistics: columnStats.records.length > 0 ? columnStats.records[0] : null,
      sample_values: sampleValues,
      timestamp: new Date().toISOString()
    };

    return MCPResponse.success(
      { stats },
      `Estatísticas da coluna '${columnName}' da tabela '${schemaName}.${tableName}' obtidas com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de listagem de extensões
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleListExtensions(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Listando extensões instaladas`, {
      requestId: request.requestId
    });

    // Executa a consulta para listar extensões
    const result = await this.connection.query(`
      SELECT
        e.extname AS name,
        e.extversion AS version,
        n.nspname AS schema,
        c.description,
        e.extrelocatable AS relocatable,
        e.extconfig AS config_table
      FROM
        pg_catalog.pg_extension e
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
        LEFT JOIN pg_catalog.pg_description c ON c.objoid = e.oid AND c.classoid = 'pg_catalog.pg_extension'::pg_catalog.regclass
      ORDER BY
        e.extname
    `);

    // Obter extensões disponíveis (não instaladas)
    const available = await this.connection.query(`
      SELECT
        name,
        default_version,
        installed_version,
        comment
      FROM
        pg_available_extensions
      WHERE
        installed_version IS NULL
      ORDER BY
        name
    `);

    const extensions = {
      installed: result.records,
      available: available.records
    };

    return MCPResponse.success(
      { extensions },
      `Listadas ${result.records.length} extensões instaladas e ${available.records.length} disponíveis para instalação`,
      request.requestId
    );
  }

  /**
   * Processa a operação de listagem de tipos de dados
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleListDataTypes(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Listando tipos de dados`, {
      requestId: request.requestId
    });

    // Executa a consulta para listar tipos de dados
    const result = await this.connection.query(`
      SELECT
        t.typname AS name,
        pg_catalog.format_type(t.oid, NULL) AS format,
        t.typlen AS internal_length,
        CASE
          WHEN t.typlen = -1 THEN 'variable'
          WHEN t.typlen = -2 THEN 'unlimited'
          ELSE 'fixed'
        END AS length_type,
        t.typtype AS type_type,
        n.nspname AS schema,
        CASE WHEN t.typcategory = 'A' THEN true ELSE false END AS is_array,
        CASE WHEN t.typtype = 'e' THEN true ELSE false END AS is_enum,
        CASE WHEN t.typtype = 'c' THEN true ELSE false END AS is_composite,
        CASE WHEN t.typtype = 'd' THEN true ELSE false END AS is_domain,
        CASE WHEN t.typtype = 'r' THEN true ELSE false END AS is_range,
        CASE WHEN t.typelem <> 0 THEN
          (SELECT typname FROM pg_catalog.pg_type WHERE oid = t.typelem)
        ELSE NULL END AS element_type
      FROM
        pg_catalog.pg_type t
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
      WHERE
        (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
        AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
        AND n.nspname NOT IN ('pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
      ORDER BY
        n.nspname, t.typname
    `);

    return MCPResponse.success(
      { dataTypes: result.records },
      `Listados ${result.records.length} tipos de dados`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção da versão do PostgreSQL
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetPostgresVersion(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo versão do PostgreSQL`, {
      requestId: request.requestId
    });

    // Executa a consulta para obter a versão do PostgreSQL
    const result = await this.connection.query(`
      SELECT 
        version() AS full_version,
        current_setting('server_version') AS server_version,
        current_setting('server_version_num') AS server_version_num,
        current_setting('server_min_messages') AS server_min_messages
    `);

    return MCPResponse.success(
      { version: result.records[0] },
      `Versão do PostgreSQL obtida com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de listagem de catálogos do sistema
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetSystemCatalogs(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Listando catálogos do sistema`, {
      requestId: request.requestId
    });

    // Executa a consulta para listar catálogos do sistema
    const result = await this.connection.query(`
      SELECT
        c.relname AS name,
        CASE c.relkind
          WHEN 'r' THEN 'table'
          WHEN 'v' THEN 'view'
          WHEN 'm' THEN 'materialized view'
          WHEN 'i' THEN 'index'
          WHEN 'S' THEN 'sequence'
          WHEN 's' THEN 'special'
          WHEN 'f' THEN 'foreign table'
          WHEN 'p' THEN 'partitioned table'
          ELSE c.relkind::text
        END AS type,
        pg_size_pretty(pg_relation_size(c.oid)) AS size,
        d.description
      FROM
        pg_catalog.pg_class c
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_catalog.pg_description d ON d.objoid = c.oid AND d.classoid = 'pg_catalog.pg_class'::pg_catalog.regclass
      WHERE
        n.nspname = 'pg_catalog'
        AND c.relkind IN ('r', 'v')
      ORDER BY
        c.relkind, c.relname
    `);

    return MCPResponse.success(
      { catalogs: result.records },
      `Listados ${result.records.length} catálogos do sistema`,
      request.requestId
    );
  }
} 