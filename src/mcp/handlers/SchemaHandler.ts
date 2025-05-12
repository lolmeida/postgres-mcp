/**
 * MCP SchemaHandler
 * 
 * Handler para gerenciamento de schemas através do protocolo MCP.
 * Implementa métodos para listar, criar e modificar objetos de schema como
 * tabelas, colunas, índices, etc.
 */

import { IMCPHandler } from '../router/MCPRouter';
import { MCPRequest } from '../models/MCPRequest';
import { MCPResponse } from '../models/MCPResponse';
import { SchemaService } from '../../services/SchemaService';
import { createComponentLogger } from '../../utils/logger';

/**
 * Handler para operações de schema via MCP
 */
export class SchemaHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_schema';
  private schemaService: SchemaService;
  private logger = createComponentLogger('SchemaHandler');

  /**
   * Cria uma nova instância do SchemaHandler
   * 
   * @param schemaService Serviço de schema a ser utilizado
   */
  constructor(schemaService: SchemaService) {
    this.schemaService = schemaService;
  }

  /**
   * Processa requisições MCP para operações de schema
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
              'listTables', 'getTableDetails', 'createTable', 'alterTable', 'dropTable',
              'listSchemas', 'createSchema', 'dropSchema',
              'listIndexes', 'createIndex', 'dropIndex',
              'listForeignKeys', 'addForeignKey', 'dropForeignKey'
            ] 
          },
          request.requestId
        );
      }

      switch (operation) {
        case 'listTables':
          return await this.handleListTables(request);
        case 'getTableDetails':
          return await this.handleGetTableDetails(request);
        case 'createTable':
          return await this.handleCreateTable(request);
        case 'alterTable':
          return await this.handleAlterTable(request);
        case 'dropTable':
          return await this.handleDropTable(request);
        case 'listSchemas':
          return await this.handleListSchemas(request);
        case 'createSchema':
          return await this.handleCreateSchema(request);
        case 'dropSchema':
          return await this.handleDropSchema(request);
        case 'listIndexes':
          return await this.handleListIndexes(request);
        case 'createIndex':
          return await this.handleCreateIndex(request);
        case 'dropIndex':
          return await this.handleDropIndex(request);
        case 'listForeignKeys':
          return await this.handleListForeignKeys(request);
        case 'addForeignKey':
          return await this.handleAddForeignKey(request);
        case 'dropForeignKey':
          return await this.handleDropForeignKey(request);
        default:
          return MCPResponse.error(
            `Operação '${operation}' não suportada pelo handler de schema`,
            { 
              availableOperations: [
                'listTables', 'getTableDetails', 'createTable', 'alterTable', 'dropTable',
                'listSchemas', 'createSchema', 'dropSchema',
                'listIndexes', 'createIndex', 'dropIndex',
                'listForeignKeys', 'addForeignKey', 'dropForeignKey'
              ] 
            },
            request.requestId
          );
      }
    } catch (error) {
      this.logger.error(`Erro ao processar requisição de schema: ${error.message}`, { 
        stack: error.stack,
        requestId: request.requestId
      });
      
      return MCPResponse.error(
        `Erro ao processar operação de schema: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }

  /**
   * Processa a operação de listagem de tabelas
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleListTables(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const schemaName = request.parameters?.schemaName || 'public';
    const includeSystem = request.parameters?.includeSystem === true;
    const includeViews = request.parameters?.includeViews !== false;

    this.logger.debug(`Listando tabelas no schema ${schemaName}`, {
      includeSystem, includeViews, requestId: request.requestId
    });

    // Executa a operação
    const tables = await this.schemaService.listTables({
      schemaName,
      includeSystem,
      includeViews
    });

    return MCPResponse.success(
      { tables },
      `Listadas ${tables.length} tabelas no schema '${schemaName}'`,
      request.requestId
    );
  }

  /**
   * Processa a operação de obtenção de detalhes de uma tabela
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleGetTableDetails(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const includeRelations = request.parameters?.includeRelations !== false;
    const includeIndexes = request.parameters?.includeIndexes !== false;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Obtendo detalhes da tabela ${schemaName}.${tableName}`, {
      includeRelations, includeIndexes, requestId: request.requestId
    });

    // Executa a operação
    const tableDetails = await this.schemaService.getTableDetails(
      tableName,
      schemaName,
      { includeRelations, includeIndexes }
    );

    if (!tableDetails) {
      return MCPResponse.error(
        `Tabela '${schemaName}.${tableName}' não encontrada`,
        null,
        request.requestId
      );
    }

    return MCPResponse.success(
      tableDetails,
      `Detalhes da tabela '${schemaName}.${tableName}' obtidos com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de criação de tabela
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleCreateTable(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const columns = request.parameters?.columns;
    const primaryKey = request.parameters?.primaryKey;
    const indexes = request.parameters?.indexes;
    const foreignKeys = request.parameters?.foreignKeys;
    const ifNotExists = request.parameters?.ifNotExists === true;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    if (!columns || !Array.isArray(columns) || columns.length === 0) {
      return MCPResponse.error(
        'Parâmetro obrigatório "columns" não fornecido ou inválido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Criando tabela ${schemaName}.${tableName}`, {
      columns, primaryKey, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.createTable(
      tableName,
      schemaName,
      columns,
      { primaryKey, indexes, foreignKeys, ifNotExists }
    );

    return MCPResponse.success(
      result,
      `Tabela '${schemaName}.${tableName}' criada com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de alteração de tabela
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleAlterTable(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const addColumns = request.parameters?.addColumns;
    const alterColumns = request.parameters?.alterColumns;
    const dropColumns = request.parameters?.dropColumns;
    const newName = request.parameters?.newName;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    if (!addColumns && !alterColumns && !dropColumns && !newName) {
      return MCPResponse.error(
        'Pelo menos um dos parâmetros de alteração (addColumns, alterColumns, dropColumns, newName) deve ser fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Alterando tabela ${schemaName}.${tableName}`, {
      addColumns, alterColumns, dropColumns, newName, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.alterTable(
      tableName,
      schemaName,
      { addColumns, alterColumns, dropColumns, newName }
    );

    const newTableName = newName || tableName;
    return MCPResponse.success(
      result,
      `Tabela '${schemaName}.${tableName}' alterada com sucesso${newName ? ` para '${schemaName}.${newName}'` : ''}`,
      request.requestId
    );
  }

  /**
   * Processa a operação de remoção de tabela
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleDropTable(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const ifExists = request.parameters?.ifExists !== false;
    const cascade = request.parameters?.cascade === true;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Removendo tabela ${schemaName}.${tableName}`, {
      ifExists, cascade, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.dropTable(
      tableName,
      schemaName,
      { ifExists, cascade }
    );

    return MCPResponse.success(
      result,
      `Tabela '${schemaName}.${tableName}' removida com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de listagem de schemas
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleListSchemas(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const includeSystem = request.parameters?.includeSystem === true;

    this.logger.debug(`Listando schemas`, {
      includeSystem, requestId: request.requestId
    });

    // Executa a operação
    const schemas = await this.schemaService.listSchemas({ includeSystem });

    return MCPResponse.success(
      { schemas },
      `Listados ${schemas.length} schemas`,
      request.requestId
    );
  }

  /**
   * Processa a operação de criação de schema
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleCreateSchema(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const schemaName = request.parameters?.schemaName;
    const ifNotExists = request.parameters?.ifNotExists !== false;

    // Validação
    if (!schemaName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "schemaName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Criando schema ${schemaName}`, {
      ifNotExists, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.createSchema(
      schemaName,
      { ifNotExists }
    );

    return MCPResponse.success(
      result,
      `Schema '${schemaName}' criado com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de remoção de schema
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleDropSchema(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const schemaName = request.parameters?.schemaName;
    const ifExists = request.parameters?.ifExists !== false;
    const cascade = request.parameters?.cascade === true;

    // Validação
    if (!schemaName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "schemaName" não fornecido',
        null,
        request.requestId
      );
    }

    if (schemaName === 'public' && !request.parameters?.force) {
      return MCPResponse.error(
        'Não é possível remover o schema "public" sem o parâmetro "force"',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Removendo schema ${schemaName}`, {
      ifExists, cascade, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.dropSchema(
      schemaName,
      { ifExists, cascade }
    );

    return MCPResponse.success(
      result,
      `Schema '${schemaName}' removido com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de listagem de índices
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleListIndexes(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Listando índices da tabela ${schemaName}.${tableName}`, {
      requestId: request.requestId
    });

    // Executa a operação
    const indexes = await this.schemaService.listIndexes(tableName, schemaName);

    return MCPResponse.success(
      { indexes },
      `Listados ${indexes.length} índices da tabela '${schemaName}.${tableName}'`,
      request.requestId
    );
  }

  /**
   * Processa a operação de criação de índice
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleCreateIndex(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const indexName = request.parameters?.indexName;
    const columns = request.parameters?.columns;
    const unique = request.parameters?.unique === true;
    const method = request.parameters?.method;
    const where = request.parameters?.where;
    const ifNotExists = request.parameters?.ifNotExists !== false;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    if (!columns || !Array.isArray(columns) || columns.length === 0) {
      return MCPResponse.error(
        'Parâmetro obrigatório "columns" não fornecido ou inválido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Criando índice ${indexName || '(auto)'} na tabela ${schemaName}.${tableName}`, {
      columns, unique, method, where, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.createIndex(
      tableName,
      schemaName,
      columns,
      { indexName, unique, method, where, ifNotExists }
    );

    return MCPResponse.success(
      result,
      `Índice '${result.indexName}' criado com sucesso na tabela '${schemaName}.${tableName}'`,
      request.requestId
    );
  }

  /**
   * Processa a operação de remoção de índice
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleDropIndex(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const indexName = request.parameters?.indexName;
    const schemaName = request.parameters?.schemaName || 'public';
    const ifExists = request.parameters?.ifExists !== false;

    // Validação
    if (!indexName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "indexName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Removendo índice ${schemaName}.${indexName}`, {
      ifExists, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.dropIndex(
      indexName,
      schemaName,
      { ifExists }
    );

    return MCPResponse.success(
      result,
      `Índice '${schemaName}.${indexName}' removido com sucesso`,
      request.requestId
    );
  }

  /**
   * Processa a operação de listagem de chaves estrangeiras
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleListForeignKeys(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Listando chaves estrangeiras da tabela ${schemaName}.${tableName}`, {
      requestId: request.requestId
    });

    // Executa a operação
    const foreignKeys = await this.schemaService.listForeignKeys(tableName, schemaName);

    return MCPResponse.success(
      { foreignKeys },
      `Listadas ${foreignKeys.length} chaves estrangeiras da tabela '${schemaName}.${tableName}'`,
      request.requestId
    );
  }

  /**
   * Processa a operação de adição de chave estrangeira
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleAddForeignKey(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const constraintName = request.parameters?.constraintName;
    const columns = request.parameters?.columns;
    const referenceTable = request.parameters?.referenceTable;
    const referenceSchema = request.parameters?.referenceSchema || 'public';
    const referenceColumns = request.parameters?.referenceColumns;
    const onDelete = request.parameters?.onDelete;
    const onUpdate = request.parameters?.onUpdate;
    const deferrable = request.parameters?.deferrable === true;
    const initiallyDeferred = request.parameters?.initiallyDeferred === true;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    if (!columns || !Array.isArray(columns) || columns.length === 0) {
      return MCPResponse.error(
        'Parâmetro obrigatório "columns" não fornecido ou inválido',
        null,
        request.requestId
      );
    }

    if (!referenceTable) {
      return MCPResponse.error(
        'Parâmetro obrigatório "referenceTable" não fornecido',
        null,
        request.requestId
      );
    }

    if (!referenceColumns || !Array.isArray(referenceColumns) || referenceColumns.length === 0) {
      return MCPResponse.error(
        'Parâmetro obrigatório "referenceColumns" não fornecido ou inválido',
        null,
        request.requestId
      );
    }

    if (columns.length !== referenceColumns.length) {
      return MCPResponse.error(
        'O número de colunas deve ser igual ao número de colunas de referência',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Adicionando chave estrangeira à tabela ${schemaName}.${tableName}`, {
      columns, referenceTable, referenceColumns, onDelete, onUpdate, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.addForeignKey(
      tableName,
      schemaName,
      columns,
      referenceTable,
      referenceColumns,
      {
        constraintName,
        referenceSchema,
        onDelete,
        onUpdate,
        deferrable,
        initiallyDeferred
      }
    );

    return MCPResponse.success(
      result,
      `Chave estrangeira '${result.constraintName}' adicionada com sucesso à tabela '${schemaName}.${tableName}'`,
      request.requestId
    );
  }

  /**
   * Processa a operação de remoção de chave estrangeira
   * 
   * @param request Requisição MCP
   * @returns Resposta MCP
   */
  private async handleDropForeignKey(request: MCPRequest): Promise<MCPResponse> {
    // Extrai parâmetros da requisição
    const tableName = request.parameters?.tableName;
    const schemaName = request.parameters?.schemaName || 'public';
    const constraintName = request.parameters?.constraintName;
    const ifExists = request.parameters?.ifExists !== false;

    // Validação
    if (!tableName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "tableName" não fornecido',
        null,
        request.requestId
      );
    }

    if (!constraintName) {
      return MCPResponse.error(
        'Parâmetro obrigatório "constraintName" não fornecido',
        null,
        request.requestId
      );
    }

    this.logger.debug(`Removendo chave estrangeira ${constraintName} da tabela ${schemaName}.${tableName}`, {
      ifExists, requestId: request.requestId
    });

    // Executa a operação
    const result = await this.schemaService.dropForeignKey(
      tableName,
      schemaName,
      constraintName,
      { ifExists }
    );

    return MCPResponse.success(
      result,
      `Chave estrangeira '${constraintName}' removida com sucesso da tabela '${schemaName}.${tableName}'`,
      request.requestId
    );
  }
} 