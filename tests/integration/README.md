# Testes de Integração do PostgreSQL MCP

Este diretório contém testes de integração para o PostgreSQL MCP, utilizando Docker para criar um container PostgreSQL isolado para os testes.

## Estrutura

- `conftest.py`: Configuração do PyTest e inicialização do container PostgreSQL
- `test_crud_operations.py`: Testes das operações CRUD básicas (Create, Read, Update, Delete)
- `test_transactions.py`: Testes das operações de transação
- `test_filters.py`: Testes dos diferentes tipos de filtros
- `test_postgres_features.py`: Testes para recursos específicos do PostgreSQL

## Como executar

### Pré-requisitos

- Docker
- Python 3.10 ou superior
- Pacotes listados em requirements-dev.txt

### Instalação

```bash
pip install -e .
pip install -r requirements-dev.txt
```

### Execução dos testes

```bash
# Executar todos os testes de integração
python -m pytest tests/integration -v

# Executar um teste específico
python -m pytest tests/integration/test_crud_operations.py -v

# Executar um método de teste específico
python -m pytest tests/integration/test_crud_operations.py::TestReadOperations::test_read_table_all_records -v
```

## Status dos testes

### Problemas conhecidos

1. Os testes estão enfrentando problemas de compatibilidade com a implementação atual da classe PostgresMCP:
   - Problemas com a inicialização dos serviços
   - Ausência de método `execute_tool` para executar comandos diretos
   - Incompatibilidade do parâmetro 'mode' com os valores aceitos pelo enum MCPMode

### Próximos passos

1. Corrigir a infraestrutura de testes para isolar os testes da implementação atual do PostgresMCP
2. Implementar testes diretos contra o banco de dados PostgreSQL
3. Atualizar os testes conforme a API do PostgresMCP evolui 