/**
 * MCP FunctionHandler
 * 
 * Handler para gerenciamento de funções e procedimentos armazenados no PostgreSQL através do protocolo MCP.
 */

import { IMCPHandler } from '../mcp/router/MCPRouter';
import { MCPRequest } from '../mcp/models/MCPRequest';
import { MCPResponse } from '../mcp/models/MCPResponse';
import { FunctionService } from '../services/FunctionService';
import { 
  FunctionInfo, FunctionListOptions, FunctionDetailOptions, 
  FunctionExecutionParams 
} from '../models/FunctionInfo';
import { createComponentLogger } from '../utils/logger';

/**
 * Handler para operações com funções via MCP
 */
export class FunctionHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_function';
  private functionService: FunctionService;
  private logger = createComponentLogger('FunctionHandler');

  /**
   * Cria uma nova instância do FunctionHandler
   * 
   * @param functionService Serviço de funções a ser utilizado
   */
  constructor(functionService: FunctionService) {
    this.functionService = functionService;
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
        if (!parameters.functionName) {
          throw new Error("Required parameter 'functionName' is missing");
        }
        if (typeof parameters.functionName !== 'string') {
          throw new Error("Parameter 'functionName' must be a string");
        }
        break;
        
      case 'execute':
        if (!parameters.functionName) {
          throw new Error("Required parameter 'functionName' is missing");
        }
        if (typeof parameters.functionName !== 'string') {
          throw new Error("Parameter 'functionName' must be a string");
        }
        if (parameters.args && !Array.isArray(parameters.args)) {
          throw new Error("Parameter 'args' must be an array");
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
        const listOptions: FunctionListOptions = {
          includeFunctions: parameters.includeFunctions !== false,
          includeProcedures: parameters.includeProcedures !== false,
          language: parameters.language,
          limit: parameters.limit || 100,
          offset: parameters.offset || 0
        };
        
        const functions = await this.functionService.listFunctions(schema, listOptions);
        return { success: true, data: functions };
        
      case 'get':
        const detailOptions: FunctionDetailOptions = {
          includeDefinition: parameters.includeDefinition !== false
        };
        
        const functionInfo = await this.functionService.getFunctionDetails(
          parameters.functionName,
          schema,
          detailOptions
        );
        return { success: true, data: functionInfo };
        
      case 'execute':
        const execParams: FunctionExecutionParams = {
          functionName: parameters.functionName,
          schemaName: schema,
          args: parameters.args || []
        };
        
        const result = await this.functionService.executeFunction(execParams);
        return { success: true, data: result };
        
      default:
        throw new Error(`Unsupported operation: ${operation}`);
    }
  }
} 