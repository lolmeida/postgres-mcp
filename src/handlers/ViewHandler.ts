/**
 * MCP ViewHandler
 * 
 * Handler para gerenciamento de views no PostgreSQL através do protocolo MCP.
 */

import { IMCPHandler } from '../mcp/router/MCPRouter';
import { MCPRequest } from '../mcp/models/MCPRequest';
import { MCPResponse } from '../mcp/models/MCPResponse';
import { ViewService } from '../services/ViewService';
import { ViewInfo, ViewListOptions, ViewDetailOptions, MaterializedViewRefreshOptions } from '../models/ViewInfo';
import { createComponentLogger } from '../utils/logger';

/**
 * Handler para operações com views via MCP
 */
export class ViewHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_view';
  private viewService: ViewService;
  private logger = createComponentLogger('ViewHandler');

  /**
   * Cria uma nova instância do ViewHandler
   * 
   * @param viewService Serviço de views a ser utilizado
   */
  constructor(viewService: ViewService) {
    this.viewService = viewService;
  }

  /**
   * Executa o handler para a requisição fornecida
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  async handle(request: MCPRequest): Promise<MCPResponse> {
    try {
      // Valida os parâmetros da requisição
      const parameters = this.validateParameters(request.parameters || {});
      
      // Processa a requisição
      return await this.processRequest(parameters);
    } catch (error: any) {
      // Converte erros para o formato MCP adequado
      return {
        success: false,
        error: {
          message: error.message || 'Ocorreu um erro desconhecido',
          type: error.errorType || 'internal_error',
          details: error.details || undefined
        }
      };
    }
  }

  /**
   * Valida os parâmetros da requisição MCP
   * 
   * @param parameters Parâmetros da requisição
   * @returns Parâmetros validados
   */
  private validateParameters(parameters: Record<string, any>): Record<string, any> {
    // Validação comum para todas as operações
    if (!parameters.operation) {
      throw new Error("Required parameter 'operation' is missing");
    }

    const operation = parameters.operation;
    
    // Validações específicas por operação
    switch (operation) {
      case 'list':
        // Schema é opcional, mas se fornecido deve ser string
        if (parameters.schema && typeof parameters.schema !== 'string') {
          throw new Error("Parameter 'schema' must be a string");
        }
        break;
        
      case 'get':
        if (!parameters.viewName) {
          throw new Error("Required parameter 'viewName' is missing");
        }
        if (typeof parameters.viewName !== 'string') {
          throw new Error("Parameter 'viewName' must be a string");
        }
        break;
        
      case 'refresh':
        if (!parameters.viewName) {
          throw new Error("Required parameter 'viewName' is missing");
        }
        if (typeof parameters.viewName !== 'string') {
          throw new Error("Parameter 'viewName' must be a string");
        }
        break;
        
      default:
        throw new Error(`Unsupported operation: ${operation}`);
    }

    return parameters;
  }

  /**
   * Processa a requisição MCP
   * 
   * @param parameters Parâmetros validados
   * @returns Resposta MCP
   */
  private async processRequest(parameters: Record<string, any>): Promise<MCPResponse> {
    const operation = parameters.operation;
    const schema = parameters.schema || 'public';

    switch (operation) {
      case 'list':
        const listOptions: ViewListOptions = {
          includeRegularViews: parameters.includeRegularViews !== false,
          includeMaterializedViews: parameters.includeMaterializedViews !== false,
          limit: parameters.limit || 100,
          offset: parameters.offset || 0
        };
        
        const views = await this.viewService.listViews(schema, listOptions);
        return { success: true, data: views };
        
      case 'get':
        const detailOptions: ViewDetailOptions = {
          includeColumns: parameters.includeColumns !== false,
          includeDefinition: parameters.includeDefinition !== false
        };
        
        const viewInfo = await this.viewService.getViewDetails(
          parameters.viewName,
          schema,
          detailOptions
        );
        return { success: true, data: viewInfo };
        
      case 'refresh':
        const refreshOptions: MaterializedViewRefreshOptions = {
          concurrently: parameters.concurrently === true,
          withData: parameters.withData !== false
        };
        
        const success = await this.viewService.refreshMaterializedView(
          parameters.viewName,
          schema,
          refreshOptions
        );
        return { success: true, data: success };
        
      default:
        throw new Error(`Unsupported operation: ${operation}`);
    }
  }
} 