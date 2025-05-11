# Testes Standalone do PostgreSQL MCP

Este diretório contém testes independentes para os filtros e construtores de consulta do PostgreSQL MCP, implementados sem dependências diretas do código principal para facilitar o teste isolado.

## Arquivos de Teste

- `test_standalone_filters.py`: Testes unitários para todos os modelos de filtro
- `test_standalone_query_builder.py`: Testes para o QueryBuilder com filtros básicos
- `test_integrated.py`: Testes integrados que verificam a interação entre filtros e QueryBuilder

## Como Executar os Testes

Para executar apenas os testes standalone:

```bash
python run_tests.py --standalone
```

Para executar com saída detalhada:

```bash
python run_tests.py --standalone --verbose
```

Você também pode executar diretamente neste diretório:

```bash
cd standalone_tests
pytest
```

## Modelos de Filtro Testados

- **ComparisonFilter**: Operações de comparação (eq, gt, lt, gte, lte, ne)
- **TextFilter**: Operações de texto (like, ilike, match, imatch)
- **ListFilter**: Operações de lista (in, nin)
- **NullFilter**: Filtros para valores nulos (is null, is not null)
- **ArrayFilter**: Operações em arrays (contains, contained_by, etc.)
- **JsonbFilter**: Operações em campos JSONB (jsonb_contains, has_key, etc.)
- **GeometricFilter**: Operações geométricas (distance, near, bounding_box, etc.)

## Notas Importantes

- Estes testes são implementados com Pydantic V2, usando `model_validator` em vez do obsoleto `root_validator`.
- Os campos com palavras-chave reservadas (como `in` e `is`) são tratados usando aliases.
- São mantidos separados do diretório principal de testes para evitar problemas de importação e conflitos. 