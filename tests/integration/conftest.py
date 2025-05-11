"""
Configuração para testes de integração com PostgreSQL utilizando Docker diretamente.
"""
import os
import asyncio
import uuid
import time
import pytest
import asyncpg
import docker

# Marca todos os testes neste diretório como testes de integração
pytestmark = pytest.mark.integration

@pytest.fixture(scope="session")
def event_loop():
    """Sobrescreve o fixture event_loop padrão do pytest-asyncio para ter escopo de sessão."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def postgres_container(event_loop):
    """Inicializa um contêiner PostgreSQL para testes usando Docker diretamente."""
    client = docker.from_env()
    
    # Cria um container com nome único para evitar conflitos
    container_name = f"postgres-test-{uuid.uuid4().hex[:8]}"
    
    # Configurações do PostgreSQL
    pg_user = "postgres"
    pg_password = "postgres"
    pg_db = "test_db"
    pg_port = 5432
    host_port = 15432  # Porta no host
    
    # Inicia o container
    container = client.containers.run(
        "postgres:15.3",
        name=container_name,
        environment={
            "POSTGRES_USER": pg_user,
            "POSTGRES_PASSWORD": pg_password,
            "POSTGRES_DB": pg_db
        },
        ports={'5432/tcp': host_port},
        detach=True,
        remove=True
    )
    
    # Espera o container iniciar
    time.sleep(3)
    
    # Connection string para asyncpg
    conn_url = f"postgresql://{pg_user}:{pg_password}@localhost:{host_port}/{pg_db}"
    
    # Esperar até que o banco de dados esteja pronto
    retries = 10
    while retries > 0:
        try:
            conn = await asyncpg.connect(conn_url)
            await conn.close()
            break
        except Exception:
            retries -= 1
            await asyncio.sleep(1)
    
    if retries == 0:
        raise Exception("Não foi possível conectar ao banco de dados PostgreSQL")
    
    # Configuração do banco de dados
    conn = await asyncpg.connect(conn_url)
    
    # Executar scripts de inicialização
    fixtures_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")
    
    async def execute_sql_file(filename):
        file_path = os.path.join(fixtures_dir, filename)
        with open(file_path, "r") as f:
            sql = f.read()
            await conn.execute(sql)
    
    await execute_sql_file("schemas.sql")
    await execute_sql_file("tables.sql")
    await execute_sql_file("sample_data.sql")
    
    await conn.close()
    
    # Retorna um objeto com as informações necessárias
    container_info = {
        "container": container,
        "connection_url": conn_url
    }
    
    yield container_info
    
    # Limpeza
    container.stop()

@pytest.fixture
async def postgres_connection(postgres_container):
    """Fornece uma conexão ao banco de dados PostgreSQL de teste."""
    conn = await asyncpg.connect(postgres_container["connection_url"])
    yield conn
    await conn.close()

class PostgresMCPTestClient:
    """Classe adaptadora para PostgresMCP que facilita o uso em testes."""
    
    def __init__(self, mcp_instance):
        """Inicializa o cliente de teste com uma instância PostgresMCP."""
        self.mcp = mcp_instance
    
    async def execute_tool(self, tool: str, parameters: dict):
        """
        Executa uma ferramenta MCP.
        
        Args:
            tool: Nome da ferramenta a ser executada
            parameters: Parâmetros para a ferramenta
            
        Returns:
            Resultado da execução da ferramenta
        """
        # Como não temos acesso direto ao método de roteamento,
        # vamos criar uma requisição simulada e usar o roteador
        # para executar a ferramenta
        request = {
            "tool": tool,
            "parameters": parameters
        }
        
        # Usar o roteador para executar a ferramenta
        return await self.mcp.router.route(request)

@pytest.fixture
async def mcp_client(postgres_container):
    """Configura e fornece um cliente PostgreSQL MCP."""
    from postgres_mcp import PostgresMCP
    
    # Extrair informações da URL de conexão
    conn_url = postgres_container["connection_url"]
    # postgresql://user:password@host:port/dbname
    user_pass, host_port_db = conn_url.split('@')
    protocol, user_pass = user_pass.split('://')
    user, password = user_pass.split(':')
    host_port, db_name = host_port_db.split('/')
    host, port = host_port.split(':')
    
    # Inicializar PostgresMCP com os parâmetros corretos
    mcp = PostgresMCP(
        db_host=host,
        db_port=int(port),
        db_name=db_name,
        db_user=user,
        db_password=password,
        mode="stdio",  # Valor válido para MCPMode
        test_mode=True  # Usar modo de teste para evitar tentativas de conexão adicionais
    )
    
    # Inicializar os componentes do MCP que seriam inicializados com start()
    # mas sem iniciar o servidor
    await mcp._initialize_repository()
    mcp._initialize_services()
    mcp._initialize_handlers()
    
    # Criar e retornar um cliente adaptador
    test_client = PostgresMCPTestClient(mcp)
    yield test_client
    
    # Cleanup
    await mcp.repository.close() 