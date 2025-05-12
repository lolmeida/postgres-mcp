/**
 * FilterParser
 * 
 * Parser para converter filtros JSON em condições SQL.
 * Suporta diversos operadores de comparação, filtros de texto, e tipos específicos do PostgreSQL.
 */

import { v4 as uuidv4 } from 'uuid';
import { createComponentLogger } from '../utils/logger';

/**
 * Tipos de operadores suportados
 */
export enum FilterOperator {
  // Operadores básicos
  EQUALS = 'eq',
  NOT_EQUALS = 'neq',
  GREATER_THAN = 'gt',
  LESS_THAN = 'lt',
  GREATER_THAN_EQUALS = 'gte',
  LESS_THAN_EQUALS = 'lte',
  
  // Operadores de texto
  LIKE = 'like',
  ILIKE = 'ilike',
  REGEX = 'regex',
  
  // Operadores de lista
  IN = 'in',
  NOT_IN = 'not_in',
  
  // Operadores de nulos
  IS_NULL = 'is_null',
  IS_NOT_NULL = 'is_not_null',
  
  // Operadores de array
  ARRAY_CONTAINS = 'contains',
  ARRAY_CONTAINED_BY = 'contained_by',
  ARRAY_OVERLAPS = 'overlaps',
  
  // Operadores JSONB
  JSONB_CONTAINS = 'jsonb_contains',
  JSONB_CONTAINED_BY = 'jsonb_contained_by',
  JSONB_EXISTS = 'jsonb_exists',
  JSONB_PATH = 'jsonb_path',
  
  // Operadores geométricos
  GEO_CONTAINS = 'geo_contains',
  GEO_CONTAINED_BY = 'geo_contained_by',
  GEO_OVERLAPS = 'geo_overlaps',
  GEO_DISTANCE = 'geo_distance'
}

/**
 * Interface para parâmetros SQL gerados pelo parser
 */
export interface SQLParameter {
  name: string;
  value: any;
}

/**
 * Resultado da conversão de filtros para SQL
 */
export interface FilterParserResult {
  sql: string;
  parameters: SQLParameter[];
}

/**
 * Classes para representar filtros compostos
 */
export class AndFilter {
  constructor(public filters: any[]) {}
}

export class OrFilter {
  constructor(public filters: any[]) {}
}

export class NotFilter {
  constructor(public filter: any) {}
}

/**
 * Funções auxiliares para criação de filtros compostos
 */
export const and = (filters: any[]): AndFilter => new AndFilter(filters);
export const or = (filters: any[]): OrFilter => new OrFilter(filters);
export const not = (filter: any): NotFilter => new NotFilter(filter);

/**
 * Parser de filtros JSON para SQL
 */
export class FilterParser {
  private logger = createComponentLogger('FilterParser');
  private paramCounter: number = 0;
  private parameters: SQLParameter[] = [];
  
  /**
   * Converte filtros JSON em condições SQL com parâmetros
   * 
   * @param filters Objeto de filtros ou array de filtros
   * @returns Resultado contendo SQL e parâmetros
   */
  public parse(filters: any): FilterParserResult {
    this.paramCounter = 0;
    this.parameters = [];
    
    if (!filters || Object.keys(filters).length === 0) {
      return { sql: 'TRUE', parameters: [] };
    }
    
    const sql = this.parseFilters(filters);
    
    return {
      sql,
      parameters: this.parameters
    };
  }
  
  /**
   * Analisa filtros e converte em condições SQL
   * 
   * @param filters Filtros a serem analisados
   * @returns String SQL representando as condições
   */
  private parseFilters(filters: any): string {
    // Verifica se é um filtro composto (AND, OR, NOT)
    if (filters instanceof AndFilter) {
      return this.parseAndFilter(filters);
    } else if (filters instanceof OrFilter) {
      return this.parseOrFilter(filters);
    } else if (filters instanceof NotFilter) {
      return this.parseNotFilter(filters);
    }
    
    // Se for um array, trata como AND
    if (Array.isArray(filters)) {
      return this.parseAndFilter(new AndFilter(filters));
    }
    
    // Filtro simples: objeto com pares chave-valor
    const conditions = Object.entries(filters).map(([field, condition]) => {
      return this.parseCondition(field, condition);
    });
    
    return conditions.join(' AND ');
  }
  
  /**
   * Analisa filtros AND
   * 
   * @param andFilter Filtro AND
   * @returns String SQL para o filtro AND
   */
  private parseAndFilter(andFilter: AndFilter): string {
    if (!andFilter.filters.length) return 'TRUE';
    
    const conditions = andFilter.filters.map(filter => this.parseFilters(filter));
    const nonEmptyConditions = conditions.filter(c => c && c !== 'TRUE');
    
    if (!nonEmptyConditions.length) return 'TRUE';
    if (nonEmptyConditions.length === 1) return nonEmptyConditions[0];
    
    return `(${nonEmptyConditions.join(' AND ')})`;
  }
  
  /**
   * Analisa filtros OR
   * 
   * @param orFilter Filtro OR
   * @returns String SQL para o filtro OR
   */
  private parseOrFilter(orFilter: OrFilter): string {
    if (!orFilter.filters.length) return 'FALSE';
    
    const conditions = orFilter.filters.map(filter => this.parseFilters(filter));
    const nonEmptyConditions = conditions.filter(c => c && c !== 'FALSE');
    
    if (!nonEmptyConditions.length) return 'FALSE';
    if (nonEmptyConditions.length === 1) return nonEmptyConditions[0];
    
    return `(${nonEmptyConditions.join(' OR ')})`;
  }
  
  /**
   * Analisa filtros NOT
   * 
   * @param notFilter Filtro NOT
   * @returns String SQL para o filtro NOT
   */
  private parseNotFilter(notFilter: NotFilter): string {
    const condition = this.parseFilters(notFilter.filter);
    
    if (condition === 'TRUE') return 'FALSE';
    if (condition === 'FALSE') return 'TRUE';
    
    return `NOT (${condition})`;
  }
  
  /**
   * Gera um nome único para um parâmetro SQL
   * 
   * @returns Nome do parâmetro
   */
  private generateParamName(): string {
    this.paramCounter++;
    return `p${this.paramCounter}`;
  }
  
  /**
   * Adiciona um parâmetro à lista de parâmetros
   * 
   * @param value Valor do parâmetro
   * @returns Nome do parâmetro
   */
  private addParameter(value: any): string {
    const name = this.generateParamName();
    this.parameters.push({ name, value });
    return name;
  }
  
  /**
   * Analisa uma condição de filtro e converte para SQL
   * 
   * @param field Nome do campo
   * @param condition Condição a ser aplicada
   * @returns String SQL representando a condição
   */
  private parseCondition(field: string, condition: any): string {
    // Se a condição for um objeto, pode conter operadores específicos
    if (condition !== null && typeof condition === 'object' && !Array.isArray(condition)) {
      return this.parseOperatorCondition(field, condition);
    }
    
    // Caso especial: se a condição for null, usa IS NULL
    if (condition === null) {
      return `${this.quoteIdentifier(field)} IS NULL`;
    }
    
    // Caso padrão: igualdade simples
    const paramName = this.addParameter(condition);
    return `${this.quoteIdentifier(field)} = $${paramName}`;
  }
  
  /**
   * Analisa condições com operadores específicos
   * 
   * @param field Nome do campo
   * @param conditions Objeto com operadores e valores
   * @returns String SQL representando a condição com operadores
   */
  private parseOperatorCondition(field: string, conditions: any): string {
    const quotedField = this.quoteIdentifier(field);
    const operators = Object.entries(conditions);
    
    if (operators.length === 0) {
      return 'TRUE';
    }
    
    const parts = operators.map(([operator, value]) => {
      switch (operator as FilterOperator) {
        // Operadores básicos
        case FilterOperator.EQUALS:
          if (value === null) return `${quotedField} IS NULL`;
          const eqParamName = this.addParameter(value);
          return `${quotedField} = $${eqParamName}`;
          
        case FilterOperator.NOT_EQUALS:
          if (value === null) return `${quotedField} IS NOT NULL`;
          const neqParamName = this.addParameter(value);
          return `${quotedField} <> $${neqParamName}`;
          
        case FilterOperator.GREATER_THAN:
          const gtParamName = this.addParameter(value);
          return `${quotedField} > $${gtParamName}`;
          
        case FilterOperator.LESS_THAN:
          const ltParamName = this.addParameter(value);
          return `${quotedField} < $${ltParamName}`;
          
        case FilterOperator.GREATER_THAN_EQUALS:
          const gteParamName = this.addParameter(value);
          return `${quotedField} >= $${gteParamName}`;
          
        case FilterOperator.LESS_THAN_EQUALS:
          const lteParamName = this.addParameter(value);
          return `${quotedField} <= $${lteParamName}`;
        
        // Operadores de texto
        case FilterOperator.LIKE:
          const likeParamName = this.addParameter(value);
          return `${quotedField} LIKE $${likeParamName}`;
          
        case FilterOperator.ILIKE:
          const ilikeParamName = this.addParameter(value);
          return `${quotedField} ILIKE $${ilikeParamName}`;
          
        case FilterOperator.REGEX:
          const regexParamName = this.addParameter(value);
          return `${quotedField} ~ $${regexParamName}`;
        
        // Operadores de lista
        case FilterOperator.IN:
          if (!Array.isArray(value) || value.length === 0) return 'FALSE';
          const inParamName = this.addParameter(value);
          return `${quotedField} = ANY($${inParamName}::text[])`;
          
        case FilterOperator.NOT_IN:
          if (!Array.isArray(value) || value.length === 0) return 'TRUE';
          const notInParamName = this.addParameter(value);
          return `${quotedField} <> ALL($${notInParamName}::text[])`;
        
        // Operadores de nulos
        case FilterOperator.IS_NULL:
          return value ? `${quotedField} IS NULL` : `${quotedField} IS NOT NULL`;
          
        case FilterOperator.IS_NOT_NULL:
          return value ? `${quotedField} IS NOT NULL` : `${quotedField} IS NULL`;
          
        // Operadores de array
        case FilterOperator.ARRAY_CONTAINS:
          const containsParamName = this.addParameter(value);
          return `${quotedField} @> $${containsParamName}`;
          
        case FilterOperator.ARRAY_CONTAINED_BY:
          const containedByParamName = this.addParameter(value);
          return `${quotedField} <@ $${containedByParamName}`;
          
        case FilterOperator.ARRAY_OVERLAPS:
          const overlapsParamName = this.addParameter(value);
          return `${quotedField} && $${overlapsParamName}`;
        
        // Operadores JSONB
        case FilterOperator.JSONB_CONTAINS:
          const jsonbContainsParamName = this.addParameter(value);
          return `${quotedField} @> $${jsonbContainsParamName}::jsonb`;
          
        case FilterOperator.JSONB_CONTAINED_BY:
          const jsonbContainedByParamName = this.addParameter(value);
          return `${quotedField} <@ $${jsonbContainedByParamName}::jsonb`;
          
        case FilterOperator.JSONB_EXISTS:
          const jsonbExistsParamName = this.addParameter(value);
          return `${quotedField} ? $${jsonbExistsParamName}`;
          
        case FilterOperator.JSONB_PATH:
          const jsonbPathParamName = this.addParameter(value);
          return `${quotedField} @@ $${jsonbPathParamName}::jsonpath`;
          
        // Operadores geométricos
        case FilterOperator.GEO_CONTAINS:
          const geoContainsParamName = this.addParameter(value);
          return `${quotedField} ~ $${geoContainsParamName}::geometry`;
          
        case FilterOperator.GEO_CONTAINED_BY:
          const geoContainedByParamName = this.addParameter(value);
          return `${quotedField} @ $${geoContainedByParamName}::geometry`;
          
        case FilterOperator.GEO_OVERLAPS:
          const geoOverlapsParamName = this.addParameter(value);
          return `${quotedField} && $${geoOverlapsParamName}::geometry`;
          
        case FilterOperator.GEO_DISTANCE:
          if (!value.point || !value.distance) {
            this.logger.warn(`Operador ${operator} requer 'point' e 'distance'`);
            return 'FALSE';
          }
          const geoPointParamName = this.addParameter(value.point);
          const geoDistanceParamName = this.addParameter(value.distance);
          return `ST_DWithin(${quotedField}, $${geoPointParamName}::geometry, $${geoDistanceParamName})`;
          
        default:
          this.logger.warn(`Operador desconhecido: ${operator}`);
          return 'TRUE';
      }
    });
    
    return parts.join(' AND ');
  }
  
  /**
   * Coloca identificadores SQL entre aspas para evitar conflitos com palavras reservadas
   * 
   * @param identifier Identificador a ser formatado
   * @returns Identificador com aspas
   */
  private quoteIdentifier(identifier: string): string {
    // Verifica caminho JSON (campo->objeto->propriedade)
    if (identifier.includes('->')) {
      const parts = identifier.split('->');
      const quotedBase = `"${parts[0].replace(/"/g, '""')}"`;
      
      return parts.slice(1).reduce((result, part) => {
        // Verifica se é acesso a texto (->) ou JSONB (->>)
        if (part.startsWith('>')) {
          return `${result}->>'${part.substring(1).replace(/'/g, "''")}'`;
        } else {
          return `${result}->'${part.replace(/'/g, "''")}'`;
        }
      }, quotedBase);
    }
    
    // Identificador simples
    return `"${identifier.replace(/"/g, '""')}"`;
  }
} 