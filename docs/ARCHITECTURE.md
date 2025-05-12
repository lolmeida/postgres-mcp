# PostgreSQL MCP (JavaScript) - Arquitetura

## Visão Geral da Arquitetura Planejada

O PostgreSQL MCP para JavaScript será construído como uma arquitetura modular em camadas, seguindo princípios de design limpo e separação de responsabilidades. Esta arquitetura permitirá extensibilidade, testabilidade e manutenção simplificada.

```
┌─────────────────────────────────────────────────────────────┐
│                  Interface MCP (MCP-Core)                    │
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

A implementação atual (versão 0.1.0) do PostgreSQL MCP para JavaScript está em fase inicial de desenvolvimento. Estamos começando pela definição da arquitetura e planejamento das funcionalidades.

### Componentes a Serem Implementados:
- **Interface MCP**: Implementação de MCPServer e MCPRouter com suporte a STDIO e HTTP
- **Handlers**: Desenvolvimento de handlers para operações de esquema, CRUD e transações
- **Serviços**: Implementação de TableService, SchemaService, QueryService, TransactionService, CacheService e MetricsService
- **Repositório**: Implementação de PostgresRepository com suporte a todas as operações básicas e avançadas
- **Filtros**: Sistema de filtros robusto para consultas avançadas

## Componentes Principais Planejados

### 1. Interface MCP

**Responsabilidade**: Fornecerá um endpoint compatível com MCP para receber e responder a solicitações de ferramentas.

**Componentes**:
- `MCPServer`: Abstração do servidor MCP que suportará diferentes modos de transporte
- `MCPRouter`: Gerenciará o roteamento de solicitações para os handlers apropriados
- `MCPResponse`: Formatará respostas no padrão MCP

**Tecnologias**:
- MCP-Core para implementação do protocolo MCP
- Express.js para API HTTP

### 2. Camada de Handlers

**Responsabilidade**: Processará requisições específicas das ferramentas, validará parâmetros e orquestrará os serviços.

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

**Responsabilidade**: Implementará a lógica de negócios e orquestrará operações entre repositórios.

**Componentes**:
- `TableService`: Gerenciará operações nas tabelas
- `QueryService`: Construirá e otimizará consultas
- `ValidationService`: Validará dados antes de operações
- `SecurityService`: Gerenciará aspectos de segurança e permissões
- `TransactionService`: Gerenciará transações do PostgreSQL
- `SchemaService`: Gerenciará operações relacionadas a schemas (específico do PostgreSQL)
- `CacheService`: Gerenciará cache de consultas e metadados com Node-cache
- `MetricsService`: Monitorará e analisará métricas de desempenho do sistema

**Padrões**:
- Serviços stateless
- Uso de interfaces para desacoplamento
- Decoradores para instrumentação de métricas

### 4. Camada de Repositório

**Responsabilidade**: Abstrairá acesso a dados e operações no PostgreSQL.

**Componentes**:
- `RepositoryBase`: Interface base para operações CRUD
- `TableRepository`: Implementação específica para tabelas do PostgreSQL
- `QueryBuilder`: Construtor de consultas para o PostgreSQL
- `SchemaRepository`: Manipulará operações de schema (específico do PostgreSQL)

**Padrões**:
- Repository Pattern
- Unit of Work para operações transacionais
- Estratégia de cache para consultas frequentes

### 5. PostgreSQL Driver

**Responsabilidade**: Camada fina que encapsulará a comunicação direta com o banco de dados PostgreSQL.

**Componentes**:
- `PostgreSQLClient`: Wrapper em torno da biblioteca node-postgres (pg)
- `ConnectionManager`: Gerenciará pool de conexões para otimização
- `TransactionManager`: Controlará transações e savepoints
- `PostgresSchemaManager`: Gerencia operações relacionadas ao schema do PostgreSQL
- `PostgresSchemaQueries`: Armazena todas as consultas SQL usadas pelo PostgresSchemaManager
- `PostgresQueryBuilder`: Construtor de consultas SQL para operações dinâmicas

**Tecnologias**:
- Biblioteca node-postgres (pg) para comunicação com PostgreSQL
- Sistema de retry e circuit breaker para resiliência

## Modelos de Dados Planejados

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

## Fluxos de Dados Planejados

### Fluxo de Leitura (Read)

1. Requisição MCP chegará ao `MCPServer`
2. `MCPRouter` roteará para `ReadTableHandler`
3. Handler validará parâmetros usando modelos Joi/Zod
4. `QueryService` construirá a consulta SQL otimizada
5. `TableRepository` executará a consulta via driver PostgreSQL
6. Resultados serão transformados em `DataResponse`
7. Resposta será formatada e retornada ao cliente

### Fluxo de Escrita (Create/Update/Delete)

1. Requisição MCP chegará ao `MCPServer`
2. `MCPRouter` roteará para o handler específico
3. Handler validará parâmetros usando modelos Joi/Zod
4. `ValidationService` validará a integridade dos dados
5. `SecurityService` verificará permissões (se configurado)
6. `TransactionService` iniciará uma transação se necessário
7. `TableRepository` executará a operação via driver PostgreSQL
8. Transação será confirmada (commit) ou revertida (rollback) baseado no resultado
9. Resultados serão transformados em resposta apropriada
10. Resposta será formatada e retornada ao cliente

### Fluxo de Consulta Personalizada (Execute Query)

1. Requisição MCP chegará ao `MCPServer`
2. `MCPRouter` roteará para `ExecuteQueryHandler`
3. Handler validará parâmetros e consulta SQL
4. `SecurityService` verificará permissões para execute_query
5. `ValidationService` sanitizará a consulta SQL para segurança
6. `QueryService` executará a consulta diretamente via driver PostgreSQL
7. Resultados serão transformados em `DataResponse`
8. Resposta será formatada e retornada ao cliente

## Recursos PostgreSQL Específicos a Serem Implementados

### 1. Suporte a Múltiplos Schemas

O PostgreSQL MCP suportará operações em múltiplos schemas, permitindo:
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

## Estratégias de Resiliência Planejadas

1. **Retry com Backoff Exponencial**
   - Tentativas automáticas para falhas transitórias
   - Tempo de espera aumentará exponencialmente entre tentativas

2. **Circuit Breaker**
   - Evitará sobrecarga em caso de falhas persistentes
   - Falha rápido quando o sistema subjacente estiver comprometido

3. **Pool de Conexões**
   - Gerenciamento eficiente de conexões ao PostgreSQL
   - Limite configurável de conexões máximas
   - Keepalive para evitar conexões inativas

4. **Cache**
   - A ser implementado através do CacheService dedicado
   - Armazenamento em cache de:
     - Resultados de consultas (tabelas e SQL personalizadas)
     - Metadados de tabelas e schemas
   - Estratégia TTL (Time to Live) configurável
   - Mecanismos de invalidação automática em operações de escrita

## Sistema de Métricas Planejado

### Arquitetura do MetricsService

O MetricsService será um componente central para monitoramento e diagnóstico de desempenho em todo o sistema PostgreSQL MCP. Será projetado para coletar, armazenar e analisar métricas de desempenho sem impacto significativo na performance do sistema principal.

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
   - Integração com bibliotecas para métricas do sistema operacional
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

O MetricsService será integrado com outros componentes do sistema através de injeção de dependência, permitindo uma instrumentação não-intrusiva e desacoplada da lógica de negócios principal.

## Considerações sobre Segurança

1. **Gestão de Credenciais**
   - Carregamento seguro via variáveis de ambiente
   - Suporte a conexão via SSL/TLS
   - Nunca expostas em logs ou respostas

2. **Validação de Entrada**
   - Validação rigorosa para prevenir injeção SQL
   - Parametrização de todas as consultas
   - Joi/Zod para validação de esquema

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

## Plano de Testes

A estratégia de testes do PostgreSQL MCP será abrangente, cobrindo múltiplos níveis:

### Testes Unitários

* **Testes de Serviços**: Verificarão a lógica de negócio isoladamente
* **Testes de Handlers**: Verificarão o processamento de requisições
* **Testes de Modelos**: Assegurarão a correta validação e comportamento dos modelos de dados
* **Testes de Filtros**: Validarão a conversão correta dos modelos de filtro para SQL
* **Testes do QueryBuilder**: Verificarão a geração adequada de consultas SQL com filtros complexos

### Testes de Integração

* **Testes com PostgreSQL Real**: Usando Docker para criar bancos de teste
* **Testes End-to-End**: Simulando o fluxo completo de requisições MCP

### Ambiente de Testes

* **Banco de Dados de Teste**: PostgreSQL em contêiner Docker
* **Fixtures de Teste**: Dados pré-definidos para testes consistentes
* **Mocks e Stubs**: Para componentes externos e serviços dependentes

## Extensibilidade

A arquitetura do PostgreSQL MCP será projetada para ser extensível:

* **Handlers Plugáveis**: Novos handlers poderão ser adicionados facilmente
* **Serviços Modulares**: Serviços poderão ser estendidos ou substituídos
* **Filtros Customizáveis**: O sistema de filtros poderá ser estendido para novos tipos ou operadores
* **Transporte Flexível**: Novos modos de transporte poderão ser adicionados (gRPC, WebSockets, etc.)

## Configuração e Deployment

O PostgreSQL MCP suportará várias opções de configuração e deployment:

* **Variáveis de Ambiente**: Configuração via variáveis de ambiente
* **Arquivo de Configuração**: Configuração via arquivo JSON/YAML
* **Programática**: Configuração via API
* **Deployment**: Suporte para deployment como serviço standalone, Docker, ou função serverless

## Serviços Auxiliares Implementados

O PostgreSQL MCP implementou quatro serviços auxiliares principais que fornecem funcionalidades complementares para a operação do sistema.

### 1. LoggingService

O LoggingService implementa um sistema de logging avançado baseado na biblioteca Winston, fornecendo recursos de registro extensivos e configuráveis.

**Características principais:**

- **Múltiplos níveis de log**: error, warn, info, http, verbose, debug, silly
- **Rotação de logs diária**: utilizando winston-daily-rotate-file para gerenciamento automático de arquivos
- **Formatos personalizáveis**: suporte para formatos JSON e texto, com capacidade de personalização
- **Loggers específicos por componente**: permitindo filtrar logs por componente do sistema
- **Transporte para console e arquivo**: configurável independentemente com níveis de log específicos
- **Registro de erros aprimorado**: captura completa dos stack traces e metadados adicionais

**Exemplo de uso:**

```typescript
// Criação de um logger com configuração personalizada
const logger = new LoggingService({}, {
  logDir: './logs',
  level: 'debug',
  enableConsole: true,
  enableFileLogging: true,
  rotation: {
    maxSize: '10m',
    maxFiles: 5
  }
});

// Usando um logger específico para um componente
const dbLogger = logger.getComponentLogger('Database');
dbLogger.info('Conexão estabelecida');
dbLogger.warn('Consulta lenta detectada', { query: 'SELECT * FROM large_table', duration: '200ms' });
```

### 2. CacheService

O CacheService implementa um sistema de cache em memória para melhorar o desempenho de operações repetitivas ou custosas.

**Características principais:**

- **Cache baseado em TTL (Time To Live)**: controle de expiração automatizado
- **Estratégia LRU (Least Recently Used)**: para evitar excesso de consumo de memória
- **Invalidação baseada em tags**: permitindo invalidar grupos de entradas relacionadas
- **Estatísticas de desempenho**: monitoramento de hits, misses e uso de memória
- **API assíncrona com padrão getOrSet**: minimizando recálculos desnecessários
- **Cache de múltiplas camadas**: suporte para cache de metadados, schemas e tabelas

**Exemplo de uso:**

```typescript
// Inicialização do serviço de cache
const cache = new CacheService({
  defaultTtl: 60 * 1000, // 1 minuto
  maxItems: 1000,
  checkInterval: 5 * 60 * 1000 // 5 minutos
});

// Padrão getOrSet para cálculos caros
const data = await cache.getOrSet(
  'expensive-calculation',
  async () => {
    // Cálculo custoso só executado em caso de cache miss
    return performExpensiveCalculation();
  },
  { ttl: 300 * 1000 } // 5 minutos
);

// Invalidação baseada em tag quando os dados mudam
await cache.invalidateByTag('user-data');

// Obter estatísticas do cache
const stats = cache.getStats();
console.log(`Taxa de acerto: ${stats.hitRate * 100}%`);
```

### 3. MetricsService

O MetricsService implementa um sistema de coleta e análise de métricas de desempenho para monitoramento em tempo real.

**Características principais:**

- **Métricas de temporização**: medindo duração de operações críticas
- **Contadores e medidores**: para estatísticas de operações e uso de recursos
- **Sistema de eventos baseado em observadores**: para notificações de eventos de métrica
- **Métricas de memória e sistema**: monitoramento de recursos do sistema
- **Relatórios de desempenho**: geração de relatórios detalhados com estatísticas agregadas
- **Medição assíncrona simplificada**: usando padrão de alto nível para medir operações assíncronas

**Exemplo de uso:**

```typescript
// Inicialização do serviço de métricas
const metrics = new MetricsService({
  enableDetailedMetrics: true,
  trackMemoryUsage: true
});

// Inscrição em eventos de métrica para logging ou alertas
metrics.subscribe('timing', (metric) => {
  if (metric.duration > 500) {
    logger.warn(`Operação lenta detectada: ${metric.category}.${metric.name} - ${metric.duration}ms`);
  }
});

// Medição de operações assíncronas
const result = await metrics.measure(
  'database',
  'query-execution',
  async () => {
    return await connection.query('SELECT * FROM large_table');
  },
  { query: 'SELECT * FROM large_table' }
);

// Obtenção de estatísticas
const stats = metrics.getTimingStats('database');
console.log(`Tempo médio de consulta: ${stats.avgTime.toFixed(2)}ms`);
```

### 4. SecurityService

O SecurityService implementa um sistema de controle de acesso baseado em papéis (RBAC) para proteger recursos no banco de dados.

**Características principais:**

- **Controle de acesso baseado em papéis (RBAC)**: com permissões granulares
- **Permissões específicas por recurso**: permitindo controle preciso sobre tabelas e operações
- **Níveis de permissão hierárquicos**: READ, WRITE, ADMIN, etc.
- **Gerenciamento de usuários integrado**: com suporte para múltiplos papéis por usuário
- **Registro de eventos de segurança**: para auditoria e conformidade
- **Modo estrito opcional**: requer permissões explícitas para todas as operações

**Exemplo de uso:**

```typescript
// Inicialização do serviço de segurança
const security = new SecurityService({
  enabled: true,
  strictMode: false,
  logEvents: true
});

// Registro de papéis com permissões específicas
security.registerRole({
  name: 'analyst',
  description: 'Analista de dados com acesso de leitura',
  defaultPermission: PermissionLevel.READ,
  permissions: [
    {
      resourceType: ResourceType.TABLE,
      resourceName: 'public.sales',
      permissionLevel: PermissionLevel.READ
    }
  ]
});

// Verificação de permissões
const canExecuteQuery = security.hasPermission(
  'user-123',
  ResourceType.TABLE,
  'public.sales',
  PermissionLevel.READ,
  { operation: 'SELECT' }
);

// Aplicação de permissões (lança exceção se não permitido)
security.enforcePermission(
  'user-123',
  ResourceType.TABLE,
  'public.sales',
  PermissionLevel.WRITE,
  { operation: 'UPDATE' }
);
```

Estes serviços auxiliares trabalham em conjunto com os serviços principais (TableService, QueryService, SchemaService e TransactionService) para fornecer uma experiência completa e robusta de acesso a bancos de dados PostgreSQL, com foco em desempenho, segurança e monitoramento.