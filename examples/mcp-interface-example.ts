/**
 * Exemplo de uso da interface MCP
 * 
 * Este exemplo demonstra como configurar e usar os componentes
 * MCP implementados, incluindo:
 * - Configuração do servidor PostgreSQL MCP
 * - Implementação de handlers personalizados
 * - Processamento de requisições MCP
 * - Transporte via STDIO e HTTP
 */

import {
  // Core MCP
  PostgresMCPServer,
  IMCPHandler,
  
  // Modelos
  MCPRequest,
  MCPResponse,
  
  // Transporte
  TransportMode,
  
  // Serviços
  QueryService,
  SchemaService,
  
  // Utilidades
  createComponentLogger
} from '../src';

// Logger para o exemplo
const logger = createComponentLogger('MCPExample');

/**
 * Implementação de um handler MCP para listar tabelas
 */
class ListTablesHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_list_tables';
  private schemaService: SchemaService;
  
  constructor(schemaService: SchemaService) {
    this.schemaService = schemaService;
  }
  
  async handle(request: MCPRequest): Promise<MCPResponse> {
    try {
      // Extrai parâmetros da requisição
      const schemaName = request.parameters?.schema || 'public';
      const includeSystem = request.parameters?.includeSystem === true;
      
      logger.info(`Listando tabelas para schema: ${schemaName}`, { includeSystem });
      
      // Usa o SchemaService para listar tabelas
      const tables = await this.schemaService.listTables(schemaName, {
        includeViews: true
      });
      
      // Retorna a resposta
      return MCPResponse.success(
        { tables },
        `Encontrada(s) ${tables.length} tabela(s) no schema '${schemaName}'`,
        request.requestId
      );
      
    } catch (error: any) {
      logger.error(`Erro ao listar tabelas: ${error.message}`, { stack: error.stack });
      return MCPResponse.error(
        `Erro ao listar tabelas: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }
}

/**
 * Implementação de um handler MCP para executar consultas SQL
 */
class ExecuteQueryHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_execute_query';
  private queryService: QueryService;
  
  constructor(queryService: QueryService) {
    this.queryService = queryService;
  }
  
  async handle(request: MCPRequest): Promise<MCPResponse> {
    try {
      // Extrai parâmetros da requisição
      const sql = request.parameters?.sql;
      const parameters = request.parameters?.parameters || [];
      const maxRows = request.parameters?.maxRows || 1000;
      
      if (!sql) {
        return MCPResponse.error(
          'Parâmetro obrigatório "sql" não fornecido',
          null,
          request.requestId
        );
      }
      
      logger.info(`Executando consulta SQL`, { query: sql });
      
      // Executa a consulta usando o QueryService
      const result = await this.queryService.executeQuery(sql, {
        parameters,
        maxRows
      });
      
      // Retorna a resposta
      return MCPResponse.success(
        result,
        `Consulta executada com sucesso. ${(result as any).records?.length || 0} registro(s) retornado(s).`,
        request.requestId
      );
      
    } catch (error: any) {
      logger.error(`Erro ao executar consulta: ${error.message}`, { stack: error.stack });
      return MCPResponse.error(
        `Erro ao executar consulta: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }
}

/**
 * Implementação de um handler MCP para obter detalhes de uma tabela
 */
class GetTableDetailsHandler implements IMCPHandler {
  readonly toolName: string = 'mcp_postgres_get_table_details';
  private schemaService: SchemaService;
  
  constructor(schemaService: SchemaService) {
    this.schemaService = schemaService;
  }
  
  async handle(request: MCPRequest): Promise<MCPResponse> {
    try {
      // Extrai parâmetros da requisição
      const tableName = request.parameters?.tableName;
      const schemaName = request.parameters?.schemaName || 'public';
      const includeRelations = request.parameters?.includeRelations !== false;
      const includeIndexes = request.parameters?.includeIndexes !== false;
      
      if (!tableName) {
        return MCPResponse.error(
          'Parâmetro obrigatório "tableName" não fornecido',
          null,
          request.requestId
        );
      }
      
      logger.info(`Obtendo detalhes da tabela: ${schemaName}.${tableName}`);
      
      // Obtém os detalhes da tabela
      const tableDetails = await this.schemaService.getTableDetails(
        tableName,
        schemaName,
        { includeRelations, includeIndexes }
      );
      
      // Retorna a resposta
      return MCPResponse.success(
        tableDetails,
        `Detalhes da tabela '${schemaName}.${tableName}' obtidos com sucesso`,
        request.requestId
      );
      
    } catch (error: any) {
      logger.error(`Erro ao obter detalhes da tabela: ${error.message}`, { stack: error.stack });
      return MCPResponse.error(
        `Erro ao obter detalhes da tabela: ${error.message}`,
        { stack: error.stack },
        request.requestId
      );
    }
  }
}

/**
 * Função principal para configurar e iniciar o servidor MCP
 */
async function startMCPServer() {
  try {
    // Configuração para o servidor PostgreSQL MCP
    const serverOptions = {
      database: {
        host: 'localhost',
        port: 5432,
        database: 'postgres',
        user: 'postgres',
        password: 'postgres',
        defaultSchema: 'public'
      },
      transport: {
        // Usar STDIO para exemplos simples, HTTP para aplicações reais
        mode: TransportMode.STDIO,
        port: 3000,   // Usado apenas para modo HTTP
        host: 'localhost',  // Usado apenas para modo HTTP
        path: '/mcp'  // Usado apenas para modo HTTP
      },
      security: {
        enabled: false  // Desabilitar por simplicidade no exemplo
      },
      logging: {
        level: 'debug',
        enableConsole: true
      }
    };
    
    logger.info('Iniciando servidor PostgreSQL MCP...');
    
    // Cria o servidor PostgreSQL MCP
    const mcpServer = new PostgresMCPServer(serverOptions);
    
    // Registra handlers para as ferramentas suportadas
    logger.info('Registrando handlers...');
    
    // Obtém os serviços necessários
    const schemaService = mcpServer.getService('schema') as SchemaService;
    const queryService = mcpServer.getService('query') as QueryService;
    
    // Registra os handlers
    mcpServer.registerHandler(new ListTablesHandler(schemaService));
    mcpServer.registerHandler(new ExecuteQueryHandler(queryService));
    mcpServer.registerHandler(new GetTableDetailsHandler(schemaService));
    
    // Inicia o servidor MCP
    await mcpServer.start();
    
    // No modo STDIO, podemos simular uma requisição para exemplificar
    if (serverOptions.transport.mode === TransportMode.STDIO) {
      setTimeout(() => {
        // Cria uma requisição exemplo para listar tabelas
        logger.info('Simulando requisição para listar tabelas...');
        
        // Estrutura da requisição
        const requestExample = JSON.stringify({
          tool: 'mcp_postgres_list_tables',
          parameters: {
            schema: 'public',
            includeSystem: false
          },
          requestId: 'req_example_01'
        });
        
        // No modo STDIO, a entrada vem do stdin
        // Mas ao invés de escrever manualmente, usamos este código para simular
        process.stdin.emit('data', requestExample);
      }, 1000);
    }
    
    // Registra handlers para interrupção limpa
    process.on('SIGINT', async () => {
      try {
        logger.info('Recebido sinal de interrupção, encerrando servidor...');
        await mcpServer.stop();
        logger.info('Servidor encerrado com sucesso');
        process.exit(0);
      } catch (error: any) {
        logger.error(`Erro ao encerrar servidor: ${error.message}`);
        process.exit(1);
      }
    });
    
    logger.info(`Ferramentas disponíveis: ${mcpServer.getAvailableTools().join(', ')}`);
    
  } catch (error: any) {
    logger.error(`Erro ao iniciar servidor MCP: ${error.message}`, { stack: error.stack });
    process.exit(1);
  }
}

// Iniciar o servidor
startMCPServer().catch((error: any) => {
  logger.error(`Erro fatal: ${error.message}`, { stack: error.stack });
  process.exit(1);
}); 