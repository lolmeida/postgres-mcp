# PostgreSQL MCP para JavaScript

PostgreSQL Model Context Protocol (MCP) para integração com LLMs utilizando JavaScript/Node.js.

## 📋 Requisitos

- Node.js 16+
- npm ou yarn
- Docker (opcional, para ambiente de desenvolvimento)

## 🚀 Início Rápido com Docker

A maneira mais fácil de executar o PostgreSQL MCP é usando Docker Compose, que gerencia tanto o banco de dados PostgreSQL quanto o servidor MCP.

### 1. Iniciar os serviços

```bash
./run-mcp.sh start
```

Este comando inicia o PostgreSQL e o servidor MCP. O PostgreSQL estará disponível na porta 5432 e o servidor MCP na porta 8432.

### 2. Verificar o status dos serviços

```bash
./run-mcp.sh ps
```

### 3. Visualizar logs

```bash
./run-mcp.sh logs
```

### 4. Testar a conexão com o MCP

```bash
./run-mcp.sh test
```

### 5. Parar os serviços

```bash
./run-mcp.sh stop
```

## 🔄 Integração com o Cursor

Para configurar o Cursor para usar o PostgreSQL MCP:

1. Inicie os serviços Docker:
   ```bash
   ./run-mcp.sh start
   ```

2. Configure o Cursor:
   ```bash
   ./run-mcp.sh setup-cursor
   ```

3. Reinicie o Cursor.

4. Nas configurações do Cursor, vá para a seção MCP e verifique se o servidor "postgres" está habilitado.

## 🛠️ Desenvolvimento Local

Para desenvolvimento local sem Docker:

1. Clone o repositório e instale as dependências:
   ```bash
   git clone https://github.com/seu-usuario/mcp-postgres-js.git
   cd mcp-postgres-js
   npm install
   ```

2. Configure as variáveis de ambiente em um arquivo `.env`:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=postgres
   MCP_PORT=8432
   MCP_MODE=http
   ```

3. Inicie o PostgreSQL:
   ```bash
   docker start postgres-mcp
   ```

4. Inicie o servidor MCP:
   ```bash
   npm start
   ```

## 📚 Referências

- [Documentação do MCP](https://cursor.sh/docs/mcp)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [node-postgres](https://node-postgres.com/)

## 📝 Licença

Este projeto é licenciado sob os termos da licença MIT.

## Status do Projeto

Status atual: **Versão 0.1.0** (Em desenvolvimento inicial)

O PostgreSQL MCP para JavaScript está em fase inicial de desenvolvimento. O projeto visa implementar as seguintes funcionalidades:

- Operações CRUD completas (criar, ler, atualizar, excluir)
- Sistema de filtros avançado
- Gerenciamento de transações
- Compatibilidade com múltiplos schemas
- Modos de transporte STDIO e HTTP
- Sistema de cache para otimização de consultas
- Sistema de métricas para monitoramento de desempenho
- Suporte a tipos de dados PostgreSQL específicos:
  - Arrays
  - JSON/JSONB
  - Tipos geométricos (point, line, box, polygon)
- Gerenciamento de views e funções

## Sobre o Projeto

PostgreSQL MCP permite que LLMs realizem operações complexas em bancos de dados PostgreSQL através de um conjunto de comandos padronizados. Isso inclui consultas, mutações e análises de dados, tudo através de uma interface unificada.

### Recursos Planejados

- 🔍 **Consultas Flexíveis**: Filtros avançados, ordenação e projeção de colunas
- 🛠️ **Operações Completas de CRUD**: Criação, leitura, atualização e exclusão
- 🔄 **Transações**: Suporte completo a transações, garantindo integridade dos dados
- 📊 **Análise de Esquema**: Descoberta automática de tabelas, colunas e tipos de dados
- 🔐 **Segurança**: Proteção contra injeção SQL e validação de entrada
- 🚀 **Performance**: Cache otimizado e pool de conexões eficiente
- 📏 **Métricas**: Monitoramento de performance e uso de recursos

## Instalação (A ser implementado)

Após o desenvolvimento, a instalação será feita via:

### Via npm

```bash
npm install mcp-postgres-js
```

### Via yarn

```bash
yarn add mcp-postgres-js
```

### A partir do repositório

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/mcp-postgres-js.git
cd mcp-postgres-js

# Instale as dependências
npm install

# Execute o servidor MCP
npm start
```

## Uso Básico (Exemplo Planejado)

```javascript
const { PostgresMCPServer } = require('mcp-postgres-js');
require('dotenv').config();

// Criar e iniciar o servidor MCP
const server = new PostgresMCPServer({
  dbHost: process.env.DB_HOST || 'localhost',
  dbPort: parseInt(process.env.DB_PORT || '5432'),
  dbName: process.env.DB_NAME || 'postgres',
  dbUser: process.env.DB_USER || 'postgres',
  dbPassword: process.env.DB_PASSWORD || 'postgres',
  mode: process.env.MCP_MODE || 'http',
  port: parseInt(process.env.MCP_PORT || '8432')
});

server.start().then(() => {
  console.log('PostgreSQL MCP server started!');
}).catch(err => {
  console.error('Failed to start PostgreSQL MCP server:', err);
});
```

## Exemplo de Comandos Planejados

### Listar Tabelas

```json
{
  "tool": "list_tables",
  "parameters": {
    "schema": "public"
  }
}
```

### Ler Registros

```json
{
  "tool": "read_table",
  "parameters": {
    "table": "users",
    "filters": {
      "active": true,
      "age": { "gte": 18 }
    },
    "columns": ["id", "name", "email"],
    "limit": 100,
    "order_by": "name",
    "ascending": true
  }
}
```

### Criar Registro

```json
{
  "tool": "create_record",
  "parameters": {
    "table": "products",
    "data": {
      "name": "Smartphone XYZ",
      "price": 999.99,
      "in_stock": true,
      "categories": ["electronics", "mobile"],
      "specs": {
        "cpu": "Octa-core",
        "ram": "8GB",
        "storage": "128GB"
      },
      "store_locations": [
        {"lat": 37.7749, "lng": -122.4194},
        {"lat": 40.7128, "lng": -74.0060}
      ]
    }
  }
}
```

## Documentação

A documentação detalhada será desenvolvida ao longo do projeto:

- [API Reference](docs/API_REFERENCE.md)
- [Exemplos de Código](docs/CODE_EXAMPLES.md)
- [Guia de Configuração](docs/CONFIGURATION.md)
- [Arquitetura](docs/ARCHITECTURE.md)

## Contribuição

Contribuições são bem-vindas! Por favor, consulte [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Roadmap

Veja o [TASK.md](docs/TASK.md) para acompanhar o progresso do desenvolvimento e as funcionalidades planejadas. 