/**
 * MCP Router
 * 
 * Implementação do roteador para o protocolo MCP que recebe requisições
 * e roteia para os handlers apropriados.
 */

import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { createComponentLogger } from '../../utils/logger';

/**
 * Interface para handlers de requisições MCP
 */
export interface IMCPHandler {
  /**
   * Nome da ferramenta que o handler processa
   */
  readonly toolName: string;
  
  /**
   * Executa o handler para a requisição fornecida
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  handle(request: MCPRequest): Promise<MCPResponse>;
}

/**
 * Opções para a configuração do roteador MCP
 */
export interface MCPRouterOptions {
  /**
   * Se deve validar estritamente os parâmetros das requisições
   */
  strictValidation?: boolean;
  
  /**
   * Handler padrão para requisições não encontradas
   */
  defaultHandler?: (request: MCPRequest) => Promise<MCPResponse>;
  
  /**
   * Handlers de erro personalizados
   */
  errorHandlers?: {
    /**
     * Handler para erros de validação
     */
    validationError?: (error: Error, request: MCPRequest) => Promise<MCPResponse>;
    
    /**
     * Handler para erros internos
     */
    internalError?: (error: Error, request: MCPRequest) => Promise<MCPResponse>;
  };
}

/**
 * Classe que implementa o roteamento de requisições MCP
 */
export class MCPRouter {
  private handlers: Map<string, IMCPHandler>;
  private options: MCPRouterOptions;
  private logger = createComponentLogger('MCPRouter');
  
  /**
   * Cria uma nova instância do roteador MCP
   * 
   * @param options Opções de configuração do roteador
   */
  constructor(options: MCPRouterOptions = {}) {
    this.handlers = new Map<string, IMCPHandler>();
    this.options = {
      strictValidation: options.strictValidation ?? false,
      defaultHandler: options.defaultHandler,
      errorHandlers: options.errorHandlers || {}
    };
  }
  
  /**
   * Registra um handler para uma ferramenta específica
   * 
   * @param handler Handler a ser registrado
   * @throws Error se já houver um handler registrado para a mesma ferramenta
   */
  registerHandler(handler: IMCPHandler): void {
    if (this.handlers.has(handler.toolName)) {
      throw new Error(`Handler for tool '${handler.toolName}' is already registered`);
    }
    
    this.handlers.set(handler.toolName, handler);
    this.logger.debug(`Registered handler for tool '${handler.toolName}'`);
  }
  
  /**
   * Remove o registro de um handler
   * 
   * @param toolName Nome da ferramenta
   * @returns true se o handler foi removido, false se não foi encontrado
   */
  unregisterHandler(toolName: string): boolean {
    const removed = this.handlers.delete(toolName);
    if (removed) {
      this.logger.debug(`Unregistered handler for tool '${toolName}'`);
    }
    return removed;
  }
  
  /**
   * Roteia uma requisição para o handler apropriado
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  async route(request: MCPRequest): Promise<MCPResponse> {
    const startTime = Date.now();
    
    try {
      // Verifica se existe um handler registrado para a ferramenta
      const handler = this.handlers.get(request.tool);
      
      if (!handler) {
        this.logger.warn(`No handler found for tool '${request.tool}'`);
        
        // Usa o handler padrão se disponível
        if (this.options.defaultHandler) {
          return this.options.defaultHandler(request);
        }
        
        // Retorna um erro padrão
        return MCPResponse.error(
          `Tool '${request.tool}' not found`,
          { availableTools: Array.from(this.handlers.keys()) },
          request.requestId,
          Date.now() - startTime
        );
      }
      
      // Executa o handler
      this.logger.debug(`Routing request to handler for tool '${request.tool}'`, { requestId: request.requestId });
      const response = await handler.handle(request);
      
      // Adiciona informações de processamento à resposta se elas não estiverem presentes
      if (!response.processingTime) {
        response.processingTime = Date.now() - startTime;
      }
      
      if (!response.requestId) {
        response.requestId = request.requestId;
      }
      
      return response;
      
    } catch (err: any) {
      const error = err as Error;
      
      this.logger.error(`Error processing request for tool '${request.tool}'`, { 
        error: error.message,
        stack: error.stack,
        requestId: request.requestId
      });
      
      // Handler de erro personalizado para erro de validação
      if (error.name === 'ValidationError' && this.options.errorHandlers?.validationError) {
        return this.options.errorHandlers.validationError(error, request);
      }
      
      // Handler de erro personalizado para erro interno
      if (this.options.errorHandlers?.internalError) {
        return this.options.errorHandlers.internalError(error, request);
      }
      
      // Retorna um erro padrão
      return MCPResponse.error(
        error.message,
        { stack: error.stack },
        request.requestId,
        Date.now() - startTime
      );
    }
  }
  
  /**
   * Retorna a lista de ferramentas disponíveis
   * 
   * @returns Array com os nomes das ferramentas registradas
   */
  getAvailableTools(): string[] {
    return Array.from(this.handlers.keys());
  }
  
  /**
   * Limpa todos os handlers registrados
   */
  clear(): void {
    this.handlers.clear();
    this.logger.debug('Cleared all handlers');
  }
} 