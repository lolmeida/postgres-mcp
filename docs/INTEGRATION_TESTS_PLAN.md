# Plano de Implementação de Testes de Integração com PostgreSQL

Este documento detalha o plano para implementação de testes de integração para o PostgreSQL MCP, usando um banco de dados PostgreSQL real através do Docker.

## Objetivos

1. Validar o funcionamento real do PostgreSQL MCP com um banco de dados PostgreSQL
2. Testar o comportamento das operações em condições reais
3. Verificar a corretude das consultas SQL geradas
4. Testar o desempenho das operações

## Ferramentas a Serem Utilizadas

- **Docker**: Para iniciar instâncias isoladas de PostgreSQL
- **Jest**: Para estrutura de testes
- **jest-extended**: Para asserções estendidas
- **testcontainers**: Para gerenciamento de contêineres Docker em testes
- **node-postgres**: Cliente PostgreSQL

## Estrutura de Diretórios Planejada

```
tests/
├── integration/                   # Testes de integração
│   ├── setup.js                   # Configuração para testes de integração
│   ├── crud.test.js               # Testes de operações CRUD
│   ├── transactions.test.js       # Testes de transações
│   ├── filters.test.js            # Testes do sistema de filtros com DB real
│   ├── postgres-features.test.js  # Testes de recursos específicos do PostgreSQL
│   └── README.md                  # Documentação dos testes de integração
└── fixtures/                      # Dados de teste reutilizáveis
    ├── schemas.sql                # Definições de esquemas para testes
    ├── tables.sql                 # Definições de tabelas para testes
    └── sample_data.sql            # Dados de amostra para testes
```

## Plano de Implementação

### 1. Configuração do Ambiente de Teste

- [ ] Criar estrutura de diretórios para testes de integração
- [ ] Configurar Jest com configurações para testes de integração
- [ ] Implementar setup.js com fixtures para contêiner Docker PostgreSQL
- [ ] Criar script de inicialização do banco de dados de teste

### 2. Testes de Operações CRUD

- [ ] Testes de criação de registros (insert)
- [ ] Testes de leitura de registros (select)
- [ ] Testes de atualização de registros (update)
- [ ] Testes de exclusão de registros (delete)
- [ ] Testes de operações em lote

### 3. Testes de Transações

- [ ] Testes de commit de transações
- [ ] Testes de rollback de transações
- [ ] Testes de transações aninhadas
- [ ] Testes de isolamento de transações

### 4. Testes de Filtros com Banco de Dados Real

- [ ] Testes de filtros de comparação
- [ ] Testes de filtros de texto
- [ ] Testes de filtros de lista
- [ ] Testes de filtros para valores nulos
- [ ] Testes de filtros para arrays
- [ ] Testes de filtros para campos JSON/JSONB
- [ ] Testes de filtros para tipos geométricos

### 5. Testes de Recursos Específicos do PostgreSQL

- [ ] Testes de views (criação, consulta, atualização, exclusão)
- [ ] Testes de funções armazenadas (criação, execução, exclusão)
- [ ] Testes de triggers
- [ ] Testes de CTEs (Common Table Expressions)
- [ ] Testes de Window Functions

### 6. Testes de Desempenho

- [ ] Testes de throughput para operações CRUD
- [ ] Testes de latência para consultas complexas
- [ ] Testes de concorrência
- [ ] Testes de carga com volumes grandes de dados

## Potenciais Desafios e Estratégias

Durante a implementação dos testes de integração, podemos enfrentar os seguintes desafios:

1. **Gerenciamento de Dependências**: Configurar e inicializar corretamente o PostgreSQL em um ambiente de testes automatizados.
   - **Estratégia**: Utilizar a biblioteca testcontainers para gerenciar os contêineres Docker de forma consistente.

2. **Isolamento de Testes**: Garantir que cada teste seja executado em um ambiente limpo.
   - **Estratégia**: Implementar limpeza automática do banco após cada teste ou utilizar schemas temporários.

3. **Concorrência**: Lidar com possíveis problemas de concorrência durante testes paralelos.
   - **Estratégia**: Configurar os testes para executarem sequencialmente ou implementar mecanismos de isolamento de dados.

## Proposta de Implementação do Docker Container

```javascript
const { GenericContainer } = require('testcontainers');
const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Fixture para o contêiner PostgreSQL
const setupPostgresContainer = async () => {
  // Iniciar um contêiner PostgreSQL
  const container = await new GenericContainer('postgres:15.3')
    .withExposedPorts(5432)
    .withEnvironment({
      POSTGRES_USER: 'postgres',
      POSTGRES_PASSWORD: 'postgres',
      POSTGRES_DB: 'test_db'
    })
    .start();
  
  // Obter informações de conexão
  const connectionInfo = {
    host: container.getHost(),
    port: container.getMappedPort(5432),
    user: 'postgres',
    password: 'postgres',
    database: 'test_db'
  };

  // Configurar cliente PostgreSQL
  const client = new Client(connectionInfo);
  await client.connect();
  
  // Inicializar o banco de dados com os scripts de teste
  const schemasSQL = fs.readFileSync(
    path.join(__dirname, '../fixtures/schemas.sql'),
    'utf8'
  );
  const tablesSQL = fs.readFileSync(
    path.join(__dirname, '../fixtures/tables.sql'),
    'utf8'
  );
  const sampleDataSQL = fs.readFileSync(
    path.join(__dirname, '../fixtures/sample_data.sql'),
    'utf8'
  );
  
  await client.query(schemasSQL);
  await client.query(tablesSQL);
  await client.query(sampleDataSQL);
  
  // Retornar container e cliente para uso nos testes
  return {
    container,
    client,
    connectionInfo
  };
};

module.exports = { setupPostgresContainer };
```

## Próximos Passos

1. **Configuração de Ambiente**: Implementar a estrutura básica de diretórios e configuração de Jest
2. **Implementação de Fixtures**: Desenvolver scripts SQL para criação de schemas, tabelas e dados de exemplo
3. **Testes Básicos**: Implementar testes iniciais de operações CRUD
4. **Testes Avançados**: Desenvolver testes de transações e recursos específicos
5. **Testes de Desempenho**: Implementar testes de desempenho e carga

## Cronograma Proposto

1. **Sprint 1**: Configuração de ambiente e implementação de fixtures (Semanas 1-2)
2. **Sprint 2**: Testes de operações CRUD e transações (Semanas 3-4)
3. **Sprint 3**: Testes de filtros e recursos específicos do PostgreSQL (Semanas 5-6)
4. **Sprint 4**: Testes de desempenho e integração com CI/CD (Semanas 7-8)

## Considerações de CI/CD

Para execução em ambientes de CI/CD, considerar:
- Configurar workflow específico para testes de integração
- Usar caching para imagens Docker
- Executar testes de integração após testes unitários bem-sucedidos
- Configurar timeouts adequados para testes de desempenho 