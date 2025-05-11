# Documentação do PostgreSQL MCP

Bem-vindo à documentação oficial do PostgreSQL MCP! Este projeto implementa o Model Context Protocol (MCP) para permitir que Modelos de Linguagem Grandes (LLMs) interajam diretamente com bancos de dados PostgreSQL.

## Status do Projeto

**Versão atual: 0.1.0 (75% concluído)**

O PostgreSQL MCP implementou todas as funcionalidades principais, incluindo:
- ✅ Operações CRUD completas (criar, ler, atualizar, excluir)
- ✅ Sistema de filtros avançado
- ✅ Gerenciamento de transações
- ✅ Compatibilidade com múltiplos schemas
- ✅ Estrutura completa de camadas (Handlers, Services, Repository)
- ✅ Sistema de cache para otimização de consultas

**Próximos desenvolvimentos:**
- 🔲 Testes automatizados abrangentes
- 🔲 Suporte avançado para tipos específicos do PostgreSQL
- 🔲 Otimizações adicionais de desempenho 
- 🔲 Documentação expandida para casos de uso 

## Sobre o PostgreSQL MCP

O PostgreSQL MCP serve como uma ponte entre LLMs e bancos de dados PostgreSQL, fornecendo um conjunto padronizado de ferramentas para operações de banco de dados. Isso permite que modelos como Claude e GPT consultem e modifiquem dados no PostgreSQL seguindo o protocolo MCP.

### Principais Recursos

- **Operações CRUD completas** para tabelas do PostgreSQL
- **Filtros avançados** para consultas sofisticadas
- **Validação e segurança** integradas
- **Fácil integração** com LLMs que suportam o protocolo MCP
- **Modos de operação** flexíveis (STDIO e HTTP)
- **Suporte a transações** nativas do PostgreSQL
- **Funcionalidades avançadas** específicas do PostgreSQL (JSON, arrays, funções)

## Status do Projeto

O PostgreSQL MCP está atualmente na versão 0.1.0 com aproximadamente 75% das funcionalidades implementadas. O projeto completou as seguintes fases:

- ✅ **Fase 1**: Preparação e Estrutura Inicial
- ✅ **Fase 2**: Implementação da Camada de Conexão PostgreSQL
- ✅ **Fase 3**: Implementação da Camada de Serviços
- ✅ **Fase 4**: Implementação da Interface MCP

As principais funcionalidades disponíveis incluem:
- Operações CRUD completas (criar, ler, atualizar, excluir registros)
- Sistema de filtros avançado com suporte a operadores de comparação, texto e listas
- Gerenciamento de transações (begin, commit, rollback)
- Suporte a múltiplos schemas
- Consultas SQL personalizadas
- Modos de transporte flexíveis (STDIO, HTTP)

Em desenvolvimento:
- Funcionalidades avançadas para tipos específicos do PostgreSQL (arrays, JSON/JSONB)
- Testes abrangentes (unitários, integração, end-to-end)
- Otimizações de desempenho e cache
- Documentação abrangente de deployment

## Navegação da Documentação

### [💫 Introdução](./PLANNING.md)
- [Visão Geral do Projeto](./PLANNING.md)
- [Arquitetura](./ARCHITECTURE.md)
- [Requisitos e Planejamento](./PRD.md)

### [🚀 Guias](./guides/index.md)
- [Guia Inicial](./guides/getting-started.md)
- [Guia de Filtros](./guides/filters.md)
- [Mais guias...](./guides/index.md)

### [📚 Referência API](./api/index.md)
- [Lista de Ferramentas](./api/index.md)
- [Ferramenta list_tables](./api/list_tables.md)
- [Ferramenta read_table](./api/read_table.md)
- [Mais ferramentas...](./api/index.md)

### [🔧 Desenvolvimento](./INTEGRATION_TESTS.md)
- [Testes de Integração](./INTEGRATION_TESTS.md)
- [CI/CD](./CI_CD.md)
- [Segurança](./SECURITY.md)

### [📋 Exemplos](./CODE_EXAMPLES.md)
- [Exemplos de Código](./CODE_EXAMPLES.md)

## Instalação Rápida

```bash
pip install postgres-mcp
```

## Configuração Básica

```python
from postgres_mcp import PostgresMCP

# Inicializa o servidor MCP
mcp = PostgresMCP(
    db_host="localhost",
    db_port=5432,
    db_name="mydatabase",
    db_user="myuser",
    db_password="mypassword"
)

# Inicia o servidor (modo STDIO padrão)
mcp.start()
```

## Exemplo Rápido

### Listar Tabelas

```json
{
  "tool": "list_tables",
  "parameters": {
    "schema": "public"
  }
}
```

### Consultar Dados

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "produtos",
    "filters": {
      "categoria": "eletrônicos",
      "preco": {
        "lte": 100
      }
    },
    "limit": 5
  }
}
```

## Próximos Passos

- [Siga o Guia Inicial](./guides/getting-started.md) para começar a usar o PostgreSQL MCP
- Explore os [Exemplos de Código](./CODE_EXAMPLES.md) para ver casos de uso comuns
- Consulte a [Referência de API](./api/index.md) para detalhes sobre todas as ferramentas disponíveis

## Contribuindo

Contribuições são bem-vindas! Por favor, leia nossas [diretrizes de contribuição](https://github.com/yourusername/postgres-mcp/blob/main/CONTRIBUTING.md) antes de enviar um pull request.

## Último Update

Última atualização da documentação: 12 de Maio de 2025