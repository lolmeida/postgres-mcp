/**
 * Interface que define todas as possíveis configurações para o servidor MCP PostgreSQL
 */
export interface MCPConfig {
  // Configurações do Banco de Dados
  dbHost?: string;
  dbPort?: number;
  dbName?: string;
  dbUser?: string;
  dbPassword?: string;
  dbSsl?: 'disable' | 'allow' | 'prefer' | 'require' | 'verify-ca' | 'verify-full';

  // Configurações do Servidor MCP
  mode?: 'stdio' | 'http';
  port?: number;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  logSqlQueries?: boolean;
  testMode?: boolean;

  // Configurações de Pool de Conexões
  poolMinSize?: number;
  poolMaxSize?: number;

  // Configurações de Timeouts
  commandTimeout?: number;
  transactionTimeout?: number;

  // Configurações de Limites
  maxQueryRows?: number;

  // Configurações de Cache
  cacheMaxSize?: number;
  cacheTtl?: number;

  // Logger personalizado (opcional)
  logger?: any;
}

/**
 * Classe que encapsula os valores padrão e carrega configurações de variáveis de ambiente
 */
export class ConfigLoader {
  /**
   * Carrega configurações de variáveis de ambiente e/ou valores passados explicitamente
   * 
   * @param config Configurações passadas explicitamente (opcional)
   * @returns Configuração final combinada com valores padrão
   */
  static load(config: Partial<MCPConfig> = {}): MCPConfig {
    // Lê variáveis de ambiente (caso dotenv esteja configurado)
    return {
      // Configurações do Banco de Dados
      dbHost: config.dbHost || process.env.DB_HOST || 'localhost',
      dbPort: config.dbPort || parseInt(process.env.DB_PORT || '5432', 10),
      dbName: config.dbName || process.env.DB_NAME || 'postgres',
      dbUser: config.dbUser || process.env.DB_USER || 'postgres',
      dbPassword: config.dbPassword || process.env.DB_PASSWORD || 'postgres',
      dbSsl: (config.dbSsl || process.env.DB_SSL || 'prefer') as MCPConfig['dbSsl'],

      // Configurações do Servidor MCP
      mode: (config.mode || process.env.MCP_MODE || 'stdio') as MCPConfig['mode'],
      port: config.port || parseInt(process.env.MCP_PORT || '8432', 10),
      logLevel: (config.logLevel || process.env.MCP_LOG_LEVEL || 'info') as MCPConfig['logLevel'],
      logSqlQueries: config.logSqlQueries !== undefined 
        ? config.logSqlQueries 
        : process.env.MCP_LOG_SQL === 'true',
      testMode: config.testMode || false,

      // Configurações de Pool de Conexões
      poolMinSize: config.poolMinSize || parseInt(process.env.POOL_MIN_SIZE || '1', 10),
      poolMaxSize: config.poolMaxSize || parseInt(process.env.POOL_MAX_SIZE || '10', 10),

      // Configurações de Timeouts
      commandTimeout: config.commandTimeout || parseInt(process.env.COMMAND_TIMEOUT || '30', 10),
      transactionTimeout: config.transactionTimeout || parseInt(process.env.TRANSACTION_TIMEOUT || '300', 10),

      // Configurações de Limites
      maxQueryRows: config.maxQueryRows || parseInt(process.env.MAX_QUERY_ROWS || '5000', 10),

      // Configurações de Cache
      cacheMaxSize: config.cacheMaxSize || parseInt(process.env.CACHE_MAX_SIZE || '1000', 10),
      cacheTtl: config.cacheTtl || parseInt(process.env.CACHE_TTL || '3600', 10),

      // Logger personalizado
      logger: config.logger || undefined,
    };
  }
} 