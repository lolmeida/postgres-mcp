/**
 * Exemplo Básico de Uso do PostgreSQL MCP
 * 
 * Este exemplo demonstra a configuração e uso básico do PostgreSQL MCP.
 */

import { PostgresMCPServer, MCPConfig } from '../src/index';

// Função principal assíncrona
async function main() {
  console.log('Iniciando exemplo básico do PostgreSQL MCP');

  // Configurando o servidor MCP
  const config: Partial<MCPConfig> = {
    // Configurações de conexão com o banco de dados
    dbHost: 'localhost',
    dbPort: 5432,
    dbName: 'mcp_example',
    dbUser: 'postgres',
    dbPassword: 'postgres',
    
    // Configurações do servidor MCP
    mode: 'stdio', // Pode ser 'http' para API REST
    logLevel: 'info',
    
    // Outras configurações
    poolMinSize: 1,
    poolMaxSize: 5,
    cacheTtl: 60 // segundos
  };

  // Criar instância do servidor MCP
  const mcpServer = new PostgresMCPServer(config);
  
  try {
    // Iniciar o servidor
    console.log('Iniciando servidor MCP...');
    await mcpServer.start();
    
    // Exemplo de como enviar uma requisição MCP (simulado, já que o modo real seria STDIO/HTTP)
    const response = await mcpServer.handle({
      tool: 'list_tables',
      parameters: {
        schema: 'public'
      }
    });
    
    console.log('Resposta do MCP:', JSON.stringify(response, null, 2));
    
    // Parar o servidor após o uso
    console.log('Parando servidor MCP...');
    await mcpServer.stop();
    
    console.log('Exemplo finalizado com sucesso');
  } catch (error) {
    console.error('Erro ao executar exemplo:', error);
  }
}

// Executar o exemplo
main().catch(console.error); 