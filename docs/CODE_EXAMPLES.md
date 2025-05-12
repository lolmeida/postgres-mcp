# PostgreSQL MCP (JavaScript) - Exemplos de Código

Este documento contém exemplos de código para usar e estender o PostgreSQL MCP em JavaScript.

## Exemplos de Uso

### 1. Configuração Básica

```javascript
// Importar dependências
const { PostgresMCPServer } = require('mcp-postgres-js');
const dotenv = require('dotenv');

// Carregar variáveis de ambiente do arquivo .env
dotenv.config();

// Inicializar o servidor MCP
const server = new PostgresMCPServer({
  dbHost: process.env.DB_HOST,
  dbPort: parseInt(process.env.DB_PORT || '5432'),
  dbName: process.env.DB_NAME,
  dbUser: process.env.DB_USER,
  dbPassword: process.env.DB_PASSWORD,
  mode: process.env.MCP_MODE || 'stdio' // ou 'http' para HTTP
});

// Iniciar o servidor
server.start()
  .then(() => console.log('MCP Server started successfully'))
  .catch(err => console.error('Failed to start MCP Server:', err));
```

### 2. Cliente para Testes HTTP

```javascript
const axios = require('axios');

class PostgresMCPClient {
  constructor(url = 'http://localhost:8432/mcp') {
    this.url = url;
  }
  
  async callTool(tool, parameters) {
    try {
      const response = await axios.post(
        this.url,
        { tool, parameters }
      );
      return response.data;
    } catch (error) {
      console.error('Error calling MCP tool:', error.message);
      throw error;
    }
  }
  
  async readTable(table, options = {}) {
    const { 
      schema = 'public', 
      filters = null, 
      columns = null, 
      orderBy = null, 
      ascending = true, 
      limit = null, 
      offset = null 
    } = options;
    
    const parameters = { table, schema };
    
    if (filters) parameters.filters = filters;
    if (columns) parameters.columns = columns;
    if (orderBy) {
      parameters.order_by = orderBy;
      parameters.ascending = ascending;
    }
    if (limit) parameters.limit = limit;
    if (offset) parameters.offset = offset;
    
    return this.callTool('read_table', parameters);
  }
  
  async createRecord(table, data, options = {}) {
    const { schema = 'public', returning = null } = options;
    
    const parameters = {
      table,
      schema,
      data
    };
    
    if (returning) parameters.returning = returning;
    
    return this.callTool('create_record', parameters);
  }
  
  async updateRecords(table, filters, data, options = {}) {
    const { schema = 'public', returning = null } = options;
    
    const parameters = {
      table,
      schema,
      filters,
      data
    };
    
    if (returning) parameters.returning = returning;
    
    return this.callTool('update_records', parameters);
  }
  
  async deleteRecords(table, filters, options = {}) {
    const { schema = 'public', returning = null } = options;
    
    const parameters = {
      table,
      schema,
      filters
    };
    
    if (returning) parameters.returning = returning;
    
    return this.callTool('delete_records', parameters);
  }
  
  async executeQuery(query, options = {}) {
    const { params = null, readOnly = true } = options;
    
    const parameters = {
      query,
      read_only: readOnly
    };
    
    if (params) parameters.params = params;
    
    return this.callTool('execute_query', parameters);
  }
  
  async beginTransaction(isolationLevel = 'read_committed') {
    const parameters = {
      isolation_level: isolationLevel
    };
    return this.callTool('begin_transaction', parameters);
  }
  
  async commitTransaction(transactionId) {
    const parameters = {
      transaction_id: transactionId
    };
    return this.callTool('commit_transaction', parameters);
  }
  
  async rollbackTransaction(transactionId, savepoint = null) {
    const parameters = {
      transaction_id: transactionId
    };
    
    if (savepoint) parameters.savepoint = savepoint;
    
    return this.callTool('rollback_transaction', parameters);
  }
}

module.exports = PostgresMCPClient;
```

### 3. Exemplos de Chamadas de API

#### Leitura de Registros

```javascript
const PostgresMCPClient = require('./client');
const client = new PostgresMCPClient();

// Função assíncrona para buscar usuários ativos
async function fetchActiveUsers() {
  try {
    const users = await client.readTable('users', {
      schema: 'public',
      filters: { active: true },
      columns: ['id', 'name', 'email', 'created_at'],
      orderBy: 'created_at',
      ascending: false,
      limit: 10
    });
    
    console.log(JSON.stringify(users, null, 2));
    return users;
  } catch (error) {
    console.error('Error fetching users:', error);
  }
}

fetchActiveUsers();
```

#### Criação de Registro

```javascript
const PostgresMCPClient = require('./client');
const client = new PostgresMCPClient();

// Função assíncrona para criar um novo usuário
async function createNewUser() {
  try {
    const result = await client.createRecord('users', {
      name: 'John Doe',
      email: 'john@example.com',
      active: true,
      metadata: {
        preferences: {
          theme: 'dark',
          notifications: true
        }
      }
    }, {
      returning: ['id', 'name', 'email']
    });
    
    console.log(JSON.stringify(result, null, 2));
    return result;
  } catch (error) {
    console.error('Error creating user:', error);
  }
}

createNewUser();
```

#### Atualização de Registros

```javascript
const PostgresMCPClient = require('./client');
const client = new PostgresMCPClient();

// Função assíncrona para desativar usuários inativos há mais de 30 dias
async function deactivateInactiveUsers() {
  try {
    const result = await client.updateRecords(
      'users',
      { last_active: { lt: '2023-01-01' } },
      { 
        active: false, 
        deactivated_at: new Date().toISOString() 
      }
    );
    
    console.log(JSON.stringify(result, null, 2));
    return result;
  } catch (error) {
    console.error('Error updating users:', error);
  }
}

deactivateInactiveUsers();
```

#### Exclusão de Registros

```javascript
const PostgresMCPClient = require('./client');
const client = new PostgresMCPClient();

// Função assíncrona para excluir usuários inativos
async function deleteInactiveUsers() {
  try {
    const result = await client.deleteRecords(
      'users',
      { active: false }
    );
    
    console.log(JSON.stringify(result, null, 2));
    return result;
  } catch (error) {
    console.error('Error deleting users:', error);
  }
}

deleteInactiveUsers();
```

### 4. Trabalhando com Tipos Específicos do PostgreSQL

#### Utilizando Arrays

```javascript
// Criar registro com campo array
const result = await client.createRecord(
  'products',
  {
    name: 'Camiseta Estampada',
    price: 29.99,
    sizes: ['P', 'M', 'G', 'GG'],  // Campo array
    colors: ['Azul', 'Preto', 'Branco']  // Campo array
  }
);

// Filtrar por valores em arrays
const shirts = await client.readTable('products', {
  schema: 'public',
  filters: {
    sizes: { contains: ['M', 'G'] },  // Produtos que têm tamanhos M e G
    colors: { overlap: ['Azul'] }     // Produtos que têm a cor Azul
  }
});
```

#### Utilizando JSONB

```javascript
// Criar registro com campo JSONB
const result = await client.createRecord(
  'users',
  {
    name: 'Maria Silva',
    email: 'maria@example.com',
    preferences: {
      theme: 'light',
      notifications: {
        email: true,
        sms: false,
        push: true
      },
      favorites: [1, 2, 3]
    }  // Campo JSONB
  }
);

// Filtrar usando campos JSONB
const users = await client.readTable('users', {
  schema: 'public',
  filters: {
    'preferences->theme': 'light',  // Consulta simples de JSONB
    'preferences->notifications->push': true  // Consulta aninhada
  }
});

// Consulta avançada com JSONB usando jsonb_path
const users_with_email = await client.readTable('users', {
  schema: 'public',
  filters: {
    preferences: {
      jsonb_path: '$.notifications.email ? (@ == true)'
    }
  }
});
```

## Exemplos de Tipos Geométricos

Os exemplos a seguir demonstram como utilizar tipos geométricos do PostgreSQL através do PostgreSQL MCP.

### Exemplo 1: Buscar Restaurantes Próximos

```javascript
const axios = require('axios');

async function findNearbyRestaurants() {
  const client = new PostgresMCPClient();
  
  // Coordenadas do usuário
  const userLocation = '(37.7749,-122.4194)';  // San Francisco
  const maxDistance = 2.0;  // km
  
  // Buscar restaurantes próximos
  const response = await client.callTool('read_table', {
    table: 'restaurants',
    filters: {
      location: {
        near: `${userLocation},${maxDistance}`
      }
    },
    columns: ['id', 'name', 'cuisine', 'rating'],
    limit: 10
  });
  
  // Processar resultados
  const restaurants = response.results;
  console.log(`Encontrados ${restaurants.length} restaurantes próximos:`);
  
  restaurants.forEach(restaurant => {
    console.log(`- ${restaurant.name} (${restaurant.cuisine}) - ${restaurant.rating}/5 estrelas`);
  });
  
  return restaurants;
}

// Executar a função
findNearbyRestaurants();
```

### Exemplo 2: Verificar Imóveis em Área de Interesse

```javascript
const axios = require('axios');

async function findPropertiesInArea() {
  const client = new PostgresMCPClient();
  
  // Definir polígono da área de interesse
  // Formato: ((x1,y1),(x2,y2),...,(xn,yn))
  const areaOfInterest = '((37.78,-122.42),(37.78,-122.40),(37.76,-122.40),(37.76,-122.42),(37.78,-122.42))';
  
  // Buscar imóveis dentro da área
  const response = await client.callTool('read_table', {
    table: 'properties',
    filters: {
      location: {
        within: areaOfInterest
      },
      price: {
        lte: 1000000
      },
      bedrooms: {
        gte: 2
      }
    },
    columns: ['id', 'address', 'price', 'bedrooms', 'bathrooms'],
    order_by: 'price',
    ascending: true
  });
  
  // Processar resultados
  const properties = response.results;
  console.log(`Encontrados ${properties.length} imóveis na área de interesse:`);
  
  properties.forEach(property => {
    console.log(`- ${property.address}: $${property.price.toLocaleString()} - ${property.bedrooms} quartos, ${property.bathrooms} banheiros`);
  });
  
  return properties;
}

// Executar a função
findPropertiesInArea();
```

### Exemplo 3: Verificar Sobreposição de Rotas

```javascript
const axios = require('axios');

async function findIntersectingRoutes() {
  const client = new PostgresMCPClient();
  
  // Definir uma rota de referência (polígono representando um corredor)
  const referenceRoute = '((37.78,-122.42),(37.78,-122.40),(37.775,-122.40),(37.775,-122.42),(37.78,-122.42))';
  
  // Buscar rotas que se cruzam com a rota de referência
  const response = await client.callTool('read_table', {
    table: 'routes',
    filters: {
      path: {
        intersects: referenceRoute
      },
      is_active: true
    },
    columns: ['id', 'name', 'type', 'distance']
  });
  
  // Processar resultados
  const routes = response.results;
  console.log(`Encontradas ${routes.length} rotas que cruzam a rota de referência:`);
  
  routes.forEach(route => {
    console.log(`- ${route.name} (${route.type}): ${route.distance} km`);
  });
  
  return routes;
}

// Executar a função
findIntersectingRoutes();
```

### Exemplo 4: Criando Dados com Tipos Geométricos

```javascript
const axios = require('axios');

async function createParkData() {
  const client = new PostgresMCPClient();
  
  // Criar um novo parque com dados geométricos
  const response = await client.callTool('create_record', {
    table: 'parks',
    data: {
      name: 'Golden Gate Park',
      center_point: '(37.7694,-122.4862)',  // Ponto central
      boundary: '((37.7759,-122.5108),(37.7759,-122.4577),(37.7629,-122.4577),(37.7629,-122.5108),(37.7759,-122.5108))',  // Perímetro aproximado
      area_sqkm: 4.1,
      has_playground: true,
      has_dogpark: true
    }
  });
  
  // Verificar resposta
  const result = response;
  if (result.error) {
    console.error(`Erro ao criar parque: ${result.error}`);
  } else {
    console.log(`Parque criado com sucesso! ID: ${result.id}`);
  }
  
  return result;
}

// Executar a função
createParkData();
```

## Exemplos de Implementação

### 1. Criando um Novo Handler

```javascript
const { HandlerBase } = require('mcp-postgres-js');
const { CustomRequest } = require('../models/request');
const { DataResponse, ErrorResponse } = require('../models/response');

class CustomHandler extends HandlerBase {
  /**Handler personalizado para uma nova ferramenta.*/
  
  async handle(params) {
    /**
     * Processa a requisição da ferramenta personalizada.
     * 
     * @param {Object} params - Parâmetros da requisição
     * @returns {Object} - Resposta formatada
     */
    try {
      // Valida parâmetros
      const request = new CustomRequest(params);
      
      // Processa a requisição (exemplo)
      const result = await this.services.custom_service.process(request);
      
      // Retorna resposta de sucesso
      return new DataResponse(
        true,
        result,
        result.length > 0 ? result.length : 1
      ).model_dump();
      
    } catch (e) {
      // Loga o erro
      this.logger.error(`Erro ao processar custom_tool: ${e.message}`);
      
      // Retorna resposta de erro
      return new ErrorResponse(
        false,
        {
          message: e.message,
          type: e.constructor.name
        }
      ).model_dump();
    }
  }
}

module.exports = CustomHandler;
```

### 2. Implementando um Novo Repositório

```javascript
const { RepositoryBase } = require('mcp-postgres-js');
const { PostgresClient } = require('../adapters/client');

class CustomRepository extends RepositoryBase {
  /**Repositório personalizado para um tipo específico de dados.*/
  
  constructor(postgres_client) {
    /**
     * Inicializa o repositório.
     * 
     * @param {PostgresClient} postgres_client - Cliente PostgreSQL
     */
    super();
    this.client = postgres_client;
    this.schema = 'public';
    this.table_name = 'custom_table';
  }
  
  async get_by_criteria(criteria, limit = null) {
    /**
     * Busca registros por critérios específicos.
     * 
     * @param {Object} criteria - Critérios de busca
     * @param {Number} [limit] - Limite de registros
     * @returns {Promise<Array<Object>>} - Lista de registros correspondentes
     */
    // Constrói a consulta SQL base
    let query = `
      SELECT * FROM ${this.schema}.${this.table_name}
      WHERE 1=1
    `;
    const params = [];
    let param_index = 1;
    
    // Adiciona condições com base nos critérios
    for (const key in criteria) {
      const value = criteria[key];
      if (typeof value === 'object' && Object.keys(value).length === 1) {
        const [op, val] = Object.entries(value)[0];
        if (op === '>') {
          query += ` AND ${key} > $${param_index}`;
        } else if (op === '<') {
          query += ` AND ${key} < $${param_index}`;
        } else if (op === '>=') {
          query += ` AND ${key} >= $${param_index}`;
        } else if (op === '<=') {
          query += ` AND ${key} <= $${param_index}`;
        } else if (op === 'like') {
          query += ` AND ${key} LIKE $${param_index}`;
        }
        params.push(val);
        param_index++;
      } else {
        query += ` AND ${key} = $${param_index}`;
        params.push(value);
        param_index++;
      }
    }
    
    // Adiciona limite se especificado
    if (limit) {
      query += ` LIMIT $${param_index}`;
      params.push(limit);
    }
    
    // Executa a consulta
    const records = await this.client.fetch(query, ...params);
    
    // Converte para dicionários
    return records.map(record => ({ ...record }));
  }
}

module.exports = CustomRepository;
```

### 3. Implementando Autenticação Avançada

```javascript
const { Settings } = require('mcp-postgres-js');
const { SecurityService } = require('../services/security');
const { JWTAuthMiddleware } = require('../middleware/auth');

// Define as políticas de acesso
const policies = {
  tables: {
    users: {
      read: ['admin', 'user'],
      create: ['admin'],
      update: ['admin'],
      delete: ['admin']
    },
    posts: {
      read: ['admin', 'user'],
      create: ['admin', 'user'],
      update: ['admin', 'user', 'post_owner'],
      delete: ['admin', 'post_owner']
    }
  },
  schemas: {
    public: ['admin', 'user'],
    admin: ['admin'],
    analytics: ['admin', 'analyst']
  }
};

// Configurar middleware de autenticação JWT
const jwt_middleware = new JWTAuthMiddleware(
  secret_key=process.env.JWT_SECRET,
  algorithm='HS256',
  role_claim='role',
  exclude_paths=['/health']
);

// Configura o serviço de segurança
const security_service = new SecurityService(
  // Função para verificar permissões
  permission_checker=function(user, action, resource) {
    return (
      user.role in policies.tables.get(resource, {})[action] ||
      user.role in policies.schemas.get(resource, []) ||
      user.id == resource.get('owner_id')  // Para regras específicas de propriedade
    );
  },
  // Configuração de Row-Level Security
  row_level_security=true
);

// Uso no servidor MCP
const server = new PostgresMCPServer({
  dbHost: process.env.DB_HOST,
  dbPort: parseInt(process.env.DB_PORT || '5432'),
  dbName: process.env.DB_NAME,
  dbUser: process.env.DB_USER,
  dbPassword: process.env.DB_PASSWORD,
  mode: 'streamable-http',
  security_service,
  middleware=[jwt_middleware]
});
```

### 4. Implementando Cache

```javascript
const { QueryCache } = require('mcp-postgres-js');
const { QueryService } = require('../services/query');
const { TableRepository } = require('../repositories/table');

// Configuração do cache
const cache = new QueryCache(
  max_size=100,  // Máximo de entradas no cache
  ttl=300  // Tempo de vida em segundos (5 minutos)
);

// Uso no serviço de consulta
const query_service = new QueryService(
  table_repository=new TableRepository(...),
  cache
);

// Exemplo de método cached
async function get_cached_data(self, schema, table, filters, columns=null, order_by=null, ascending=true, limit=null, offset=null) {
  // Gera uma chave de cache baseada nos parâmetros
  const cache_key = `${schema}:${table}:${JSON.stringify(filters)}:${JSON.stringify(columns)}:${order_by}:${ascending}:${limit}:${offset}`;
  
  // Tenta obter do cache
  const cached_result = self.cache.get(cache_key);
  if (cached_result) {
    return cached_result;
  }
  
  // Se não estiver no cache, busca do repositório
  const result = await self.repository.get_records(
    schema=schema,
    table=table,
    filters=filters,
    columns=columns,
    order_by=order_by,
    ascending=ascending,
    limit=limit,
    offset=offset
  );
  
  // Armazena no cache
  self.cache.set(cache_key, result);
  
  return result;
}
```

### 5. Exemplo de Integração com Pool de Conexões

```javascript
const asyncpg = require('asyncpg');
const { PostgresMCPServer } = require('mcp-postgres-js');

async function setup_db_pool() {
  // Configura pool de conexões com PostgreSQL
  const pool = await asyncpg.create_pool(
    host=process.env.DB_HOST,
    port=parseInt(process.env.DB_PORT || '5432'),
    database=process.env.DB_NAME,
    user=process.env.DB_USER,
    password=process.env.DB_PASSWORD,
    min_size=5,        // Mínimo de conexões no pool
    max_size=20,       // Máximo de conexões no pool
    command_timeout=60, // Timeout para comandos
    max_inactive_connection_lifetime=300  // Tempo máximo de vida para conexões inativas
  );
  
  // Configuração de inicialização para todas as conexões
  async function init_connection(conn) {
    // Configura timezone
    await conn.execute("SET timezone = 'UTC'");
    // Configura outras variáveis de sessão
    await conn.execute("SET application_name = 'postgres_mcp'");
  }

  // Substitui o pool existente com nosso pool personalizado
  await pool.execute(init_connection);
  
  return pool;
}

// Inicializa o servidor com pool personalizado
async function start_server() {
  // Cria o pool de conexões
  const db_pool = await setup_db_pool();
  
  // Inicializa o servidor com o pool
  const server = new PostgresMCPServer({
    connection_pool: db_pool,
    mode: 'stdio'
  });
  
  // Inicia o servidor
  await server.start();
}

// Execução principal
if (require.main === module) {
  start_server();
}
```

## Cache

### Obter Estatísticas do Cache

```javascript
const axios = require('axios');

function get_cache_stats(base_url = 'http://localhost:8000') {
  /**
   * Obtém estatísticas de uso do cache.
   */
  return axios.post(
    base_url,
    { tool: 'get_cache_stats' }
  ).then(response => response.data);
}

// Exemplo de uso
get_cache_stats()
  .then(stats => {
    console.log(`Taxa de acerto do cache: ${stats.data.hit_ratio}`);
    console.log(`Total de acertos: ${stats.data.hits}`);
    console.log(`Total de falhas: ${stats.data.misses}`);
  });
```

### Limpar Cache

```javascript
const axios = require('axios');

function clear_cache(base_url = 'http://localhost:8000', scope = 'all', table = null, schema = 'public') {
  /**
   * Limpa o cache do sistema.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} scope - Escopo da limpeza ('all', 'table', 'schema')
   * @param {String} [table] - Nome da tabela (obrigatório quando scope='table')
   * @param {String} [schema] - Nome do schema (obrigatório quando scope='schema')
   */
  const params = { scope };
  
  if (scope === 'table') {
    params.table = table;
    params.schema = schema;
  } else if (scope === 'schema') {
    params.schema = schema;
  }
  
  return axios.post(
    base_url,
    {
      tool: 'clear_cache',
      parameters: params
    }
  ).then(response => response.data);
}

// Exemplo: limpar cache de uma tabela específica
clear_cache(scope='table', table='users', schema='public')
  .then(result => console.log(result.data.message));

// Exemplo: limpar todo o cache
clear_cache()
  .then(result => console.log(result.data.message));
```

## Métricas e Monitoramento

### Obter Métricas de Desempenho

```javascript
const axios = require('axios');

function get_metrics(base_url = 'http://localhost:8000', metric_type = null, operation = null, window_seconds = 60) {
  /**
   * Obtém métricas de desempenho do sistema.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} [metric_type] - Tipo específico de métrica ('execution_times', 'errors', 'resource_usage', 'operations_per_second')
   * @param {String} [operation] - Nome da operação para filtrar (quando metric_type='execution_times')
   * @param {Number} [window_seconds] - Janela de tempo em segundos (quando metric_type='operations_per_second')
   */
  const params = {};
  
  if (metric_type) {
    params.metric_type = metric_type;
    
    if (metric_type === 'execution_times' && operation) {
      params.operation = operation;
    } else if (metric_type === 'operations_per_second') {
      params.window_seconds = window_seconds;
    }
  }
  
  return axios.post(
    base_url,
    {
      tool: 'get_metrics',
      parameters
    }
  ).then(response => response.data);
}

// Exemplo: obter todas as métricas
get_metrics()
  .then(all_metrics => {
    console.log(`Tempo total de atividade: ${all_metrics.data.uptime_seconds} segundos`);
    console.log(`Total de operações: ${all_metrics.data.total_operations}`);
    console.log(`Taxa de erro: ${all_metrics.data.error_rate.toFixed(2)}%`);
  });

// Exemplo: obter apenas métricas de tempo de execução
get_metrics(metric_type='execution_times')
  .then(exec_times => {
    for (const op in exec_times.data) {
      console.log(`${op}: min=${exec_times.data[op].min.toFixed(3)}s, avg=${exec_times.data[op].avg.toFixed(3)}s, max=${exec_times.data[op].max.toFixed(3)}s`);
    }
  });

// Exemplo: obter uso de recursos
get_metrics(metric_type='resource_usage')
  .then(resources => {
    if ('cpu_usage' in resources.data) {
      const cpu = resources.data.cpu_usage;
      console.log(`CPU: atual=${cpu.current.toFixed(0)}%, média=${cpu.avg.toFixed(0)}%, máximo=${cpu.max.toFixed(0)}%`);
    }
  });
}

### Resetar Métricas

```javascript
const axios = require('axios');

function reset_metrics(base_url = 'http://localhost:8000') {
  /**
   * Reseta todas as métricas de desempenho coletadas.
   */
  return axios.post(
    base_url,
    { tool: 'reset_metrics' }
  ).then(response => response.data);
}

// Exemplo de uso
reset_metrics()
  .then(result => console.log(result.data.message));
}

## Operações com Views

Exemplos de como trabalhar com views PostgreSQL usando o PostgreSQL MCP.

### Listar Views

```javascript
const axios = require('axios');

function list_views(base_url = 'http://localhost:8000', schema = 'public', include_materialized = true) {
  /**
   * Lista todas as views em um schema.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} schema - Nome do schema
   * @param {Boolean} include_materialized - Se deve incluir views materializadas
   */
  return axios.post(
    base_url,
    {
      tool: 'list_views',
      parameters: {
        schema,
        include_materialized
      }
    }
  ).then(response => response.data);
}

// Exemplo: listar todas as views no schema 'public'
list_views()
  .then(views => console.log(`Views encontradas: ${views.data}`));

// Exemplo: listar apenas views normais (não materializadas) no schema 'analytics'
list_views(schema='analytics', include_materialized=false)
  .then(views => console.log(`Views normais encontradas: ${views.data}`));
}

### Descrever View

```javascript
const axios = require('axios');

function describe_view(base_url = 'http://localhost:8000', view = 'active_users', schema = 'public') {
  /**
   * Obtém informações detalhadas sobre uma view.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} view - Nome da view
   * @param {String} schema - Nome do schema
   */
  return axios.post(
    base_url,
    {
      tool: 'describe_view',
      parameters: {
        view,
        schema
      }
    }
  ).then(response => response.data);
}

// Exemplo: descrever uma view
describe_view(view='customer_orders')
  .then(view_info => {
    console.log(`Nome: ${view_info.data.name}`);
    console.log(`Schema: ${view_info.data.schema}`);
    console.log(`Definição: ${view_info.data.definition}`);
    console.log(`Materializada: ${view_info.data.is_materialized}`);
    console.log('Colunas:');
    view_info.data.columns.forEach(column => {
      console.log(`  - ${column.name} (${column.data_type})`);
    });
  });
}

### Ler Dados de uma View

```javascript
const axios = require('axios');

function read_view(base_url = 'http://localhost:8000', view = 'sales_summary', schema = 'public', 
                  filters = null, columns = null, order_by = null, ascending = true, limit = null, offset = null) {
  /**
   * Lê registros de uma view.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} view - Nome da view
   * @param {String} schema - Nome do schema
   * @param {Object} [filters] - Filtros para a consulta
   * @param {Array} [columns] - Colunas específicas a retornar
   * @param {String} [orderBy] - Coluna para ordenação
   * @param {Boolean} [ascending] - Direção da ordenação
   * @param {Number} [limit] - Limite de registros a retornar
   * @param {Number} [offset] - Número de registros a pular
   */
  const params = {
    view,
    schema
  };
  
  if (filters) params.filters = filters;
  if (columns) params.columns = columns;
  if (orderBy) {
    params.order_by = order_by;
    params.ascending = ascending;
  }
  if (limit) params.limit = limit;
  if (offset) params.offset = offset;
  
  return axios.post(
    base_url,
    {
      tool: 'read_view',
      parameters
    }
  ).then(response => response.data);
}

// Exemplo: leitura simples de uma view
read_view(view='active_users')
  .then(results => {
    console.log(`Total de usuários ativos: ${results.count}`);
    results.data.forEach(user => {
      console.log(`ID: ${user.id}, Nome: ${user.name}, Email: ${user.email}`);
    });
  });

// Exemplo: leitura com filtros e paginação
read_view(
  view='order_summary',
  schema='reporting',
  filters={
    order_date: { gte: '2023-01-01' },
    total_amount: { gt: 1000 }
  },
  columns=['order_id', 'customer_name', 'total_amount', 'order_date'],
  order_by='total_amount',
  ascending=false,
  limit=10
)
  .then(results => {
    console.log(`Pedidos de alto valor: ${results.count}`);
    results.data.forEach(order => {
      console.log(`Pedido #${order.order_id}: ${order.customer_name} - R$ ${order.total_amount.toFixed(2)}`);
    });
  });
}

### Criar View

```javascript
const axios = require('axios');

function create_view(base_url = 'http://localhost:8000', view = 'active_users', definition = null, 
                   schema = 'public', is_materialized = false, replace = false) {
  /**
   * Cria ou atualiza uma view.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} view - Nome da view
   * @param {String} [definition] - Definição SQL da view
   * @param {String} schema - Nome do schema
   * @param {Boolean} is_materialized - Se é uma view materializada
   * @param {Boolean} replace - Se deve substituir caso já exista
   */
  return axios.post(
    base_url,
    {
      tool: 'create_view',
      parameters: {
        view,
        schema,
        definition,
        is_materialized,
        replace
      }
    }
  ).then(response => response.data);
}

// Exemplo: criar uma view simples
create_view(
  view='active_users',
  definition='SELECT id, name, email FROM users WHERE active = true'
)
  .then(result => console.log(`View criada: ${result.data.name}`));

// Exemplo: criar uma view materializada
create_view(
  view='monthly_revenue',
  schema='analytics',
  definition='''
    SELECT 
      DATE_TRUNC('month', order_date) as month,
      SUM(amount) as revenue
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
  ''',
  is_materialized=true,
  replace=true
)
  .then(result => console.log(`View materializada criada: ${result.data.name}`));
}

### Atualizar View Materializada

```javascript
const axios = require('axios');

function refresh_materialized_view(base_url = 'http://localhost:8000', view = 'daily_stats', 
                                 schema = 'public', concurrently = false) {
  /**
   * Atualiza uma view materializada.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} view - Nome da view materializada
   * @param {String} schema - Nome do schema
   * @param {Boolean} concurrently - Se deve atualizar concorrentemente (sem bloquear leituras)
   */
  return axios.post(
    base_url,
    {
      tool: 'refresh_materialized_view',
      parameters: {
        view,
        schema,
        concurrently
      }
    }
  ).then(response => response.data);
}

// Exemplo: atualizar uma view materializada
refresh_materialized_view(view='sales_summary')
  .then(result => {
    if (result.data.success) {
      console.log('View materializada atualizada com sucesso!');
    } else {
      console.log('Erro ao atualizar view materializada.');
    }
  });

// Exemplo: atualizar concorrentemente (sem bloquear leituras)
refresh_materialized_view(
  view='customer_stats',
  schema='analytics',
  concurrently=true
)
  .then(result => console.log(result.data.message || 'Atualização concorrente completada.'));
}

### Excluir View

```javascript
const axios = require('axios');

function drop_view(base_url = 'http://localhost:8000', view = 'temp_view', 
                 schema = 'public', if_exists = false, cascade = false) {
  /**
   * Exclui uma view.
   * 
   * @param {String} base_url - URL base do servidor MCP
   * @param {String} view - Nome da view
   * @param {String} schema - Nome do schema
   * @param {Boolean} if_exists - Se deve ignorar caso não exista
   * @param {Boolean} cascade - Se deve excluir objetos dependentes
   */
  return axios.post(
    base_url,
    {
      tool: 'drop_view',
      parameters: {
        view,
        schema,
        if_exists,
        cascade
      }
    }
  ).then(response => response.data);
}

// Exemplo: excluir uma view
drop_view(view='old_report')
  .then(result => {
    if (result.data.success) {
      console.log('View excluída com sucesso!');
    } else {
      console.log('Erro ao excluir view.');
    }
  });

// Exemplo: excluir uma view com dependências, ignorando se não existir
drop_view(
  view='temp_analysis',
  schema='analytics',
  if_exists=true,
  cascade=true
)
  .then(result => console.log(result.data.message || 'View excluída com sucesso.'));
}

## Exemplos de Uso de Views

### Listando Views

```javascript
const axios = require('axios');

function list_views_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Listar todas as views no schema public
  client.callTool('list_views', { schema: 'public' })
    .then(result => {
      console.log('Views:', result.data);
    });
}

// Executar o exemplo
list_views_example();
```

### Descrevendo uma View

```javascript
const axios = require('axios');

function describe_view_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Descrever uma view específica
  client.callTool('describe_view', {
    view: 'product_summary',
    schema: 'public'
  })
    .then(result => {
      const view_info = result.data;
      console.log(`Nome: ${view_info.name}`);
      console.log(`Schema: ${view_info.schema}`);
      console.log(`Materializada: ${view_info.is_materialized}`);
      console.log(`Definição: ${view_info.definition}`);
      console.log('Colunas:');
      view_info.columns.forEach(column => {
        console.log(`  - ${column.name} (${column.data_type})`);
      });
    });
}

// Executar o exemplo
describe_view_example();
```

### Criando uma View

```javascript
const axios = require('axios');

function create_view_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Criar uma view simples
  client.callTool('create_view', {
    view: 'customer_orders',
    query: '''
      SELECT c.customer_id, c.name, COUNT(o.order_id) as total_orders, SUM(o.amount) as total_spent
      FROM customers c
      LEFT JOIN orders o ON c.customer_id = o.customer_id
      GROUP BY c.customer_id, c.name
    ''',
    replace: true
  })
    .then(result => {
      console.log(`View criada: ${result.success}`);
    });
  
  // Criar uma view materializada
  client.callTool('create_view', {
    view: 'product_stats',
    query: '''
      SELECT p.product_id, p.name, p.category, 
             COUNT(oi.order_id) as order_count,
             SUM(oi.quantity) as total_sold
      FROM products p
      LEFT JOIN order_items oi ON p.product_id = oi.product_id
      GROUP BY p.product_id, p.name, p.category
    ''',
    materialized: true,
    with_data: true
  })
    .then(result => {
      console.log(`View materializada criada: ${result.success}`);
    });
}

// Executar o exemplo
create_view_example();
```

### Atualizando uma View Materializada

```javascript
const axios = require('axios');

function refresh_view_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Atualizar uma view materializada
  client.callTool('refresh_view', {
    view: 'product_stats',
    schema: 'public',
    concurrently: true
  })
    .then(result => {
      console.log(`View atualizada: ${result.success}`);
    });
}

// Executar o exemplo
refresh_view_example();
```

### Excluindo uma View

```javascript
const axios = require('axios');

function drop_view_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Excluir uma view
  client.callTool('drop_view', {
    view: 'customer_orders',
    schema: 'public',
    if_exists: true,
    cascade: false
  })
    .then(result => {
      console.log(`View excluída: ${result.success}`);
    });
}

// Executar o exemplo
drop_view_example();
```

## Exemplos de Uso de Funções e Procedimentos

### Listando Funções

```javascript
const axios = require('axios');

function list_functions_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Listar todas as funções no schema public
  client.callTool('list_functions', { schema: 'public' })
    .then(result => {
      console.log('Funções:', result.data);
    });
  
  // Listar apenas funções (sem procedimentos)
  client.callTool('list_functions', {
    schema: 'public',
    include_procedures: false
  })
    .then(result => {
      console.log('Funções (sem procedimentos):', result.data);
    });
  
  // Listar sem funções de agregação
  client.callTool('list_functions', {
    schema: 'public',
    include_aggregates: false
  })
    .then(result => {
      console.log('Funções (sem agregação):', result.data);
    });
}

// Executar o exemplo
list_functions_example();
```

### Descrevendo uma Função

```javascript
const axios = require('axios');

function describe_function_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Descrever uma função específica
  client.callTool('describe_function', {
    function: 'calculate_discount',
    schema: 'public'
  })
    .then(result => {
      const func_info = result.data;
      console.log(`Nome: ${func_info.name}`);
      console.log(`Schema: ${func_info.schema}`);
      console.log(`Tipo de retorno: ${func_info.return_type}`);
      console.log(`Linguagem: ${func_info.language}`);
      console.log(`É procedimento: ${func_info.is_procedure}`);
      
      console.log('Argumentos:');
      func_info.argument_types.forEach((arg_type, index) => {
        const arg_name = func_info.argument_names[index] || `arg${index+1}`;
        const arg_default = func_info.argument_defaults[index] || 'sem padrão';
        console.log(`  - ${arg_name} (${arg_type}), padrão: ${arg_default}`);
      });
      
      console.log(`Definição:\n${func_info.definition}`);
    });
}

// Executar o exemplo
describe_function_example();
```

### Criando uma Função

```javascript
const axios = require('axios');

function create_function_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Criar uma função simples
  client.callTool('create_function', {
    function: 'calculate_discount',
    schema: 'public',
    return_type: 'numeric',
    argument_definitions: [
      { name: 'price', type: 'numeric' },
      { name: 'discount_percent', type: 'numeric', default: '10' }
    ],
    definition: '''
      BEGIN
        RETURN price - (price * discount_percent / 100);
      END;
    ''',
    language: 'plpgsql',
    replace: true,
    volatility: 'immutable'
  })
    .then(result => {
      console.log(`Função criada: ${result.success}`);
    });
  
  // Criar um procedimento
  client.callTool('create_function', {
    function: 'update_product_price',
    schema: 'public',
    return_type: 'void',
    argument_definitions: [
      { name: 'product_id_param', type: 'integer' },
      { name: 'new_price', type: 'numeric' }
    ],
    definition: '''
      BEGIN
        UPDATE products SET price = new_price WHERE product_id = product_id_param;
      END;
    ''',
    language: 'plpgsql',
    is_procedure: true,
    replace: true
  })
    .then(result => {
      console.log(`Procedimento criado: ${result.success}`);
    });
}

// Executar o exemplo
create_function_example();
```

### Executando uma Função

```javascript
const axios = require('axios');

function execute_function_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Executar uma função com argumentos posicionais
  client.callTool('execute_function', {
    function: 'calculate_discount',
    schema: 'public',
    args: [100.00, 20]
  })
    .then(result => {
      console.log(`Resultado da função com argumentos posicionais: ${result.data}`);
    });
  
  // Executar uma função com argumentos nomeados
  client.callTool('execute_function', {
    function: 'calculate_discount',
    schema: 'public',
    named_args: {
      price: 200.00,
      discount_percent: 15
    }
  })
    .then(result => {
      console.log(`Resultado da função com argumentos nomeados: ${result.data}`);
    });
  
  // Executar um procedimento
  client.callTool('execute_function', {
    function: 'update_product_price',
    schema: 'public',
    args: [1, 29.99]
  })
    .then(result => {
      console.log(`Procedimento executado: ${result.success}`);
    });
}

// Executar o exemplo
execute_function_example();
```

### Excluindo uma Função

```javascript
const axios = require('axios');

function drop_function_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Excluir uma função
  client.callTool('drop_function', {
    function: 'calculate_discount',
    schema: 'public',
    if_exists: true,
    cascade: false,
    arg_types: ['numeric', 'numeric']  // Importante para diferenciar funções com mesmo nome
  })
    .then(result => {
      console.log(`Função excluída: ${result.success}`);
    });
  
  // Excluir um procedimento
  client.callTool('drop_function', {
    function: 'update_product_price',
    schema: 'public',
    if_exists: true
  })
    .then(result => {
      console.log(`Procedimento excluído: ${result.success}`);
    });
}

// Executar o exemplo
drop_function_example();
```

## Exemplo de Uso Combinado

### Criando e Utilizando uma Função em uma Consulta

```javascript
const axios = require('axios');

function combined_example() {
  // Inicializar o cliente MCP
  const client = new PostgresMCPClient();
  
  // Criar uma função para cálculo de desconto
  client.callTool('create_function', {
    function: 'calculate_discount',
    schema: 'public',
    return_type: 'numeric',
    argument_definitions: [
      { name: 'price', type: 'numeric' },
      { name: 'discount_percent', type: 'numeric', default: '10' }
    ],
    definition: '''
      BEGIN
        RETURN price - (price * discount_percent / 100);
      END;
    ''',
    language: 'plpgsql',
    replace: true,
    volatility: 'immutable'
  });
  
  // Criar uma view que utiliza a função
  client.callTool('create_view', {
    view: 'discounted_products',
    query: '''
      SELECT 
        product_id, 
        name, 
        price, 
        calculate_discount(price, 15) as discounted_price
      FROM 
        products
    ''',
    replace: true
  });
  
  // Consultar a view
  client.callTool('query', {
    query: 'SELECT * FROM discounted_products WHERE price > $1',
    params: [50.00]
  })
    .then(result => {
      console.log('Produtos com desconto:');
      result.data.forEach(product => {
        console.log(`  - ${product.name}: $${product.price} -> $${product.discounted_price}`);
      });
    });
}

// Executar o exemplo
combined_example();
```