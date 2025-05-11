# Ferramenta `clear_cache`

## Descrição

Esta ferramenta permite limpar o cache do sistema PostgreSQL MCP, total ou parcialmente. É possível limpar todo o cache, o cache de um schema específico ou apenas o cache de uma tabela específica.

## Parâmetros

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `scope` | string | Escopo da limpeza: 'all', 'table' ou 'schema' | Não (default: "all") |
| `table` | string | Nome da tabela quando scope='table' | Condicional |
| `schema` | string | Nome do schema (quando scope='schema' ou 'table') | Condicional |

## Exemplos de Requisição

### Limpar todo o cache

```json
{
  "tool": "clear_cache"
}
```

### Limpar cache para uma tabela específica

```json
{
  "tool": "clear_cache",
  "parameters": {
    "scope": "table",
    "table": "users",
    "schema": "public"
  }
}
```

### Limpar cache para um schema inteiro

```json
{
  "tool": "clear_cache",
  "parameters": {
    "scope": "schema",
    "schema": "public"
  }
}
```

## Resposta

A resposta confirma a limpeza do cache e inclui uma mensagem descritiva:

```json
{
  "success": true,
  "data": {
    "message": "Cache da tabela public.users limpo"
  }
}
```

## Códigos de Erro

Se ocorrer um erro durante a limpeza do cache, a resposta terá um dos seguintes formatos:

### Erro de validação

```json
{
  "success": false,
  "error": {
    "message": "Parâmetro 'table' obrigatório quando scope='table'",
    "type": "validation_error"
  }
}
```

### Valor inválido para scope

```json
{
  "success": false,
  "error": {
    "message": "Valor inválido para 'scope': invalid_scope. Valores válidos: 'all', 'table', 'schema'",
    "type": "validation_error"
  }
}
```

## Notas de Uso

- Use esta ferramenta com cuidado, pois limpar o cache pode reduzir temporariamente o desempenho até que o cache seja populado novamente
- Limpe o cache apenas quando necessário, como após grandes atualizações de dados ou quando quiser garantir que os dados mais recentes sejam obtidos
- Para tabelas que são frequentemente atualizadas, pode ser útil limpar o cache delas periodicamente
- A limpeza de todo o cache deve ser utilizada apenas em situações específicas, como durante o diagnóstico de problemas ou antes de operações de manutenção

## Exemplo de Uso em Python

```python
import requests

def clear_cache(scope="all", table=None, schema=None, base_url="http://localhost:8000"):
    parameters = {"scope": scope}
    
    if scope == "table":
        if not table:
            raise ValueError("Parâmetro 'table' obrigatório quando scope='table'")
        parameters["table"] = table
        parameters["schema"] = schema or "public"
        
    elif scope == "schema":
        if not schema:
            raise ValueError("Parâmetro 'schema' obrigatório quando scope='schema'")
        parameters["schema"] = schema
    
    response = requests.post(
        base_url,
        json={
            "tool": "clear_cache",
            "parameters": parameters
        }
    )
    return response.json()

# Limpar todo o cache
clear_cache()

# Limpar cache para uma tabela específica
clear_cache(scope="table", table="users", schema="public")

# Limpar cache para um schema inteiro
clear_cache(scope="schema", schema="public")
``` 