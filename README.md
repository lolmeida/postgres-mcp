# PostgreSQL MCP

PostgreSQL MCP é uma implementação do Model Context Protocol (MCP) para permitir que Modelos de Linguagem Grandes (LLMs) interajam diretamente com bancos de dados PostgreSQL.

## Status do Projeto

Status atual: **Versão 0.1.0** (99% concluído)

O PostgreSQL MCP implementou todas as funcionalidades principais, incluindo:
- Operações CRUD completas (criar, ler, atualizar, excluir)
- Sistema de filtros avançado
- Gerenciamento de transações
- Compatibilidade com múltiplos schemas
- Modos de transporte STDIO e HTTP
- Sistema de cache para otimização de consultas
- Sistema de métricas para monitoramento de desempenho
- Suporte avançado para tipos de dados PostgreSQL específicos:
  - Arrays
  - JSON/JSONB
  - Tipos geométricos (point, line, box, polygon)
- Gerenciamento completo de views:
  - Listagem e descrição de views
  - Criação de views normais e materializadas
  - Atualização de views materializadas
  - Acesso a dados via views
- Funções e Procedimentos:
  - Listagem, descrição, criação, execução e exclusão

Testes implementados:
- Testes unitários para serviços e handlers
- Testes abrangentes para o sistema de filtros
- Testes para o QueryBuilder com suporte a múltiplos operadores
- Testes para serialização/deserialização MCP

Próximos desenvolvimentos:
- Testes de integração com Testcontainers
- Testes end-to-end para operações completas
- Otimizações adicionais de desempenho
- Documentação expandida de deployment

## Sobre o Projeto

PostgreSQL MCP permite que LLMs realizem operações complexas em bancos de dados PostgreSQL através de um conjunto de comandos padronizados. Isso inclui consultas, mutações e análises de dados, tudo através de uma interface unificada.

### Recursos Principais

- 🔍 **Consultas Flexíveis**: Filtros avançados, ordenação e projeção de colunas
- 🛠️ **Operações Completas de CRUD**: Criação, leitura, atualização e exclusão
- 🔄 **Transações**: Suporte completo a transações, garantindo integridade dos dados
- 📊 **Análise de Esquema**: Descoberta automática de tabelas, colunas e tipos de dados
- 🔐 **Segurança**: Proteção contra injeção SQL e validação de entrada
- 🚀 **Performance**: Cache otimizado e pool de conexões eficiente
- 📏 **Métricas**: Monitoramento de performance e uso de recursos

## Instalação

### Via pip

```bash
pip install postgres-mcp
```

### Via requirements.txt

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/postgres-mcp.git
cd postgres-mcp

# Instale as dependências
pip install -r requirements.txt

# Execute o servidor MCP
python -m postgres_mcp
```

## Uso Básico

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

## Exemplo de Comandos

### Listar Tabelas

```json
{
  "tool": "list_tables",
  "parameters": {
    "schema": "public"
  }
}
```

### Ler Registros

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "filters": {
      "active": true,
      "age": { "gte": 18 }
    },
    "columns": ["id", "name", "email"],
    "limit": 100,
    "order_by": "name",
    "ascending": true
  }
}
```

### Criar Registro

```json
{
  "tool": "create_record",
  "parameters": {
    "table": "products",
    "data": {
      "name": "Smartphone XYZ",
      "price": 999.99,
      "in_stock": true,
      "categories": ["electronics", "mobile"],
      "specs": {
        "cpu": "Octa-core",
        "ram": "8GB",
        "storage": "128GB"
      },
      "store_locations": [
        {"lat": 37.7749, "lng": -122.4194},
        {"lat": 40.7128, "lng": -74.0060}
      ]
    }
  }
}
```

## Documentação

Para documentação completa, consulte [docs/index.md](docs/index.md).

- [API Reference](docs/API_REFERENCE.md)
- [Exemplos de Código](docs/CODE_EXAMPLES.md)
- [Guia de Configuração](docs/CONFIGURATION.md)
- [Arquitetura](docs/ARCHITECTURE.md)

## Contribuição

Contribuições são bem-vindas! Por favor, consulte [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Funcionalidades Principais

* **CRUD Completo**: Operações de criação, leitura, atualização e exclusão.
* **Sistema de Filtragem Avançado**: Consultas complexas com suporte para uma variedade de operadores.
* **Transações**: Gerenciamento de transações para operações atômicas.
* **Multi-Schema**: Compatibilidade com múltiplos schemas.
* **Sistema de Cache**: Cache de consultas para otimização de desempenho.
* **Sistema de Métricas**: Monitoramento de desempenho e uso.
* **Tipos Avançados PostgreSQL**: Suporte para tipos arrays, JSON/JSONB e tipos geométricos.
* **Views**: Gerenciamento completo de views (listagem, descrição, criação, atualização, exclusão).
* **Funções e Procedimentos**: Suporte a funções e procedimentos armazenados (listagem, descrição, criação, execução, exclusão).

## Começando

### Pré-requisitos

* Python 3.8+
* PostgreSQL 12+
* asyncpg
* pydantic
* cachetools
* psutil 