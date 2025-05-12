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

### 4. Testar a conexão

Após iniciar os serviços, você pode testar a conexão executando um dos exemplos:

```bash
npx ts-node examples/basic-usage.ts
```

## 🛠️ Instalação e Uso Manual

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/mcp-postgres-js.git
cd mcp-postgres-js

# Instale as dependências
npm install

# Construa o projeto
npm run build
```

### Configuração

1. Crie um arquivo `.env` baseado no `.env.example`:

```bash
cp .env.example .env
```

2. Edite o arquivo `.env` para configurar as credenciais do PostgreSQL e outras opções.

### Executar em modo de desenvolvimento

```bash
npm run dev
```

### Executar os testes

```bash
npm test
```

## 📚 Documentação

Consulte a [documentação completa](docs/index.md) para:

- [Guia de Início Rápido](docs/guides/getting-started.md)
- [Referência de API](docs/API_REFERENCE.md)
- [Exemplos de Código](docs/CODE_EXAMPLES.md)
- [Arquitetura do Projeto](docs/ARCHITECTURE.md)

## 🔄 Operações Básicas

### Construir o projeto

```bash
npm run build
```

### Executar o linter

```bash
npm run lint
```

### Formatar o código

```bash
npm run format
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, verifique as [diretrizes de contribuição](CONTRIBUTING.md) antes de enviar um pull request.

## 📝 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes. 