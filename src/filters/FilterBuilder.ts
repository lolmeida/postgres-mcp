/**
 * FilterBuilder
 * 
 * Builder para construir filtros SQL a partir de objetos JSON.
 * Integra todos os adaptadores de filtro (básico, array, JSONB, geométrico)
 * em uma única interface fácil de usar.
 */

import { FilterParser, FilterParserResult, and, or, not } from './FilterParser';
import { ArrayFilterAdapter } from './ArrayFilterAdapter';
import { JSONBFilterAdapter } from './JSONBFilterAdapter';
import { GeoFilterAdapter } from './GeoFilterAdapter';
import { createComponentLogger } from '../utils/logger';

/**
 * Opções para a construção de filtros
 */
export interface FilterBuilderOptions {
  /**
   * Se deve detectar automaticamente tipos específicos de filtro (array, JSONB, geo)
   * Default: true
   */
  autoDetectTypes?: boolean;
  
  /**
   * Se deve escapar identificadores SQL
   * Default: true
   */
  escapeIdentifiers?: boolean;
  
  /**
   * Prefixo para todos os campos (ex: "t." para prefixar campos com alias de tabela)
   */
  fieldPrefix?: string;
}

/**
 * Builder para construir filtros SQL a partir de objetos JSON
 */
export class FilterBuilder {
  private logger = createComponentLogger('FilterBuilder');
  private parser: FilterParser;
  private filters: any;
  private options: FilterBuilderOptions;
  
  /**
   * Construtor do FilterBuilder
   * 
   * @param options Opções para configurar o comportamento do builder
   */
  constructor(options: FilterBuilderOptions = {}) {
    this.parser = new FilterParser();
    this.filters = {};
    this.options = {
      autoDetectTypes: options.autoDetectTypes !== false,
      escapeIdentifiers: options.escapeIdentifiers !== false,
      fieldPrefix: options.fieldPrefix || ''
    };
  }
  
  /**
   * Adiciona um filtro simples
   * 
   * @param field Nome do campo
   * @param value Valor ou condição
   * @returns this (para encadeamento)
   */
  public where(field: string, value: any): FilterBuilder {
    const prefixedField = this.prefixField(field);
    this.filters[prefixedField] = value;
    return this;
  }
  
  /**
   * Adiciona um filtro de array
   * 
   * @param field Nome do campo
   * @param options Opções de filtro de array
   * @returns this (para encadeamento)
   */
  public whereArray(field: string, options: any): FilterBuilder {
    const prefixedField = this.prefixField(field);
    const arrayFilter = ArrayFilterAdapter.adaptArrayFilter(prefixedField, options);
    
    // Merge os filtros
    this.filters = {
      ...this.filters,
      ...arrayFilter
    };
    
    return this;
  }
  
  /**
   * Adiciona um filtro JSONB
   * 
   * @param field Nome do campo
   * @param options Opções de filtro JSONB
   * @returns this (para encadeamento)
   */
  public whereJSONB(field: string, options: any): FilterBuilder {
    const prefixedField = this.prefixField(field);
    const jsonbFilter = JSONBFilterAdapter.adaptJSONBFilter(prefixedField, options);
    
    // Merge os filtros
    this.filters = {
      ...this.filters,
      ...jsonbFilter
    };
    
    return this;
  }
  
  /**
   * Adiciona um filtro geométrico
   * 
   * @param field Nome do campo
   * @param options Opções de filtro geométrico
   * @returns this (para encadeamento)
   */
  public whereGeo(field: string, options: any): FilterBuilder {
    const prefixedField = this.prefixField(field);
    const geoFilter = GeoFilterAdapter.adaptGeoFilter(prefixedField, options);
    
    // Merge os filtros
    this.filters = {
      ...this.filters,
      ...geoFilter
    };
    
    return this;
  }
  
  /**
   * Adiciona um filtro composto AND (e lógico)
   * 
   * @param filters Array de filtros ou funções que retornam filtros
   * @returns this (para encadeamento)
   */
  public whereAnd(filters: any[] | ((builder: FilterBuilder) => void)[]): FilterBuilder {
    let processedFilters: any[];
    
    if (filters.length > 0 && typeof filters[0] === 'function') {
      // Caso sejam funções, execute cada uma com um novo builder
      processedFilters = (filters as ((builder: FilterBuilder) => void)[]).map(builderFn => {
        const subBuilder = new FilterBuilder(this.options);
        builderFn(subBuilder);
        return subBuilder.getFilters();
      });
    } else {
      // Caso contrário, assume que são objetos de filtro direto
      processedFilters = filters as any[];
    }
    
    // Adiciona o filtro AND
    const andCondition = and(processedFilters);
    this.addFilter(andCondition);
    
    return this;
  }
  
  /**
   * Adiciona um filtro composto OR (ou lógico)
   * 
   * @param filters Array de filtros ou funções que retornam filtros
   * @returns this (para encadeamento)
   */
  public whereOr(filters: any[] | ((builder: FilterBuilder) => void)[]): FilterBuilder {
    let processedFilters: any[];
    
    if (filters.length > 0 && typeof filters[0] === 'function') {
      // Caso sejam funções, execute cada uma com um novo builder
      processedFilters = (filters as ((builder: FilterBuilder) => void)[]).map(builderFn => {
        const subBuilder = new FilterBuilder(this.options);
        builderFn(subBuilder);
        return subBuilder.getFilters();
      });
    } else {
      // Caso contrário, assume que são objetos de filtro direto
      processedFilters = filters as any[];
    }
    
    // Adiciona o filtro OR
    const orCondition = or(processedFilters);
    this.addFilter(orCondition);
    
    return this;
  }
  
  /**
   * Adiciona um filtro NOT (negação)
   * 
   * @param filter Filtro ou função que retorna um filtro
   * @returns this (para encadeamento)
   */
  public whereNot(filter: any | ((builder: FilterBuilder) => void)): FilterBuilder {
    let processedFilter: any;
    
    if (typeof filter === 'function') {
      const subBuilder = new FilterBuilder(this.options);
      filter(subBuilder);
      processedFilter = subBuilder.getFilters();
    } else {
      processedFilter = filter;
    }
    
    // Adiciona o filtro NOT
    const notCondition = not(processedFilter);
    this.addFilter(notCondition);
    
    return this;
  }
  
  /**
   * Adiciona um filtro raw (SQL direto)
   * 
   * @param sql String SQL
   * @param params Parâmetros para o SQL
   * @returns this (para encadeamento)
   */
  public whereRaw(sql: string, params: any[] = []): FilterBuilder {
    // Para SQL raw, criamos um objeto especial que será tratado pelo parser
    this.filters[`__raw_${Object.keys(this.filters).length}`] = {
      __raw: {
        sql,
        params
      }
    };
    
    return this;
  }
  
  /**
   * Adiciona filtros a partir de um objeto JSON
   * 
   * @param filters Objeto com filtros
   * @param autoDetect Se deve detectar automaticamente tipos específicos
   * @returns this (para encadeamento)
   */
  public fromJSON(filters: any, autoDetect: boolean = this.options.autoDetectTypes): FilterBuilder {
    if (!filters || typeof filters !== 'object') {
      return this;
    }
    
    // Itera por cada par chave-valor no objeto de filtros
    Object.entries(filters).forEach(([field, condition]) => {
      const prefixedField = this.prefixField(field);
      
      // Se autoDetect estiver ativado, tenta identificar tipos especiais
      if (autoDetect && typeof condition === 'object' && condition !== null) {
        if (ArrayFilterAdapter.isArrayFilter(condition)) {
          this.whereArray(field, condition);
          return;
        }
        
        if (JSONBFilterAdapter.isJSONBFilter(condition)) {
          this.whereJSONB(field, condition);
          return;
        }
        
        if (GeoFilterAdapter.isGeoFilter(condition)) {
          this.whereGeo(field, condition);
          return;
        }
      }
      
      // Caso padrão: filtro simples
      this.where(field, condition);
    });
    
    return this;
  }
  
  /**
   * Adiciona um filtro ao builder
   * 
   * @param filter Filtro a ser adicionado
   */
  private addFilter(filter: any): void {
    if (Array.isArray(this.filters)) {
      this.filters.push(filter);
    } else if (this.filters && typeof this.filters === 'object') {
      // Se já temos filtros existentes, precisamos convertê-los para formato AND
      if (Object.keys(this.filters).length > 0) {
        const existingFilters = { ...this.filters };
        this.filters = [existingFilters, filter];
      } else {
        this.filters = filter;
      }
    } else {
      this.filters = filter;
    }
  }
  
  /**
   * Adiciona prefixo ao nome do campo, se configurado
   * 
   * @param field Nome do campo
   * @returns Nome do campo com prefixo
   */
  private prefixField(field: string): string {
    // Não adiciona prefixo a campos com expressões especiais ou já prefixados
    if (!this.options.fieldPrefix || 
        field.includes('(') || 
        field.includes(')') || 
        field.includes(' ') ||
        field.startsWith(this.options.fieldPrefix)) {
      return field;
    }
    
    return `${this.options.fieldPrefix}${field}`;
  }
  
  /**
   * Retorna os filtros configurados
   * 
   * @returns Objeto de filtros
   */
  public getFilters(): any {
    return this.filters;
  }
  
  /**
   * Constrói a condição SQL e parâmetros a partir dos filtros configurados
   * 
   * @returns Resultado contendo SQL e parâmetros
   */
  public build(): FilterParserResult {
    return this.parser.parse(this.filters);
  }
  
  /**
   * Constrói um where para ser usado diretamente em queries
   * 
   * @returns String de condição where ou string vazia se não houver filtros
   */
  public buildWhere(): string {
    const result = this.build();
    
    if (result.sql === 'TRUE') {
      return '';
    }
    
    return `WHERE ${result.sql}`;
  }
  
  /**
   * Limpa todos os filtros configurados
   * 
   * @returns this (para encadeamento)
   */
  public clear(): FilterBuilder {
    this.filters = {};
    return this;
  }
} 