# PostgreSQL MCP - Exemplos de Código

Este documento contém exemplos de código para usar e estender o PostgreSQL MCP.

## Exemplos de Uso

### 1. Configuração Básica

```python
import os
from dotenv import load_dotenv
from postgres_mcp import PostgresMCPServer

# Carrega variáveis de ambiente de .env
load_dotenv()

# Inicializa o servidor MCP
server = PostgresMCPServer(
    db_host=os.getenv("DB_HOST"),
    db_port=int(os.getenv("DB_PORT", "5432")),
    db_name=os.getenv("DB_NAME"),
    db_user=os.getenv("DB_USER"),
    db_password=os.getenv("DB_PASSWORD"),
    transport="stdio"  # ou "streamable-http" para HTTP
)

# Inicia o servidor
server.start()
```

### 2. Cliente para Testes HTTP

```python
import requests
import json

class PostgresMCPClient:
    def __init__(self, url="http://localhost:3000/mcp"):
        self.url = url
    
    def call_tool(self, tool, parameters):
        response = requests.post(
            self.url,
            json={"tool": tool, "parameters": parameters}
        )
        return response.json()
    
    def read_table(self, table, schema="public", filters=None, columns=None, order_by=None, ascending=True, limit=None, offset=None):
        parameters = {"table": table, "schema": schema}
        
        if filters:
            parameters["filters"] = filters
        
        if columns:
            parameters["columns"] = columns
        
        if order_by:
            parameters["order_by"] = order_by
            parameters["ascending"] = ascending
        
        if limit:
            parameters["limit"] = limit
            
        if offset:
            parameters["offset"] = offset
        
        return self.call_tool("read_table", parameters)
    
    def create_record(self, table, data, schema="public", returning=None):
        parameters = {
            "table": table,
            "schema": schema,
            "data": data
        }
        
        if returning:
            parameters["returning"] = returning
            
        return self.call_tool("create_record", parameters)
    
    def update_records(self, table, filters, data, schema="public", returning=None):
        parameters = {
            "table": table,
            "schema": schema,
            "filters": filters,
            "data": data
        }
        
        if returning:
            parameters["returning"] = returning
            
        return self.call_tool("update_records", parameters)
    
    def delete_records(self, table, filters, schema="public", returning=None):
        parameters = {
            "table": table,
            "schema": schema,
            "filters": filters
        }
        
        if returning:
            parameters["returning"] = returning
            
        return self.call_tool("delete_records", parameters)
    
    def execute_query(self, query, params=None, read_only=True):
        parameters = {
            "query": query,
            "read_only": read_only
        }
        
        if params:
            parameters["params"] = params
            
        return self.call_tool("execute_query", parameters)
    
    def begin_transaction(self, isolation_level="read_committed"):
        parameters = {
            "isolation_level": isolation_level
        }
        return self.call_tool("begin_transaction", parameters)
    
    def commit_transaction(self, transaction_id):
        parameters = {
            "transaction_id": transaction_id
        }
        return self.call_tool("commit_transaction", parameters)
    
    def rollback_transaction(self, transaction_id, savepoint=None):
        parameters = {
            "transaction_id": transaction_id
        }
        
        if savepoint:
            parameters["savepoint"] = savepoint
            
        return self.call_tool("rollback_transaction", parameters)
```

### 3. Exemplos de Chamadas de API

#### Leitura de Registros

```python
client = PostgresMCPClient()

# Buscar usuários ativos
users = client.read_table(
    table="users",
    schema="public",
    filters={"active": True},
    columns=["id", "name", "email", "created_at"],
    order_by="created_at",
    ascending=False,
    limit=10
)
print(json.dumps(users, indent=2))
```

#### Criação de Registro

```python
# Criar um novo usuário
result = client.create_record(
    table="users",
    schema="public",
    data={
        "name": "John Doe",
        "email": "john@example.com",
        "active": True,
        "metadata": {"preferences": {"theme": "dark", "notifications": True}}
    },
    returning=["id", "name", "email"]
)
print(json.dumps(result, indent=2))
```

#### Atualização de Registros

```python
# Atualizar registros (desativar usuários inativos há mais de 30 dias)
result = client.update_records(
    table="users",
    schema="public",
    filters={"last_active": {"lt": "2023-01-01"}},
    data={"active": False, "deactivated_at": "2023-02-01T00:00:00Z"}
)
print(json.dumps(result, indent=2))
```

#### Exclusão de Registros

```python
# Excluir usuários inativos
result = client.delete_records(
    table="users",
    schema="public",
    filters={"active": False}
)
print(json.dumps(result, indent=2))
```

#### Consulta Personalizada

```python
# Executar uma consulta personalizada
result = client.execute_query(
    query="""
    SELECT 
        p.name as product_name,
        c.name as category_name,
        SUM(o.quantity) as total_sold
    FROM 
        orders o
    JOIN 
        products p ON o.product_id = p.id
    JOIN 
        categories c ON p.category_id = c.id
    WHERE 
        o.created_at >= $1
    GROUP BY 
        p.name, c.name
    ORDER BY 
        total_sold DESC
    LIMIT $2
    """,
    params=["2023-01-01", 10],
    read_only=True
)
print(json.dumps(result, indent=2))
```

#### Operações Transacionais

```python
# Transferência de saldo entre contas (transação)
tx = client.begin_transaction(isolation_level="serializable")
transaction_id = tx["data"]["transaction_id"]

try:
    # Reduz o saldo na conta 1
    client.update_records(
        table="accounts",
        schema="public",
        filters={"id": "acc_123"},
        data={"balance": {"decrement": 100.0}}
    )
    
    # Adiciona saldo na conta 2
    client.update_records(
        table="accounts",
        schema="public",
        filters={"id": "acc_456"},
        data={"balance": {"increment": 100.0}}
    )
    
    # Registra a transação
    client.create_record(
        table="transactions",
        schema="public",
        data={
            "from_account": "acc_123",
            "to_account": "acc_456",
            "amount": 100.0,
            "description": "Transferência"
        }
    )
    
    # Confirma a transação
    client.commit_transaction(transaction_id)
    print("Transferência realizada com sucesso!")
    
except Exception as e:
    # Reverte a transação em caso de erro
    client.rollback_transaction(transaction_id)
    print(f"Erro ao realizar transferência: {e}")
```

### 4. Trabalhando com Tipos Específicos do PostgreSQL

#### Utilizando Arrays

```python
# Criar registro com campo array
result = client.create_record(
    table="products",
    schema="public",
    data={
        "name": "Camiseta Estampada",
        "price": 29.99,
        "sizes": ["P", "M", "G", "GG"],  # Campo array
        "colors": ["Azul", "Preto", "Branco"]  # Campo array
    }
)

# Filtrar por valores em arrays
shirts = client.read_table(
    table="products",
    schema="public",
    filters={
        "sizes": {"contains": ["M", "G"]},  # Produtos que têm tamanhos M e G
        "colors": {"overlap": ["Azul"]}     # Produtos que têm a cor Azul
    }
)
```

#### Utilizando JSONB

```python
# Criar registro com campo JSONB
result = client.create_record(
    table="users",
    schema="public",
    data={
        "name": "Maria Silva",
        "email": "maria@example.com",
        "preferences": {
            "theme": "light",
            "notifications": {
                "email": True,
                "sms": False,
                "push": True
            },
            "favorites": [1, 2, 3]
        }  # Campo JSONB
    }
)

# Filtrar usando campos JSONB
users = client.read_table(
    table="users",
    schema="public",
    filters={
        "preferences->theme": "light",  # Consulta simples de JSONB
        "preferences->notifications->push": True  # Consulta aninhada
    }
)

# Consulta avançada com JSONB usando jsonb_path
users_with_email = client.read_table(
    table="users",
    schema="public",
    filters={
        "preferences": {
            "jsonb_path": "$.notifications.email ? (@ == true)"
        }
    }
)
```

## Exemplos de Implementação

### 1. Criando um Novo Handler

```python
from typing import Dict, Any
from postgres_mcp.handlers.base import HandlerBase
from postgres_mcp.models.request import CustomRequest
from postgres_mcp.models.response import DataResponse, ErrorResponse

class CustomHandler(HandlerBase):
    """Handler personalizado para uma nova ferramenta."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição da ferramenta personalizada.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = CustomRequest(**params)
            
            # Processa a requisição (exemplo)
            result = await self.services.custom_service.process(request)
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=result,
                count=len(result) if isinstance(result, list) else 1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao processar custom_tool: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()
```

### 2. Implementando um Novo Repositório

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from postgres_mcp.repositories.base import RepositoryBase
from postgres_mcp.adapters.client import PostgresClient

class CustomRepository(RepositoryBase):
    """Repositório personalizado para um tipo específico de dados."""
    
    def __init__(self, postgres_client: PostgresClient):
        """
        Inicializa o repositório.
        
        Args:
            postgres_client: Cliente PostgreSQL
        """
        self.client = postgres_client
        self.schema = "public"
        self.table_name = "custom_table"
    
    async def get_by_criteria(
        self, 
        criteria: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca registros por critérios específicos.
        
        Args:
            criteria: Critérios de busca
            limit: Limite de registros
            
        Returns:
            Lista de registros correspondentes
        """
        # Constrói a consulta SQL base
        query = f"""
            SELECT * FROM {self.schema}.{self.table_name}
            WHERE 1=1
        """
        params = []
        param_index = 1
        
        # Adiciona condições com base nos critérios
        for key, value in criteria.items():
            if isinstance(value, dict) and len(value) == 1:
                op, val = next(iter(value.items()))
                if op == ">":
                    query += f" AND {key} > ${param_index}"
                elif op == "<":
                    query += f" AND {key} < ${param_index}"
                elif op == ">=":
                    query += f" AND {key} >= ${param_index}"
                elif op == "<=":
                    query += f" AND {key} <= ${param_index}"
                elif op == "like":
                    query += f" AND {key} LIKE ${param_index}"
                params.append(val)
                param_index += 1
            else:
                query += f" AND {key} = ${param_index}"
                params.append(value)
                param_index += 1
        
        # Adiciona limite se especificado
        if limit:
            query += f" LIMIT ${param_index}"
            params.append(limit)
        
        # Executa a consulta
        records = await self.client.fetch(query, *params)
        
        # Converte para dicionários
        return [dict(record) for record in records]
```

### 3. Implementando Autenticação Avançada

```python
from postgres_mcp.config.settings import Settings
from postgres_mcp.services.security import SecurityService
from postgres_mcp.middleware.auth import JWTAuthMiddleware

# Define as políticas de acesso
policies = {
    "tables": {
        "users": {
            "read": ["admin", "user"],
            "create": ["admin"],
            "update": ["admin"],
            "delete": ["admin"]
        },
        "posts": {
            "read": ["admin", "user"],
            "create": ["admin", "user"],
            "update": ["admin", "user", "post_owner"],
            "delete": ["admin", "post_owner"]
        }
    },
    "schemas": {
        "public": ["admin", "user"],
        "admin": ["admin"],
        "analytics": ["admin", "analyst"]
    }
}

# Configurar middleware de autenticação JWT
jwt_middleware = JWTAuthMiddleware(
    secret_key=os.getenv("JWT_SECRET"),
    algorithm="HS256",
    role_claim="role",
    exclude_paths=["/health"]
)

# Configura o serviço de segurança
security_service = SecurityService(
    # Função para verificar permissões
    permission_checker=lambda user, action, resource: (
        user["role"] in policies["tables"].get(resource, {}).get(action, []) or
        user["role"] in policies["schemas"].get(resource, []) or
        user["id"] == resource.get("owner_id")  # Para regras específicas de propriedade
    ),
    # Configuração de Row-Level Security
    row_level_security=True
)

# Uso no servidor MCP
server = PostgresMCPServer(
    db_host=os.getenv("DB_HOST"),
    db_port=int(os.getenv("DB_PORT", "5432")),
    db_name=os.getenv("DB_NAME"),
    db_user=os.getenv("DB_USER"),
    db_password=os.getenv("DB_PASSWORD"),
    transport="streamable-http",
    security_service=security_service,
    middleware=[jwt_middleware]
)
```

### 4. Implementando Cache

```python
from postgres_mcp.utils.cache import QueryCache
from postgres_mcp.services.query import QueryService
from postgres_mcp.repositories.table import TableRepository

# Configuração do cache
cache = QueryCache(
    max_size=100,  # Máximo de entradas no cache
    ttl=300  # Tempo de vida em segundos (5 minutos)
)

# Uso no serviço de consulta
query_service = QueryService(
    table_repository=TableRepository(...),
    cache=cache
)

# Exemplo de método cached
async def get_cached_data(self, schema, table, filters, columns=None, order_by=None, ascending=True, limit=None, offset=None):
    # Gera uma chave de cache baseada nos parâmetros
    cache_key = f"{schema}:{table}:{hash(str(filters))}:{str(columns)}:{order_by}:{ascending}:{limit}:{offset}"
    
    # Tenta obter do cache
    cached_result = self.cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Se não estiver no cache, busca do repositório
    result = await self.repository.get_records(
        schema=schema,
        table=table,
        filters=filters,
        columns=columns,
        order_by=order_by,
        ascending=ascending,
        limit=limit,
        offset=offset
    )
    
    # Armazena no cache
    self.cache.set(cache_key, result)
    
    return result
```

### 5. Exemplo de Integração com Pool de Conexões

```python
import asyncpg
from postgres_mcp import PostgresMCPServer

async def setup_db_pool():
    # Configura pool de conexões com PostgreSQL
    pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        min_size=5,        # Mínimo de conexões no pool
        max_size=20,       # Máximo de conexões no pool
        command_timeout=60, # Timeout para comandos
        max_inactive_connection_lifetime=300  # Tempo máximo de vida para conexões inativas
    )
    
    # Configuração de inicialização para todas as conexões
    async def init_connection(conn):
        # Configura timezone
        await conn.execute("SET timezone = 'UTC'")
        # Configura outras variáveis de sessão
        await conn.execute("SET application_name = 'postgres_mcp'")
    
    # Substitui o pool existente com nosso pool personalizado
    await pool.execute(init_connection)
    
    return pool

# Inicializa o servidor com pool personalizado
async def start_server():
    # Cria o pool de conexões
    db_pool = await setup_db_pool()
    
    # Inicializa o servidor com o pool
    server = PostgresMCPServer(
        connection_pool=db_pool,
        transport="stdio"
    )
    
    # Inicia o servidor
    await server.start()

# Execução principal
if __name__ == "__main__":
    import asyncio
    asyncio.run(start_server())
```