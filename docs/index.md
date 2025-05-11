# PostgreSQL MCP - Documentação

Bem-vindo à documentação oficial do PostgreSQL MCP, uma implementação do Model Context Protocol para PostgreSQL que permite a Modelos de Linguagem Grandes (LLMs) interagir diretamente com bancos de dados PostgreSQL.

## Visão Geral

O PostgreSQL MCP funciona como uma ponte entre LLMs e bancos de dados PostgreSQL, oferecendo uma API padronizada para consultas, mutações e análises de dados. Utilizando o Model Context Protocol (MCP), o projeto permite que modelos de linguagem executem operações complexas em bancos de dados sem a necessidade de código intermediário extensivo.

## Status do Projeto

**Versão atual: 0.1.0 (99% completo)**

Todas as funcionalidades principais foram implementadas e testadas, incluindo:
- CRUD completo
- Sistema de filtros avançado 
- Gerenciamento de transações
- Suporte a múltiplos schemas
- Operações para views e funções armazenadas
- Suporte a tipos de dados avançados

## Documentação Disponível

### Guias de Uso
- [Guia de Início Rápido](guides/quickstart.md)
- [Configuração e Conexão](guides/configuration.md)
- [Operações CRUD](guides/crud.md)
- [Filtros e Consultas](guides/filters.md)
- [Transações](guides/transactions.md)
- [Views e Funções](guides/views_functions.md)

### Referência de API
- [API Completa](API_REFERENCE.md)
- [Objetos e Tipos](api/types.md)
- [Parâmetros de Requisição](api/request_parameters.md)
- [Respostas e Códigos de Erro](api/responses.md)

### Desenvolvimento e Contribuição
- [Arquitetura](ARCHITECTURE.md)
- [Guia de Contribuição](../CONTRIBUTING.md)
- [Exemplos de Código](CODE_EXAMPLES.md)

## Funcionalidades Principais

### Core
- **Conexão PostgreSQL**: Conexão robusta com pool gerenciado
- **Operações CRUD**: Suporte completo para criar, ler, atualizar e excluir dados
- **Consultas Flexíveis**: Sistema avançado de filtragem, ordenação e projeção
- **Transações**: Suporte a transações ACID completas
- **Segurança**: Proteção contra injeção SQL e validação de entrada

### PostgreSQL Avançado
- **Tipos de Dados**: Suporte a tipos avançados como arrays, JSON/JSONB e geométricos
- **Views**: Gerenciamento completo de views (normais e materializadas)
- **Funções e Procedimentos**: Suporte completo a funções e procedimentos armazenados
- **Múltiplos Schemas**: Trabalho com múltiplos schemas em um único banco de dados

### Performance e Monitoramento
- **Cache**: Sistema de cache para otimização de consultas frequentes
- **Métricas**: Monitoramento detalhado de desempenho e uso
- **Pool de Conexões**: Gerenciamento eficiente de conexões

## Testes e Qualidade

O projeto inclui uma suíte abrangente de testes:

- **Testes Unitários**: Cobertura completa para serviços e handlers
- **Testes de Filtros**: Validação de todos os modelos de filtro e conversão para SQL
- **Testes do QueryBuilder**: Verificação da geração correta de consultas SQL com filtros complexos
- **Testes de Serialização/Deserialização**: Validação da comunicação via MCP
- **Testes de Integração**: Testes com banco de dados PostgreSQL real usando Docker

### Testes de Integração

Os testes de integração estão implementados e utilizam contêineres Docker para executar instâncias isoladas do PostgreSQL. Eles abrangem:
- Operações CRUD completas
- Transações (commit, rollback, isolamento)
- Sistema de filtros com dados reais
- Recursos específicos do PostgreSQL (views, funções, CTEs)

No entanto, os testes de integração atualmente enfrentam alguns desafios técnicos, incluindo:
- Incompatibilidades de interface com a implementação atual do PostgresMCP
- Problemas na inicialização de serviços em ambiente de teste

Estamos trabalhando para resolver essas limitações. Para mais detalhes, consulte o arquivo [INTEGRATION_TESTS_PLAN.md](../INTEGRATION_TESTS_PLAN.md).

Além disso, o projeto segue boas práticas de desenvolvimento:
- Docstrings completas em todas as funções e classes
- Tipagem estática com mypy
- Validação de dados com Pydantic

## Começando

Para começar a usar o PostgreSQL MCP, consulte o [Guia de Início Rápido](guides/quickstart.md) ou siga estes passos básicos:

```python
from postgres_mcp import run_postgres_mcp
import asyncio

async def main():
    await run_postgres_mcp(
        connection_string="postgresql://user:password@localhost:5432/database",
        mode="http",
        port=8000
    )

asyncio.run(main())
```

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- asyncpg
- pydantic
- fastmcp

## Licença

Este projeto é licenciado sob a [Licença MIT](../LICENSE).