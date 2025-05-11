# PostgreSQL MCP - Arquitetura

## Visão Geral da Arquitetura

O PostgreSQL MCP é construído como uma arquitetura modular em camadas, seguindo princípios de design limpo e separação de responsabilidades. Esta arquitetura permite extensibilidade, testabilidade e manutenção simplificada.

```
┌─────────────────────────────────────────────────────────────┐
│                  Interface MCP (FastMCP)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Camada de Handlers                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Camada de Serviços                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Camada de Repositório                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      PostgreSQL Driver                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                      PostgreSQL Database
```

## Status Atual da Implementação

A implementação atual (versão 0.1.0) do PostgreSQL MCP concluiu com sucesso a arquitetura central e as funcionalidades principais. Todos os componentes essenciais nas camadas de Interface MCP, Handlers, Serviços e Repositório estão implementados e operacionais.

### Componentes Implementados:
- **Interface MCP**: Implementação completa de MCPServer e MCPRouter com suporte a STDIO e HTTP
- **Handlers**: Todos os handlers principais foram implementados, incluindo operações de esquema, CRUD e transações
- **Serviços**: Implementação completa de TableService, SchemaService, QueryService, TransactionService, CacheService e MetricsService
- **Repositório**: Implementação completa de PostgresRepository com suporte a todas as operações básicas e avançadas
- **Filtros**: Sistema de filtros robusto para consultas avançadas

### Componentes em Desenvolvimento:
- Suporte a tipos de dados específicos do PostgreSQL (arrays, JSON/JSONB)
- Testes abrangentes
- Otimizações de desempenho e cache
- Documentação expandida

## Componentes Principais

### 1. Interface MCP

**Responsabilidade**: Fornece um endpoint compatível com MCP para receber e responder a solicitações de ferramentas.

**Componentes**:
- `MCPServer`: Abstração do servidor MCP que suporta diferentes modos de transporte
- `MCPRouter`: Gerencia o roteamento de solicitações para os handlers apropriados
- `MCPResponse`: Formata respostas no padrão MCP

**Tecnologias**:
- FastMCP para implementação do protocolo MCP

### 2. Camada de Handlers

**Responsabilidade**: Processa requisições específicas das ferramentas, valida parâmetros e orquestra os serviços.

**Componentes**:
- `HandlerBase`: Classe base abstrata para todos os handlers
- Handlers específicos para cada ferramenta:
  - `ReadTableHandler`
  - `CreateRecordHandler`
  - `CreateRecordsHandler`
  - `UpdateRecordsHandler`
  - `DeleteRecordsHandler`
  - `ExecuteQueryHandler` (específico do PostgreSQL)
  - `ListSchemasHandler` (específico do PostgreSQL)
  - `GetCacheStatsHandler` (gerenciamento de cache)
  - `ClearCacheHandler` (gerenciamento de cache)
  - `GetMetricsHandler` (monitoramento de desempenho)
  - `ResetMetricsHandler` (monitoramento de desempenho)

**Padrões**:
- Command Pattern para processamento de requisições
- Injeção de dependência para acesso aos serviços

### 3. Camada de Serviços

**Responsabilidade**: Implementa a lógica de negócios e orquestra operações entre repositórios.

**Componentes**:
- `TableService`: Gerencia operações nas tabelas
- `QueryService`: Constrói e otimiza consultas
- `ValidationService`: Valida dados antes de operações
- `SecurityService`: Gerencia aspectos de segurança e permissões
- `TransactionService`: Gerencia transações do PostgreSQL
- `SchemaService`: Gerencia operações relacionadas a schemas (específico do PostgreSQL)
- `CacheService`: Gerencia cache de consultas e metadados
- `MetricsService`: Monitora e analisa métricas de desempenho do sistema

**Padrões**:
- Serviços stateless
- Uso de interfaces para desacoplamento
- Decoradores para instrumentação de métricas

### 4. Camada de Repositório

**Responsabilidade**: Abstrai acesso a dados e operações no PostgreSQL.

**Componentes**:
- `RepositoryBase`: Interface base para operações CRUD
- `TableRepository`: Implementação específica para tabelas do PostgreSQL
- `QueryBuilder`: Construtor de consultas para o PostgreSQL
- `SchemaRepository`: Manipula operações de schema (específico do PostgreSQL)

**Padrões**:
- Repository Pattern
- Unit of Work para operações transacionais
- Estratégia de cache para consultas frequentes

### 5. PostgreSQL Driver

**Responsabilidade**: Camada fina que encapsula a comunicação direta com o banco de dados PostgreSQL.

**Componentes**:
- `PostgreSQLClient`: Wrapper em torno da biblioteca psycopg ou asyncpg
- `ConnectionManager`: Gerencia pool de conexões para otimização
- `TransactionManager`: Controla transações e savepoints

**Tecnologias**:
- Biblioteca asyncpg para comunicação assíncrona com PostgreSQL
- Sistema de retry e circuit breaker para resiliência

## Modelos de Dados

### Modelos de Requisição

```
RequestBase
  ├─ TableRequest
  │    ├─ ReadRequest
  │    ├─ CreateRequest
  │    ├─ CreateBatchRequest
  │    ├─ UpdateRequest
  │    └─ DeleteRequest
  ├─ SchemaRequest
  │    ├─ ListTablesRequest
  │    └─ ListSchemasRequest
  ├─ CacheRequest
  │    ├─ GetCacheStatsRequest
  │    └─ ClearCacheRequest
  ├─ MetricsRequest
  │    ├─ GetMetricsRequest
  │    └─ ResetMetricsRequest
  └─ QueryRequest
       └─ ExecuteQueryRequest
```

### Modelos de Resposta

```
ResponseBase
  ├─ SuccessResponse
  │    ├─ DataResponse
  │    └─ AcknowledgementResponse
  └─ ErrorResponse
       ├─ ValidationErrorResponse
       ├─ DatabaseErrorResponse
       ├─ SecurityErrorResponse
       └─ QueryErrorResponse
```

## Fluxos de Dados

### Fluxo de Leitura (Read)

1. Requisição MCP chega ao `MCPServer`
2. `MCPRouter` roteia para `ReadTableHandler`
3. Handler valida parâmetros usando modelos Pydantic
4. `QueryService` constrói a consulta SQL otimizada
5. `TableRepository` executa a consulta via driver PostgreSQL
6. Resultados são transformados em `DataResponse`
7. Resposta é formatada e retornada ao cliente

### Fluxo de Escrita (Create/Update/Delete)

1. Requisição MCP chega ao `MCPServer`
2. `MCPRouter` roteia para o handler específico
3. Handler valida parâmetros usando modelos Pydantic
4. `ValidationService` valida a integridade dos dados
5. `SecurityService` verifica permissões (se configurado)
6. `TransactionService` inicia uma transação se necessário
7. `TableRepository` executa a operação via driver PostgreSQL
8. Transação é confirmada (commit) ou revertida (rollback) baseado no resultado
9. Resultados são transformados em resposta apropriada
10. Resposta é formatada e retornada ao cliente

### Fluxo de Consulta Personalizada (Execute Query)

1. Requisição MCP chega ao `MCPServer`
2. `MCPRouter` roteia para `ExecuteQueryHandler`
3. Handler valida parâmetros e consulta SQL
4. `SecurityService` verifica permissões para execute_query
5. `ValidationService` sanitiza a consulta SQL para segurança
6. `QueryService` executa a consulta diretamente via driver PostgreSQL
7. Resultados são transformados em `DataResponse`
8. Resposta é formatada e retornada ao cliente

## Recursos PostgreSQL Específicos

### 1. Suporte a Múltiplos Schemas

O PostgreSQL MCP suporta operações em múltiplos schemas, permitindo:
- Listagem de schemas disponíveis
- Especificação de schema em operações de tabela
- Controle de acesso por schema

### 2. Tipos de Dados Avançados

Suporte para tipos nativos do PostgreSQL:
- Arrays
- JSON/JSONB
- Tipos geométricos
- Tipos de rede (INET, CIDR)
- Tipos personalizados

### 3. Recursos Transacionais

Suporte completo para transações:
- Início/Commit/Rollback explícitos
- Níveis de isolamento configuráveis
- Savepoints

### 4. Funcionalidades PostgreSQL Avançadas

Acesso a recursos específicos do PostgreSQL:
- Funções e procedimentos armazenados
- Triggers
- Views
- Consultas com Common Table Expressions (CTEs)
- Window Functions

## Estratégias de Resiliência

1. **Retry com Backoff Exponencial**
   - Tentativas automáticas para falhas transitórias
   - Tempo de espera aumenta exponencialmente entre tentativas

2. **Circuit Breaker**
   - Evita sobrecarga em caso de falhas persistentes
   - Falha rápido quando o sistema subjacente está comprometido

3. **Pool de Conexões**
   - Gerenciamento eficiente de conexões ao PostgreSQL
   - Limite configurável de conexões máximas
   - Keepalive para evitar conexões inativas

4. **Cache**
   - Implementado através do CacheService dedicado
   - Armazenamento em cache de:
     - Resultados de consultas (tabelas e SQL personalizadas)
     - Metadados de tabelas e schemas
   - Estratégia TTL (Time to Live) configurável
   - Mecanismos de invalidação automática em operações de escrita

## Sistema de Métricas

### Arquitetura do MetricsService

O MetricsService é um componente central para monitoramento e diagnóstico de desempenho em todo o sistema PostgreSQL MCP. Foi projetado para coletar, armazenar e analisar métricas de desempenho sem impacto significativo na performance do sistema principal.

#### Componentes do Sistema de Métricas:

1. **Núcleo de Coleta de Métricas**
   - Rastreamento de tempos de execução para operações
   - Contagem de operações por tipo
   - Registro de erros e exceções
   - Monitoramento de recursos do sistema (CPU, memória, conexões)

2. **Decoradores de Instrumentação**
   - `track_execution_time`: Decorador para medir o tempo de execução de funções síncronas e assíncronas
   - Suporte a amostragem configurável para reduzir sobrecarga em ambientes de produção

3. **Armazenamento de Métricas**
   - Histórico limitado por configuração para evitar consumo excessivo de memória
   - Thread-safe para ambientes com múltiplas threads/tarefas assíncronas
   - Mecanismos de rotação para dados históricos

4. **Análise Estatística**
   - Cálculo de estatísticas em tempo real (mín, máx, média, mediana, percentis)
   - Análise de tendências temporais
   - Cálculo de taxas de erro e throughput

5. **Monitoramento de Recursos**
   - Integração com `psutil` para métricas do sistema operacional
   - Monitoramento do pool de conexões PostgreSQL
   - Monitoramento do uso de cache

#### Fluxo de Dados de Métricas:

1. Instrumentação aplicada às operações críticas através de decoradores
2. Métricas coletadas e armazenadas em estruturas thread-safe
3. Intervalos de amostragem aplicados para reduzir sobrecarga
4. Análise estatística realizada sob demanda
5. Métricas expostas através dos handlers MCP para consulta

#### Benefícios do Sistema de Métricas:

- **Diagnóstico de Problemas**: Identificação rápida de operações lentas
- **Otimização de Performance**: Dados para guiar otimizações
- **Análise de Padrões de Uso**: Compreensão de como o sistema é utilizado
- **Planejamento de Capacidade**: Dados para prever necessidades futuras
- **Monitoramento de Saúde**: Visibilidade em tempo real da saúde do sistema

O MetricsService é integrado com outros componentes do sistema através de injeção de dependência, permitindo uma instrumentação não-intrusiva e desacoplada da lógica de negócios principal.

## Considerações sobre Segurança

1. **Gestão de Credenciais**
   - Carregamento seguro via variáveis de ambiente
   - Suporte a conexão via SSL/TLS
   - Nunca expostas em logs ou respostas

2. **Validação de Entrada**
   - Validação rigorosa para prevenir injeção SQL
   - Parametrização de todas as consultas
   - Pydantic para validação de esquema

3. **Política de Permissões**
   - Integração com modelo de permissões do PostgreSQL (roles e grants)
   - Validação de permissões por tabela/operação
   - Controle de acesso por função

4. **Sanitização de Consultas SQL**
   - Análise e validação de consultas SQL personalizadas
   - Prevenção de operações potencialmente perigosas
   - Lista branca de comandos e construções SQL permitidos

5. **Auditoria**
   - Logging estruturado de todas as operações
   - Sem dados sensíveis em logs
   - Integração opcional com funcionalidades de auditoria do PostgreSQL