# Plano de Implementação de Testes de Integração com PostgreSQL

Este documento detalha o plano para implementação de testes de integração para o PostgreSQL MCP, usando um banco de dados PostgreSQL real através do Docker.

## Objetivos

1. Validar o funcionamento real do PostgreSQL MCP com um banco de dados PostgreSQL
2. Testar o comportamento das operações em condições reais
3. Verificar a corretude das consultas SQL geradas
4. Testar o desempenho das operações

## Ferramentas a Serem Utilizadas

- **Docker**: Para iniciar instâncias isoladas de PostgreSQL
- **pytest-asyncio**: Para suporte a testes assíncronos
- **pytest-cov**: Para análise de cobertura de código
- **asyncpg**: Cliente PostgreSQL assíncrono

## Estrutura de Diretórios

```
tests/
├── integration/                   # Testes de integração
│   ├── conftest.py                # Configuração para testes de integração
│   ├── test_crud_operations.py    # Testes de operações CRUD
│   ├── test_transactions.py       # Testes de transações
│   ├── test_filters.py            # Testes do sistema de filtros com DB real
│   ├── test_postgres_features.py  # Testes de recursos específicos do PostgreSQL
│   └── README.md                  # Documentação dos testes de integração
└── fixtures/                      # Dados de teste reutilizáveis
    ├── schemas.sql                # Definições de esquemas para testes
    ├── tables.sql                 # Definições de tabelas para testes
    └── sample_data.sql            # Dados de amostra para testes
```

## Status Atual da Implementação

### 1. Configuração do Ambiente de Teste

- [x] Criar estrutura de diretórios para testes de integração
- [x] Configurar pytest.ini com marcadores para testes de integração
- [x] Implementar conftest.py com fixtures para contêiner Docker PostgreSQL
- [x] Criar script de inicialização do banco de dados de teste

### 2. Testes de Operações CRUD

- [x] Testes de criação de registros (insert)
- [x] Testes de leitura de registros (select)
- [x] Testes de atualização de registros (update)
- [x] Testes de exclusão de registros (delete)
- [x] Testes de operações em lote

### 3. Testes de Transações

- [x] Testes de commit de transações
- [x] Testes de rollback de transações
- [x] Testes de transações aninhadas
- [x] Testes de isolamento de transações

### 4. Testes de Filtros com Banco de Dados Real

- [x] Testes de filtros de comparação
- [x] Testes de filtros de texto
- [x] Testes de filtros de lista
- [x] Testes de filtros para valores nulos
- [x] Testes de filtros para arrays
- [x] Testes de filtros para campos JSONB
- [x] Testes de filtros para tipos geométricos

### 5. Testes de Recursos Específicos do PostgreSQL

- [x] Testes de views (criação, consulta, atualização, exclusão)
- [x] Testes de funções armazenadas (criação, execução, exclusão)
- [x] Testes de triggers
- [x] Testes de CTEs (Common Table Expressions)
- [x] Testes de Window Functions

### 6. Testes de Desempenho

- [ ] Testes de throughput para operações CRUD
- [ ] Testes de latência para consultas complexas
- [ ] Testes de concorrência
- [ ] Testes de carga com volumes grandes de dados

## Problemas Conhecidos e Desafios

Atualmente enfrentamos os seguintes desafios com a implementação dos testes de integração:

1. **Incompatibilidade de Interface**: A implementação atual da classe PostgresMCP não expõe um método `execute_tool` que os testes esperam usar. Estamos trabalhando em um adaptador para solucionar isto.

2. **Inicialização de Serviços**: Existem problemas na inicialização dos serviços quando executados em ambiente de teste, particularmente com o CacheService.

3. **Compatibilidade de Parâmetros**: Incompatibilidade entre os parâmetros esperados pela classe PostgresMCP e aqueles fornecidos pelos testes, especialmente o parâmetro 'mode'.

## Estratégia para Resolver Problemas

1. Implementar uma classe adaptadora PostgresMCPTestClient que encapsula a classe PostgresMCP e expõe a interface necessária para os testes
2. Modificar a inicialização de serviços para funcionar corretamente em ambiente de teste
3. Atualizar a documentação de testes com instruções detalhadas sobre como executar os testes

## Implementação Atual do Docker Container

```python
import pytest
import asyncio
import uuid
import time
import docker
import asyncpg

@pytest.fixture(scope="session")
async def postgres_container():
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
    
    # Retorna um objeto com as informações necessárias
    container_info = {
        "container": container,
        "connection_url": conn_url
    }
    
    yield container_info
    
    # Limpeza
    container.stop()
```

## Próximos Passos

1. **Corrigir Problemas de Interface**: Finalizar a implementação da classe adaptadora para PostgresMCP
2. **Revisar Inicialização de Serviços**: Identificar e corrigir problemas na inicialização de serviços
3. **Implementar Testes de Desempenho**: Uma vez que os testes básicos funcionem corretamente
4. **Integrar com CI/CD**: Automatizar a execução de testes de integração no pipeline CI/CD

## Cronograma Atualizado

1. **Sprint 1**: Resolver problemas de compatibilidade e interface (em andamento)
2. **Sprint 2**: Implementação de testes de desempenho
3. **Sprint 3**: Integração com CI/CD e documentação final

## Considerações de CI/CD

Para execução em ambientes de CI/CD, considerar:
- Configurar workflow específico para testes de integração
- Usar caching para imagens Docker
- Executar testes de integração após testes unitários bem-sucedidos
- Configurar timeouts adequados para testes de desempenho 