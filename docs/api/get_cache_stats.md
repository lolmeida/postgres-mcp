# Ferramenta `get_cache_stats`

## Descrição

Esta ferramenta retorna estatísticas detalhadas sobre o uso do cache no sistema PostgreSQL MCP. As estatísticas incluem informações como número de acertos (hits), falhas (misses), taxa de acerto (hit ratio), e capacidade de cada cache.

## Parâmetros

Esta ferramenta não requer parâmetros.

## Exemplo de Requisição

```json
{
  "tool": "get_cache_stats"
}
```

## Resposta

A resposta contém estatísticas detalhadas do cache, incluindo:

```json
{
  "success": true,
  "data": {
    "hits": 3250,               // Número de acertos no cache
    "misses": 750,              // Número de falhas no cache
    "invalidations": 120,       // Número de invalidações manuais/automáticas
    "hit_ratio": "81.25%",      // Percentual de acertos (hits / total de requisições)
    "table_cache_size": 428,    // Número atual de itens no cache de tabelas
    "schema_cache_size": 12,    // Número atual de itens no cache de schemas
    "metadata_cache_size": 56,  // Número atual de itens no cache de metadados
    "table_cache_capacity": 1000, // Capacidade máxima do cache de tabelas
    "schema_cache_capacity": 100, // Capacidade máxima do cache de schemas
    "metadata_cache_capacity": 200 // Capacidade máxima do cache de metadados
  }
}
```

## Código de Erro

Se ocorrer um erro ao obter as estatísticas do cache, a resposta terá o seguinte formato:

```json
{
  "success": false,
  "error": {
    "message": "Erro ao obter estatísticas do cache",
    "type": "internal_error"
  }
}
```

## Notas de Uso

- Esta ferramenta é útil para monitoramento de desempenho e diagnóstico de problemas de cache
- A taxa de acerto (hit_ratio) é um indicador importante da eficácia do cache - valores acima de 80% geralmente indicam um bom desempenho
- O número de invalidações pode ajudar a entender se o cache está sendo limpo com muita frequência

## Exemplo de Uso em Python

```python
import requests

def get_cache_stats(base_url="http://localhost:8000"):
    response = requests.post(
        base_url,
        json={"tool": "get_cache_stats"}
    )
    return response.json()

stats = get_cache_stats()
print(f"Taxa de acertos do cache: {stats['data']['hit_ratio']}")
print(f"Tamanho atual do cache de tabelas: {stats['data']['table_cache_size']}")
``` 