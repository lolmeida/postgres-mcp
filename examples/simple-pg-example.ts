/**
 * Exemplo simples e independente para testar views e funções no PostgreSQL
 * Não depende dos serviços implementados no projeto, apenas do driver pg do PostgreSQL.
 */

import { Client } from 'pg';
import { config } from 'dotenv';

// Carrega variáveis de ambiente
config();

// Definindo interfaces para tipagem
interface FunctionParameter {
  name: string;
  type: string;
  position: number;
}

interface DatabaseFunction {
  name: string;
  type: string;
  returnType: string;
  parameters: FunctionParameter[];
}

// Função principal de exemplo
async function runSimpleExample() {
  console.log('Iniciando teste simples de views e funções no PostgreSQL...');
  
  // Cria cliente de conexão com o PostgreSQL
  const client = new Client({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres'
  });
  
  try {
    // Conecta ao banco de dados
    console.log('Conectando ao PostgreSQL...');
    await client.connect();
    console.log('Conexão estabelecida!');
    
    // 1. Criar tabela de exemplo
    console.log('\n1. Criando tabela de exemplo...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS sample_data (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        value NUMERIC,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);
    
    // 2. Inserir dados de exemplo se tabela estiver vazia
    const countResult = await client.query('SELECT COUNT(*) FROM sample_data');
    if (parseInt(countResult.rows[0].count) === 0) {
      console.log('Inserindo dados de exemplo...');
      await client.query(`
        INSERT INTO sample_data (name, value) VALUES
        ('Item 1', 10.5),
        ('Item 2', 20.75),
        ('Item 3', 30),
        ('Item 4', 40.25),
        ('Item 5', 50.5)
      `);
    }
    
    // 3. Criar uma view regular
    console.log('\n2. Criando uma view regular...');
    await client.query(`
      CREATE OR REPLACE VIEW sample_view AS
      SELECT id, name, value, created_at
      FROM sample_data
      WHERE value > 15
    `);
    
    // 4. Listar views no schema public
    console.log('\n3. Listando views no schema public...');
    const viewsResult = await client.query(`
      SELECT table_name AS view_name, view_definition
      FROM information_schema.views
      WHERE table_schema = 'public'
    `);
    
    console.log('Views encontradas:');
    viewsResult.rows.forEach((view: { view_name: string; view_definition: string }) => {
      console.log(`- ${view.view_name}: ${view.view_definition.substring(0, 50)}...`);
    });
    
    // 5. Consultar dados da view
    console.log('\n4. Consultando dados da view sample_view...');
    const viewDataResult = await client.query('SELECT * FROM sample_view');
    console.log('Dados da view:');
    console.table(viewDataResult.rows);
    
    // 6. Criar uma view materializada
    console.log('\n5. Criando uma view materializada...');
    await client.query(`
      DROP MATERIALIZED VIEW IF EXISTS sample_mview
    `);
    
    await client.query(`
      CREATE MATERIALIZED VIEW sample_mview AS
      SELECT id, name, value, created_at, 
             CASE WHEN value > 30 THEN 'High' ELSE 'Low' END as value_category
      FROM sample_data
      WITH DATA
    `);
    
    // 7. Listar views materializadas
    console.log('\n6. Listando views materializadas...');
    const mviewsResult = await client.query(`
      SELECT matviewname, matviewowner, ispopulated
      FROM pg_matviews
      WHERE schemaname = 'public'
    `);
    
    console.log('Views materializadas encontradas:');
    console.table(mviewsResult.rows);
    
    // 8. Consultar dados da view materializada
    console.log('\n7. Consultando dados da view materializada...');
    const mviewDataResult = await client.query('SELECT * FROM sample_mview');
    console.log('Dados da view materializada:');
    console.table(mviewDataResult.rows);
    
    // 9. Atualizar a view materializada
    console.log('\n8. Atualizando a view materializada...');
    await client.query('REFRESH MATERIALIZED VIEW sample_mview');
    console.log('View materializada atualizada com sucesso!');
    
    // 10. Criar uma função armazenada
    console.log('\n9. Criando uma função armazenada...');
    await client.query(`
      CREATE OR REPLACE FUNCTION get_sample_data(limit_count INTEGER)
      RETURNS TABLE (
        id INTEGER,
        name TEXT,
        value NUMERIC,
        value_category TEXT
      )
      LANGUAGE SQL
      STABLE
      AS $$
        SELECT id, name, value, 
               CASE WHEN value > 30 THEN 'High' ELSE 'Low' END as value_category
        FROM sample_data
        ORDER BY value DESC
        LIMIT limit_count;
      $$;
    `);
    
    // 11. Listar funções no schema public
    console.log('\n10. Listando funções no schema public...');
    const functionsResult = await client.query(`
      SELECT routines.routine_name AS function_name,
             routines.routine_type AS function_type,
             routines.data_type AS return_type,
             parameters.parameter_name,
             parameters.data_type AS parameter_type,
             parameters.ordinal_position
      FROM information_schema.routines
      LEFT JOIN information_schema.parameters ON 
           routines.specific_name = parameters.specific_name
      WHERE routines.specific_schema = 'public'
        AND routines.routine_name NOT LIKE 'pg_%'
      ORDER BY routines.routine_name, parameters.ordinal_position
    `);
    
    // Organizar as funções de maneira mais estruturada
    const functions: Record<string, DatabaseFunction> = {};
    functionsResult.rows.forEach((row: any) => {
      if (!functions[row.function_name]) {
        functions[row.function_name] = {
          name: row.function_name,
          type: row.function_type,
          returnType: row.return_type,
          parameters: []
        };
      }
      
      if (row.parameter_name) {
        functions[row.function_name].parameters.push({
          name: row.parameter_name,
          type: row.parameter_type,
          position: row.ordinal_position
        });
      }
    });
    
    console.log('Funções encontradas:');
    Object.values(functions).forEach((func: DatabaseFunction) => {
      console.log(`- ${func.name} (${func.type}):`);
      console.log(`  Retorno: ${func.returnType}`);
      if (func.parameters.length > 0) {
        console.log('  Parâmetros:');
        func.parameters.forEach((param: FunctionParameter) => {
          console.log(`    ${param.name}: ${param.type}`);
        });
      }
    });
    
    // 12. Executar a função armazenada
    console.log('\n11. Executando a função get_sample_data(3)...');
    const functionResult = await client.query('SELECT * FROM get_sample_data(3)');
    console.log('Resultado da função:');
    console.table(functionResult.rows);
    
    console.log('\nTestes concluídos com sucesso!');
    
  } catch (error) {
    console.error('Erro durante a execução do exemplo:', error);
  } finally {
    // Desconecta do banco de dados
    await client.end();
    console.log('Conexão encerrada.');
  }
}

// Executa o exemplo
runSimpleExample().catch(error => {
  console.error('Erro fatal:', error);
  process.exit(1);
}); 