# Guia Inicial - PostgreSQL MCP

Este guia fornece instruções passo a passo para começar a usar o PostgreSQL MCP em seu projeto.

## Pré-requisitos

- Python 3.10 ou superior
- Acesso a um banco de dados PostgreSQL (local ou remoto)
- Credenciais de acesso ao PostgreSQL com privilégios adequados

## Instalação

Instale o pacote usando pip:

```bash
pip install postgres-mcp
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

#### Configuração Programática

```python
from postgres_mcp import PostgresMCP

mcp = PostgresMCP(
    db_host="localhost",
    db_port=5432,
    db_name="mydatabase",
    db_user="myuser",
    db_password="mypassword",
    db_ssl="prefer"  # Opções: disable, allow, prefer, require, verify-ca, verify-full
)
```

## Modos de Operação

O PostgreSQL MCP suporta dois modos de operação:

### 1. Modo STDIO (Padrão)

Este modo é ideal para integração com LLMs que usam o protocolo MCP.

```python
from postgres_mcp import PostgresMCP

# Inicializa no modo STDIO (padrão)
mcp = PostgresMCP()

# Inicia o servidor
mcp.start()
```

### 2. Modo HTTP

O modo HTTP é útil para desenvolvimento, testes e chamadas de API diretas.

```python
from postgres_mcp import PostgresMCP

# Inicializa no modo HTTP
mcp = PostgresMCP(mode="http", port=8000)

# Inicia o servidor HTTP
mcp.start()
```

## Configuração Avançada

### 1. Configurando Tamanho do Pool de Conexões

```python
from postgres_mcp import PostgresMCP

mcp = PostgresMCP(
    db_host="localhost",
    db_port=5432,
    db_name="mydatabase",
    db_user="myuser",
    db_password="mypassword",
    pool_min_size=5,
    pool_max_size=20
)
```

### 2. Configurando Timeout e Limites

```python
from postgres_mcp import PostgresMCP

mcp = PostgresMCP(
    db_host="localhost",
    db_port=5432,
    db_name="mydatabase",
    db_user="myuser",
    db_password="mypassword",
    command_timeout=60,  # Timeout em segundos para comandos
    max_query_rows=10000,  # Limite máximo de linhas para consultas
    transaction_timeout=300  # Timeout em segundos para transações
)
```

### 3. Configurando Logging

```python
from postgres_mcp import PostgresMCP
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("postgres_mcp.log")
    ]
)

# Inicializa com configuração de logging personalizada
mcp = PostgresMCP(
    db_host="localhost",
    db_port=5432,
    db_name="mydatabase",
    db_user="myuser",
    db_password="mypassword",
    log_level="INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_sql_queries=True  # Log de todas as consultas SQL executadas
)
```

## Exemplos de Uso

### Listar Schemas Disponíveis

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta list_schemas
response = mcp.handle({
    "tool": "list_schemas",
    "parameters": {}
})

print(response)
```

### Listar Tabelas Disponíveis

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta list_tables
response = mcp.handle({
    "tool": "list_tables",
    "parameters": {
        "schema": "public",
        "include_views": True
    }
})

print(response)
```

### Descrever Estrutura de Tabela

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta describe_table
response = mcp.handle({
    "tool": "describe_table",
    "parameters": {
        "table": "users",
        "schema": "public"
    }
})

print(response)
```

### Consultar Registros

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta read_table
response = mcp.handle({
    "tool": "read_table",
    "parameters": {
        "table": "users",
        "schema": "public",
        "filters": {
            "is_active": True,
            "created_at": {
                "gte": "2023-01-01T00:00:00Z"
            }
        },
        "columns": ["id", "name", "email", "created_at"],
        "order_by": "created_at",
        "ascending": False,
        "limit": 5
    }
})

print(response)
```

### Criar um Registro

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta create_record
response = mcp.handle({
    "tool": "create_record",
    "parameters": {
        "table": "tasks",
        "schema": "public",
        "data": {
            "title": "Completar documentação",
            "description": "Finalizar guias de uso do MCP",
            "status": "pending",
            "due_date": "2023-08-30",
            "assigned_to": "user123",
            "priority": "high"
        },
        "returning": ["id", "title", "status"]
    }
})

print(response)
```

### Atualizar Registros

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta update_records
response = mcp.handle({
    "tool": "update_records",
    "parameters": {
        "table": "tasks",
        "schema": "public",
        "filters": {
            "status": "pending",
            "due_date": {
                "lt": "2023-07-01"
            }
        },
        "data": {
            "status": "overdue",
            "updated_at": "2023-07-01T00:00:00Z"
        },
        "returning": ["id", "title", "status", "due_date"]
    }
})

print(response)
```

### Executar Consulta SQL Personalizada

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Executa a ferramenta execute_query
response = mcp.handle({
    "tool": "execute_query",
    "parameters": {
        "query": """
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
        "params": [True, 5],
        "read_only": True
    }
})

print(response)
```

### Usando Transações

```python
from postgres_mcp import PostgresMCP

# Inicializa o cliente em modo teste
mcp = PostgresMCP(test_mode=True)

# Inicia uma transação
tx_response = mcp.handle({
    "tool": "begin_transaction",
    "parameters": {
        "isolation_level": "serializable"
    }
})

transaction_id = tx_response["data"]["transaction_id"]

try:
    # Atualiza um registro dentro da transação
    mcp.handle({
        "tool": "update_records",
        "parameters": {
            "table": "accounts",
            "schema": "public",
            "filters": {"id": "acc_123"},
            "data": {"balance": {"decrement": 100.00}},
            "transaction_id": transaction_id
        }
    })
    
    # Cria um registro dentro da mesma transação
    mcp.handle({
        "tool": "create_record",
        "parameters": {
            "table": "transfers",
            "schema": "public",
            "data": {
                "from_account": "acc_123", 
                "to_account": "acc_456",
                "amount": 100.00,
                "status": "completed"
            },
            "transaction_id": transaction_id
        }
    })
    
    # Confirma a transação
    mcp.handle({
        "tool": "commit_transaction",
        "parameters": {
            "transaction_id": transaction_id
        }
    })
    
except Exception as e:
    # Em caso de erro, reverte a transação
    mcp.handle({
        "tool": "rollback_transaction",
        "parameters": {
            "transaction_id": transaction_id
        }
    })
    print(f"Erro: {str(e)}")
```

## Integração com LLMs

### Exemplo com Anthropic (Claude)

```python
import anthropic
from postgres_mcp import PostgresMCP

# Inicializar o cliente MCP em modo teste
mcp = PostgresMCP(test_mode=True)

# Inicializar cliente Claude
client = anthropic.Anthropic(api_key="your-api-key")

# Preparar ferramentas para Claude
tools = [
    {
        "name": "list_tables",
        "description": "Lista todas as tabelas disponíveis no banco de dados PostgreSQL",
        "input_schema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string", "description": "Nome do schema (default: public)"},
                "include_views": {"type": "boolean", "description": "Incluir views nos resultados"}
            }
        }
    },
    {
        "name": "read_table",
        "description": "Consulta registros de uma tabela PostgreSQL",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Nome da tabela"},
                "schema": {"type": "string", "description": "Nome do schema (default: public)"},
                "filters": {"type": "object", "description": "Filtros da consulta"},
                "columns": {"type": "array", "description": "Colunas específicas a retornar"},
                "limit": {"type": "number", "description": "Limite de registros a retornar"}
            },
            "required": ["table"]
        }
    },
    {
        "name": "execute_query",
        "description": "Executa uma consulta SQL personalizada",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta SQL a executar"},
                "params": {"type": "array", "description": "Parâmetros para a consulta"},
                "read_only": {"type": "boolean", "description": "Se a consulta é somente leitura"}
            },
            "required": ["query"]
        }
    }
]

# Função para processar chamadas de ferramenta
def process_tool_call(tool_call):
    tool_name = tool_call["name"]
    parameters = tool_call["parameters"]
    
    # Processar a chamada através do MCP
    result = mcp.handle({
        "tool": tool_name,
        "parameters": parameters
    })
    
    return result

# Exemplo de uso com Claude
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0,
    tools=tools,
    messages=[
        {"role": "user", "content": "Liste todas as tabelas no schema public e depois mostre os 5 usuários mais recentes."}
    ]
)

# Processar e responder às chamadas de ferramentas de Claude
for tool_call in message.content:
    if hasattr(tool_call, "tool_use"):
        tool_result = process_tool_call(tool_call.tool_use)
        # Enviar resultado de volta para o LLM
        # ...
```

### Exemplo com OpenAI (GPT)

```python
import openai
from postgres_mcp import PostgresMCP

# Inicializar o cliente MCP em modo teste
mcp = PostgresMCP(test_mode=True)

# Configurar OpenAI
openai.api_key = "your-api-key"

# Preparar as ferramentas para OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Lista todas as tabelas disponíveis no banco de dados PostgreSQL",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Nome do schema (default: public)"},
                    "include_views": {"type": "boolean", "description": "Incluir views nos resultados"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_table",
            "description": "Consulta registros de uma tabela PostgreSQL",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Nome da tabela"},
                    "schema": {"type": "string", "description": "Nome do schema (default: public)"},
                    "filters": {"type": "object", "description": "Filtros da consulta"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Colunas específicas a retornar"},
                    "limit": {"type": "number", "description": "Limite de registros a retornar"}
                },
                "required": ["table"]
            }
        }
    }
]

# Função para processar chamadas de ferramenta
def process_tool_call(tool_call):
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # Processar a chamada através do MCP
    result = mcp.handle({
        "tool": function_name,
        "parameters": arguments
    })
    
    return result

# Exemplo de uso com GPT
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Liste todas as tabelas no banco de dados e depois mostre os 5 usuários mais recentes."}
    ],
    tools=tools,
    tool_choice="auto"
)

# Processar e responder às chamadas de ferramentas
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        tool_result = process_tool_call(tool_call)
        # Enviar resultado de volta para o LLM
        # ...
```

## Próximos Passos

- Veja a [Referência de API](../API_REFERENCE.md) para documentação detalhada de todas as ferramentas
- Explore o [Guia de Filtros](./filters.md) para entender as opções de filtragem avançada
- Consulte os [Exemplos de Código](../CODE_EXAMPLES.md) para casos de uso mais avançados
- Leia sobre [Transações](./transactions.md) para entender o gerenciamento de transações
- Aprenda sobre [Tipos Avançados do PostgreSQL](./advanced-types.md) para trabalhar com JSON, arrays e outros tipos