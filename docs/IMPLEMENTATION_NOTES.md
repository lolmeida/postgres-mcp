# Notas de Implementação - Suporte a Views e Funções PostgreSQL

## Visão Geral
Esta implementação adiciona suporte completo para gerenciamento de views (regulares e materializadas) e funções armazenadas (functions e procedures) no PostgreSQL através do MCP (Model Context Protocol).

## Componentes Implementados

### 1. Modelos de Dados
- **ViewInfo**: Representa views regulares e materializadas, com propriedades específicas.
- **FunctionInfo**: Representa funções e procedimentos armazenados, incluindo informações como argumentos, tipo de retorno e volatilidade.

### 2. Extensões do PostgresSchemaManager
- Adicionados métodos para listar, recuperar e gerenciar views:
  - `listViews`
  - `getViewInfo` 
  - `getViewDefinition`
  - `refreshMaterializedView`
- Adicionados métodos para funções armazenadas:
  - `getFunctionInfo`
  - `getFunctionDefinition`
  - `executeFunction`

### 3. Serviços
- **ViewService**: Gerencia operações com views, encapsulando lógica de negócios.
  - Lista views por schema
  - Obtém detalhes de views
  - Suporte a refresh de views materializadas
- **FunctionService**: Gerencia operações com funções armazenadas.
  - Lista funções por schema
  - Obtém detalhes de funções
  - Executa funções com parâmetros

### 4. Handlers MCP
- **ViewHandler**: Expõe operações com views através do MCP.
  - Operações: `list`, `get`, `refresh`
- **FunctionHandler**: Expõe operações com funções através do MCP.
  - Operações: `list`, `get`, `execute`

### 5. Integração
- Configurada a inicialização dos novos serviços no PostgresMCPServer
- Registrados os novos handlers para tratamento de requisições
- Adicionadas exportações no arquivo index.ts principal

## Funcionalidades Suportadas

### Views
- Listar todas as views (regulares e materializadas) em um schema
- Obter definição SQL e detalhes de uma view específica
- Atualizar (refresh) views materializadas com suporte a opções CONCURRENTLY e WITH DATA

### Funções
- Listar todas as funções e procedimentos em um schema
- Obter definição SQL e detalhes de uma função específica
- Executar funções com parâmetros, retornando os resultados
- Tratamento diferenciado para funções (retornam dados) e procedimentos (executam ações)

## Exemplo de Uso

### Listando Views (via MCP)
```json
{
  "operation": "mcp_postgres_view",
  "parameters": {
    "operation": "list",
    "schema": "public",
    "includeRegularViews": true,
    "includeMaterializedViews": true
  }
}
```

### Executando Função (via MCP)
```json
{
  "operation": "mcp_postgres_function",
  "parameters": {
    "operation": "execute",
    "functionName": "get_customer",
    "schema": "public",
    "args": [123]
  }
}
```

## Verificação de Funcionalidade

Foi criado um script de exemplo simples (`examples/simple-pg-example.ts`) que testa diretamente as operações no PostgreSQL para confirmar que tudo está funcionando corretamente. O teste realiza as seguintes operações:

1. Cria uma tabela `sample_data` com dados de exemplo
2. Cria uma view regular (`sample_view`) sobre esses dados
3. Lista as views existentes no schema public
4. Consulta os dados da view regular
5. Cria uma view materializada (`sample_mview`)
6. Lista as views materializadas existentes
7. Consulta os dados da view materializada
8. Atualiza a view materializada
9. Cria uma função armazenada (`get_sample_data`)
10. Lista as funções existentes no schema
11. Executa a função armazenada

Todos os testes foram concluídos com sucesso, confirmando que as implementações estão corretas e o banco de dados PostgreSQL está configurado adequadamente para suportar views (regulares e materializadas) e funções armazenadas.

## Próximos Passos

As próximas funcionalidades a serem implementadas são:
- Suporte a múltiplos schemas
- Suporte a tipos de dados avançados
- Suporte a CTEs e Window Functions 