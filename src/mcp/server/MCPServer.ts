/**
 * MCP Server
 * 
 * Implementação do servidor para o protocolo MCP que coordena
 * o transporte, roteador e handlers.
 */

import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { IMCPTransport, TransportMode, MCPTransportFactory } from '../transport/MCPTransport';
import { MCPRouter, IMCPHandler, MCPRouterOptions } from '../router/MCPRouter';
import { createComponentLogger } from '../../utils/logger';
import { MCPConfig } from '../../core/MCPConfig';

/**
 * Opções para configuração do servidor MCP
 */
export interface MCPServerOptions {
  /**
   * Configuração do transporte
   */
  transport: {
    /**
     * Modo de transporte
     */
    mode: TransportMode | string;
    
    /**
     * Configuração específica do modo de transporte
     */
    config?: any;
  };
  
  /**
   * Opções do roteador
   */
  router?: MCPRouterOptions;
  
  /**
   * Configuração do MCP
   */
  mcpConfig?: MCPConfig;
}

/**
 * Tipo de callback para eventos do servidor
 */
export type ServerEventCallback = (data?: any) => void;

/**
 * Classe que implementa o servidor MCP
 * 
 * Esta classe coordena o transporte (como as requisições são recebidas e as respostas enviadas),
 * o roteador (que direciona as requisições para os handlers apropriados) e os handlers
 * (que processam as requisições e geram respostas).
 */
export class MCPServer {
  private transport: IMCPTransport;
  private router: MCPRouter;
  private logger = createComponentLogger('MCPServer');
  private running: boolean = false;
  private eventHandlers: Map<string, ServerEventCallback[]> = new Map();
  
  /**
   * Cria uma nova instância do servidor MCP
   * 
   * @param options Opções de configuração do servidor
   */
  constructor(options: MCPServerOptions) {
    // Configuração do transporte
    const transportMode = options.transport.mode as TransportMode;
    this.transport = MCPTransportFactory.createTransport(transportMode, options.transport.config);
    
    // Configuração do roteador
    this.router = new MCPRouter(options.router);
    
    // Inicializa os handlers de eventos
    this.eventHandlers.set('start', []);
    this.eventHandlers.set('stop', []);
    this.eventHandlers.set('request', []);
    this.eventHandlers.set('response', []);
    this.eventHandlers.set('error', []);
  }
  
  /**
   * Inicia o servidor MCP
   * 
   * @throws Error se o servidor já estiver em execução
   */
  async start(): Promise<void> {
    if (this.running) {
      throw new Error('MCP Server is already running');
    }
    
    try {
      this.logger.info('Starting MCP Server...');
      
      // Inicializa o transporte
      await this.transport.initialize();
      
      // Configura o listener para requisições
      this.transport.receive().on('request', this.handleRequest.bind(this));
      this.transport.receive().on('error', this.handleError.bind(this));
      
      this.running = true;
      this.logger.info('MCP Server started successfully');
      
      // Notifica os listeners do evento 'start'
      this.triggerEvent('start');
      
    } catch (err: any) {
      const error = err as Error;
      this.logger.error('Failed to start MCP Server', { error: error.message, stack: error.stack });
      throw error;
    }
  }
  
  /**
   * Para o servidor MCP
   * 
   * @throws Error se o servidor não estiver em execução
   */
  async stop(): Promise<void> {
    if (!this.running) {
      throw new Error('MCP Server is not running');
    }
    
    try {
      this.logger.info('Stopping MCP Server...');
      
      // Encerra o transporte
      await this.transport.shutdown();
      
      this.running = false;
      this.logger.info('MCP Server stopped successfully');
      
      // Notifica os listeners do evento 'stop'
      this.triggerEvent('stop');
      
    } catch (err: any) {
      const error = err as Error;
      this.logger.error('Failed to stop MCP Server', { error: error.message, stack: error.stack });
      throw error;
    }
  }
  
  /**
   * Registra um handler para uma ferramenta específica
   * 
   * @param handler Handler a ser registrado
   */
  registerHandler(handler: IMCPHandler): void {
    this.router.registerHandler(handler);
  }
  
  /**
   * Remove o registro de um handler
   * 
   * @param toolName Nome da ferramenta
   * @returns true se o handler foi removido, false se não foi encontrado
   */
  unregisterHandler(toolName: string): boolean {
    return this.router.unregisterHandler(toolName);
  }
  
  /**
   * Retorna a lista de ferramentas disponíveis
   * 
   * @returns Array com os nomes das ferramentas registradas
   */
  getAvailableTools(): string[] {
    return this.router.getAvailableTools();
  }
  
  /**
   * Registra um callback para um evento específico do servidor
   * 
   * @param event Nome do evento ('start', 'stop', 'request', 'response', 'error')
   * @param callback Função de callback a ser executada quando o evento ocorrer
   * @throws Error se o evento não for suportado
   */
  on(event: string, callback: ServerEventCallback): void {
    if (!this.eventHandlers.has(event)) {
      throw new Error(`Unsupported event: ${event}`);
    }
    
    this.eventHandlers.get(event)!.push(callback);
  }
  
  /**
   * Remove um callback registrado para um evento específico
   * 
   * @param event Nome do evento
   * @param callback Função de callback a ser removida
   * @returns true se o callback foi removido, false se não foi encontrado
   * @throws Error se o evento não for suportado
   */
  off(event: string, callback: ServerEventCallback): boolean {
    if (!this.eventHandlers.has(event)) {
      throw new Error(`Unsupported event: ${event}`);
    }
    
    const handlers = this.eventHandlers.get(event)!;
    const index = handlers.indexOf(callback);
    
    if (index !== -1) {
      handlers.splice(index, 1);
      return true;
    }
    
    return false;
  }
  
  /**
   * Processa uma requisição recebida
   * 
   * @param request Requisição MCP
   */
  private async handleRequest(request: MCPRequest): Promise<void> {
    try {
      this.logger.debug(`Received request for tool '${request.tool}'`, { requestId: request.requestId });
      
      // Notifica os listeners do evento 'request'
      this.triggerEvent('request', request);
      
      // Roteia a requisição para o handler apropriado
      const response = await this.router.route(request);
      
      // Envia a resposta
      await this.transport.send(response);
      
      this.logger.debug(`Sent response for tool '${request.tool}'`, { 
        requestId: request.requestId,
        success: response.success
      });
      
      // Notifica os listeners do evento 'response'
      this.triggerEvent('response', { request, response });
      
    } catch (err: any) {
      const error = err as Error;
      this.handleError(error, request);
    }
  }
  
  /**
   * Processa um erro ocorrido durante o processamento de uma requisição
   * 
   * @param error Erro ocorrido
   * @param request Requisição associada ao erro (opcional)
   */
  private async handleError(error: Error, request?: MCPRequest): Promise<void> {
    this.logger.error('Error handling request', { 
      error: error.message, 
      stack: error.stack,
      requestId: request?.requestId
    });
    
    // Notifica os listeners do evento 'error'
    this.triggerEvent('error', { error, request });
    
    // Se houver uma requisição associada, envia uma resposta de erro
    if (request) {
      try {
        const response = MCPResponse.error(
          error.message,
          { stack: error.stack },
          request.requestId
        );
        
        await this.transport.send(response);
        
      } catch (err: any) {
        const sendError = err as Error;
        this.logger.error('Failed to send error response', { 
          error: sendError.message,
          requestId: request.requestId
        });
      }
    }
  }
  
  /**
   * Dispara um evento para todos os callbacks registrados
   * 
   * @param event Nome do evento
   * @param data Dados do evento (opcional)
   */
  private triggerEvent(event: string, data?: any): void {
    if (this.eventHandlers.has(event)) {
      for (const callback of this.eventHandlers.get(event)!) {
        try {
          callback(data);
        } catch (err: any) {
          const error = err as Error;
          this.logger.error(`Error in event listener for '${event}'`, { 
            error: error.message,
            stack: error.stack
          });
        }
      }
    }
  }
  
  /**
   * Verifica se o servidor está em execução
   * 
   * @returns true se o servidor estiver em execução, false caso contrário
   */
  isRunning(): boolean {
    return this.running;
  }
} 