# Guia Inicial - PostgreSQL MCP

Este guia fornece instruções passo a passo para começar a usar o PostgreSQL MCP em seu projeto.

## Pré-requisitos

- Node.js 16 ou superior
- npm ou yarn
- Acesso a um banco de dados PostgreSQL (local ou remoto)
- Credenciais de acesso ao PostgreSQL com privilégios adequados

## Instalação

### Via npm

Instale o pacote usando npm:

```bash
npm install mcp-postgres-js
```

### Via yarn

```bash
yarn add mcp-postgres-js
```

### Diretamente do repositório

Você também pode instalar diretamente do repositório:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/mcp-postgres-js.git
cd mcp-postgres-js

# Instale as dependências
npm install

# Execute o servidor MCP
npm start
```

## Configuração Básica

### 1. Configure as Credenciais do PostgreSQL

Existem duas formas de configurar as credenciais:

#### Usando Variáveis de Ambiente

Crie um arquivo `.env` na raiz do seu projeto:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
DB_USER=myuser
DB_PASSWORD=mypassword
DB_SSL=prefer
```

E carregue as variáveis no seu código:

```javascript
require('dotenv').config();
```

#### Configuração Programática

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

const mcp = new PostgresMCPServer({
  dbHost: 'localhost',
  dbPort: 5432,
  dbName: 'mydatabase',
  dbUser: 'myuser',
  dbPassword: 'mypassword',
  dbSsl: 'prefer'  // Opções: disable, allow, prefer, require, verify-ca, verify-full
});
```

## Modos de Operação

O PostgreSQL MCP suporta dois modos de operação:

### 1. Modo STDIO (Padrão)

Este modo é ideal para integração com LLMs que usam o protocolo MCP.

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa no modo STDIO (padrão)
const mcp = new PostgresMCPServer();

// Inicia o servidor
mcp.start()
  .then(() => console.log('Servidor MCP iniciado no modo STDIO'))
  .catch(err => console.error('Erro ao iniciar servidor:', err));
```

### 2. Modo HTTP

O modo HTTP é útil para desenvolvimento, testes e chamadas de API diretas.

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa no modo HTTP
const mcp = new PostgresMCPServer({
  mode: 'http',
  port: 8000
});

// Inicia o servidor HTTP
mcp.start()
  .then(() => console.log('Servidor MCP HTTP iniciado na porta 8000'))
  .catch(err => console.error('Erro ao iniciar servidor:', err));
```

## Configuração Avançada

### 1. Configurando Tamanho do Pool de Conexões

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

const mcp = new PostgresMCPServer({
  dbHost: 'localhost',
  dbPort: 5432,
  dbName: 'mydatabase',
  dbUser: 'myuser',
  dbPassword: 'mypassword',
  poolMinSize: 5,
  poolMaxSize: 20
});
```

### 2. Configurando Timeout e Limites

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

const mcp = new PostgresMCPServer({
  dbHost: 'localhost',
  dbPort: 5432,
  dbName: 'mydatabase',
  dbUser: 'myuser',
  dbPassword: 'mypassword',
  commandTimeout: 60,  // Timeout em segundos para comandos
  maxQueryRows: 10000,  // Limite máximo de linhas para consultas
  transactionTimeout: 300  // Timeout em segundos para transações
});
```

### 3. Configurando Logging

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');
const winston = require('winston');

// Configurar logger personalizado
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'postgres_mcp.log' })
  ]
});

// Inicializa com configuração de logging personalizada
const mcp = new PostgresMCPServer({
  dbHost: 'localhost',
  dbPort: 5432,
  dbName: 'mydatabase',
  dbUser: 'myuser',
  dbPassword: 'mypassword',
  logLevel: 'info',  // debug, info, warn, error
  logSqlQueries: true,  // Log de todas as consultas SQL executadas
  logger: logger  // Instância de logger personalizada
});
```

## Estrutura do Código

O PostgreSQL MCP é organizado em uma arquitetura de camadas bem definida:

### Camada de Conexão e Consultas

- `PostgresConfig`: Configuração do banco de dados PostgreSQL usando o padrão Builder
- `PostgresConnection`: Gerencia a conexão com o banco de dados e execução de consultas
- `PostgresConnectionManager`: Administra múltiplas conexões para diferentes bancos
- `PostgresSchemaManager`: Executa operações relacionadas ao schema do PostgreSQL
- `PostgresSchemaQueries`: Contém todas as consultas SQL usadas pelo SchemaManager
- `PostgresQueryBuilder`: Constrói consultas SQL dinâmicas com proteção contra injeção SQL

### Camada de Repositórios

- `RepositoryBase`: Interface base para operações CRUD
- `PostgresRepository`: Implementação para operações em tabelas no PostgreSQL

### Camada de Serviços (Em desenvolvimento)

- `ServiceBase`: Interface base para todos os serviços
- Serviços especializados para diferentes operações

### Camada de Handlers (Em desenvolvimento)

- `HandlerBase`: Interface base para handlers de requisições MCP
- Handlers especializados para cada tipo de operação

## Exemplos de Uso

### Listar Schemas Disponíveis

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta list_schemas
mcp.handle({
  tool: 'list_schemas',
  parameters: {}
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Listar Tabelas Disponíveis

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta list_tables
mcp.handle({
  tool: 'list_tables',
  parameters: {
    schema: 'public',
    includeViews: true
  }
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Descrever Estrutura de Tabela

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta describe_table
mcp.handle({
  tool: 'describe_table',
  parameters: {
    table: 'users',
    schema: 'public'
  }
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Consultar Registros

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta read_table
mcp.handle({
  tool: 'read_table',
  parameters: {
    table: 'users',
    schema: 'public',
    filters: {
      isActive: true,
      createdAt: {
        gte: '2023-01-01T00:00:00Z'
      }
    },
    columns: ['id', 'name', 'email', 'createdAt'],
    orderBy: 'createdAt',
    ascending: false,
    limit: 5
  }
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Criar um Registro

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta create_record
mcp.handle({
  tool: 'create_record',
  parameters: {
    table: 'tasks',
    schema: 'public',
    data: {
      title: 'Completar documentação',
      description: 'Finalizar guias de uso do MCP',
      status: 'pending',
      dueDate: '2023-08-30',
      assignedTo: 'user123',
      priority: 'high'
    },
    returning: ['id', 'title', 'status']
  }
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Atualizar Registros

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta update_records
mcp.handle({
  tool: 'update_records',
  parameters: {
    table: 'tasks',
    schema: 'public',
    filters: {
      status: 'pending',
      dueDate: {
        lt: '2023-07-01'
      }
    },
    data: {
      status: 'overdue',
      updatedAt: '2023-07-01T00:00:00Z'
    },
    returning: ['id', 'title', 'status', 'dueDate']
  }
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Executar Consulta SQL Personalizada

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Executa a ferramenta execute_query
mcp.handle({
  tool: 'execute_query',
  parameters: {
    query: """
    SELECT 
        users.name, 
        COUNT(tasks.id) as task_count 
    FROM 
        users 
    LEFT JOIN 
        tasks ON users.id = tasks.assigned_to 
    WHERE 
        users.is_active = $1 
    GROUP BY 
        users.name 
    HAVING 
        COUNT(tasks.id) > $2 
    ORDER BY 
        task_count DESC
    """,
    params: [true, 5],
    read_only: true
  }
})
.then(response => {
  console.log(response);
})
.catch(err => {
  console.error('Erro:', err);
});
```

### Usando Transações

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializa o cliente em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Inicia uma transação
mcp.handle({
  tool: 'begin_transaction',
  parameters: {
    isolation_level: 'serializable'
  }
})
.then(tx_response => {
  const transaction_id = tx_response.data.transaction_id;

  try {
    // Atualiza um registro dentro da transação
    mcp.handle({
      tool: 'update_records',
      parameters: {
        table: 'accounts',
        schema: 'public',
        filters: { id: 'acc_123' },
        data: { balance: { decrement: 100.00 } },
        transaction_id: transaction_id
      }
    });
    
    // Cria um registro dentro da mesma transação
    mcp.handle({
      tool: 'create_record',
      parameters: {
        table: 'transfers',
        schema: 'public',
        data: {
          from_account: 'acc_123', 
          to_account: 'acc_456',
          amount: 100.00,
          status: 'completed'
        },
        transaction_id: transaction_id
      }
    });
    
    // Confirma a transação
    mcp.handle({
      tool: 'commit_transaction',
      parameters: {
        transaction_id: transaction_id
      }
    });
    
  } catch (e) {
    // Em caso de erro, reverte a transação
    mcp.handle({
      tool: 'rollback_transaction',
      parameters: {
        transaction_id: transaction_id
      }
    });
    console.error(`Erro: ${e.message}`);
  }
})
.catch(err => {
  console.error('Erro:', err);
});
```

## Integração com LLMs

### Exemplo com Anthropic (Claude)

```javascript
import anthropic from 'anthropic';
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializar o cliente MCP em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Inicializar cliente Claude
const client = new anthropic.Anthropic({ apiKey: 'your-api-key' });

// Preparar ferramentas para Claude
const tools = [
  {
    name: 'list_tables',
    description: 'Lista todas as tabelas disponíveis no banco de dados PostgreSQL',
    input_schema: {
      type: 'object',
      properties: {
        schema: { type: 'string', description: 'Nome do schema (default: public)' },
        include_views: { type: 'boolean', description: 'Incluir views nos resultados' }
      }
    }
  },
  {
    name: 'read_table',
    description: 'Consulta registros de uma tabela PostgreSQL',
    input_schema: {
      type: 'object',
      properties: {
        table: { type: 'string', description: 'Nome da tabela' },
        schema: { type: 'string', description: 'Nome do schema (default: public)' },
        filters: { type: 'object', description: 'Filtros da consulta' },
        columns: { type: 'array', description: 'Colunas específicas a retornar' },
        limit: { type: 'number', description: 'Limite de registros a retornar' }
      },
      required: ['table']
    }
  },
  {
    name: 'execute_query',
    description: 'Executa uma consulta SQL personalizada',
    input_schema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Consulta SQL a executar' },
        params: { type: 'array', description: 'Parâmetros para a consulta' },
        read_only: { type: 'boolean', description: 'Se a consulta é somente leitura' }
      },
      required: ['query']
    }
  }
];

// Função para processar chamadas de ferramenta
const process_tool_call = async (tool_call) => {
  const tool_name = tool_call.name;
  const parameters = tool_call.parameters;
  
  // Processar a chamada através do MCP
  const result = await mcp.handle({
    tool: tool_name,
    parameters: parameters
  });
  
  return result;
};

// Exemplo de uso com Claude
const message = await client.messages.create(
  model: 'claude-3-opus-20240229',
  max_tokens: 1000,
  temperature: 0,
  tools: tools,
  messages: [
    { role: 'user', content: 'Liste todas as tabelas no schema public e depois mostre os 5 usuários mais recentes.' }
  ]
);

// Processar e responder às chamadas de ferramentas de Claude
for (const tool_call of message.content) {
  if (tool_call.tool_use) {
    const tool_result = await process_tool_call(tool_call.tool_use);
    // Enviar resultado de volta para o LLM
    // ...
  }
}
```

### Exemplo com OpenAI (GPT)

```javascript
import openai from 'openai';
const { PostgresMCPServer } = require('mcp-postgres-js');

// Inicializar o cliente MCP em modo teste
const mcp = new PostgresMCPServer({ testMode: true });

// Configurar OpenAI
const openai_client = new openai.OpenAI({ apiKey: 'your-api-key' });

// Preparar as ferramentas para OpenAI
const tools = [
  {
    type: 'function',
    function: {
      name: 'list_tables',
      description: 'Lista todas as tabelas disponíveis no banco de dados PostgreSQL',
      parameters: {
        type: 'object',
        properties: {
          schema: { type: 'string', description: 'Nome do schema (default: public)' },
          include_views: { type: 'boolean', description: 'Incluir views nos resultados' },
        },
        required: []
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'read_table',
      description: 'Consulta registros de uma tabela PostgreSQL',
      parameters: {
        type: 'object',
        properties: {
          table: { type: 'string', description: 'Nome da tabela' },
          schema: { type: 'string', description: 'Nome do schema (default: public)' },
          filters: { type: 'object', description: 'Filtros da consulta' },
          columns: { type: 'array', items: { type: 'string' }, description: 'Colunas específicas a retornar' },
          limit: { type: 'number', description: 'Limite de registros a retornar' }
        },
        required: ['table']
      }
    }
  }
];

// Função para processar chamadas de ferramenta
const process_tool_call = async (tool_call) => {
  const function_name = tool_call.name;
  const arguments = JSON.parse(tool_call.arguments);
  
  // Processar a chamada através do MCP
  const result = await mcp.handle({
    tool: function_name,
    parameters: arguments
  });
  
  return result;
};

// Exemplo de uso com GPT
const response = await openai_client.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Liste todas as tabelas no banco de dados e depois mostre os 5 usuários mais recentes.' }
  ],
  tools: tools,
  tool_choice: 'auto'
});

// Processar e responder às chamadas de ferramentas
const message = response.choices[0].message;
if (message.tool_calls) {
  for (const tool_call of message.tool_calls) {
    const tool_result = await process_tool_call(tool_call);
    // Enviar resultado de volta para o LLM
    // ...
  }
}
```

## Próximos Passos

- Veja a [Referência de API](../API_REFERENCE.md) para documentação detalhada de todas as ferramentas
- Explore o [Guia de Filtros](./filters.md) para entender as opções de filtragem avançada
- Consulte os [Exemplos de Código](../CODE_EXAMPLES.md) para casos de uso mais avançados
- Leia sobre [Transações](./transactions.md) para entender o gerenciamento de transações
- Aprenda sobre [Tipos Avançados do PostgreSQL](./advanced-types.md) para trabalhar com JSON, arrays e outros tipos