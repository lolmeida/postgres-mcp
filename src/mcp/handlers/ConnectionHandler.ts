/**
 * MCP ConnectionHandler
 * 
 * Handler para operações relacionadas à conexão com o banco de dados PostgreSQL.
 * Implementa métodos para testar conexão, obter status e configurações.
 */

import { IMCPHandler } from '../router/MCPRouter';
import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { PostgresConnection } from '../../database/PostgresConnection';
import { PostgresConfig } from '../../database/PostgresConfig';
import { createComponentLogger } from '../../utils/logger';

/**
 * Handler para operações de conexão via MCP
 */
export class ConnectionHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_connection';
  private connection: PostgresConnection;
  private logger = createComponentLogger('ConnectionHandler');

  /**
   * Cria uma nova instância do ConnectionHandler
   * 
   * @param connection Conexão com o banco de dados
   */
  constructor(connection: PostgresConnection) {
    this.connection = connection;
  }

  /**
   * Processa requisições MCP para operações de conexão
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
              'testConnection', 'getConnectionStatus', 'getConnectionConfig',
              'getPoolStats', 'disconnect', 'reconnect'
            ] 
          },
          request.requestId
        );
      }

      switch (operation) {
        case 'testConnection':
          return await this.handleTestConnection(request);
        case 'getConnectionStatus':
          return await this.handleGetConnectionStatus(request);
        case 'getConnectionConfig':
          return await this.handleGetConnectionConfig(request);
        case 'getPoolStats':
          return await this.handleGetPoolStats(request);
        case 'disconnect':
          return await this.handleDisconnect(request);
        case 'reconnect':
          return await this.handleReconnect(request);
        default:
          return MCPResponse.error(
            `Operação '${operation}' não suportada pelo handler de conexão`,
            { 
              availableOperations: [
                'testConnection', 'getConnectionStatus', 'getConnectionConfig',
                'getPoolStats', 'disconnect', 'reconnect'
              ] 
            },
            request.requestId
          );
      }
    } catch (error) {
      this.logger.error(`Erro ao processar requisição de conexão: ${error.message}`, { 
        stack: error.stack,
        requestId: request.requestId
      });
      
      return MCPResponse.error(
        `Erro ao processar operação de conexão: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de teste de conexão
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleTestConnection(request: MCPRequest): Promise<MCPResponse> {
    const params = request.parameters || {};
    const host = params.host;
    const port = params.port;
    const database = params.database;
    const user = params.user;
    const password = params.password;
    const connectionString = params.connectionString;
    const ssl = params.ssl;
    const timeoutMs = params.timeoutMs || 5000;

    // Se nenhum parâmetro for fornecido, testa a conexão atual
    if (!host && !connectionString) {
      this.logger.debug(`Testando conexão atual com o banco de dados`, { 
        requestId: request.requestId 
      });

      try {
        const startTime = Date.now();
        const result = await this.connection.query('SELECT 1 AS connection_test');
        const endTime = Date.now();
        
        if (result.records[0].connection_test === 1) {
          return MCPResponse.success(
            { 
              success: true, 
              message: 'Conexão com o banco de dados está funcionando',
              latencyMs: endTime - startTime
            },
            'Teste de conexão bem-sucedido',
            request.requestId
          );
        } else {
          return MCPResponse.error(
            'Resultado inesperado do teste de conexão',
            { success: false },
            request.requestId
          );
        }
      } catch (error) {
        return MCPResponse.error(
          `Falha no teste de conexão: ${error.message}`,
          { 
            success: false, 
            error: error.message,
            stack: error.stack
          },
          request.requestId
        );
      }
    }
    
    // Testa uma nova conexão com os parâmetros fornecidos
    this.logger.debug(`Testando nova conexão com o banco de dados`, { 
      host, port, database, user, ssl, requestId: request.requestId 
    });

    // Cria uma configuração temporária
    const config = new PostgresConfig({
      host,
      port,
      database,
      user,
      password,
      connectionString,
      ssl,
      min: 1,
      max: 1,
      connectionTimeoutMs: timeoutMs
    });

    // Cria uma conexão temporária
    const tempConnection = new PostgresConnection(config);

    try {
      const startTime = Date.now();
      await tempConnection.connect();
      
      const result = await tempConnection.query('SELECT 1 AS connection_test');
      const endTime = Date.now();
      
      await tempConnection.disconnect();
      
      if (result.records[0].connection_test === 1) {
        return MCPResponse.success(
          { 
            success: true, 
            message: 'Conexão com o banco de dados está funcionando',
            latencyMs: endTime - startTime,
            config: this.sanitizeConfig(config)
          },
          'Teste de conexão bem-sucedido',
          request.requestId
        );
      } else {
        return MCPResponse.error(
          'Resultado inesperado do teste de conexão',
          { success: false },
          request.requestId
        );
      }
    } catch (error) {
      try {
        await tempConnection.disconnect();
      } catch (disconnectError) {
        // Ignora erros ao desconectar
      }
      
      return MCPResponse.error(
        `Falha no teste de conexão: ${error.message}`,
        { 
          success: false, 
          error: error.message,
          stack: error.stack
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de obtenção do status da conexão
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetConnectionStatus(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo status da conexão`, { requestId: request.requestId });

    const isConnected = this.connection.isConnected();
    let latencyMs = null;
    let serverVersion = null;

    // Tenta obter latência e versão do servidor se estiver conectado
    if (isConnected) {
      try {
        const startTime = Date.now();
        const result = await this.connection.query('SELECT version() AS version');
        const endTime = Date.now();
        
        latencyMs = endTime - startTime;
        serverVersion = result.records[0].version;
      } catch (error) {
        this.logger.warn(`Não foi possível obter informações adicionais da conexão: ${error.message}`);
      }
    }

    const status = {
      connected: isConnected,
      latencyMs,
      serverVersion,
      connectionUptime: this.connection.getConnectionUptime(),
      poolSize: this.connection.getPoolSize(),
      timestamp: new Date().toISOString()
    };

    return MCPResponse.success(
      { status },
      `Status da conexão obtido com sucesso: ${isConnected ? 'conectado' : 'desconectado'}`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção das configurações da conexão
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetConnectionConfig(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo configurações da conexão`, { requestId: request.requestId });

    const config = this.connection.getConfig();
    const sanitizedConfig = this.sanitizeConfig(config);

    return MCPResponse.success(
      { config: sanitizedConfig },
      'Configurações da conexão obtidas com sucesso',
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção de estatísticas do pool de conexões
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetPoolStats(request: MCPRequest): Promise<MCPResponse> {
    this.logger.debug(`Obtendo estatísticas do pool de conexões`, { requestId: request.requestId });

    const stats = await this.connection.getPoolStats();

    return MCPResponse.success(
      { stats },
      'Estatísticas do pool de conexões obtidas com sucesso',
      request.requestId
    );
  }

  /**
   * Processa a operação de desconexão
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleDisconnect(request: MCPRequest): Promise<MCPResponse> {
    const force = request.parameters?.force === true;
    
    this.logger.debug(`Desconectando do banco de dados`, { 
      force, requestId: request.requestId 
    });

    if (!this.connection.isConnected()) {
      return MCPResponse.success(
        { alreadyDisconnected: true },
        'Já desconectado do banco de dados',
        request.requestId
      );
    }

    try {
      await this.connection.disconnect(force);
      
      return MCPResponse.success(
        { success: true },
        'Desconectado do banco de dados com sucesso',
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao desconectar do banco de dados: ${error.message}`,
        { 
          success: false, 
          error: error.message,
          stack: error.stack
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de reconexão
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleReconnect(request: MCPRequest): Promise<MCPResponse> {
    const force = request.parameters?.force === true;
    
    this.logger.debug(`Reconectando ao banco de dados`, { 
      force, requestId: request.requestId 
    });

    try {
      // Desconecta primeiro, se já estiver conectado
      if (this.connection.isConnected()) {
        await this.connection.disconnect(force);
      }
      
      // Reconecta
      await this.connection.connect();
      
      // Verifica se a conexão está funcionando
      const result = await this.connection.query('SELECT 1 AS connection_test');
      const isConnected = result.records[0].connection_test === 1;
      
      if (isConnected) {
        return MCPResponse.success(
          { success: true },
          'Reconectado ao banco de dados com sucesso',
          request.requestId
        );
      } else {
        return MCPResponse.error(
          'Falha ao reconectar: resultado inesperado do teste de conexão',
          { success: false },
          request.requestId
        );
      }
    } catch (error) {
      return MCPResponse.error(
        `Falha ao reconectar ao banco de dados: ${error.message}`,
        { 
          success: false, 
          error: error.message,
          stack: error.stack
        },
        request.requestId
      );
    }
  }

  /**
   * Remove informações sensíveis da configuração
   * 
   * @param config Configuração a ser sanitizada
   * @returns Configuração sem informações sensíveis
   */
  private sanitizeConfig(config: PostgresConfig): any {
    const sanitized = { ...config.getOptions() };
    
    // Remove senha
    if (sanitized.password) {
      sanitized.password = '********';
    }
    
    // Remove senha da string de conexão
    if (sanitized.connectionString) {
      sanitized.connectionString = sanitized.connectionString.replace(
        /password=([^&\s]+)/gi,
        'password=********'
      );
    }
    
    return sanitized;
  }
} 