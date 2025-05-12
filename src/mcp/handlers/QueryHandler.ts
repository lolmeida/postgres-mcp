/**
 * MCP QueryHandler
 * 
 * Handler para execução de consultas SQL através do protocolo MCP.
 * Implementa métodos para executar consultas, consultas parametrizadas
 * e consultas com resultados paginados.
 */

import { IMCPHandler } from '../router/MCPRouter';
import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { QueryService } from '../../services/QueryService';
import { createComponentLogger } from '../../utils/logger';

/**
 * Handler para execução de consultas SQL via MCP
 */
export class QueryHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_query';
  private queryService: QueryService;
  private logger = createComponentLogger('QueryHandler');

  /**
   * Cria uma nova instância do QueryHandler
   * 
   * @param queryService Serviço de consultas a ser utilizado
   */
  constructor(queryService: QueryService) {
    this.queryService = queryService;
  }

  /**
   * Processa requisições MCP para execução de consultas SQL
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  async handle(request: MCPRequest): Promise<MCPResponse> {
    try {
      // Verifica qual operação deve ser executada com base na requisição
      const operation = request.parameters?.operation || 'executeQuery';

      switch (operation) {
        case 'executeQuery':
          return await this.handleExecuteQuery(request);
        case 'executeQuerySingle':
          return await this.handleExecuteQuerySingle(request);
        case 'executeQueryCount':
          return await this.handleExecuteQueryCount(request);
        case 'explainQuery':
          return await this.handleExplainQuery(request);
        default:
          return MCPResponse.error(
            `Operação '${operation}' não suportada pelo handler de consultas`,
            { availableOperations: ['executeQuery', 'executeQuerySingle', 'executeQueryCount', 'explainQuery'] },
            request.requestId
          );
      }
    } catch (error) {
      this.logger.error(`Erro ao processar requisição de consulta: ${error.message}`, { 
        stack: error.stack,
        requestId: request.requestId
      });
      
      return MCPResponse.error(
        `Erro ao executar consulta SQL: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de execução de consulta
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleExecuteQuery(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const sql = request.parameters?.sql;
    const parameters = request.parameters?.parameters || [];
    const options = {
      maxRows: request.parameters?.maxRows || 1000,
      timeout: request.parameters?.timeout,
      convertTypes: request.parameters?.convertTypes !== false,
      usePreparedStatement: request.parameters?.usePreparedStatement !== false
    };

    // Validação
    if (!sql) {
      return MCPResponse.error(
        'Parâmetro obrigatório "sql" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Executando consulta SQL`, {
      query: sql, parameters, options, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.queryService.executeQuery(sql, {
      parameters,
      maxRows: options.maxRows,
      timeout: options.timeout,
      convertTypes: options.convertTypes,
      usePreparedStatement: options.usePreparedStatement
    });

    return MCPResponse.success(
      {
        records: result.records,
        count: result.records.length,
        fields: result.fields,
        rowCount: result.rowCount,
        command: result.command,
        executionTime: result.executionTime
      },
      `Consulta executada com sucesso. ${result.records.length} registro(s) retornado(s).`,
      request.requestId
    );
  }

  /**
   * Processa a operação de execução de consulta com retorno único
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleExecuteQuerySingle(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const sql = request.parameters?.sql;
    const parameters = request.parameters?.parameters || [];
    const options = {
      timeout: request.parameters?.timeout,
      convertTypes: request.parameters?.convertTypes !== false,
      usePreparedStatement: request.parameters?.usePreparedStatement !== false
    };

    // Validação
    if (!sql) {
      return MCPResponse.error(
        'Parâmetro obrigatório "sql" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Executando consulta SQL (single)`, {
      query: sql, parameters, options, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.queryService.executeQuerySingle(sql, {
      parameters,
      timeout: options.timeout,
      convertTypes: options.convertTypes,
      usePreparedStatement: options.usePreparedStatement
    });

    return MCPResponse.success(
      {
        record: result.record,
        fields: result.fields,
        executionTime: result.executionTime,
        found: result.found
      },
      result.found 
        ? `Consulta executada com sucesso. Registro encontrado.`
        : `Consulta executada com sucesso. Nenhum registro encontrado.`,
      request.requestId
    );
  }

  /**
   * Processa a operação de execução de consulta de contagem
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleExecuteQueryCount(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const sql = request.parameters?.sql;
    const parameters = request.parameters?.parameters || [];
    const options = {
      timeout: request.parameters?.timeout,
      usePreparedStatement: request.parameters?.usePreparedStatement !== false
    };

    // Validação
    if (!sql) {
      return MCPResponse.error(
        'Parâmetro obrigatório "sql" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Executando consulta SQL (count)`, {
      query: sql, parameters, options, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.queryService.executeQueryCount(sql, {
      parameters,
      timeout: options.timeout,
      usePreparedStatement: options.usePreparedStatement
    });

    return MCPResponse.success(
      {
        count: result.count,
        executionTime: result.executionTime
      },
      `Consulta de contagem executada com sucesso. Total: ${result.count}`,
      request.requestId
    );
  }

  /**
   * Processa a operação de explicação de consulta (EXPLAIN)
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleExplainQuery(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const sql = request.parameters?.sql;
    const parameters = request.parameters?.parameters || [];
    const options = {
      format: request.parameters?.format || 'text',
      analyze: request.parameters?.analyze === true,
      verbose: request.parameters?.verbose === true,
      buffers: request.parameters?.buffers === true,
      timing: request.parameters?.timing !== false
    };

    // Validação
    if (!sql) {
      return MCPResponse.error(
        'Parâmetro obrigatório "sql" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Explicando consulta SQL`, {
      query: sql, parameters, options, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.queryService.explainQuery(sql, {
      parameters,
      ...options
    });

    return MCPResponse.success(
      {
        plan: result.plan,
        format: result.format,
        executionTime: result.executionTime
      },
      `Plano de execução gerado com sucesso.`,
      request.requestId
    );
  }
} 