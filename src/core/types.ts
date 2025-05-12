/**
 * Definições de tipos usados em todo o sistema PostgreSQL MCP
 */

/**
 * Formato básico de resposta do MCP
 */
export interface MCPResponse<T = any> {
  success: boolean;
  data?: T;
  error?: MCPError;
  count?: number;
}

/**
 * Estrutura de erro do MCP
 */
export interface MCPError {
  message: string;
  type: MCPErrorType;
  details?: any;
}

/**
 * Tipos de erro do MCP
 */
export type MCPErrorType = 
  | 'validation_error'    // Erro de validação dos parâmetros
  | 'database_error'      // Erro ocorrido no banco de dados
  | 'security_error'      // Erro relacionado a permissões ou segurança
  | 'transaction_error'   // Erro relacionado a transações
  | 'query_error'         // Erro na execução de consulta SQL
  | 'internal_error';     // Erro interno do servidor

/**
 * Request básico do MCP
 */
export interface MCPRequest {
  tool: string;
  parameters?: Record<string, any>;
}

/**
 * Filtro básico para consultas
 */
export type MCPFilter = Record<string, any>;

/**
 * Informações de uma coluna em uma tabela
 */
export interface ColumnInfo {
  name: string;
  type: string;
  description?: string;
  isNullable: boolean;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  isUnique: boolean;
  defaultValue?: string;
  references?: {
    table: string;
    schema: string;
    column: string;
  };
}

/**
 * Informações de uma tabela
 */
export interface TableInfo {
  name: string;
  schema: string;
  description?: string;
  columns: ColumnInfo[];
  primaryKey?: string[];
  foreignKeys?: {
    columns: string[];
    referencedTable: string;
    referencedSchema: string;
    referencedColumns: string[];
  }[];
  isView: boolean;
}

/**
 * Informações de cache
 */
export interface CacheStats {
  hits: number;
  misses: number;
  invalidations: number;
  hit_ratio: string;
  table_cache_size: number;
  schema_cache_size: number;
  metadata_cache_size: number;
  table_cache_capacity: number;
  schema_cache_capacity: number;
  metadata_cache_capacity: number;
} 