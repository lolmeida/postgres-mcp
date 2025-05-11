# Guia de Tipos Avançados do PostgreSQL

Este guia demonstra como trabalhar com tipos avançados do PostgreSQL como arrays, JSON/JSONB e tipos geométricos através do PostgreSQL MCP.

## Arrays

O PostgreSQL oferece suporte a arrays de qualquer tipo de dados interno, enumerações ou tipos compostos. O PostgreSQL MCP permite que você utilize arrays em suas consultas com suporte completo para filtragem e manipulação.

### Consultando Arrays

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "produtos",
    "filters": {
      "tags": {
        "contains": ["eletrônicos", "promoção"]
      }
    }
  }
}
```

### Operadores de Array Suportados

O PostgreSQL MCP suporta os seguintes operadores para campos do tipo array:

| Operador | Descrição | Exemplo de Uso |
|----------|-----------|----------------|
| `contains` | Verifica se o array da coluna contém todos os elementos do array fornecido | `"tags": {"contains": ["eletrônicos"]}` |
| `contained_by` | Verifica se o array da coluna está contido no array fornecido | `"tags": {"contained_by": ["eletrônicos", "promoção", "importado"]}` |
| `overlap` | Verifica se o array da coluna tem elementos em comum com o array fornecido | `"tags": {"overlap": ["eletrônicos", "celulares"]}` |
| `array_length` | Verifica se o array tem o tamanho especificado | `"tags": {"array_length": 3}` |
| `array_length_gt` | Verifica se o array tem tamanho maior que o especificado | `"tags": {"array_length_gt": 2}` |
| `array_length_lt` | Verifica se o array tem tamanho menor que o especificado | `"tags": {"array_length_lt": 5}` |

### Criando e Atualizando Arrays

```json
{
  "tool": "create_record",
  "parameters": {
    "table": "produtos",
    "data": {
      "nome": "Smartphone XYZ",
      "preco": 1200.00,
      "cores_disponiveis": ["preto", "branco", "azul"],
      "especificacoes": [
        ["RAM", "8GB"],
        ["Armazenamento", "128GB"]
      ]
    }
  }
}
```

## JSON e JSONB

O PostgreSQL oferece dois tipos para armazenamento de dados JSON: `json` e `jsonb`. O tipo `jsonb` é armazenado em um formato binário que permite indexação e operações mais eficientes.

### Consultando Campos JSONB

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "usuarios",
    "filters": {
      "preferencias": {
        "jsonb_contains": {
          "tema": "escuro",
          "notificacoes": true
        }
      }
    }
  }
}
```

### Operadores JSONB Suportados

| Operador | Descrição | Exemplo de Uso |
|----------|-----------|----------------|
| `jsonb_contains` | Verifica se o campo JSONB contém os pares chave-valor especificados | `"metadados": {"jsonb_contains": {"status": "ativo"}}` |
| `jsonb_contained_by` | Verifica se o campo JSONB está contido no objeto fornecido | `"config": {"jsonb_contained_by": {"timeout": 30, "retry": true, "mode": "auto"}}` |
| `has_key` | Verifica se o campo JSONB tem a chave especificada | `"atributos": {"has_key": "cor"}` |
| `has_any_keys` | Verifica se o campo JSONB tem pelo menos uma das chaves especificadas | `"atributos": {"has_any_keys": ["cor", "tamanho"]}` |
| `has_all_keys` | Verifica se o campo JSONB tem todas as chaves especificadas | `"detalhes": {"has_all_keys": ["fabricante", "modelo", "ano"]}` |
| `jsonb_path` | Realiza uma consulta de caminho JSONB (PostgreSQL 12+) | `"documento": {"jsonb_path": "$.items[*] ? (@.price > 10)"}` |

### Criando e Atualizando JSONB

```json
{
  "tool": "create_record",
  "parameters": {
    "table": "pedidos",
    "data": {
      "cliente_id": 1001,
      "total": 450.75,
      "itens": [
        {"produto_id": 101, "quantidade": 2, "preco_unitario": 150.25},
        {"produto_id": 203, "quantidade": 1, "preco_unitario": 150.25}
      ],
      "endereco_entrega": {
        "rua": "Av. Principal",
        "numero": 123,
        "complemento": "Apto 45",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01234-567"
      }
    }
  }
}
```

## Acessando Campos Aninhados

Você pode acessar campos aninhados em objetos JSON/JSONB usando notação de ponto:

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "pedidos",
    "filters": {
      "endereco_entrega.cidade": "São Paulo",
      "endereco_entrega.estado": "SP"
    }
  }
}
```

## Tipos Geométricos

O PostgreSQL oferece suporte nativo a tipos geométricos como `point`, `line`, `circle`, `polygon` e `box`. O PostgreSQL MCP agora possui suporte completo para trabalhar com estes tipos, permitindo operações espaciais avançadas em suas aplicações.

### Operadores Geométricos Suportados

O PostgreSQL MCP suporta os seguintes operadores para campos de tipos geométricos:

| Operador | Descrição | Exemplo de Uso |
|----------|-----------|----------------|
| `distance` | Calcula a distância entre pontos | `"localizacao": {"distance": "(0,0),5.5"}` |
| `near` | Encontra pontos próximos a uma coordenada | `"localizacao": {"near": "(37.7749,-122.4194),1.5"}` |
| `contains_point` | Verifica se um polígono contém um ponto | `"area": {"contains_point": "(5,5)"}` |
| `within` | Verifica se um objeto está dentro de outro | `"ponto": {"within": "((0,0),(10,10))"}` |
| `intersects` | Verifica se objetos geométricos se interceptam | `"rota": {"intersects": "((0,0),(10,0),(5,5))"}` |
| `bounding_box` | Verifica se está dentro de uma caixa delimitadora | `"localizacao": {"bounding_box": "((0,0),(10,10))"}` |

### Formatos de Dados Geométricos

Para usar tipos geométricos, você precisa fornecer dados no formato correto:

1. **Pontos**: Coordenadas X e Y entre parênteses: `(x,y)`
   - Exemplo: `(37.7749,-122.4194)`

2. **Caixas (Box)**: Dois pontos que definem os cantos opostos: `((x1,y1),(x2,y2))`
   - Exemplo: `((0,0),(10,10))`

3. **Polígonos**: Sequência de pontos que definem o polígono: `((x1,y1),(x2,y2),...,(xn,yn))`
   - Exemplo: `((0,0),(0,10),(10,10),(10,0),(0,0))`

### Exemplos de Consultas com Tipos Geométricos

#### Encontrar locais próximos a um ponto

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "locais",
    "filters": {
      "coordenadas": {
        "near": "(37.7749,-122.4194),2.5"
      }
    }
  }
}
```

Neste exemplo, estamos buscando locais cujas coordenadas estão a uma distância máxima de 2.5 unidades do ponto (37.7749,-122.4194).

#### Calcular a distância entre pontos

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "locais",
    "filters": {
      "coordenadas": {
        "distance": "(0,0),5.0"
      }
    }
  }
}
```

Este exemplo encontra locais que estão exatamente a 5.0 unidades de distância do ponto (0,0).

#### Verificar se um ponto está dentro de uma área

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "pontos_interesse",
    "filters": {
      "coordenada": {
        "within": "((0,0),(0,10),(10,10),(10,0),(0,0))"
      }
    }
  }
}
```

Este exemplo busca pontos de interesse cuja coordenada está dentro do polígono especificado.

#### Verificar interseção entre áreas

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "areas",
    "filters": {
      "poligono": {
        "intersects": "((5,5),(15,5),(10,15),(5,5))"
      }
    }
  }
}
```

Neste exemplo, buscamos áreas cujo polígono intercepta o polígono triangular especificado.

### Criando Registros com Tipos Geométricos

```json
{
  "tool": "create_record",
  "parameters": {
    "table": "locais",
    "data": {
      "nome": "Parque Central",
      "coordenadas": "(37.7749,-122.4194)",
      "area_cobertura": "((37.7749,-122.4194),(37.7749,-122.4094),(37.7849,-122.4094),(37.7849,-122.4194),(37.7749,-122.4194))",
      "regiao_limite": "((37.77,-122.42),(37.78,-122.40))"
    }
  }
}
```

### Índices para Tipos Geométricos

Para otimizar consultas com tipos geométricos, você pode criar índices especializados:

```sql
-- Índice GiST para ponto
CREATE INDEX idx_coordenadas ON locais USING GIST (coordenadas);

-- Índice GiST para polígono
CREATE INDEX idx_area ON locais USING GIST (area);
```

Os índices GiST (Generalized Search Tree) são especialmente eficientes para tipos geométricos no PostgreSQL.

## Melhores Práticas

1. **Use JSONB em vez de JSON** quando possível, pois oferece melhor desempenho e permite indexação.

2. **Considere Normalização vs Desnormalização**: Para dados estruturados que serão frequentemente consultados independentemente, considere normalizar em tabelas separadas. Use JSON/JSONB para dados semiestruturados ou quando a flexibilidade for mais importante que o desempenho das consultas.

3. **Crie Índices para Arrays e JSONB**: Para consultas frequentes em campos de array ou JSONB, aproveite os índices específicos do PostgreSQL:
   - Índice GIN para campos JSONB: `CREATE INDEX idx_metadados ON produtos USING GIN (metadados);`
   - Índice GIN para arrays: `CREATE INDEX idx_tags ON produtos USING GIN (tags);`

4. **Use Caminho JSONB para Consultas Complexas**: Para navegação e filtragem avançada em documentos JSONB, utilize o operador de caminho JSONB.

## Limitações e Considerações

- Os filtros de array funcionam melhor com elementos de tipos simples (strings, números, booleanos).
- Operações JSONB podem ser mais lentas que operações em colunas regulares para consultas complexas.
- Tipos geométricos exigem compreensão da sintaxe específica do PostgreSQL.

---

Para mais informações sobre como usar tipos avançados do PostgreSQL, consulte a [documentação oficial do PostgreSQL](https://www.postgresql.org/docs/current/datatype.html). 