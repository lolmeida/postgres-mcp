# Guia de Filtros - PostgreSQL MCP

O PostgreSQL MCP oferece um sistema de filtragem poderoso que permite consultar dados de forma precisa e eficiente. Este guia explica em detalhes como construir filtros para suas consultas usando a API do PostgreSQL MCP.

## Conceitos Básicos

Os filtros no PostgreSQL MCP são representados como objetos JSON, onde as chaves são os nomes das colunas e os valores são os critérios de filtragem. Cada filtro é transformado em uma cláusula WHERE em SQL.

## Filtros Simples de Igualdade

Para consultas simples de igualdade, basta fornecer o valor diretamente:

```json
{
  "status": "active",
  "category": "electronics"
}
```

Este filtro é equivalente à cláusula SQL:

```sql
WHERE status = 'active' AND category = 'electronics'
```

## Operadores de Comparação

Para consultas mais complexas, você pode usar operadores de comparação:

| Operador | Descrição | Exemplo JSON | SQL Equivalente |
|----------|-----------|--------------|-----------------|
| `eq` | Igual a | `{"price": {"eq": 100}}` | `price = 100` |
| `gt` | Maior que | `{"price": {"gt": 100}}` | `price > 100` |
| `lt` | Menor que | `{"quantity": {"lt": 5}}` | `quantity < 5` |
| `gte` | Maior ou igual a | `{"rating": {"gte": 4.5}}` | `rating >= 4.5` |
| `lte` | Menor ou igual a | `{"age": {"lte": 18}}` | `age <= 18` |
| `ne` | Diferente de | `{"status": {"ne": "deleted"}}` | `status <> 'deleted'` |

### Exemplo:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "products",
    "schema": "public",
    "filters": {
      "price": {"gt": 50, "lte": 200},
      "stock": {"gte": 10}
    }
  }
}
```

Este filtro é equivalente à cláusula SQL:

```sql
WHERE price > 50 AND price <= 200 AND stock >= 10
```

## Operadores de Texto

Para filtragem baseada em texto, o PostgreSQL MCP oferece operadores de padrão:

| Operador | Descrição | Exemplo JSON | SQL Equivalente |
|----------|-----------|--------------|-----------------|
| `like` | Padrão LIKE (case sensitive) | `{"name": {"like": "%Smith%"}}` | `name LIKE '%Smith%'` |
| `ilike` | Padrão LIKE (case insensitive) | `{"email": {"ilike": "%@gmail.com"}}` | `email ILIKE '%@gmail.com'` |
| `match` | Correspondência de expressão regular | `{"code": {"match": "^[A-Z]{3}\\d{3}$"}}` | `code ~ '^[A-Z]{3}\d{3}$'` |
| `imatch` | Correspondência de regex (case insensitive) | `{"code": {"imatch": "^[a-z]{3}\\d{3}$"}}` | `code ~* '^[a-z]{3}\d{3}$'` |

### Exemplo:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "schema": "public",
    "filters": {
      "name": {"ilike": "%johnson%"},
      "phone": {"match": "^\\+1-\\d{3}-\\d{3}-\\d{4}$"}
    }
  }
}
```

## Operadores de Lista

Para filtragem baseada em conjuntos de valores:

| Operador | Descrição | Exemplo JSON | SQL Equivalente |
|----------|-----------|--------------|-----------------|
| `in` | Em uma lista de valores | `{"category": {"in": ["books", "movies"]}}` | `category IN ('books', 'movies')` |
| `nin` | Não está em uma lista | `{"status": {"nin": ["deleted", "archived"]}}` | `status NOT IN ('deleted', 'archived')` |

### Exemplo:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "orders",
    "schema": "public",
    "filters": {
      "status": {"in": ["pending", "processing"]},
      "payment_method": {"nin": ["bitcoin", "check"]}
    }
  }
}
```

## Operadores para Valores Nulos

Para verificar valores nulos:

| Operador | Descrição | Exemplo JSON | SQL Equivalente |
|----------|-----------|--------------|-----------------|
| `is` | É null ou não null | `{"deleted_at": {"is": null}}` | `deleted_at IS NULL` |
| | | `{"email": {"is": "not null"}}` | `email IS NOT NULL` |

### Exemplo:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "schema": "public",
    "filters": {
      "deleted_at": {"is": null},
      "verified_at": {"is": "not null"}
    }
  }
}
```

## Operadores para Arrays

O PostgreSQL possui operadores específicos para trabalhar com arrays:

| Operador | Descrição | Exemplo JSON | SQL Equivalente |
|----------|-----------|--------------|-----------------|
| `contains` | Array contém os elementos | `{"tags": {"contains": ["urgent"]}}` | `tags @> ARRAY['urgent']` |
| `contained_by` | Array está contido em | `{"selected_ids": {"contained_by": [1, 2, 3, 4, 5]}}` | `selected_ids <@ ARRAY[1, 2, 3, 4, 5]` |
| `overlap` | Arrays têm elementos em comum | `{"available_days": {"overlap": ["monday", "friday"]}}` | `available_days && ARRAY['monday', 'friday']` |
| `array_length` | Comprimento do array | `{"tags": {"array_length": 3}}` | `array_length(tags, 1) = 3` |
| `array_length_gt` | Comprimento maior que | `{"tags": {"array_length_gt": 2}}` | `array_length(tags, 1) > 2` |
| `array_length_lt` | Comprimento menor que | `{"tags": {"array_length_lt": 5}}` | `array_length(tags, 1) < 5` |

### Exemplo:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "products",
    "schema": "public",
    "filters": {
      "sizes": {"contains": ["M", "L"]},
      "colors": {"overlap": ["red", "blue"]},
      "categories": {"array_length_gt": 1}
    }
  }
}
```

## Operadores para JSON e JSONB

Para trabalhar com campos JSON/JSONB:

| Operador | Descrição | Exemplo JSON | SQL Equivalente |
|----------|-----------|--------------|-----------------|
| `jsonb_contains` | JSONB contém | `{"preferences": {"jsonb_contains": {"theme": "dark"}}}` | `preferences @> '{"theme": "dark"}'` |
| `jsonb_contained_by` | JSONB está contido em | `{"filters": {"jsonb_contained_by": {"price": 100, "category": "electronics"}}}` | `filters <@ '{"price": 100, "category": "electronics"}'` |
| `has_key` | JSONB tem a chave | `{"metadata": {"has_key": "version"}}` | `metadata ? 'version'` |
| `has_any_keys` | JSONB tem qualquer uma das chaves | `{"preferences": {"has_any_keys": ["theme", "language"]}}` | `preferences ?| array['theme', 'language']` |
| `has_all_keys` | JSONB tem todas as chaves | `{"contact": {"has_all_keys": ["email", "phone"]}}` | `contact ?& array['email', 'phone']` |
| `jsonb_path` | Consulta caminho JSONB | `{"data": {"jsonb_path": "$.items[*] ? (@.price > 100)"}}` | `data @@ '$.items[*] ? (@.price > 100)'` |

### Exemplo de filtro JSONB:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "schema": "public",
    "filters": {
      "preferences": {"jsonb_contains": {"notifications": {"email": true}}},
      "metadata": {"has_all_keys": ["version", "platform"]},
      "profile": {"jsonb_path": "$.address.city == \"New York\""}
    }
  }
}
```

### Consulta de chaves aninhadas em JSON/JSONB

Para acessar chaves aninhadas em JSONB, use a notação de seta (`->`):

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "schema": "public",
    "filters": {
      "preferences->theme": "dark",
      "metadata->version": {"gt": "2.0"},
      "profile->address->city": "New York"
    }
  }
}
```

Este filtro é equivalente à cláusula SQL:

```sql
WHERE preferences->>'theme' = 'dark' 
  AND (metadata->>'version')::text > '2.0'
  AND profile->'address'->>'city' = 'New York'
```

## Filtros Lógicos

Para combinar filtros com operadores lógicos:

| Operador | Descrição | Exemplo |
|----------|-----------|---------|
| `and` | Todas as condições devem ser verdadeiras | `{"and": [{...}, {...}]}` |
| `or` | Pelo menos uma condição deve ser verdadeira | `{"or": [{...}, {...}]}` |
| `not` | Nega a condição | `{"not": {...}}` |

### Exemplo de operadores lógicos:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "products",
    "schema": "public",
    "filters": {
      "or": [
        {"category": "electronics", "price": {"lt": 100}},
        {"category": "books", "author": "Stephen King"}
      ],
      "not": {"status": "deleted"}
    }
  }
}
```

Este filtro é equivalente à cláusula SQL:

```sql
WHERE (
  (category = 'electronics' AND price < 100) OR 
  (category = 'books' AND author = 'Stephen King')
) AND status <> 'deleted'
```

## Filtros para Datas e Horários

Para filtragem baseada em datas e horários:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "orders",
    "schema": "public",
    "filters": {
      "created_at": {"gte": "2023-01-01T00:00:00Z", "lt": "2023-02-01T00:00:00Z"},
      "updated_at": {"gt": "2023-01-15T00:00:00Z"},
      "delivery_date": {"is": null}
    }
  }
}
```

### Filtros de data relativos

O PostgreSQL MCP também suporta filtros de data relativos:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "events",
    "schema": "public",
    "filters": {
      "created_at": {"relative": "today"},
      "start_time": {"relative": "this week"},
      "end_time": {"relative": "next 3 days"}
    }
  }
}
```

Valores suportados para filtros relativos:

- `today`, `yesterday`, `tomorrow`
- `this week`, `last week`, `next week`
- `this month`, `last month`, `next month`
- `this year`, `last year`, `next year`
- `last X days`, `next X days`
- `last X hours`, `next X hours`

## Modificadores de Filtro

Alguns modificadores especiais podem ser aplicados aos filtros:

| Modificador | Descrição | Exemplo |
|-------------|-----------|---------|
| `case_sensitive` | Determina sensibilidade a maiúsculas/minúsculas para comparação de texto | `{"name": {"eq": "John", "case_sensitive": true}}` |
| `negate` | Nega qualquer condição | `{"status": {"in": ["active", "pending"], "negate": true}}` |

## Exemplos Completos

### Exemplo 1: Consulta complexa de produtos

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "products",
    "schema": "inventory",
    "filters": {
      "or": [
        {
          "category": "electronics",
          "price": {"gte": 500, "lte": 1000},
          "stock": {"gt": 0}
        },
        {
          "category": "computers",
          "brand": {"in": ["Apple", "Dell", "HP"]},
          "specs->ram": {"gte": "16GB"}
        }
      ],
      "status": "active",
      "created_at": {"gte": "2023-01-01T00:00:00Z"},
      "tags": {"contains": ["featured"]},
      "not": {"is_deleted": true}
    },
    "order_by": "price",
    "ascending": false,
    "limit": 20
  }
}
```

### Exemplo 2: Consulta complexa de usuários

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "schema": "public",
    "filters": {
      "and": [
        {"email": {"ilike": "%@gmail.com"}},
        {
          "or": [
            {"last_login": {"gte": {"relative": "last 30 days"}}},
            {"registration_completed": true}
          ]
        }
      ],
      "deleted_at": {"is": null},
      "preferences->notifications->email": true,
      "subscription_status": {"in": ["active", "trial"]},
      "not": {
        "role": {"in": ["admin", "moderator"]}
      }
    },
    "columns": ["id", "name", "email", "last_login", "subscription_status"],
    "order_by": "last_login",
    "ascending": false,
    "limit": 100
  }
}
```

## Melhores Práticas

1. **Seja específico**: Use filtros que restrinjam os resultados o máximo possível para melhor performance.

2. **Utilize índices**: Considere os índices existentes no banco de dados ao criar filtros. Filtros que utilizem colunas indexadas terão melhor performance.

3. **Evite operadores de texto complexos**: Operadores como `like` com curingas no início (ex: `%text`) não podem usar índices eficientemente.

4. **Limite resultados**: Sempre use o parâmetro `limit` para restringir o número de resultados retornados.

5. **Prefira operadores de igualdade**: Quando possível, use filtros de igualdade exata em vez de operadores de comparação.

6. **Otimize JSON**: Para consultas em campos JSON/JSONB, considere criar índices GIN ou usar índices específicos para as chaves mais consultadas.

7. **Teste consultas complexas**: Para operações complexas, considere usar a ferramenta `execute_query` para ter maior controle sobre a consulta SQL.

## Limitações

1. Filtros sem restrições não são permitidos para tabelas grandes (>10000 registros) por questões de performance.

2. Operações de exclusão em massa (sem filtros) são bloqueadas por segurança.

3. A profundidade máxima de filtros aninhados (com `and`/`or`) é de 5 níveis.

4. O número máximo de condições em um único filtro é limitado a 50.

5. Alguns operadores avançados podem não estar disponíveis dependendo da versão do PostgreSQL.