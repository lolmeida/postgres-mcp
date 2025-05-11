# PostgreSQL MCP

PostgreSQL MCP é uma implementação do Model Context Protocol (MCP) para permitir que Modelos de Linguagem Grandes (LLMs) interajam diretamente com bancos de dados PostgreSQL.

## Status do Projeto

Status atual: **Versão 0.1.0** (80% concluído)

O PostgreSQL MCP implementou todas as funcionalidades principais, incluindo:
- Operações CRUD completas (criar, ler, atualizar, excluir)
- Sistema de filtros avançado
- Gerenciamento de transações
- Compatibilidade com múltiplos schemas
- Modos de transporte STDIO e HTTP
- Sistema de cache para otimização de consultas
- Sistema de métricas para monitoramento de desempenho

Próximos desenvolvimentos:
- Suporte avançado para tipos de dados PostgreSQL específicos
- Testes abrangentes
- Otimizações adicionais de desempenho
- Documentação expandida de deployment

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

## Instalação

```bash
pip install postgres-mcp
```

## Uso Básico

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

## Modos de Operação

### STDIO (Padrão)

```python
from postgres_mcp import PostgresMCP

mcp = PostgresMCP()
mcp.start()
```

### HTTP

```python
from postgres_mcp import PostgresMCP

mcp = PostgresMCP(mode="http", port=8000)
mcp.start()
```

## Desenvolvimento

### Configuração do Ambiente

1. Clone o repositório:
```bash
git clone https://github.com/yourusername/postgres-mcp.git
cd postgres-mcp
```

2. Configure o ambiente com Poetry:
```bash
poetry install
```

3. Ative o ambiente virtual:
```bash
poetry shell
```

### Executando Testes

```bash
pytest
```

### Formato do Código

```bash
black src tests
isort src tests
```

## Contribuindo

Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição antes de enviar um pull request.

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes. 