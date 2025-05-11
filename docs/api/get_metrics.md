# Ferramenta `get_metrics`

## Descrição

Esta ferramenta retorna métricas de desempenho do sistema PostgreSQL MCP, incluindo tempos de execução, taxas de erro, uso de recursos e outras estatísticas que ajudam a monitorar o desempenho e saúde do sistema.

## Parâmetros

| Nome | Tipo | Descrição | Obrigatório |
|------|------|-----------|------------|
| `metric_type` | string | Tipo específico de métrica a retornar: 'execution_times', 'errors', 'resource_usage', 'operations_per_second' | Não |
| `operation` | string | Nome da operação para filtrar estatísticas (quando metric_type='execution_times') | Não |
| `window_seconds` | integer | Janela de tempo em segundos para cálculo de operações por segundo (quando metric_type='operations_per_second') | Não (default: 60) |

## Exemplos de Requisição

### Obter todas as métricas

```json
{
  "tool": "get_metrics"
}
```

### Obter métricas de tempo de execução

```json
{
  "tool": "get_metrics",
  "parameters": {
    "metric_type": "execution_times"
  }
}
```

### Obter métricas de tempo de execução para uma operação específica

```json
{
  "tool": "get_metrics",
  "parameters": {
    "metric_type": "execution_times",
    "operation": "read_table"
  }
}
```

### Obter taxa de operações por segundo

```json
{
  "tool": "get_metrics",
  "parameters": {
    "metric_type": "operations_per_second",
    "window_seconds": 120
  }
}
```

## Resposta

### Resposta de Sucesso

```json
{
  "success": true,
  "data": {
    "execution_times": {
      "read_table": {
        "min": 0.001,
        "max": 1.234,
        "avg": 0.075,
        "median": 0.045,
        "p95": 0.312,
        "count": 1250,
        "total_count": 1500
      },
      "execute_query": {
        "min": 0.005,
        "max": 2.345,
        "avg": 0.125,
        "median": 0.089,
        "p95": 0.456,
        "count": 850,
        "total_count": 1200
      }
    },
    "errors": {
      "read_table:not_found_error": 12,
      "execute_query:syntax_error": 5
    },
    "resource_usage": {
      "memory_usage": {
        "current": 45.6,
        "min": 32.1,
        "max": 67.8,
        "avg": 42.3
      },
      "cpu_usage": {
        "current": 12.3,
        "min": 5.6,
        "max": 35.7,
        "avg": 15.2
      },
      "db_connections": {
        "current": 8,
        "min": 1,
        "max": 15,
        "avg": 6.7
      }
    },
    "uptime_seconds": 3600,
    "operations_per_second": {
      "read_table": 12.5,
      "execute_query": 8.3
    },
    "total_operations": 2700,
    "total_errors": 17,
    "error_rate": 0.0063
  }
}
```

### Resposta de Erro

```json
{
  "success": false,
  "error": {
    "message": "Erro ao coletar métricas: detalhes do erro aqui",
    "type": "internal_error"
  }
}
```

## Notas

- As métricas de desempenho podem ser usadas para detectar gargalos, identificar padrões de uso e otimizar o sistema.
- As métricas de tempo de execução incluem estatísticas de mínimo, máximo, média, mediana e percentil 95.
- As taxas de erro ajudam a identificar problemas recorrentes e áreas que precisam de atenção.
- O uso de recursos ajuda a monitorar a saúde do sistema e planejar capacidade. 