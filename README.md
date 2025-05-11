# PostgreSQL MCP

PostgreSQL MCP é uma implementação do Model Context Protocol (MCP) para permitir que Modelos de Linguagem Grandes (LLMs) interajam diretamente com bancos de dados PostgreSQL.

## Status do Projeto

Status atual: **Versão 0.1.0** (85% concluído)

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

Próximos desenvolvimentos:
- Testes abrangentes
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

```bash
pip install postgres-mcp
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