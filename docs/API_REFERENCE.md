# API Reference - PostgreSQL MCP

Este documento contém a referência da API PostgreSQL MCP, detalhando todas as ferramentas disponíveis, seus parâmetros e respostas.

## Visão Geral

O PostgreSQL MCP implementa o Model Context Protocol para interação com bancos de dados PostgreSQL. As ferramentas disponíveis seguem o formato padrão MCP:

```json
{
  "tool": "nome_da_ferramenta",
  "parameters": {
    "param1": "valor1",
    "param2": "valor2"
  }
}
```

Todas as respostas têm a seguinte estrutura básica:

```json
{
  "success": true|false,
  "data": [...],
  "count": 10
}
```

Em caso de erro:

```json
{
  "success": false,
  "error": {
    "message": "Mensagem de erro",
    "type": "tipo_de_erro",
    "details": {
      // Detalhes adicionais do erro
    }
  }
}
```

## Ferramentas Disponíveis

### Ferramentas MCP

O PostgreSQL MCP implementa as seguintes ferramentas compatíveis com o Model Context Protocol (MCP):

#### `mcp_postgres_table`

Gerencia operações em tabelas do PostgreSQL.

**Operações:**

| Operação | Descrição |
|----------|-----------|
| `listTables` | Lista tabelas em um schema |
| `getTableDetails` | Obtém detalhes de uma tabela específica |
| `createTable` | Cria uma nova tabela |
| `dropTable` | Remove uma tabela existente |
| `truncateTable` | Esvazia uma tabela |
| `listTableRecords` | Lista registros de uma tabela |
| `insertRecord` | Insere um registro em uma tabela |
| `updateRecord` | Atualiza registros em uma tabela |
| `deleteRecord` | Remove registros de uma tabela |

**Exemplo:**

```json
{
  "tool": "mcp_postgres_table",
  "parameters": {
    "operation": "listTables",
    "schemaName": "public",
    "includeSystem": false
  },
  "requestId": "req_12345"
}
```

**Resposta:**

```json
{
  "status": "success",
  "data": {
    "tables": [
      { "name": "users", "schema": "public", "type": "table", "owner": "postgres" },
      { "name": "products", "schema": "public", "type": "table", "owner": "postgres" }
    ]
  },
  "message": "Encontrada(s) 2 tabela(s) no schema 'public'",
  "requestId": "req_12345"
}
```

#### `mcp_postgres_query`

Executa consultas SQL no banco de dados PostgreSQL.

**Operações:**

| Operação | Descrição |
|----------|-----------|
| `executeQuery` | Executa uma consulta SQL |
| `prepareStatement` | Prepara uma declaração SQL para execução posterior |
| `executePrepared` | Executa uma declaração SQL preparada |

**Exemplo:**

```json
{
  "tool": "mcp_postgres_query",
  "parameters": {
    "operation": "executeQuery",
    "sql": "SELECT * FROM users WHERE status = $1",
    "parameters": ["active"],
    "maxRows": 100
  },
  "requestId": "req_12346"
}
```

**Resposta:**

```json
{
  "status": "success",
  "data": {
    "records": [
      { "id": 1, "name": "John Doe", "email": "john@example.com", "status": "active" },
      { "id": 2, "name": "Jane Smith", "email": "jane@example.com", "status": "active" }
    ],
    "fields": [
      { "name": "id", "type": "integer" },
      { "name": "name", "type": "varchar" },
      { "name": "email", "type": "varchar" },
      { "name": "status", "type": "varchar" }
    ],
    "rowCount": 2,
    "executionTime": 5,
    "command": "SELECT"
  },
  "message": "Consulta executada com sucesso. 2 registro(s) retornado(s).",
  "requestId": "req_12346"
}
```

#### `mcp_postgres_schema`

Gerencia schemas e estruturas do banco de dados PostgreSQL.

**Operações:**

| Operação | Descrição |
|----------|-----------|
| `listSchemas` | Lista todos os schemas disponíveis |
| `createSchema` | Cria um novo schema |
| `dropSchema` | Remove um schema existente |
| `getSchemaDetails` | Obtém detalhes de um schema específico |
| `createIndex` | Cria um índice em uma tabela |
| `dropIndex` | Remove um índice existente |
| `listIndices` | Lista índices de uma tabela |

**Exemplo:**

```json
{
  "tool": "mcp_postgres_schema",
  "parameters": {
    "operation": "listSchemas",
    "includeSystem": false
  },
  "requestId": "req_12347"
}
```

**Resposta:**

```json
{
  "status": "success",
  "data": {
    "schemas": [
      { "name": "public", "owner": "postgres" },
      { "name": "custom", "owner": "postgres" }
    ]
  },
  "message": "Operação listSchemas executada com sucesso",
  "requestId": "req_12347"
}
```

#### `mcp_postgres_metadata`

Fornece informações sobre metadados do banco de dados PostgreSQL.

**Operações:**

| Operação | Descrição |
|----------|-----------|
| `getPostgresVersion` | Obtém a versão do PostgreSQL |
| `getDatabaseSize` | Obtém o tamanho do banco de dados |
| `getTableSize` | Obtém o tamanho de uma tabela específica |
| `listExtensions` | Lista extensões instaladas |
| `getTableStats` | Obtém estatísticas de uma tabela |

**Exemplo:**

```json
{
  "tool": "mcp_postgres_metadata",
  "parameters": {
    "operation": "getPostgresVersion"
  },
  "requestId": "req_12348"
}
```

**Resposta:**

```json
{
  "status": "success",
  "data": {
    "version": {
      "full_version": "PostgreSQL 14.5 on x86_64-pc-linux-gnu",
      "server_version": "14.5",
      "server_version_num": "140005"
    }
  },
  "message": "Operação getPostgresVersion executada com sucesso",
  "requestId": "req_12348"
}
```

#### `mcp_postgres_connection`

Gerencia conexões com o banco de dados PostgreSQL.

**Operações:**

| Operação | Descrição |
|----------|-----------|
| `getConnectionStatus` | Obtém o status da conexão atual |
| `testConnection` | Testa a conexão com o banco de dados |
| `reconnect` | Reconecta ao banco de dados |
| `getConnectionInfo` | Obtém informações detalhadas da conexão |

**Exemplo:**

```json
{
  "tool": "mcp_postgres_connection",
  "parameters": {
    "operation": "getConnectionStatus"
  },
  "requestId": "req_12349"
}
```

**Resposta:**

```json
{
  "status": "success",
  "data": {
    "status": {
      "connected": true,
      "latencyMs": 5,
      "serverVersion": "PostgreSQL 14.5",
      "connectionUptime": 3600,
      "poolSize": 5,
      "timestamp": "2024-05-12T21:48:31.031Z"
    }
  },
  "message": "Operação getConnectionStatus executada com sucesso",
  "requestId": "req_12349"
}
```

#### `mcp_postgres_transaction`

Gerencia transações no banco de dados PostgreSQL.

**Operações:**

| Operação | Descrição |
|----------|-----------|
| `begin` | Inicia uma nova transação |
| `commit` | Confirma uma transação ativa |
| `rollback` | Reverte uma transação ativa |
| `getTransactionStatus` | Obtém o status da transação atual |
| `savepoint` | Cria um ponto de salvamento na transação atual |
| `rollbackToSavepoint` | Reverte para um ponto de salvamento específico |

**Exemplo:**

```json
{
  "tool": "mcp_postgres_transaction",
  "parameters": {
    "operation": "begin",
    "isolationLevel": "read committed",
    "readOnly": false
  },
  "requestId": "req_12350"
}
```

**Resposta:**

```json
{
  "status": "success",
  "data": {
    "transactionId": "tx_123456",
    "isolationLevel": "read committed",
    "readOnly": false,
    "deferrable": false
  },
  "message": "Transação iniciada com sucesso",
  "requestId": "req_12350"
}
```

### 1. `list_schemas`

Lista todos os schemas disponíveis no banco de dados.

**Parâmetros:**

Esta ferramenta não requer parâmetros.

**Exemplo:**

```json
{
  "tool": "list_schemas"
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    "public",
    "auth",
    "analytics",
    "custom"
  ],
  "count": 4
}
```

### 2. `list_tables`

Lista todas as tabelas disponíveis em um schema específico ou em todos os schemas.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `schema` | string | Nome do schema (default: "public") | Não |
| `include_views` | boolean | Incluir views nos resultados | Não (default: false) |

**Exemplo:**

```json
{
  "tool": "list_tables",
  "parameters": {
    "schema": "public",
    "include_views": true
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    {"name": "users", "type": "table", "schema": "public"},
    {"name": "products", "type": "table", "schema": "public"},
    {"name": "orders", "type": "table", "schema": "public"},
    {"name": "active_users", "type": "view", "schema": "public"}
  ],
  "count": 4
}
```

### 3. `describe_table`

Retorna informações detalhadas sobre a estrutura de uma tabela, incluindo colunas, tipos de dados, restrições e índices.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `table` | string | Nome da tabela | Sim |
| `schema` | string | Nome do schema (default: "public") | Não |

**Exemplo:**

```json
{
  "tool": "describe_table",
  "parameters": {
    "table": "users",
    "schema": "public"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "columns": [
      {"name": "id", "type": "uuid", "nullable": false, "default": "uuid_generate_v4()"},
      {"name": "name", "type": "character varying(255)", "nullable": false, "default": null},
      {"name": "email", "type": "character varying(255)", "nullable": false, "default": null},
      {"name": "created_at", "type": "timestamp with time zone", "nullable": false, "default": "now()"}
    ],
    "primary_key": ["id"],
    "foreign_keys": [],
    "indexes": [
      {"name": "users_pkey", "columns": ["id"], "unique": true},
      {"name": "users_email_key", "columns": ["email"], "unique": true}
    ],
    "schema": "public"
  },
  "count": 1
}
```

### 4. `read_table`

Lê registros de uma tabela com suporte a filtros, ordenação e limite.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `table` | string | Nome da tabela | Sim |
| `schema` | string | Nome do schema (default: "public") | Não |
| `filters` | object | Filtros da consulta | Não |
| `columns` | array | Colunas específicas a retornar | Não (default: "*") |
| `order_by` | string | Coluna para ordenação | Não |
| `ascending` | boolean | Direção da ordenação (true=asc, false=desc) | Não (default: true) |
| `limit` | number | Limite de registros a retornar | Não |
| `offset` | number | Número de registros a pular | Não |

**Exemplo:**

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "schema": "public", 
    "filters": {
      "status": "active",
      "age": {
        "gt": 18
      }
    },
    "columns": ["id", "name", "email", "status", "age"],
    "order_by": "created_at",
    "ascending": false,
    "limit": 10,
    "offset": 0
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "John Doe",
      "email": "john@example.com",
      "status": "active",
      "age": 30
    },
    // ... mais registros
  ],
  "count": 5
}
```

### 5. `create_record`

Cria um único registro na tabela especificada.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `table` | string | Nome da tabela | Sim |
| `schema` | string | Nome do schema (default: "public") | Não |
| `data` | object | Dados do registro a criar | Sim |
| `returning` | array | Colunas a retornar após criação | Não (default: ["*"]) |

**Exemplo:**

```json
{
  "tool": "create_record",
  "parameters": {
    "table": "users",
    "schema": "public",
    "data": {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "status": "active",
      "age": 28
    },
    "returning": ["id", "name", "email"]
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  "count": 1
}
```

### 6. `create_batch`

Cria múltiplos registros em uma única operação.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `table` | string | Nome da tabela | Sim |
| `schema` | string | Nome do schema (default: "public") | Não |
| `records` | array | Lista de registros a criar | Sim |
| `returning` | array | Colunas a retornar após criação | Não (default: ["*"]) |
| `batch_size` | number | Tamanho do lote para inserção | Não (default: 100) |

**Exemplo:**

```json
{
  "tool": "create_batch",
  "parameters": {
    "table": "products",
    "schema": "public",
    "records": [
      {
        "name": "Produto 1",
        "price": 19.99,
        "category": "electronics"
      },
      {
        "name": "Produto 2",
        "price": 29.99,
        "category": "clothing"
      }
    ],
    "returning": ["id", "name", "price"],
    "batch_size": 50
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "Produto 1",
      "price": 19.99
    },
    {
      "id": "7c5aba41-f6ee-4a56-8b6d-1c5abcdef123",
      "name": "Produto 2",
      "price": 29.99
    }
  ],
  "count": 2
}
```

### 7. `update_records`

Atualiza registros que correspondem aos filtros especificados.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `table` | string | Nome da tabela | Sim |
| `schema` | string | Nome do schema (default: "public") | Não |
| `filters` | object | Filtros para selecionar registros a atualizar | Sim |
| `data` | object | Dados a atualizar | Sim |
| `returning` | array | Colunas a retornar após atualização | Não (default: ["*"]) |

**Exemplo:**

```json
{
  "tool": "update_records",
  "parameters": {
    "table": "users",
    "schema": "public",
    "filters": {
      "status": "inactive"
    },
    "data": {
      "status": "archived",
      "updated_at": "2023-06-20T15:00:00Z"
    },
    "returning": ["id", "name", "status", "updated_at"]
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Usuário Inativo",
      "status": "archived",
      "updated_at": "2023-06-20T15:00:00Z"
    },
    // ... mais registros atualizados
  ],
  "count": 3
}
```

### 8. `delete_records`

Exclui registros que correspondem aos filtros especificados.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `table` | string | Nome da tabela | Sim |
| `schema` | string | Nome do schema (default: "public") | Não |
| `filters` | object | Filtros para selecionar registros a excluir | Sim |
| `returning` | array | Colunas a retornar após exclusão | Não (default: ["*"]) |

**Exemplo:**

```json
{
  "tool": "delete_records",
  "parameters": {
    "table": "temp_logs",
    "schema": "public",
    "filters": {
      "created_at": {
        "lt": "2023-01-01T00:00:00Z"
      }
    },
    "returning": ["id", "message", "created_at"]
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    {
      "id": "log123",
      "message": "Log antigo",
      "created_at": "2022-11-15T10:30:00Z"
    },
    // ... mais registros excluídos
  ],
  "count": 15
}
```

### 9. `execute_query`

Executa uma consulta SQL personalizada (uso restrito, requer permissões).

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `query` | string | Consulta SQL a executar | Sim |
| `params` | array | Parâmetros para a consulta | Não |
| `read_only` | boolean | Se a consulta é somente leitura | Não (default: true) |

**Exemplo:**

```json
{
  "tool": "execute_query",
  "parameters": {
    "query": "SELECT u.name, COUNT(o.id) as orders_count FROM users u JOIN orders o ON u.id = o.user_id WHERE u.status = $1 GROUP BY u.name ORDER BY orders_count DESC LIMIT $2",
    "params": ["active", 10],
    "read_only": true
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": [
    {
      "name": "John Doe",
      "orders_count": 15
    },
    {
      "name": "Jane Smith",
      "orders_count": 12
    },
    // ... mais resultados
  ],
  "count": 10
}
```

### 10. `begin_transaction`

Inicia uma transação para operações subsequentes.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `isolation_level` | string | Nível de isolamento da transação | Não (default: "read_committed") |

**Exemplo:**

```json
{
  "tool": "begin_transaction",
  "parameters": {
    "isolation_level": "serializable"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "transaction_id": "tx_123456789",
    "isolation_level": "serializable",
    "started_at": "2023-06-20T15:30:00Z"
  },
  "count": 1
}
```

### 11. `commit_transaction`

Confirma uma transação em andamento.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `transaction_id` | string | ID da transação a confirmar | Sim |

**Exemplo:**

```json
{
  "tool": "commit_transaction",
  "parameters": {
    "transaction_id": "tx_123456789"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "transaction_id": "tx_123456789",
    "status": "committed",
    "committed_at": "2023-06-20T15:35:00Z"
  },
  "count": 1
}
```

### 12. `rollback_transaction`

Reverte uma transação em andamento.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `transaction_id` | string | ID da transação a reverter | Sim |
| `savepoint` | string | Nome do savepoint (opcional) | Não |

**Exemplo:**

```json
{
  "tool": "rollback_transaction",
  "parameters": {
    "transaction_id": "tx_123456789",
    "savepoint": "point_after_insert"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "transaction_id": "tx_123456789",
    "status": "rolled_back",
    "rollback_to": "point_after_insert",
    "rolled_back_at": "2023-06-20T15:40:00Z"
  },
  "count": 1
}
```

### 13. `get_cache_stats`

Retorna estatísticas sobre o uso do cache do sistema.

**Parâmetros:**

Esta ferramenta não requer parâmetros.

**Exemplo:**

```json
{
  "tool": "get_cache_stats"
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "hits": 3250,
    "misses": 750,
    "invalidations": 120,
    "hit_ratio": "81.25%",
    "table_cache_size": 428,
    "schema_cache_size": 12,
    "metadata_cache_size": 56,
    "table_cache_capacity": 1000,
    "schema_cache_capacity": 100,
    "metadata_cache_capacity": 200
  }
}
```

### 14. `clear_cache`

Limpa o cache do sistema, total ou parcialmente.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `scope` | string | Escopo da limpeza: 'all', 'table' ou 'schema' | Não (default: "all") |
| `table` | string | Nome da tabela quando scope='table' | Condicional |
| `schema` | string | Nome do schema (quando scope='schema' ou 'table') | Condicional |

**Exemplo 1:** Limpar todo o cache

```json
{
  "tool": "clear_cache"
}
```

**Exemplo 2:** Limpar cache para uma tabela específica

```json
{
  "tool": "clear_cache",
  "parameters": {
    "scope": "table",
    "table": "users",
    "schema": "public"
  }
}
```

**Exemplo 3:** Limpar cache para um schema inteiro

```json
{
  "tool": "clear_cache",
  "parameters": {
    "scope": "schema",
    "schema": "public"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "message": "Cache da tabela public.users limpo"
  }
}
```

### 15. `get_metrics`

Retorna métricas de desempenho do sistema.

**Parâmetros:**

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `metric_type` | string | Tipo específico de métrica a retornar: 'execution_times', 'errors', 'resource_usage', 'operations_per_second' | Não |
| `operation` | string | Nome da operação para filtrar estatísticas (quando metric_type='execution_times') | Não |
| `window_seconds` | integer | Janela de tempo em segundos para cálculo de operações por segundo (quando metric_type='operations_per_second') | Não (default: 60) |

**Exemplo:**

```json
{
  "tool": "get_metrics",
  "parameters": {
    "metric_type": "execution_times"
  }
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "execution_times": {
      "read_table": {
        "min": 0.001,
        "max": 1.234,
        "avg": 0.075,
        "median": 0.045,
        "p95": 0.312,
        "count": 1250,
        "total_count": 1500
      },
      "execute_query": {
        "min": 0.005,
        "max": 2.345,
        "avg": 0.125,
        "median": 0.089,
        "p95": 0.456,
        "count": 850,
        "total_count": 1200
      }
    }
  }
}
```

### 16. `reset_metrics`

Reseta todas as métricas de desempenho coletadas pelo sistema.

**Parâmetros:**

Esta ferramenta não requer parâmetros.

**Exemplo:**

```json
{
  "tool": "reset_metrics"
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "message": "Métricas resetadas com sucesso"
  }
}
```

## Operadores de Filtro

O PostgreSQL MCP suporta os seguintes operadores para filtros:

| Operador | Descrição | Exemplo |
|----------|-----------|---------|
| `eq` | Igual a | `{"status": {"eq": "active"}}` |
| `gt` | Maior que | `{"price": {"gt": 100}}` |
| `lt` | Menor que | `{"age": {"lt": 18}}` |
| `gte` | Maior ou igual a | `{"rating": {"gte": 4.5}}` |
| `lte` | Menor ou igual a | `{"quantity": {"lte": 10}}` |
| `like` | Padrão LIKE (case sensitive) | `{"name": {"like": "%Smith%"}}` |
| `ilike` | Padrão LIKE (case insensitive) | `{"email": {"ilike": "%@gmail.com"}}` |
| `in` | Em lista de valores | `{"category": {"in": ["books", "movies"]}}` |
| `is` | É null ou não null | `{"deleted_at": {"is": null}}` |
| `contains` | Contém (para arrays e JSONB) | `{"tags": {"contains": ["urgent"]}}` |
| `contained_by` | Contido em (para arrays) | `{"selected_ids": {"contained_by": [1, 2, 3, 4, 5]}}` |
| `overlap` | Sobreposição (para arrays) | `{"available_days": {"overlap": ["monday", "friday"]}}` |
| `match` | Correspondência regex | `{"code": {"match": "^[A-Z]{3}\\d{3}$"}}` |
| `jsonb_path` | Consulta caminho JSONB | `{"metadata": {"jsonb_path": "$.address.city ? (@ == \"New York\")"}}` |

Para filtros de igualdade simples, você também pode usar a sintaxe abreviada:

```json
{
  "status": "active",
  "category": "electronics"
}
```

## Níveis de Isolamento de Transação

O PostgreSQL MCP suporta os seguintes níveis de isolamento para transações:

| Nível | Descrição |
|-------|-----------|
| `read_uncommitted` | Permite leitura de dados não confirmados (no PostgreSQL, é tratado como read_committed) |
| `read_committed` | Só permite leitura de dados confirmados (padrão) |
| `repeatable_read` | Garante que dados lidos permaneçam consistentes durante a transação |
| `serializable` | Mais alto nível de isolamento, previne anomalias de concorrência |

## Códigos de Erro

| Tipo | Descrição |
|------|-----------|
| `validation_error` | Erro de validação dos parâmetros da requisição |
| `database_error` | Erro do banco de dados ao processar a operação |
| `security_error` | Erro relacionado a permissões ou políticas de segurança |
| `transaction_error` | Erro relacionado a transações |
| `query_error` | Erro na execução de consulta SQL personalizada |
| `internal_error` | Erro interno do servidor |

## Limitações e Melhores Práticas

- Utilize filtros específicos para evitar transferência de grandes volumes de dados
- Para operações em lote, use valores razoáveis de `batch_size` (entre 50 e 500)
- As exclusões em massa devem sempre incluir filtros
- Operações de atualização sem filtros são bloqueadas por segurança
- Use transações para operações que requerem consistência
- Para consultas complexas, considere o uso de `execute_query` com parâmetros apropriados
- Aproveite os recursos específicos do PostgreSQL como JSONB e arrays quando apropriado

## Componentes Internos

### PostgresConnection

Interface de conexão com o banco de dados PostgreSQL, fornecendo métodos para executar consultas e gerenciar transações.

### PostgresConnectionManager

Gerencia múltiplas conexões com bancos de dados PostgreSQL, permitindo o uso de diferentes conexões para diferentes propósitos.

### PostgresSchemaManager

Responsável por operações relacionadas ao schema do PostgreSQL, como listagem de tabelas, colunas e restrições.

### PostgresSchemaQueries

Armazena todas as consultas SQL utilizadas pelo PostgresSchemaManager. Esta separação facilita a manutenção e organização do código, melhorando a legibilidade e permitindo uma melhor otimização das consultas.

### PostgresQueryBuilder

Construtor de consultas SQL que permite criar consultas dinâmicas de forma segura e com proteção contra injeção SQL.