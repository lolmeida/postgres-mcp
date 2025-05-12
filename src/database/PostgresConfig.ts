/**
 * Configurações para conexão com o PostgreSQL
 * 
 * Esta classe define e valida as configurações específicas para conexão
 * com bancos de dados PostgreSQL, incluindo pool de conexões e opções SSL.
 */

import Joi from 'joi';
import { MCPConfig } from '../core/MCPConfig';

/**
 * Nível de segurança SSL
 */
export type SSLMode = 'disable' | 'allow' | 'prefer' | 'require' | 'verify-ca' | 'verify-full';

/**
 * Interface de configuração para conexões PostgreSQL
 */
export interface PostgresConnectionConfig {
  // Informações básicas de conexão
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  
  // Configurações de pool
  poolMin: number;
  poolMax: number;
  
  // Configurações de timeout
  connectionTimeoutMillis: number;
  idleTimeoutMillis: number;
  
  // Configurações SSL
  sslMode: SSLMode;
  sslCert?: string;
  sslKey?: string;
  sslRootCert?: string;
  
  // Configurações de query
  statementTimeout?: number;
  queryLogEnabled: boolean;
}

/**
 * Validador de configuração PostgreSQL
 */
export class PostgresConfigValidator {
  /**
   * Esquema de validação da configuração
   */
  private static schema = Joi.object({
    host: Joi.string().required(),
    port: Joi.number().port().required(),
    database: Joi.string().required(),
    user: Joi.string().required(),
    password: Joi.string().allow('').required(),
    
    poolMin: Joi.number().min(0).required(),
    poolMax: Joi.number().min(1).required(),
    
    connectionTimeoutMillis: Joi.number().min(0).required(),
    idleTimeoutMillis: Joi.number().min(0).required(),
    
    sslMode: Joi.string().valid('disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full').required(),
    sslCert: Joi.string().when('sslMode', {
      is: Joi.valid('require', 'verify-ca', 'verify-full'),
      then: Joi.optional(),
      otherwise: Joi.forbidden()
    }),
    sslKey: Joi.string().when('sslMode', {
      is: Joi.valid('require', 'verify-ca', 'verify-full'),
      then: Joi.optional(),
      otherwise: Joi.forbidden()
    }),
    sslRootCert: Joi.string().when('sslMode', {
      is: Joi.valid('verify-ca', 'verify-full'),
      then: Joi.required(),
      otherwise: Joi.forbidden()
    }),
    
    statementTimeout: Joi.number().min(0).optional(),
    queryLogEnabled: Joi.boolean().required()
  });

  /**
   * Valida a configuração PostgreSQL
   * 
   * @param config Configuração a validar
   * @returns Configuração validada
   * @throws Error se a validação falhar
   */
  static validate(config: Partial<PostgresConnectionConfig>): PostgresConnectionConfig {
    const { error, value } = this.schema.validate(config);
    if (error) {
      throw new Error(`Configuração PostgreSQL inválida: ${error.message}`);
    }
    
    // Validação adicional: poolMin deve ser menor que poolMax
    if (value.poolMin >= value.poolMax) {
      throw new Error('Configuração PostgreSQL inválida: poolMin deve ser menor que poolMax');
    }
    
    return value;
  }
}

/**
 * Builder para configuração PostgreSQL
 */
export class PostgresConfigBuilder {
  private config: Partial<PostgresConnectionConfig> = {
    host: 'localhost',
    port: 5432,
    database: 'postgres',
    user: 'postgres',
    password: '',
    
    poolMin: 1,
    poolMax: 10,
    
    connectionTimeoutMillis: 30000,
    idleTimeoutMillis: 30000,
    
    sslMode: 'disable',
    
    queryLogEnabled: false
  };

  /**
   * Define o host de conexão
   */
  withHost(host: string): this {
    this.config.host = host;
    return this;
  }

  /**
   * Define a porta de conexão
   */
  withPort(port: number): this {
    this.config.port = port;
    return this;
  }

  /**
   * Define o nome do banco de dados
   */
  withDatabase(database: string): this {
    this.config.database = database;
    return this;
  }

  /**
   * Define o usuário do banco de dados
   */
  withUser(user: string): this {
    this.config.user = user;
    return this;
  }

  /**
   * Define a senha do banco de dados
   */
  withPassword(password: string): this {
    this.config.password = password;
    return this;
  }

  /**
   * Define as configurações de pool
   */
  withPool(min: number, max: number): this {
    this.config.poolMin = min;
    this.config.poolMax = max;
    return this;
  }

  /**
   * Define os timeouts de conexão
   */
  withTimeouts(connection: number, idle: number): this {
    this.config.connectionTimeoutMillis = connection;
    this.config.idleTimeoutMillis = idle;
    return this;
  }

  /**
   * Define o timeout de statements SQL
   */
  withStatementTimeout(timeout: number): this {
    this.config.statementTimeout = timeout;
    return this;
  }

  /**
   * Define o modo SSL
   */
  withSSL(mode: SSLMode, certPaths?: { cert?: string; key?: string; rootCert?: string }): this {
    this.config.sslMode = mode;
    
    if (certPaths) {
      this.config.sslCert = certPaths.cert;
      this.config.sslKey = certPaths.key;
      this.config.sslRootCert = certPaths.rootCert;
    }
    
    return this;
  }

  /**
   * Ativa o log de queries
   */
  withQueryLogging(enabled: boolean): this {
    this.config.queryLogEnabled = enabled;
    return this;
  }

  /**
   * Constrói a configuração a partir da configuração MCP
   * 
   * @param mcpConfig Configuração MCP
   * @returns Builder para encadeamento
   */
  fromMCPConfig(mcpConfig: MCPConfig): this {
    this.config = {
      ...this.config,
      host: mcpConfig.dbHost || 'localhost',
      port: mcpConfig.dbPort || 5432,
      database: mcpConfig.dbName || 'postgres',
      user: mcpConfig.dbUser || 'postgres',
      password: mcpConfig.dbPassword || '',
      
      poolMin: mcpConfig.poolMinSize || 1,
      poolMax: mcpConfig.poolMaxSize || 10,
      
      connectionTimeoutMillis: (mcpConfig.commandTimeout || 30) * 1000,
      idleTimeoutMillis: 30000,
      
      sslMode: mcpConfig.dbSsl || 'disable',
      
      queryLogEnabled: mcpConfig.logSqlQueries || false,
    };
    
    return this;
  }

  /**
   * Constrói e valida a configuração
   * 
   * @returns Configuração PostgreSQL validada
   */
  build(): PostgresConnectionConfig {
    return PostgresConfigValidator.validate(this.config);
  }
} 