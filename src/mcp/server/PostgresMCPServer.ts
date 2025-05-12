/**
 * PostgreSQL MCP Server
 * 
 * Implementação específica do servidor MCP para PostgreSQL, integrando
 * com os serviços e repositórios do banco de dados PostgreSQL.
 */

import { MCPServer, MCPServerOptions } from './MCPServer';
import { TransportMode } from '../transport/MCPTransport';
import { IMCPHandler } from '../router/MCPRouter';
import { MCPConfig } from '../../core/MCPConfig';
import { PostgresConfig } from '../../database/PostgresConfig';
import { PostgresConnection } from '../../database/PostgresConnection';
import { createComponentLogger } from '../../utils/logger';

// Importação de serviços
import { TableService } from '../../services/TableService';
import { QueryService } from '../../services/QueryService';
import { SchemaService } from '../../services/SchemaService';
import { TransactionService, IsolationLevel } from '../../services/TransactionService';
import { ValidationService } from '../../services/ValidationService';
import { SecurityService } from '../../services/SecurityService';
import { LoggingService } from '../../services/LoggingService';
import { CacheService } from '../../services/CacheService';
import { MetricsService } from '../../services/MetricsService';

// Importação de handlers
import {
  TableHandler,
  QueryHandler,
  SchemaHandler,
  MetadataHandler,
  ConnectionHandler,
  TransactionHandler
} from '../handlers';

/**
 * Opções de configuração do servidor MCP para PostgreSQL
 */
export interface PostgresMCPServerOptions {
  /**
   * Configurações de banco de dados
   */
  database?: {
    /**
     * Host do banco de dados
     */
    host?: string;
    
    /**
     * Porta do banco de dados
     */
    port?: number;
    
    /**
     * Nome do banco de dados
     */
    database?: string;
    
    /**
     * Usuário do banco de dados
     */
    user?: string;
    
    /**
     * Senha do banco de dados
     */
    password?: string;
    
    /**
     * String de conexão completa (alternativa aos parâmetros individuais)
     */
    connectionString?: string;
    
    /**
     * Schema padrão
     */
    defaultSchema?: string;
    
    /**
     * Tamanho máximo do pool de conexões
     */
    maxPoolSize?: number;
    
    /**
     * Timeout de aquisição de conexão em milissegundos
     */
    connectionTimeoutMs?: number;
    
    /**
     * Timeout de inatividade em milissegundos
     */
    idleTimeoutMs?: number;
    
    /**
     * Se deve usar SSL
     */
    ssl?: boolean | object;
  };
  
  /**
   * Configurações de transporte
   */
  transport?: {
    /**
     * Modo de transporte
     */
    mode?: TransportMode | string;
    
    /**
     * Porta para o servidor HTTP (quando aplicável)
     */
    port?: number;
    
    /**
     * Host para o servidor HTTP (quando aplicável)
     */
    host?: string;
    
    /**
     * Rota para o endpoint MCP (quando aplicável)
     */
    path?: string;
  };
  
  /**
   * Configurações do MCP
   */
  mcp?: Partial<MCPConfig>;
  
  /**
   * Configurações de segurança
   */
  security?: {
    /**
     * Se a segurança está ativada
     */
    enabled?: boolean;
    
    /**
     * Se o modo estrito está ativado (requer permissões explícitas)
     */
    strictMode?: boolean;
  };
  
  /**
   * Configurações de cache
   */
  cache?: {
    /**
     * Se o cache está ativado
     */
    enabled?: boolean;
    
    /**
     * TTL padrão em milissegundos
     */
    defaultTtl?: number;
    
    /**
     * Número máximo de itens no cache
     */
    maxItems?: number;
  };
  
  /**
   * Configurações de log
   */
  logging?: {
    /**
     * Nível de log
     */
    level?: string;
    
    /**
     * Se o log para console está ativado
     */
    enableConsole?: boolean;
    
    /**
     * Se o log para arquivo está ativado
     */
    enableFileLogging?: boolean;
    
    /**
     * Diretório para os arquivos de log
     */
    logDir?: string;
  };
  
  /**
   * Configurações de métricas
   */
  metrics?: {
    /**
     * Se as métricas estão ativadas
     */
    enabled?: boolean;
    
    /**
     * Se deve rastrear o uso de memória
     */
    trackMemoryUsage?: boolean;
    
    /**
     * Taxa de amostragem (0-1)
     */
    samplingRate?: number;
  };
}

/**
 * Implementação do servidor MCP para PostgreSQL
 */
export class PostgresMCPServer {
  private server: MCPServer;
  private connection: PostgresConnection;
  private services: {
    table: TableService;
    query: QueryService;
    schema: SchemaService;
    transaction: TransactionService;
    validation: ValidationService;
    security: SecurityService;
    logging: LoggingService;
    cache: CacheService;
    metrics: MetricsService;
  };
  
  private config: PostgresMCPServerOptions;
  private logger = createComponentLogger('PostgresMCPServer');
  private handlers: IMCPHandler[] = [];
  
  /**
   * Cria uma nova instância do servidor MCP para PostgreSQL
   * 
   * @param options Opções de configuração do servidor
   */
  constructor(options: PostgresMCPServerOptions = {}) {
    this.config = this.normalizeConfig(options);
    
    // Configurar conexão PostgreSQL
    const dbConfig = this.createPostgresConfig(this.config.database || {});
    this.connection = new PostgresConnection(dbConfig);
    
    // Inicializar serviços
    this.services = this.initializeServices(this.config);
    
    // Configurar servidor MCP
    const serverOptions = this.createMCPServerOptions();
    this.server = new MCPServer(serverOptions);
    
    // Registrar handlers
    this.registerHandlers();
  }
  
  /**
   * Normaliza a configuração com valores padrão
   * 
   * @param options Opções de configuração fornecidas
   * @returns Opções de configuração normalizadas
   */
  private normalizeConfig(options: PostgresMCPServerOptions): PostgresMCPServerOptions {
    return {
      database: {
        host: options.database?.host || 'localhost',
        port: options.database?.port || 5432,
        database: options.database?.database || 'postgres',
        user: options.database?.user || 'postgres',
        password: options.database?.password || '',
        connectionString: options.database?.connectionString,
        defaultSchema: options.database?.defaultSchema || 'public',
        maxPoolSize: options.database?.maxPoolSize || 10,
        connectionTimeoutMs: options.database?.connectionTimeoutMs || 30000,
        idleTimeoutMs: options.database?.idleTimeoutMs || 60000,
        ssl: options.database?.ssl || false
      },
      transport: {
        mode: options.transport?.mode || TransportMode.STDIO,
        port: options.transport?.port || 8000,
        host: options.transport?.host || 'localhost',
        path: options.transport?.path || '/mcp'
      },
      mcp: options.mcp || {},
      security: {
        enabled: options.security?.enabled ?? false,
        strictMode: options.security?.strictMode ?? false
      },
      cache: {
        enabled: options.cache?.enabled ?? true,
        defaultTtl: options.cache?.defaultTtl || 5 * 60 * 1000, // 5 minutos
        maxItems: options.cache?.maxItems || 1000
      },
      logging: {
        level: options.logging?.level || 'info',
        enableConsole: options.logging?.enableConsole ?? true,
        enableFileLogging: options.logging?.enableFileLogging ?? false,
        logDir: options.logging?.logDir || 'logs'
      },
      metrics: {
        enabled: options.metrics?.enabled ?? true,
        trackMemoryUsage: options.metrics?.trackMemoryUsage ?? true,
        samplingRate: options.metrics?.samplingRate ?? 1.0
      }
    };
  }
  
  /**
   * Cria a configuração do PostgreSQL a partir das opções
   * 
   * @param options Opções de configuração do banco de dados
   * @returns Configuração do PostgreSQL
   */
  private createPostgresConfig(options: any): PostgresConfig {
    return new PostgresConfig({
      host: options.host,
      port: options.port,
      database: options.database,
      user: options.user,
      password: options.password,
      connectionString: options.connectionString,
      ssl: options.ssl,
      defaultSchema: options.defaultSchema,
      max: options.maxPoolSize,
      connectionTimeoutMs: options.connectionTimeoutMs,
      idleTimeoutMs: options.idleTimeoutMs
    });
  }
  
  /**
   * Inicializa os serviços do servidor
   * 
   * @param config Configuração do servidor
   * @returns Serviços inicializados
   */
  private initializeServices(config: PostgresMCPServerOptions): any {
    // Serviço de logging
    const loggingService = new LoggingService(config.mcp || {}, {
      logDir: config.logging?.logDir,
      level: config.logging?.level as any,
      enableConsole: config.logging?.enableConsole,
      enableFileLogging: config.logging?.enableFileLogging
    });
    
    // Serviço de métricas
    const metricsService = new MetricsService({
      enableDetailedMetrics: config.metrics?.enabled,
      trackMemoryUsage: config.metrics?.trackMemoryUsage,
      samplingRate: config.metrics?.samplingRate
    });
    
    // Serviço de cache
    const cacheService = new CacheService({
      enabled: config.cache?.enabled,
      defaultTtl: config.cache?.defaultTtl,
      maxItems: config.cache?.maxItems
    });
    
    // Serviço de segurança
    const securityService = new SecurityService({
      enabled: config.security?.enabled,
      strictMode: config.security?.strictMode
    });
    
    // Serviço de validação
    const validationService = new ValidationService();
    
    // Serviço de transação
    const transactionService = new TransactionService(this.connection);
    
    // Serviço de esquema
    const schemaService = new SchemaService(this.connection);
    
    // Serviço de consulta
    const queryService = new QueryService(this.connection, {
      securityService,
      validationService,
      metricsService,
      cacheService
    });
    
    // Serviço de tabela
    const tableService = new TableService(this.connection, {
      queryService,
      validationService,
      securityService,
      metricsService,
      cacheService
    });
    
    return {
      table: tableService,
      query: queryService,
      schema: schemaService,
      transaction: transactionService,
      validation: validationService,
      security: securityService,
      logging: loggingService,
      cache: cacheService,
      metrics: metricsService
    };
  }
  
  /**
   * Cria as opções para o servidor MCP
   * 
   * @returns Opções do servidor MCP
   */
  private createMCPServerOptions(): MCPServerOptions {
    const transportConfig: any = {
      port: this.config.transport?.port,
      host: this.config.transport?.host,
      path: this.config.transport?.path
    };
    
    return {
      transport: {
        mode: this.config.transport?.mode || TransportMode.STDIO,
        config: transportConfig
      },
      router: {
        strictValidation: this.config.security?.strictMode
      },
      mcpConfig: this.config.mcp as MCPConfig
    };
  }
  
  /**
   * Registra os handlers para as ferramentas MCP
   * 
   * Este método deve ser implementado para registrar os handlers
   * específicos para cada ferramenta suportada pelo PostgreSQL MCP.
   */
  private registerHandlers(): void {
    // Cria e registra os handlers
    const tableHandler = new TableHandler(this.services.table);
    this.server.registerHandler(tableHandler);
    this.handlers.push(tableHandler);

    const queryHandler = new QueryHandler(this.services.query);
    this.server.registerHandler(queryHandler);
    this.handlers.push(queryHandler);

    const schemaHandler = new SchemaHandler(this.services.schema);
    this.server.registerHandler(schemaHandler);
    this.handlers.push(schemaHandler);

    const metadataHandler = new MetadataHandler(this.services.schema, this.connection);
    this.server.registerHandler(metadataHandler);
    this.handlers.push(metadataHandler);

    const connectionHandler = new ConnectionHandler(this.connection);
    this.server.registerHandler(connectionHandler);
    this.handlers.push(connectionHandler);

    const transactionHandler = new TransactionHandler(this.services.transaction);
    this.server.registerHandler(transactionHandler);
    this.handlers.push(transactionHandler);

    this.logger.info('Registered all standard MCP handlers', {
      handlerCount: this.handlers.length,
      handlers: this.handlers.map(h => h.toolName)
    });
  }
  
  /**
   * Adiciona um handler personalizado ao servidor
   * 
   * @param handler Handler a ser adicionado
   */
  registerHandler(handler: IMCPHandler): void {
    this.server.registerHandler(handler);
    this.handlers.push(handler);
    this.logger.debug(`Registered custom handler for tool '${handler.toolName}'`);
  }
  
  /**
   * Inicia o servidor MCP
   */
  async start(): Promise<void> {
    try {
      this.logger.info('Starting PostgreSQL MCP Server...');
      
      // Inicializa serviços
      await this.initializeAllServices();
      
      // Conecta ao banco de dados
      await this.connection.connect();
      this.logger.info('Connected to PostgreSQL database');
      
      // Inicia o servidor MCP
      await this.server.start();
      
      this.logger.info('PostgreSQL MCP Server started successfully');
      
    } catch (error) {
      this.logger.error('Failed to start PostgreSQL MCP Server', { 
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }
  
  /**
   * Inicializa todos os serviços
   */
  private async initializeAllServices(): Promise<void> {
    try {
      await this.services.logging.initialize();
      await this.services.metrics.initialize();
      await this.services.cache.initialize();
      await this.services.security.initialize();
      
      this.logger.info('All services initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize services', { 
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }
  
  /**
   * Para o servidor MCP
   */
  async stop(): Promise<void> {
    try {
      this.logger.info('Stopping PostgreSQL MCP Server...');
      
      // Para o servidor MCP
      await this.server.stop();
      
      // Desconecta do banco de dados
      await this.connection.disconnect();
      this.logger.info('Disconnected from PostgreSQL database');
      
      // Finaliza serviços
      await this.shutdownAllServices();
      
      this.logger.info('PostgreSQL MCP Server stopped successfully');
      
    } catch (error) {
      this.logger.error('Failed to stop PostgreSQL MCP Server', { 
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }
  
  /**
   * Finaliza todos os serviços
   */
  private async shutdownAllServices(): Promise<void> {
    try {
      await this.services.cache.shutdown();
      await this.services.metrics.shutdown();
      // Outros serviços que precisam de finalização
      
      this.logger.info('All services shut down successfully');
      
    } catch (error) {
      this.logger.error('Failed to shut down services', { 
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }
  
  /**
   * Retorna a lista de ferramentas disponíveis
   * 
   * @returns Array com os nomes das ferramentas registradas
   */
  getAvailableTools(): string[] {
    return this.server.getAvailableTools();
  }
  
  /**
   * Obtém uma instância de um serviço específico
   * 
   * @param serviceName Nome do serviço
   * @returns Instância do serviço ou undefined se não encontrado
   */
  getService(serviceName: string): any {
    if (serviceName in this.services) {
      return this.services[serviceName];
    }
    return undefined;
  }
  
  /**
   * Verifica se o servidor está em execução
   * 
   * @returns true se o servidor estiver em execução, false caso contrário
   */
  isRunning(): boolean {
    return this.server.isRunning();
  }
} 