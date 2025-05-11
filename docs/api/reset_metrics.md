# Ferramenta `reset_metrics`

## Descrição

Esta ferramenta permite resetar todas as métricas de desempenho coletadas pelo sistema PostgreSQL MCP. É útil após realizar ajustes no sistema ou quando se deseja iniciar uma nova sessão de monitoramento.

## Parâmetros

Esta ferramenta não requer parâmetros.

## Exemplo de Requisição

```json
{
  "tool": "reset_metrics"
}
```

## Resposta

### Resposta de Sucesso

```json
{
  "success": true,
  "data": {
    "message": "Métricas resetadas com sucesso"
  }
}
```

### Resposta de Erro

```json
{
  "success": false,
  "error": {
    "message": "Erro ao resetar métricas: detalhes do erro aqui",
    "type": "internal_error"
  }
}
```

## Notas

- Resetar as métricas zera todos os contadores e limpa históricos de tempo de execução, erros e uso de recursos.
- O timestamp de início do sistema (uptime) também é resetado.
- Esta operação não pode ser desfeita - uma vez resetadas, as métricas anteriores são perdidas.
- É recomendável exportar ou salvar as métricas antes de resetá-las se os dados históricos forem importantes. 