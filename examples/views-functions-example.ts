/**
 * Exemplo de uso das funcionalidades de views e funções no MCP PostgreSQL
 * 
 * Este exemplo demonstra como utilizar os novos recursos para:
 * - Listar views em um schema
 * - Obter detalhes de uma view específica
 * - Atualizar uma view materializada
 * - Listar funções em um schema
 * - Obter detalhes de uma função específica
 * - Executar uma função armazenada
 */

import { config } from 'dotenv';
import { PostgresMCPServer } from '../src/mcp/server/PostgresMCPServer';
import { ViewService } from '../src/services/ViewService';
import { FunctionService } from '../src/services/FunctionService';
import { createComponentLogger } from '../src/utils/logger';

// Carrega variáveis de ambiente do arquivo .env, se existir
config();

// Configura logger
const logger = createComponentLogger('Example');

/**
 * Função de exemplo principal
 */
async function runExample() {
  try {
    logger.info('Iniciando exemplo de views e funções...');
    
    // Configuração para o servidor PostgreSQL MCP
    const serverOptions = {
      database: {
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || '5432'),
        database: process.env.DB_NAME || 'postgres',
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'postgres',
        defaultSchema: 'public'
      },
      logging: {
        level: 'debug',
        enableConsole: true
      }
    };
    
    // Cria o servidor PostgreSQL MCP (apenas para obtermos a conexão e serviços)
    logger.info('Criando instância do servidor...');
    const mcpServer = new PostgresMCPServer(serverOptions);
    
    // Obtém os serviços necessários
    const viewService = mcpServer.getService('view') as ViewService;
    const functionService = mcpServer.getService('function') as FunctionService;
    
    // Inicia o servidor (estabelece conexão com o banco de dados)
    await mcpServer.start();
    
    logger.info('Conexão estabelecida com o banco de dados');
    
    // Exemplo 1: Criar uma view regular
    logger.info('Exemplo 1: Criando uma view regular...');
    await createSampleView();
    
    // Exemplo 2: Listar views em um schema
    logger.info('Exemplo 2: Listando views...');
    const views = await viewService.listViews('public', {
      includeRegularViews: true,
      includeMaterializedViews: true
    });
    
    logger.info(`Encontradas ${views.length} views:`);
    views.forEach(view => {
      logger.info(`  - ${view.viewName} (${view.viewType})`);
    });
    
    // Exemplo 3: Obter detalhes de uma view específica
    if (views.length > 0) {
      const viewName = views[0].viewName;
      logger.info(`Exemplo 3: Obtendo detalhes da view "${viewName}"...`);
      
      const viewDetails = await viewService.getViewDetails(viewName, 'public', {
        includeColumns: true,
        includeDefinition: true
      });
      
      logger.info('Detalhes da view:');
      logger.info(`  - Nome: ${viewDetails.viewName}`);
      logger.info(`  - Schema: ${viewDetails.schemaName}`);
      logger.info(`  - Tipo: ${viewDetails.viewType}`);
      logger.info(`  - Definição: ${viewDetails.definition}`);
      
      if (viewDetails.columns && viewDetails.columns.length > 0) {
        logger.info('  - Colunas:');
        viewDetails.columns.forEach(column => {
          logger.info(`    - ${column.name} (${column.type})`);
        });
      }
    }
    
    // Exemplo 4: Criar uma view materializada
    logger.info('Exemplo 4: Criando uma view materializada...');
    await createSampleMaterializedView();
    
    // Exemplo 5: Atualizar uma view materializada
    logger.info('Exemplo 5: Atualizando view materializada...');
    const refreshResult = await viewService.refreshMaterializedView('sample_mview', 'public', {
      concurrently: false,
      withData: true
    });
    
    logger.info(`Resultado do refresh: ${refreshResult ? 'Sucesso' : 'Falha'}`);
    
    // Exemplo 6: Criar uma função armazenada
    logger.info('Exemplo 6: Criando uma função armazenada...');
    await createSampleFunction();
    
    // Exemplo 7: Listar funções em um schema
    logger.info('Exemplo 7: Listando funções...');
    const functions = await functionService.listFunctions('public', {
      includeFunctions: true,
      includeProcedures: true
    });
    
    logger.info(`Encontradas ${functions.length} funções:`);
    functions.forEach(func => {
      logger.info(`  - ${func.functionName} (${func.functionType})`);
    });
    
    // Exemplo 8: Obter detalhes de uma função específica
    if (functions.length > 0) {
      // Filtra para encontrar nossa função de exemplo
      const sampleFunc = functions.find(f => f.functionName === 'get_sample_data');
      
      if (sampleFunc) {
        logger.info(`Exemplo 8: Obtendo detalhes da função "${sampleFunc.functionName}"...`);
        
        const functionDetails = await functionService.getFunctionDetails(
          sampleFunc.functionName, 
          'public', 
          { includeDefinition: true }
        );
        
        logger.info('Detalhes da função:');
        logger.info(`  - Nome: ${functionDetails.functionName}`);
        logger.info(`  - Schema: ${functionDetails.schemaName}`);
        logger.info(`  - Tipo: ${functionDetails.functionType}`);
        logger.info(`  - Retorno: ${functionDetails.returnType}`);
        logger.info(`  - Linguagem: ${functionDetails.language}`);
        logger.info(`  - Argumentos: ${functionDetails.arguments.map(arg => arg.name).join(', ')}`);
        
        if (functionDetails.definition) {
          logger.info(`  - Definição: ${functionDetails.definition.substring(0, 100)}...`);
        }
      }
    }
    
    // Exemplo 9: Executar uma função armazenada
    logger.info('Exemplo 9: Executando função...');
    const result = await functionService.executeFunction({
      functionName: 'get_sample_data',
      schemaName: 'public',
      args: [5] // Número de registros para retornar
    });
    
    logger.info('Resultado da execução da função:');
    console.log(result);
    
    logger.info('Exemplo concluído com sucesso!');
    
    // Encerra o servidor
    await mcpServer.stop();
    process.exit(0);
    
  } catch (error: any) {
    logger.error('Erro durante a execução do exemplo:', error);
    process.exit(1);
  }
}

/**
 * Helper para criar uma view regular de exemplo
 */
async function createSampleView() {
  const { Client } = require('pg');
  const client = new Client({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres'
  });
  
  try {
    await client.connect();
    
    // Cria tabela de exemplo se não existir
    await client.query(`
      CREATE TABLE IF NOT EXISTS sample_data (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        value NUMERIC,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);
    
    // Insere dados de exemplo se tabela estiver vazia
    const countResult = await client.query('SELECT COUNT(*) FROM sample_data');
    if (parseInt(countResult.rows[0].count) === 0) {
      await client.query(`
        INSERT INTO sample_data (name, value) VALUES
        ('Item 1', 10.5),
        ('Item 2', 20.75),
        ('Item 3', 30),
        ('Item 4', 40.25),
        ('Item 5', 50.5)
      `);
    }
    
    // Cria view de exemplo
    await client.query(`
      CREATE OR REPLACE VIEW sample_view AS
      SELECT id, name, value, created_at
      FROM sample_data
      WHERE value > 15
    `);
    
    logger.info('View regular criada com sucesso');
    
  } catch (error) {
    logger.error('Erro ao criar view regular:', error);
    throw error;
  } finally {
    await client.end();
  }
}

/**
 * Helper para criar uma view materializada de exemplo
 */
async function createSampleMaterializedView() {
  const { Client } = require('pg');
  const client = new Client({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres'
  });
  
  try {
    await client.connect();
    
    // Drop view first if it exists
    await client.query(`
      DROP MATERIALIZED VIEW IF EXISTS sample_mview
    `);
    
    // Create materialized view
    await client.query(`
      CREATE MATERIALIZED VIEW sample_mview AS
      SELECT id, name, value, created_at, 
             CASE WHEN value > 30 THEN 'High' ELSE 'Low' END as value_category
      FROM sample_data
      WITH DATA
    `);
    
    logger.info('View materializada criada com sucesso');
    
  } catch (error) {
    logger.error('Erro ao criar view materializada:', error);
    throw error;
  } finally {
    await client.end();
  }
}

/**
 * Helper para criar uma função armazenada de exemplo
 */
async function createSampleFunction() {
  const { Client } = require('pg');
  const client = new Client({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres'
  });
  
  try {
    await client.connect();
    
    // Cria função de exemplo
    await client.query(`
      CREATE OR REPLACE FUNCTION get_sample_data(limit_count INTEGER)
      RETURNS TABLE (
        id INTEGER,
        name TEXT,
        value NUMERIC,
        created_at TIMESTAMP
      )
      LANGUAGE SQL
      STABLE
      AS $$
        SELECT id, name, value, created_at
        FROM sample_data
        ORDER BY value DESC
        LIMIT limit_count;
      $$;
    `);
    
    logger.info('Função criada com sucesso');
    
  } catch (error) {
    logger.error('Erro ao criar função:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// Executa o exemplo
runExample(); 