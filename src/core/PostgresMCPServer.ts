/**
 * Classe principal do servidor PostgreSQL MCP
 * 
 * Esta classe implementa a interface do Model Context Protocol para PostgreSQL,
 * gerenciando a comunicação entre LLMs e o banco de dados PostgreSQL.
 */

import dotenv from 'dotenv';
import { Pool } from 'pg';
import { MCPConfig, ConfigLoader } from './MCPConfig';
import { createComponentLogger } from '../utils/logger';
import { MCPRouter } from './MCPRouter';
import { MCPRequest, MCPResponse } from './types';
import { InternalException } from '../utils/exceptions';

// Carrega variáveis de ambiente logo no início
dotenv.config();

/**
 * Classe principal que implementa o servidor PostgreSQL MCP
 */
export class PostgresMCPServer {
  private config: MCPConfig;
  private logger: ReturnType<typeof createComponentLogger>;
  private isRunning: boolean = false;
  private pool: Pool | null = null;
  private router: MCPRouter;

  /**
   * Construtor da classe PostgresMCPServer
   * 
   * @param config Configuração do servidor (opcional)
   */
  constructor(config: Partial<MCPConfig> = {}) {
    // Carrega configurações combinando parâmetros e variáveis de ambiente
    this.config = ConfigLoader.load(config);
    
    // Inicializa o logger
    this.logger = createComponentLogger('PostgresMCPServer', this.config);
    
    // Inicializa o router
    this.router = new MCPRouter(this.config);
    
    this.logger.debug('Servidor PostgreSQL MCP inicializado com configurações', { 
      ...this.config,
      // Omite a senha dos logs por segurança
      dbPassword: this.config.dbPassword ? '********' : undefined 
    });
  }

  /**
   * Inicia o servidor MCP
   * 
   * @returns Promise que resolve quando o servidor está pronto
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      this.logger.warn('O servidor já está em execução');
      return;
    }

    try {
      // Registra o início do servidor
      this.logger.info(`Iniciando servidor no modo: ${this.config.mode}`);

      // Inicializa o pool de conexões PostgreSQL
      await this.initDatabasePool();

      // Implementação depende do modo (stdio ou http)
      if (this.config.mode === 'http') {
        await this.startHttpServer();
      } else {
        // Modo padrão é STDIO
        await this.startStdioServer();
      }

      this.isRunning = true;
      this.logger.info('Servidor iniciado com sucesso');
    } catch (error: any) {
      this.logger.error('Falha ao iniciar o servidor', error);
      throw new InternalException(`Falha ao iniciar o servidor: ${error.message}`, error);
    }
  }

  /**
   * Inicializa o pool de conexões com o PostgreSQL
   */
  private async initDatabasePool(): Promise<void> {
    try {
      this.pool = new Pool({
        host: this.config.dbHost,
        port: this.config.dbPort,
        database: this.config.dbName,
        user: this.config.dbUser,
        password: this.config.dbPassword,
        min: this.config.poolMinSize,
        max: this.config.poolMaxSize,
        ssl: this.config.dbSsl === 'disable' ? false : {
          rejectUnauthorized: this.config.dbSsl === 'verify-ca' || this.config.dbSsl === 'verify-full'
        },
        connectionTimeoutMillis: (this.config.commandTimeout || 30) * 1000,
        idleTimeoutMillis: 30000
      } as any); // Usando "as any" temporariamente até resolver os tipos corretos

      // Testa a conexão
      const client = await this.pool.connect();
      try {
        const result = await client.query('SELECT current_database() as db, current_user as user');
        this.logger.info(`Conectado ao PostgreSQL: ${result.rows[0].db} como ${result.rows[0].user}`);
      } finally {
        client.release();
      }
    } catch (error: any) {
      this.logger.error('Falha ao inicializar o pool de conexões PostgreSQL', error);
      throw new InternalException(`Falha na conexão com o banco de dados: ${error.message}`, error);
    }
  }

  /**
   * Inicia o servidor no modo HTTP
   */
  private async startHttpServer(): Promise<void> {
    // Stub para implementação futura
    this.logger.info(`Servidor HTTP seria iniciado na porta ${this.config.port}`);
    // TODO: Implementar servidor HTTP com express ou fastify
  }

  /**
   * Inicia o servidor no modo STDIO
   */
  private async startStdioServer(): Promise<void> {
    this.logger.info('Iniciando servidor no modo STDIO');
    
    // Configura tratamento de entrada/saída
    process.stdin.resume();
    process.stdin.setEncoding('utf-8');
    
    let inputBuffer = '';
    
    process.stdin.on('data', async (chunk) => {
      inputBuffer += chunk.toString();
      
      // Processa linhas completas
      const lines = inputBuffer.split('\n');
      
      // A última linha pode estar incompleta
      inputBuffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            const request = JSON.parse(line) as MCPRequest;
            const response = await this.handle(request);
            
            // Envia a resposta para stdout
            process.stdout.write(JSON.stringify(response) + '\n');
          } catch (error: any) {
            // Em caso de erro de parsing
            const errorResponse: MCPResponse = {
              success: false,
              error: {
                message: `Falha ao processar requisição: ${error.message}`,
                type: 'internal_error'
              }
            };
            process.stdout.write(JSON.stringify(errorResponse) + '\n');
          }
        }
      }
    });
    
    // Tratamento de erro no stdin
    process.stdin.on('error', (error) => {
      this.logger.error('Erro no stream de entrada:', error);
    });
    
    // Tratamento de fechamento do stdin
    process.stdin.on('end', () => {
      this.logger.info('Stream de entrada finalizado, encerrando servidor');
      this.stop();
    });
  }

  /**
   * Para o servidor MCP
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      this.logger.warn('O servidor não está em execução');
      return;
    }

    try {
      // Fecha o pool de conexões PostgreSQL
      if (this.pool) {
        await this.pool.end();
        this.pool = null;
      }
      
      this.isRunning = false;
      this.logger.info('Servidor parado com sucesso');
    } catch (error: any) {
      this.logger.error('Falha ao parar o servidor', error);
      throw new InternalException(`Falha ao parar o servidor: ${error.message}`, error);
    }
  }

  /**
   * Manipula uma requisição MCP
   * 
   * @param request Objeto de requisição no formato MCP
   * @returns Resposta da operação
   */
  async handle(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug('Manipulando requisição', { tool: request.tool });
    
    // Roteamento para o handler adequado via MCPRouter
    return this.router.route(request);
  }

  /**
   * Registra um manipulador de ferramenta MCP
   * 
   * @param handler Manipulador a ser registrado
   */
  registerHandler(handler: any): void {
    this.router.registerHandler(handler);
  }

  /**
   * Registra múltiplos manipuladores de ferramentas MCP
   * 
   * @param handlers Array de manipuladores a serem registrados
   */
  registerHandlers(handlers: any[]): void {
    this.router.registerHandlers(handlers);
  }

  /**
   * Retorna o pool de conexões PostgreSQL
   * 
   * @returns Pool de conexões
   * @throws InternalException se o servidor não estiver iniciado
   */
  getPool(): Pool {
    if (!this.pool) {
      throw new InternalException('O pool de conexões não está inicializado');
    }
    return this.pool;
  }
} 