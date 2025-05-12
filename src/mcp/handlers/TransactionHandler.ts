/**
 * MCP TransactionHandler
 * 
 * Handler para gerenciamento de transações no banco de dados PostgreSQL
 * através do protocolo MCP.
 */

import { IMCPHandler } from '../router/MCPRouter';
import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { TransactionService } from '../../services/TransactionService';
import { createComponentLogger } from '../../utils/logger';

/**
 * Handler para operações de transação via MCP
 */
export class TransactionHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_transaction';
  private transactionService: TransactionService;
  private logger = createComponentLogger('TransactionHandler');
  private activeTransactions: Map<string, string> = new Map(); // transactionId -> sessionId

  /**
   * Cria uma nova instância do TransactionHandler
   * 
   * @param transactionService Serviço de transações a ser utilizado
   */
  constructor(transactionService: TransactionService) {
    this.transactionService = transactionService;
  }

  /**
   * Processa requisições MCP para operações de transação
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
              'begin', 'commit', 'rollback', 'executeInTransaction',
              'savepoint', 'rollbackToSavepoint', 'getTransactionStatus'
            ] 
          },
          request.requestId
        );
      }

      switch (operation) {
        case 'begin':
          return await this.handleBegin(request);
        case 'commit':
          return await this.handleCommit(request);
        case 'rollback':
          return await this.handleRollback(request);
        case 'executeInTransaction':
          return await this.handleExecuteInTransaction(request);
        case 'savepoint':
          return await this.handleSavepoint(request);
        case 'rollbackToSavepoint':
          return await this.handleRollbackToSavepoint(request);
        case 'getTransactionStatus':
          return await this.handleGetTransactionStatus(request);
        default:
          return MCPResponse.error(
            `Operação '${operation}' não suportada pelo handler de transação`,
            { 
              availableOperations: [
                'begin', 'commit', 'rollback', 'executeInTransaction',
                'savepoint', 'rollbackToSavepoint', 'getTransactionStatus'
              ] 
            },
            request.requestId
          );
      }
    } catch (error) {
      this.logger.error(`Erro ao processar requisição de transação: ${error.message}`, { 
        stack: error.stack,
        requestId: request.requestId
      });
      
      return MCPResponse.error(
        `Erro ao processar operação de transação: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de início de transação
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleBegin(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const isolationLevel = request.parameters?.isolationLevel;
    const readOnly = request.parameters?.readOnly === true;
    const deferrable = request.parameters?.deferrable === true;
    const sessionId = request.sessionId || 'default';

    // Verifica se já existe uma transação ativa para esta sessão
    for (const [txId, sessId] of this.activeTransactions.entries()) {
      if (sessId === sessionId) {
        return MCPResponse.error(
          'Já existe uma transação ativa para esta sessão',
          { transactionId: txId },
          request.requestId
        );
      }
    }

    this.logger.debug(`Iniciando transação`, {
      isolationLevel, readOnly, deferrable, sessionId, requestId: request.requestId
    });

    try {
      // Inicia a transação
      const result = await this.transactionService.begin({
        isolationLevel,
        readOnly,
        deferrable
      });

      // Registra a transação ativa
      this.activeTransactions.set(result.transactionId, sessionId);

      return MCPResponse.success(
        {
          transactionId: result.transactionId,
          isolationLevel: result.isolationLevel,
          readOnly: result.readOnly,
          deferrable: result.deferrable
        },
        `Transação iniciada com sucesso (${result.isolationLevel}${readOnly ? ', somente leitura' : ''}${deferrable ? ', adiável' : ''})`,
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao iniciar transação: ${error.message}`,
        { error: error.message },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de commit de transação
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleCommit(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const transactionId = request.parameters?.transactionId;
    const sessionId = request.sessionId || 'default';

    // Validação
    if (!transactionId) {
      return MCPResponse.error(
        'Parâmetro obrigatório "transactionId" não fornecido',
        null,
        request.requestId
      );
    }

    // Verifica se a transação pertence à sessão atual
    if (this.activeTransactions.get(transactionId) !== sessionId) {
      return MCPResponse.error(
        'Transação não encontrada ou não pertence à sessão atual',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Confirmando transação ${transactionId}`, {
      sessionId, requestId: request.requestId
    });

    try {
      // Realiza o commit
      await this.transactionService.commit(transactionId);

      // Remove a transação da lista de ativas
      this.activeTransactions.delete(transactionId);

      return MCPResponse.success(
        { transactionId },
        `Transação confirmada com sucesso`,
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao confirmar transação: ${error.message}`,
        { 
          transactionId,
          error: error.message 
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de rollback de transação
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleRollback(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const transactionId = request.parameters?.transactionId;
    const sessionId = request.sessionId || 'default';

    // Validação
    if (!transactionId) {
      return MCPResponse.error(
        'Parâmetro obrigatório "transactionId" não fornecido',
        null,
        request.requestId
      );
    }

    // Verifica se a transação pertence à sessão atual
    if (this.activeTransactions.get(transactionId) !== sessionId) {
      return MCPResponse.error(
        'Transação não encontrada ou não pertence à sessão atual',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Revertendo transação ${transactionId}`, {
      sessionId, requestId: request.requestId
    });

    try {
      // Realiza o rollback
      await this.transactionService.rollback(transactionId);

      // Remove a transação da lista de ativas
      this.activeTransactions.delete(transactionId);

      return MCPResponse.success(
        { transactionId },
        `Transação revertida com sucesso`,
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao reverter transação: ${error.message}`,
        { 
          transactionId,
          error: error.message 
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de execução de consulta em uma transação
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleExecuteInTransaction(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const transactionId = request.parameters?.transactionId;
    const sql = request.parameters?.sql;
    const parameters = request.parameters?.parameters || [];
    const sessionId = request.sessionId || 'default';

    // Validação
    if (!transactionId) {
      return MCPResponse.error(
        'Parâmetro obrigatório "transactionId" não fornecido',
        null,
        request.requestId
      );
    }

    if (!sql) {
      return MCPResponse.error(
        'Parâmetro obrigatório "sql" não fornecido',
        null,
        request.requestId
      );
    }

    // Verifica se a transação pertence à sessão atual
    if (this.activeTransactions.get(transactionId) !== sessionId) {
      return MCPResponse.error(
        'Transação não encontrada ou não pertence à sessão atual',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Executando consulta na transação ${transactionId}`, {
      sql, parameters, sessionId, requestId: request.requestId
    });

    try {
      // Executa a consulta na transação
      const result = await this.transactionService.executeQuery(
        transactionId,
        sql,
        parameters
      );

      return MCPResponse.success(
        {
          transactionId,
          records: result.records,
          rowCount: result.rowCount,
          fields: result.fields,
          command: result.command,
          executionTime: result.executionTime
        },
        `Consulta executada com sucesso na transação. ${result.records.length} registro(s) retornado(s).`,
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao executar consulta na transação: ${error.message}`,
        { 
          transactionId,
          error: error.message 
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de criação de savepoint
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleSavepoint(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const transactionId = request.parameters?.transactionId;
    const savepointName = request.parameters?.savepointName;
    const sessionId = request.sessionId || 'default';

    // Validação
    if (!transactionId) {
      return MCPResponse.error(
        'Parâmetro obrigatório "transactionId" não fornecido',
        null,
        request.requestId
      );
    }

    if (!savepointName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "savepointName" não fornecido',
        null,
        request.requestId
      );
    }

    // Verifica se a transação pertence à sessão atual
    if (this.activeTransactions.get(transactionId) !== sessionId) {
      return MCPResponse.error(
        'Transação não encontrada ou não pertence à sessão atual',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Criando savepoint "${savepointName}" na transação ${transactionId}`, {
      sessionId, requestId: request.requestId
    });

    try {
      // Cria o savepoint
      await this.transactionService.savepoint(transactionId, savepointName);

      return MCPResponse.success(
        { 
          transactionId,
          savepointName
        },
        `Savepoint "${savepointName}" criado com sucesso`,
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao criar savepoint: ${error.message}`,
        { 
          transactionId,
          savepointName,
          error: error.message 
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de rollback para um savepoint
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleRollbackToSavepoint(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const transactionId = request.parameters?.transactionId;
    const savepointName = request.parameters?.savepointName;
    const sessionId = request.sessionId || 'default';

    // Validação
    if (!transactionId) {
      return MCPResponse.error(
        'Parâmetro obrigatório "transactionId" não fornecido',
        null,
        request.requestId
      );
    }

    if (!savepointName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "savepointName" não fornecido',
        null,
        request.requestId
      );
    }

    // Verifica se a transação pertence à sessão atual
    if (this.activeTransactions.get(transactionId) !== sessionId) {
      return MCPResponse.error(
        'Transação não encontrada ou não pertence à sessão atual',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Revertendo para savepoint "${savepointName}" na transação ${transactionId}`, {
      sessionId, requestId: request.requestId
    });

    try {
      // Reverte para o savepoint
      await this.transactionService.rollbackToSavepoint(transactionId, savepointName);

      return MCPResponse.success(
        { 
          transactionId,
          savepointName
        },
        `Revertido para savepoint "${savepointName}" com sucesso`,
        request.requestId
      );
    } catch (error) {
      return MCPResponse.error(
        `Falha ao reverter para savepoint: ${error.message}`,
        { 
          transactionId,
          savepointName,
          error: error.message 
        },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de obtenção do status da transação
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetTransactionStatus(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const transactionId = request.parameters?.transactionId;
    const sessionId = request.sessionId || 'default';

    // Se não foi fornecido um ID de transação, retorna todas as transações ativas para a sessão
    if (!transactionId) {
      const sessionTransactions = [];
      
      for (const [txId, sessId] of this.activeTransactions.entries()) {
        if (sessId === sessionId) {
          try {
            const status = await this.transactionService.getTransactionStatus(txId);
            sessionTransactions.push({
              transactionId: txId,
              ...status
            });
          } catch (error) {
            this.logger.warn(`Falha ao obter status da transação ${txId}: ${error.message}`);
            // Remove transações que não existem mais
            this.activeTransactions.delete(txId);
          }
        }
      }

      return MCPResponse.success(
        { transactions: sessionTransactions },
        `${sessionTransactions.length} transação(ões) ativa(s) na sessão atual`,
        request.requestId
      );
    }

    // Verifica se a transação pertence à sessão atual
    if (this.activeTransactions.get(transactionId) !== sessionId) {
      return MCPResponse.error(
        'Transação não encontrada ou não pertence à sessão atual',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Obtendo status da transação ${transactionId}`, {
      sessionId, requestId: request.requestId
    });

    try {
      // Obtém o status da transação
      const status = await this.transactionService.getTransactionStatus(transactionId);

      return MCPResponse.success(
        { 
          transactionId,
          ...status
        },
        `Status da transação obtido com sucesso`,
        request.requestId
      );
    } catch (error) {
      // Se a transação não existe mais, a remove da lista
      if (error.message.includes('não encontrada') || error.message.includes('not found')) {
        this.activeTransactions.delete(transactionId);
      }

      return MCPResponse.error(
        `Falha ao obter status da transação: ${error.message}`,
        { 
          transactionId,
          error: error.message 
        },
        request.requestId
      );
    }
  }

  /**
   * Limpa transações inválidas ou expiradas
   */
  public async cleanupTransactions(): Promise<void> {
    const invalidTransactions = [];

    for (const [txId, _] of this.activeTransactions.entries()) {
      try {
        // Verifica se a transação ainda é válida
        await this.transactionService.getTransactionStatus(txId);
      } catch (error) {
        // Se houver erro, a transação não é mais válida
        invalidTransactions.push(txId);
      }
    }

    // Remove as transações inválidas
    for (const txId of invalidTransactions) {
      this.activeTransactions.delete(txId);
    }

    if (invalidTransactions.length > 0) {
      this.logger.debug(`Limpeza de transações: ${invalidTransactions.length} transações inválidas removidas`);
    }
  }
} 