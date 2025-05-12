/**
 * Function Service Implementation
 * 
 * Este serviço gerencia operações relacionadas a funções e procedimentos armazenados
 * no PostgreSQL, incluindo listar, obter detalhes e executar funções.
 */

import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { PostgresSchemaManager, FunctionInfo as SchemaFunctionInfo } from '../database/PostgresSchemaManager';
import { createComponentLogger } from '../utils/logger';
import { 
  FunctionInfo, FunctionType, FunctionVolatility, FunctionListOptions, 
  FunctionDetailOptions, FunctionArgument, FunctionExecutionParams 
} from '../models/FunctionInfo';
import { QueryException } from '../utils/exceptions';

/**
 * Serviço para gerenciamento de funções armazenadas
 */
export class FunctionService extends AbstractService {
  private logger = createComponentLogger('FunctionService');
  private schemaManager: PostgresSchemaManager;

  /**
   * Cria uma nova instância do serviço de funções
   * 
   * @param connection Conexão PostgreSQL
   */
  constructor(connection: PostgresConnection) {
    super();
    this.schemaManager = new PostgresSchemaManager(connection);
    this.logger.debug('Function service initialized');
  }

  /**
   * Lista funções em um schema
   * 
   * @param schemaName Nome do schema
   * @param options Opções de listagem
   * @returns Lista de funções
   */
  async listFunctions(
    schemaName: string = 'public',
    options: FunctionListOptions = {}
  ): Promise<FunctionInfo[]> {
    try {
      const limit = options.limit || 100;
      const offset = options.offset || 0;
      
      this.logger.debug(`Listing functions in schema ${schemaName}`, options);
      
      // Busca as funções no banco de dados
      const functionRows = await this.schemaManager.listFunctions(schemaName);
      
      // Filtra por tipo (function/procedure)
      let functions = functionRows
        .filter(fn => {
          if (options.includeFunctions === false && fn.functionType === 'FUNCTION') return false;
          if (options.includeProcedures === false && fn.functionType === 'PROCEDURE') return false;
          return true;
        });
      
      // Filtra por linguagem se especificado
      if (options.language) {
        functions = functions.filter(fn => fn.language === options.language);
      }
      
      // Mapeia para o modelo FunctionInfo
      const mappedFunctions = functions.map(row => this.mapToFunctionInfo(row));
      
      // Aplica paginação
      return mappedFunctions.slice(offset, offset + limit);
    } catch (error: any) {
      this.logger.error(`Failed to list functions in schema: ${schemaName}`, error);
      throw this.createError(
        `Failed to list functions: ${error.message}`,
        'database_error',
        { schemaName, cause: error }
      );
    }
  }

  /**
   * Obtém detalhes de uma função específica
   * 
   * @param functionName Nome da função
   * @param schemaName Nome do schema
   * @param options Opções de detalhes
   * @returns Informações da função
   */
  async getFunctionDetails(
    functionName: string,
    schemaName: string = 'public',
    options: FunctionDetailOptions = {}
  ): Promise<FunctionInfo> {
    try {
      const includeDefinition = options.includeDefinition ?? true;
      
      this.logger.debug(`Getting function details: ${schemaName}.${functionName}`, options);
      
      // Busca informações básicas da função
      const functionRow = await this.schemaManager.getFunctionInfo(functionName, schemaName);
      
      // Mapeia para o modelo FunctionInfo
      const functionInfo = this.mapToFunctionInfo(functionRow);
      
      // Se solicitado, adiciona a definição SQL
      if (includeDefinition) {
        functionInfo.definition = await this.schemaManager.getFunctionDefinition(functionName, schemaName);
      }
      
      return functionInfo;
    } catch (error: any) {
      this.logger.error(`Failed to get function details: ${schemaName}.${functionName}`, error);
      throw this.createError(
        `Failed to get function details: ${error.message}`,
        'database_error',
        { schemaName, functionName, cause: error }
      );
    }
  }

  /**
   * Executa uma função ou procedimento armazenado
   * 
   * @param params Parâmetros para execução da função
   * @returns Resultado da execução
   */
  async executeFunction(params: FunctionExecutionParams): Promise<any> {
    try {
      const { functionName, schemaName, args } = params;
      
      this.logger.debug(`Executing function: ${schemaName}.${functionName}`, { argsCount: args.length });
      
      // Executa a função e retorna o resultado
      return await this.schemaManager.executeFunction(functionName, schemaName, args);
    } catch (error: any) {
      this.logger.error(`Failed to execute function: ${params.schemaName}.${params.functionName}`, error);
      throw this.createError(
        `Failed to execute function: ${error.message}`,
        'database_error',
        { 
          schemaName: params.schemaName, 
          functionName: params.functionName,
          cause: error 
        }
      );
    }
  }

  /**
   * Mapeia uma linha de tabela para o modelo FunctionInfo
   * 
   * @param row Informação da função do SchemaManager
   * @returns Modelo FunctionInfo
   */
  private mapToFunctionInfo(row: SchemaFunctionInfo): FunctionInfo {
    // Mapeamento dos argumentos
    const args: FunctionArgument[] = row.argumentNames.map((name, index) => ({
      name,
      dataType: row.argumentTypes[index],
      defaultValue: row.argumentDefaults[index] || undefined
    }));
    
    return {
      functionName: row.functionName,
      schemaName: row.schemaName,
      functionType: row.functionType === 'FUNCTION' ? FunctionType.FUNCTION : FunctionType.PROCEDURE,
      returnType: row.returnType,
      arguments: args,
      language: row.language,
      volatility: this.mapVolatility(row.volatility),
      owner: row.owner,
      description: row.description
    };
  }
  
  /**
   * Mapeia string de volatilidade para enum
   */
  private mapVolatility(volatility?: string): FunctionVolatility {
    if (volatility === 'IMMUTABLE') return FunctionVolatility.IMMUTABLE;
    if (volatility === 'STABLE') return FunctionVolatility.STABLE;
    return FunctionVolatility.VOLATILE;
  }
} 