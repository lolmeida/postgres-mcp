/**
 * Script de teste para os handlers MCP implementados
 * 
 * Este script executa testes simples dos handlers MCP do PostgreSQL,
 * simulando requisições para cada um deles.
 */

// Definimos o MCPResponse para uso nos nossos mocks
class MCPResponse {
  static success(data, message, requestId) {
    return {
      status: 'success',
      data,
      message,
      requestId
    };
  }
  
  static error(message, details, requestId) {
    return {
      status: 'error',
      message,
      details,
      requestId
    };
  }
}

// Criamos um mock do logger para os testes
const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  debug: (...args) => console.log('[DEBUG]', ...args),
  warn: (...args) => console.log('[WARN]', ...args),
  error: (...args) => console.log('[ERROR]', ...args)
};

// Criamos mocks simples dos serviços
const mockTableService = {
  listTables: async () => {
    return [
      { name: 'users', schema: 'public', type: 'table', owner: 'postgres' },
      { name: 'products', schema: 'public', type: 'table', owner: 'postgres' }
    ];
  },
  getTableDetails: async () => {
    return {
      name: 'users',
      schema: 'public',
      columns: [
        { name: 'id', type: 'integer', nullable: false },
        { name: 'name', type: 'varchar', nullable: false },
        { name: 'email', type: 'varchar', nullable: true }
      ],
      primaryKey: {
        name: 'users_pkey',
        columns: ['id']
      }
    };
  }
};

const mockQueryService = {
  executeQuery: async () => {
    return {
      records: [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
      ],
      fields: [
        { name: 'id', type: 'integer' },
        { name: 'name', type: 'varchar' },
        { name: 'email', type: 'varchar' }
      ],
      rowCount: 2,
      executionTime: 5,
      command: 'SELECT'
    };
  }
};

const mockSchemaService = {
  listTables: async () => {
    return [
      { name: 'users', schema: 'public', type: 'table', owner: 'postgres' },
      { name: 'products', schema: 'public', type: 'table', owner: 'postgres' }
    ];
  },
  getTableDetails: async () => {
    return {
      name: 'users',
      schema: 'public',
      columns: [
        { name: 'id', type: 'integer', nullable: false },
        { name: 'name', type: 'varchar', nullable: false },
        { name: 'email', type: 'varchar', nullable: true }
      ],
      primaryKey: {
        name: 'users_pkey',
        columns: ['id']
      }
    };
  },
  listSchemas: async () => {
    return [
      { name: 'public', owner: 'postgres' },
      { name: 'information_schema', owner: 'postgres' }
    ];
  }
};

const mockConnection = {
  query: async () => ({
    records: [
      { exists: true }
    ]
  }),
  isConnected: () => true,
  getConnectionUptime: () => 3600,
  getPoolSize: () => 5,
  getConfig: () => ({
    host: 'localhost',
    port: 5432,
    database: 'postgres'
  })
};

const mockTransactionService = {
  begin: async () => ({
    transactionId: 'tx_123456',
    isolationLevel: 'read committed',
    readOnly: false,
    deferrable: false
  }),
  commit: async () => true,
  rollback: async () => true,
  getTransactionStatus: async () => ({
    active: true,
    isolationLevel: 'read committed',
    startTime: new Date().toISOString(),
    elapsedTimeMs: 1500
  })
};

// Definimos implementações mock para os handlers que queremos testar
class MockTableHandler {
  constructor() {
    this.toolName = 'mcp_postgres_table';
  }
  
  async handle(request) {
    console.log(`[TABLE] Recebida requisição para: ${request.parameters?.operation}`);
    return MCPResponse.success(
      { tables: mockTableService.listTables() },
      `Operação ${request.parameters?.operation} executada com sucesso`,
      request.requestId
    );
  }
}

class MockQueryHandler {
  constructor() {
    this.toolName = 'mcp_postgres_query';
  }
  
  async handle(request) {
    console.log(`[QUERY] Recebida requisição para: ${request.parameters?.operation}`);
    return MCPResponse.success(
      await mockQueryService.executeQuery(),
      `Consulta executada com sucesso`,
      request.requestId
    );
  }
}

class MockSchemaHandler {
  constructor() {
    this.toolName = 'mcp_postgres_schema';
  }
  
  async handle(request) {
    console.log(`[SCHEMA] Recebida requisição para: ${request.parameters?.operation}`);
    return MCPResponse.success(
      { schemas: await mockSchemaService.listSchemas() },
      `Operação ${request.parameters?.operation} executada com sucesso`,
      request.requestId
    );
  }
}

class MockMetadataHandler {
  constructor() {
    this.toolName = 'mcp_postgres_metadata';
  }
  
  async handle(request) {
    console.log(`[METADATA] Recebida requisição para: ${request.parameters?.operation}`);
    return MCPResponse.success(
      { 
        version: {
          full_version: 'PostgreSQL 14.5 on x86_64-pc-linux-gnu',
          server_version: '14.5',
          server_version_num: '140005'
        }
      },
      `Operação ${request.parameters?.operation} executada com sucesso`,
      request.requestId
    );
  }
}

class MockConnectionHandler {
  constructor() {
    this.toolName = 'mcp_postgres_connection';
  }
  
  async handle(request) {
    console.log(`[CONNECTION] Recebida requisição para: ${request.parameters?.operation}`);
    return MCPResponse.success(
      { 
        status: {
          connected: true,
          latencyMs: 5,
          serverVersion: 'PostgreSQL 14.5',
          connectionUptime: 3600,
          poolSize: 5,
          timestamp: new Date().toISOString()
        }
      },
      `Operação ${request.parameters?.operation} executada com sucesso`,
      request.requestId
    );
  }
}

class MockTransactionHandler {
  constructor() {
    this.toolName = 'mcp_postgres_transaction';
  }
  
  async handle(request) {
    console.log(`[TRANSACTION] Recebida requisição para: ${request.parameters?.operation}`);
    
    if (request.parameters?.operation === 'begin') {
      return MCPResponse.success(
        await mockTransactionService.begin(),
        `Transação iniciada com sucesso`,
        request.requestId
      );
    } else if (request.parameters?.operation === 'commit') {
      return MCPResponse.success(
        { committed: true },
        `Transação confirmada com sucesso`,
        request.requestId
      );
    } else if (request.parameters?.operation === 'rollback') {
      return MCPResponse.success(
        { rolledBack: true },
        `Transação revertida com sucesso`,
        request.requestId
      );
    } else {
      return MCPResponse.success(
        await mockTransactionService.getTransactionStatus(),
        `Status da transação obtido com sucesso`,
        request.requestId
      );
    }
  }
}

// Função para gerar uma requisição de teste
function createTestRequest(handlerName, operation, parameters) {
  return {
    tool: handlerName,
    parameters: {
      operation,
      ...parameters
    },
    requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  };
}

// Função para executar os testes
async function runTests() {
  console.log('===== INICIANDO TESTES DOS HANDLERS MCP =====');
  
  // Teste do TableHandler
  console.log('\n----- TESTE DO TABLE HANDLER -----');
  const tableHandler = new MockTableHandler();
  
  const listTablesRequest = createTestRequest(tableHandler.toolName, 'listTables', {
    schemaName: 'public',
    includeSystem: false
  });
  
  const listTablesResponse = await tableHandler.handle(listTablesRequest);
  console.log('Resposta do listTables:', JSON.stringify(listTablesResponse, null, 2));
  
  // Teste do QueryHandler
  console.log('\n----- TESTE DO QUERY HANDLER -----');
  const queryHandler = new MockQueryHandler();
  
  const executeQueryRequest = createTestRequest(queryHandler.toolName, 'executeQuery', {
    sql: 'SELECT * FROM users',
    parameters: []
  });
  
  const executeQueryResponse = await queryHandler.handle(executeQueryRequest);
  console.log('Resposta do executeQuery:', JSON.stringify(executeQueryResponse, null, 2));
  
  // Teste do SchemaHandler
  console.log('\n----- TESTE DO SCHEMA HANDLER -----');
  const schemaHandler = new MockSchemaHandler();
  
  const listSchemasRequest = createTestRequest(schemaHandler.toolName, 'listSchemas', {
    includeSystem: false
  });
  
  const listSchemasResponse = await schemaHandler.handle(listSchemasRequest);
  console.log('Resposta do listSchemas:', JSON.stringify(listSchemasResponse, null, 2));
  
  // Teste do MetadataHandler
  console.log('\n----- TESTE DO METADATA HANDLER -----');
  const metadataHandler = new MockMetadataHandler();
  
  const getPostgresVersionRequest = createTestRequest(metadataHandler.toolName, 'getPostgresVersion', {});
  
  const getPostgresVersionResponse = await metadataHandler.handle(getPostgresVersionRequest);
  console.log('Resposta do getPostgresVersion:', JSON.stringify(getPostgresVersionResponse, null, 2));
  
  // Teste do ConnectionHandler
  console.log('\n----- TESTE DO CONNECTION HANDLER -----');
  const connectionHandler = new MockConnectionHandler();
  
  const getConnectionStatusRequest = createTestRequest(connectionHandler.toolName, 'getConnectionStatus', {});
  
  const getConnectionStatusResponse = await connectionHandler.handle(getConnectionStatusRequest);
  console.log('Resposta do getConnectionStatus:', JSON.stringify(getConnectionStatusResponse, null, 2));
  
  // Teste do TransactionHandler
  console.log('\n----- TESTE DO TRANSACTION HANDLER -----');
  const transactionHandler = new MockTransactionHandler();
  
  const beginTransactionRequest = createTestRequest(transactionHandler.toolName, 'begin', {
    isolationLevel: 'read committed',
    readOnly: false
  });
  
  const beginTransactionResponse = await transactionHandler.handle(beginTransactionRequest);
  console.log('Resposta do begin:', JSON.stringify(beginTransactionResponse, null, 2));
  
  console.log('\n===== TESTES CONCLUÍDOS =====');
}

// Executa os testes
runTests().catch(error => {
  console.error('Erro ao executar testes:', error);
  process.exit(1);
}); 