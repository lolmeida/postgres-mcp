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

## Exemplos de Tipos Geométricos

Os exemplos a seguir demonstram como utilizar tipos geométricos do PostgreSQL através do PostgreSQL MCP.

### Exemplo 1: Buscar Restaurantes Próximos

```python
import asyncio
import json
from postgres_mcp.client import PostgresMCPClient

async def find_nearby_restaurants():
    # Inicializar o cliente
    client = PostgresMCPClient(url="http://localhost:8000")
    
    # Coordenadas do usuário
    user_location = "(37.7749,-122.4194)"  # San Francisco
    max_distance = 2.0  # km
    
    # Buscar restaurantes próximos
    response = await client.run_tool(
        tool="read_table",
        parameters={
            "table": "restaurants",
            "filters": {
                "location": {
                    "near": f"{user_location},{max_distance}"
                }
            },
            "columns": ["id", "name", "cuisine", "rating"],
            "limit": 10
        }
    )
    
    # Processar resultados
    restaurants = json.loads(response)["results"]
    print(f"Encontrados {len(restaurants)} restaurantes próximos:")
    
    for restaurant in restaurants:
        print(f"- {restaurant['name']} ({restaurant['cuisine']}) - {restaurant['rating']}/5 estrelas")
    
    return restaurants

# Executar a função
asyncio.run(find_nearby_restaurants())
```

### Exemplo 2: Verificar Imóveis em Área de Interesse

```python
import asyncio
import json
from postgres_mcp.client import PostgresMCPClient

async def find_properties_in_area():
    # Inicializar o cliente
    client = PostgresMCPClient(url="http://localhost:8000")
    
    # Definir polígono da área de interesse
    # Formato: ((x1,y1),(x2,y2),...,(xn,yn))
    area_of_interest = "((37.78,-122.42),(37.78,-122.40),(37.76,-122.40),(37.76,-122.42),(37.78,-122.42))"
    
    # Buscar imóveis dentro da área
    response = await client.run_tool(
        tool="read_table",
        parameters={
            "table": "properties",
            "filters": {
                "location": {
                    "within": area_of_interest
                },
                "price": {
                    "lte": 1000000
                },
                "bedrooms": {
                    "gte": 2
                }
            },
            "columns": ["id", "address", "price", "bedrooms", "bathrooms"],
            "order_by": "price",
            "ascending": True
        }
    )
    
    # Processar resultados
    properties = json.loads(response)["results"]
    print(f"Encontrados {len(properties)} imóveis na área de interesse:")
    
    for property in properties:
        print(f"- {property['address']}: ${property['price']:,} - {property['bedrooms']} quartos, {property['bathrooms']} banheiros")
    
    return properties

# Executar a função
asyncio.run(find_properties_in_area())
```

### Exemplo 3: Verificar Sobreposição de Rotas

```python
import asyncio
import json
from postgres_mcp.client import PostgresMCPClient

async def find_intersecting_routes():
    # Inicializar o cliente
    client = PostgresMCPClient(url="http://localhost:8000")
    
    # Definir uma rota de referência (polígono representando um corredor)
    reference_route = "((37.78,-122.42),(37.78,-122.40),(37.775,-122.40),(37.775,-122.42),(37.78,-122.42))"
    
    # Buscar rotas que se cruzam com a rota de referência
    response = await client.run_tool(
        tool="read_table",
        parameters={
            "table": "routes",
            "filters": {
                "path": {
                    "intersects": reference_route
                },
                "is_active": True
            },
            "columns": ["id", "name", "type", "distance"]
        }
    )
    
    # Processar resultados
    routes = json.loads(response)["results"]
    print(f"Encontradas {len(routes)} rotas que cruzam a rota de referência:")
    
    for route in routes:
        print(f"- {route['name']} ({route['type']}): {route['distance']} km")
    
    return routes

# Executar a função
asyncio.run(find_intersecting_routes())
```

### Exemplo 4: Criando Dados com Tipos Geométricos

```python
import asyncio
import json
from postgres_mcp.client import PostgresMCPClient

async def create_park_data():
    # Inicializar o cliente
    client = PostgresMCPClient(url="http://localhost:8000")
    
    # Criar um novo parque com dados geométricos
    response = await client.run_tool(
        tool="create_record",
        parameters={
            "table": "parks",
            "data": {
                "name": "Golden Gate Park",
                "center_point": "(37.7694,-122.4862)",  # Ponto central
                "boundary": "((37.7759,-122.5108),(37.7759,-122.4577),(37.7629,-122.4577),(37.7629,-122.5108),(37.7759,-122.5108))",  # Perímetro aproximado
                "area_sqkm": 4.1,
                "has_playground": True,
                "has_dogpark": True
            }
        }
    )
    
    # Verificar resposta
    result = json.loads(response)
    if "error" in result:
        print(f"Erro ao criar parque: {result['error']}")
    else:
        print(f"Parque criado com sucesso! ID: {result.get('id')}")
    
    return result

# Executar a função
asyncio.run(create_park_data())
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

## Cache

### Obter Estatísticas do Cache

```python
import requests

def get_cache_stats(base_url="http://localhost:8000"):
    """
    Obtém estatísticas de uso do cache.
    """
    response = requests.post(
        base_url,
        json={"tool": "get_cache_stats"}
    )
    return response.json()

# Exemplo de uso
stats = get_cache_stats()
print(f"Taxa de acerto do cache: {stats['data']['hit_ratio']}")
print(f"Total de acertos: {stats['data']['hits']}")
print(f"Total de falhas: {stats['data']['misses']}")
```

### Limpar Cache

```python
import requests

def clear_cache(base_url="http://localhost:8000", scope="all", table=None, schema="public"):
    """
    Limpa o cache do sistema.
    
    Args:
        base_url: URL base do servidor MCP
        scope: Escopo da limpeza ('all', 'table', 'schema')
        table: Nome da tabela (obrigatório quando scope='table')
        schema: Nome do schema (obrigatório quando scope='schema')
    """
    params = {"scope": scope}
    
    if scope == "table":
        params["table"] = table
        params["schema"] = schema
    elif scope == "schema":
        params["schema"] = schema
        
    response = requests.post(
        base_url,
        json={
            "tool": "clear_cache",
            "parameters": params
        }
    )
    return response.json()

# Exemplo: limpar cache de uma tabela específica
result = clear_cache(scope="table", table="users", schema="public")
print(result['data']['message'])

# Exemplo: limpar todo o cache
result = clear_cache()
print(result['data']['message'])
```

## Métricas e Monitoramento

### Obter Métricas de Desempenho

```python
import requests

def get_metrics(base_url="http://localhost:8000", metric_type=None, operation=None, window_seconds=60):
    """
    Obtém métricas de desempenho do sistema.
    
    Args:
        base_url: URL base do servidor MCP
        metric_type: Tipo específico de métrica ('execution_times', 'errors', 'resource_usage', 'operations_per_second')
        operation: Nome da operação para filtrar (quando metric_type='execution_times')
        window_seconds: Janela de tempo em segundos (quando metric_type='operations_per_second')
    """
    params = {}
    
    if metric_type:
        params["metric_type"] = metric_type
        
        if metric_type == "execution_times" and operation:
            params["operation"] = operation
        elif metric_type == "operations_per_second":
            params["window_seconds"] = window_seconds
    
    response = requests.post(
        base_url,
        json={
            "tool": "get_metrics",
            "parameters": params
        }
    )
    return response.json()

# Exemplo: obter todas as métricas
all_metrics = get_metrics()
print(f"Tempo total de atividade: {all_metrics['data']['uptime_seconds']} segundos")
print(f"Total de operações: {all_metrics['data']['total_operations']}")
print(f"Taxa de erro: {all_metrics['data']['error_rate']:.2%}")

# Exemplo: obter apenas métricas de tempo de execução
exec_times = get_metrics(metric_type="execution_times")
for op, stats in exec_times['data'].items():
    print(f"{op}: min={stats['min']:.3f}s, avg={stats['avg']:.3f}s, max={stats['max']:.3f}s")

# Exemplo: obter uso de recursos
resources = get_metrics(metric_type="resource_usage")
if 'cpu_usage' in resources['data']:
    cpu = resources['data']['cpu_usage']
    print(f"CPU: atual={cpu['current']}%, média={cpu['avg']}%, máximo={cpu['max']}%")
```

### Resetar Métricas

```python
import requests

def reset_metrics(base_url="http://localhost:8000"):
    """
    Reseta todas as métricas de desempenho coletadas.
    """
    response = requests.post(
        base_url,
        json={"tool": "reset_metrics"}
    )
    return response.json()

# Exemplo de uso
result = reset_metrics()
print(result['data']['message'])
```

## Operações com Views

Exemplos de como trabalhar com views PostgreSQL usando o PostgreSQL MCP.

### Listar Views

```python
import requests

def list_views(base_url="http://localhost:8000", schema="public", include_materialized=True):
    """
    Lista todas as views em um schema.
    
    Args:
        base_url: URL base do servidor MCP
        schema: Nome do schema
        include_materialized: Se deve incluir views materializadas
    """
    response = requests.post(
        base_url,
        json={
            "tool": "list_views",
            "parameters": {
                "schema": schema,
                "include_materialized": include_materialized
            }
        }
    )
    return response.json()

# Exemplo: listar todas as views no schema 'public'
views = list_views()
print(f"Views encontradas: {views['data']}")

# Exemplo: listar apenas views normais (não materializadas) no schema 'analytics'
views = list_views(schema="analytics", include_materialized=False)
print(f"Views normais encontradas: {views['data']}")
```

### Descrever View

```python
import requests

def describe_view(base_url="http://localhost:8000", view="active_users", schema="public"):
    """
    Obtém informações detalhadas sobre uma view.
    
    Args:
        base_url: URL base do servidor MCP
        view: Nome da view
        schema: Nome do schema
    """
    response = requests.post(
        base_url,
        json={
            "tool": "describe_view",
            "parameters": {
                "view": view,
                "schema": schema
            }
        }
    )
    return response.json()

# Exemplo: descrever uma view
view_info = describe_view(view="customer_orders")
print(f"Nome: {view_info['data']['name']}")
print(f"Schema: {view_info['data']['schema']}")
print(f"Definição: {view_info['data']['definition']}")
print(f"Materializada: {view_info['data']['is_materialized']}")
print(f"Colunas:")
for column in view_info['data']['columns']:
    print(f"  - {column['name']} ({column['data_type']})")
```

### Ler Dados de uma View

```python
import requests

def read_view(base_url="http://localhost:8000", view="sales_summary", schema="public", 
              filters=None, columns=None, order_by=None, ascending=True, limit=None, offset=None):
    """
    Lê registros de uma view.
    
    Args:
        base_url: URL base do servidor MCP
        view: Nome da view
        schema: Nome do schema
        filters: Filtros para a consulta
        columns: Colunas específicas a retornar
        order_by: Coluna para ordenação
        ascending: Direção da ordenação
        limit: Limite de registros a retornar
        offset: Número de registros a pular
    """
    params = {
        "view": view,
        "schema": schema
    }
    
    if filters:
        params["filters"] = filters
    
    if columns:
        params["columns"] = columns
    
    if order_by:
        params["order_by"] = order_by
        params["ascending"] = ascending
    
    if limit:
        params["limit"] = limit
        
    if offset:
        params["offset"] = offset
    
    response = requests.post(
        base_url,
        json={
            "tool": "read_view",
            "parameters": params
        }
    )
    return response.json()

# Exemplo: leitura simples de uma view
results = read_view(view="active_users")
print(f"Total de usuários ativos: {results['count']}")
for user in results['data']:
    print(f"ID: {user['id']}, Nome: {user['name']}, Email: {user['email']}")

# Exemplo: leitura com filtros e paginação
results = read_view(
    view="order_summary",
    schema="reporting",
    filters={
        "order_date": {"gte": "2023-01-01"},
        "total_amount": {"gt": 1000}
    },
    columns=["order_id", "customer_name", "total_amount", "order_date"],
    order_by="total_amount",
    ascending=False,
    limit=10
)
print(f"Pedidos de alto valor: {results['count']}")
for order in results['data']:
    print(f"Pedido #{order['order_id']}: {order['customer_name']} - R$ {order['total_amount']:.2f}")
```

### Criar View

```python
import requests

def create_view(base_url="http://localhost:8000", view="active_users", definition=None, 
               schema="public", is_materialized=False, replace=False):
    """
    Cria ou atualiza uma view.
    
    Args:
        base_url: URL base do servidor MCP
        view: Nome da view
        definition: Definição SQL da view
        schema: Nome do schema
        is_materialized: Se é uma view materializada
        replace: Se deve substituir caso já exista
    """
    response = requests.post(
        base_url,
        json={
            "tool": "create_view",
            "parameters": {
                "view": view,
                "schema": schema,
                "definition": definition,
                "is_materialized": is_materialized,
                "replace": replace
            }
        }
    )
    return response.json()

# Exemplo: criar uma view simples
result = create_view(
    view="active_users",
    definition="SELECT id, name, email FROM users WHERE active = true"
)
print(f"View criada: {result['data']['name']}")

# Exemplo: criar uma view materializada
result = create_view(
    view="monthly_revenue",
    schema="analytics",
    definition="""
        SELECT 
            DATE_TRUNC('month', order_date) as month,
            SUM(amount) as revenue
        FROM orders
        GROUP BY DATE_TRUNC('month', order_date)
    """,
    is_materialized=True,
    replace=True
)
print(f"View materializada criada: {result['data']['name']}")
```

### Atualizar View Materializada

```python
import requests

def refresh_materialized_view(base_url="http://localhost:8000", view="daily_stats", 
                             schema="public", concurrently=False):
    """
    Atualiza uma view materializada.
    
    Args:
        base_url: URL base do servidor MCP
        view: Nome da view materializada
        schema: Nome do schema
        concurrently: Se deve atualizar concorrentemente (sem bloquear leituras)
    """
    response = requests.post(
        base_url,
        json={
            "tool": "refresh_materialized_view",
            "parameters": {
                "view": view,
                "schema": schema,
                "concurrently": concurrently
            }
        }
    )
    return response.json()

# Exemplo: atualizar uma view materializada
result = refresh_materialized_view(view="sales_summary")
if result['data']['success']:
    print("View materializada atualizada com sucesso!")
else:
    print("Erro ao atualizar view materializada.")

# Exemplo: atualizar concorrentemente (sem bloquear leituras)
result = refresh_materialized_view(
    view="customer_stats",
    schema="analytics",
    concurrently=True
)
print(result['data']['message'] if 'message' in result['data'] else "Atualização concorrente completada.")
```

### Excluir View

```python
import requests

def drop_view(base_url="http://localhost:8000", view="temp_view", 
             schema="public", if_exists=False, cascade=False):
    """
    Exclui uma view.
    
    Args:
        base_url: URL base do servidor MCP
        view: Nome da view
        schema: Nome do schema
        if_exists: Se deve ignorar caso não exista
        cascade: Se deve excluir objetos dependentes
    """
    response = requests.post(
        base_url,
        json={
            "tool": "drop_view",
            "parameters": {
                "view": view,
                "schema": schema,
                "if_exists": if_exists,
                "cascade": cascade
            }
        }
    )
    return response.json()

# Exemplo: excluir uma view
result = drop_view(view="old_report")
if result['data']['success']:
    print("View excluída com sucesso!")
else:
    print("Erro ao excluir view.")

# Exemplo: excluir uma view com dependências, ignorando se não existir
result = drop_view(
    view="temp_analysis",
    schema="analytics",
    if_exists=True,
    cascade=True
)
print(result['data']['message'] if 'message' in result['data'] else "View excluída com sucesso.")
```

## Exemplos de Uso de Views

### Listando Views

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def list_views_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Listar todas as views no schema public
    result = await mcp.execute("list_views", {"schema": "public"})
    print("Views:", result["data"])
    
    # Listar apenas views materializadas
    result = await mcp.execute("list_views", {
        "schema": "public",
        "only_materialized": True
    })
    print("Views materializadas:", result["data"])
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(list_views_example())
```

### Descrevendo uma View

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def describe_view_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Descrever uma view específica
    result = await mcp.execute("describe_view", {
        "view": "product_summary",
        "schema": "public"
    })
    
    view_info = result["data"]
    print(f"Nome: {view_info['name']}")
    print(f"Schema: {view_info['schema']}")
    print(f"Materializada: {view_info['is_materialized']}")
    print(f"Definição: {view_info['definition']}")
    print("Colunas:")
    for column in view_info["columns"]:
        print(f"  - {column['name']} ({column['data_type']})")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(describe_view_example())
```

### Criando uma View

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def create_view_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Criar uma view simples
    result = await mcp.execute("create_view", {
        "view": "customer_orders",
        "query": """
            SELECT c.customer_id, c.name, COUNT(o.order_id) as total_orders, SUM(o.amount) as total_spent
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.name
        """,
        "replace": True
    })
    
    print(f"View criada: {result['success']}")
    
    # Criar uma view materializada
    result = await mcp.execute("create_view", {
        "view": "product_stats",
        "query": """
            SELECT p.product_id, p.name, p.category, 
                   COUNT(oi.order_id) as order_count,
                   SUM(oi.quantity) as total_sold
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id, p.name, p.category
        """,
        "materialized": True,
        "with_data": True
    })
    
    print(f"View materializada criada: {result['success']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(create_view_example())
```

### Atualizando uma View Materializada

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def refresh_view_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Atualizar uma view materializada
    result = await mcp.execute("refresh_view", {
        "view": "product_stats",
        "schema": "public",
        "concurrently": True
    })
    
    print(f"View atualizada: {result['success']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(refresh_view_example())
```

### Excluindo uma View

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def drop_view_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Excluir uma view
    result = await mcp.execute("drop_view", {
        "view": "customer_orders",
        "schema": "public",
        "if_exists": True,
        "cascade": False
    })
    
    print(f"View excluída: {result['success']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(drop_view_example())
```

## Exemplos de Uso de Funções e Procedimentos

### Listando Funções

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def list_functions_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Listar todas as funções no schema public
    result = await mcp.execute("list_functions", {"schema": "public"})
    print("Funções:", result["data"])
    
    # Listar apenas funções (sem procedimentos)
    result = await mcp.execute("list_functions", {
        "schema": "public",
        "include_procedures": False
    })
    print("Funções (sem procedimentos):", result["data"])
    
    # Listar sem funções de agregação
    result = await mcp.execute("list_functions", {
        "schema": "public",
        "include_aggregates": False
    })
    print("Funções (sem agregação):", result["data"])
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(list_functions_example())
```

### Descrevendo uma Função

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def describe_function_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Descrever uma função específica
    result = await mcp.execute("describe_function", {
        "function": "calculate_discount",
        "schema": "public"
    })
    
    func_info = result["data"]
    print(f"Nome: {func_info['name']}")
    print(f"Schema: {func_info['schema']}")
    print(f"Tipo de retorno: {func_info['return_type']}")
    print(f"Linguagem: {func_info['language']}")
    print(f"É procedimento: {func_info['is_procedure']}")
    
    print("Argumentos:")
    for i, arg_type in enumerate(func_info["argument_types"]):
        arg_name = func_info["argument_names"][i] if i < len(func_info["argument_names"]) else f"arg{i+1}"
        arg_default = func_info["argument_defaults"][i] if i < len(func_info["argument_defaults"]) else "sem padrão"
        print(f"  - {arg_name} ({arg_type}), padrão: {arg_default}")
    
    print(f"Definição:\n{func_info['definition']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(describe_function_example())
```

### Criando uma Função

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def create_function_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Criar uma função simples
    result = await mcp.execute("create_function", {
        "function": "calculate_discount",
        "schema": "public",
        "return_type": "numeric",
        "argument_definitions": [
            {"name": "price", "type": "numeric"},
            {"name": "discount_percent", "type": "numeric", "default": "10"}
        ],
        "definition": """
            BEGIN
                RETURN price - (price * discount_percent / 100);
            END;
        """,
        "language": "plpgsql",
        "replace": True,
        "volatility": "immutable"
    })
    
    print(f"Função criada: {result['success']}")
    
    # Criar um procedimento
    result = await mcp.execute("create_function", {
        "function": "update_product_price",
        "schema": "public",
        "return_type": "void",
        "argument_definitions": [
            {"name": "product_id_param", "type": "integer"},
            {"name": "new_price", "type": "numeric"}
        ],
        "definition": """
            BEGIN
                UPDATE products SET price = new_price WHERE product_id = product_id_param;
            END;
        """,
        "language": "plpgsql",
        "is_procedure": True,
        "replace": True
    })
    
    print(f"Procedimento criado: {result['success']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(create_function_example())
```

### Executando uma Função

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def execute_function_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Executar uma função com argumentos posicionais
    result = await mcp.execute("execute_function", {
        "function": "calculate_discount",
        "schema": "public",
        "args": [100.00, 20]
    })
    
    print(f"Resultado da função com argumentos posicionais: {result['data']}")
    
    # Executar uma função com argumentos nomeados
    result = await mcp.execute("execute_function", {
        "function": "calculate_discount",
        "schema": "public",
        "named_args": {
            "price": 200.00,
            "discount_percent": 15
        }
    })
    
    print(f"Resultado da função com argumentos nomeados: {result['data']}")
    
    # Executar um procedimento
    result = await mcp.execute("execute_function", {
        "function": "update_product_price",
        "schema": "public",
        "args": [1, 29.99]
    })
    
    print(f"Procedimento executado: {result['success']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(execute_function_example())
```

### Excluindo uma Função

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def drop_function_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Excluir uma função
    result = await mcp.execute("drop_function", {
        "function": "calculate_discount",
        "schema": "public",
        "if_exists": True,
        "cascade": False,
        "arg_types": ["numeric", "numeric"]  # Importante para diferenciar funções com mesmo nome
    })
    
    print(f"Função excluída: {result['success']}")
    
    # Excluir um procedimento
    result = await mcp.execute("drop_function", {
        "function": "update_product_price",
        "schema": "public",
        "if_exists": True
    })
    
    print(f"Procedimento excluído: {result['success']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(drop_function_example())
```

## Exemplo de Uso Combinado

### Criando e Utilizando uma Função em uma Consulta

```python
import asyncio
from postgres_mcp.server import PostgresMCP

async def combined_example():
    # Inicializar o cliente MCP
    mcp = PostgresMCP(host="localhost", port=5432, username="postgres", 
                      password="postgres", database="testdb")
    await mcp.connect()
    
    # Criar uma função para cálculo de desconto
    await mcp.execute("create_function", {
        "function": "calculate_discount",
        "schema": "public",
        "return_type": "numeric",
        "argument_definitions": [
            {"name": "price", "type": "numeric"},
            {"name": "discount_percent", "type": "numeric", "default": "10"}
        ],
        "definition": """
            BEGIN
                RETURN price - (price * discount_percent / 100);
            END;
        """,
        "language": "plpgsql",
        "replace": True,
        "volatility": "immutable"
    })
    
    # Criar uma view que utiliza a função
    await mcp.execute("create_view", {
        "view": "discounted_products",
        "query": """
            SELECT 
                product_id, 
                name, 
                price, 
                calculate_discount(price, 15) as discounted_price
            FROM 
                products
        """,
        "replace": True
    })
    
    # Consultar a view
    result = await mcp.execute("query", {
        "query": "SELECT * FROM discounted_products WHERE price > $1",
        "params": [50.00]
    })
    
    print("Produtos com desconto:")
    for product in result["data"]:
        print(f"  - {product['name']}: ${product['price']} -> ${product['discounted_price']}")
    
    await mcp.disconnect()

# Executar o exemplo
asyncio.run(combined_example())
```