/**
 * Exemplo do Sistema de Filtros
 * 
 * Este exemplo demonstra como usar o sistema de filtros para criar
 * condições SQL complexas a partir de objetos JSON.
 */

import { 
  FilterBuilder
} from '../src/filters';

// Logger auxiliar
function log(title: string, obj: any) {
  console.log('\n' + '-'.repeat(80));
  console.log(`${title}:`);
  console.log('-'.repeat(80));
  console.log(obj);
}

// Exemplo 1: Filtros básicos
function exemploFiltrosBasicos() {
  const builder = new FilterBuilder();
  
  builder
    .where('status', 'active')
    .where('age', { gt: 18 })
    .where('created_at', { gte: '2023-01-01' });
  
  const result = builder.build();
  
  log('Exemplo 1: Filtros básicos', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
}

// Exemplo 2: Operadores lógicos (AND, OR, NOT)
function exemploOperadoresLogicos() {
  const builder = new FilterBuilder();
  
  builder.whereOr([
    { status: 'active', type: 'admin' },
    { status: 'pending', created_at: { gt: '2023-06-01' } }
  ]);
  
  const result = builder.build();
  
  log('Exemplo 2: Operadores lógicos', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
  
  // Exemplo com funções para composição
  const builder2 = new FilterBuilder();
  
  builder2.whereAnd([
    (b) => b.where('status', 'active'),
    (b) => b.whereOr([
      { type: 'admin' },
      { type: 'manager', department: 'IT' }
    ])
  ]);
  
  const result2 = builder2.build();
  
  log('Exemplo 2.1: Operadores lógicos com funções', {
    filters: builder2.getFilters(),
    sql: result2.sql,
    parameters: result2.parameters
  });
}

// Exemplo 3: Filtros de Array
function exemploFiltrosArray() {
  const builder = new FilterBuilder();
  
  builder.whereArray('tags', {
    contains: ['important', 'urgent']
  });
  
  builder.whereArray('permissions', {
    element: 'admin'
  });
  
  const result = builder.build();
  
  log('Exemplo 3: Filtros de Array', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
}

// Exemplo 4: Filtros JSONB
function exemploFiltrosJSONB() {
  const builder = new FilterBuilder();
  
  builder.whereJSONB('data', {
    contains: { status: 'active', verified: true }
  });
  
  builder.whereJSONB('attributes', {
    has_key: 'address'
  });
  
  builder.whereJSONB('config', {
    extract_path: ['settings', 'notifications', 'email'],
    equals: true
  });
  
  const result = builder.build();
  
  log('Exemplo 4: Filtros JSONB', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
}

// Exemplo 5: Filtros Geográficos
function exemploFiltrosGeo() {
  const builder = new FilterBuilder();
  
  builder.whereGeo('location', {
    distance: {
      point: { lat: -23.5505, lng: -46.6333 }, // São Paulo
      max: 10000 // 10km
    }
  });
  
  builder.whereGeo('area', {
    within_box: {
      min: { lat: -23.6, lng: -46.7 },
      max: { lat: -23.5, lng: -46.6 }
    }
  });
  
  const result = builder.build();
  
  log('Exemplo 5: Filtros Geográficos', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
}

// Exemplo 6: Detecção automática de tipos de filtro
function exemploDeteccaoAutomatica() {
  const builder = new FilterBuilder();
  
  // Um objeto JSON com vários tipos de filtros
  const filtrosComplexos = {
    status: 'active',
    age: { gt: 18 },
    tags: { contains: ['premium', 'verified'] },
    data: { has_key: 'address', extract_path: ['profile', 'verified'], equals: true },
    location: { distance: { point: { lat: -23.5505, lng: -46.6333 }, max: 5000 } }
  };
  
  builder.fromJSON(filtrosComplexos);
  
  const result = builder.build();
  
  log('Exemplo 6: Detecção automática de tipos', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
}

// Exemplo 7: Prefixo de campos
function exemploPrefixoDeCampos() {
  const builder = new FilterBuilder({
    fieldPrefix: 't.'
  });
  
  builder
    .where('id', 1)
    .where('status', 'active')
    .where('created_at', { gt: '2023-01-01' });
  
  const result = builder.build();
  
  log('Exemplo 7: Prefixo de campos', {
    filters: builder.getFilters(),
    sql: result.sql,
    parameters: result.parameters
  });
}

// Executar todos os exemplos
console.log('===== EXEMPLOS DO SISTEMA DE FILTROS =====');

exemploFiltrosBasicos();
exemploOperadoresLogicos();
exemploFiltrosArray();
exemploFiltrosJSONB();
exemploFiltrosGeo();
exemploDeteccaoAutomatica();
exemploPrefixoDeCampos();

console.log('\n===== FIM DOS EXEMPLOS ====='); 