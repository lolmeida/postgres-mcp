# API do PostgreSQL MCP

Esta seção contém a documentação detalhada de todas as ferramentas disponíveis na API do PostgreSQL MCP.

## Ferramentas Principais

### Ferramentas de Pesquisa e Exploração
- [list_schemas](./list_schemas.md) - Lista todos os schemas disponíveis no banco de dados
- [list_tables](./list_tables.md) - Lista todas as tabelas disponíveis em um schema específico
- [describe_table](./describe_table.md) - Retorna informações detalhadas sobre a estrutura de uma tabela

### Ferramentas de Operações CRUD
- [read_table](./read_table.md) - Lê registros de uma tabela com suporte a filtros avançados
- [create_record](./create_record.md) - Cria um único registro em uma tabela
- [create_batch](./create_batch.md) - Cria múltiplos registros em uma única operação
- [update_records](./update_records.md) - Atualiza registros que correspondem aos filtros especificados
- [delete_records](./delete_records.md) - Exclui registros que correspondem aos filtros especificados

### Ferramentas de Consulta Avançada
- [execute_query](./execute_query.md) - Executa uma consulta SQL personalizada

### Ferramentas de Transação
- [begin_transaction](./begin_transaction.md) - Inicia uma transação para operações subsequentes
- [commit_transaction](./commit_transaction.md) - Confirma uma transação em andamento
- [rollback_transaction](./rollback_transaction.md) - Reverte uma transação em andamento

### Ferramentas de Cache
- [get_cache_stats](./get_cache_stats.md) - Obtém estatísticas de uso do cache
- [clear_cache](./clear_cache.md) - Limpa o cache (total ou parcialmente)

## Formato das Requisições

Todas as requisições para a API do PostgreSQL MCP seguem o formato padrão MCP:

```json
{
  "tool": "nome_da_ferramenta",
  "parameters": {
    "param1": "valor1",
    "param2": "valor2"
  }
}
```

## Formato das Respostas

Todas as respostas têm a seguinte estrutura básica:

### Resposta de Sucesso

```json
{
  "success": true,
  "data": [...],
  "count": 10
}
```

### Resposta de Erro

```json
{
  "success": false,
  "error": {
    "message": "Mensagem de erro",
    "type": "tipo_de_erro",
    "details": {
      // Detalhes adicionais do erro
    }
  }
}
```

## Códigos de Erro

A API do PostgreSQL MCP pode retornar os seguintes tipos de erro:

| Tipo | Descrição |
|------|-----------|
| `validation_error` | Erro de validação dos parâmetros da requisição |
| `database_error` | Erro do banco de dados ao processar a operação |
| `security_error` | Erro relacionado a permissões ou políticas de segurança |
| `transaction_error` | Erro relacionado a transações |
| `query_error` | Erro na execução de consulta SQL personalizada |
| `internal_error` | Erro interno do servidor |

## Melhores Práticas

1. **Use filtros específicos**: Para melhor performance, seja específico nos filtros utilizados.
2. **Limite resultados**: Sempre utilize o parâmetro `limit` para restringir o volume de dados retornados.
3. **Prefira operações em lote**: Ao criar múltiplos registros, utilize `create_batch` em vez de múltiplas chamadas a `create_record`.
4. **Use transações**: Para operações que alteram múltiplos registros, utilize transações para garantir consistência.
5. **Valide dados de entrada**: Sempre valide os dados antes de enviá-los à API para evitar erros de validação.