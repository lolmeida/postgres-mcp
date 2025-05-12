/**
 * ArrayFilterAdapter
 * 
 * Adaptador para operações de filtro com arrays PostgreSQL.
 * Implementa suporte para operações específicas com arrays como:
 * - contains (@>): array contém todos os elementos especificados
 * - contained_by (<@): array está contido em outro array
 * - overlaps (&&): array tem elementos em comum com outro array
 */

import { FilterOperator } from './FilterParser';

/**
 * Interface para representar operações com arrays no PostgreSQL
 */
export interface ArrayFilterOptions {
  /**
   * Verifica se o array contém todos os elementos especificados
   * @example { contains: [1, 2] } => column @> ARRAY[1, 2]
   */
  contains?: any[];
  
  /**
   * Verifica se o array está contido em outro array
   * @example { contained_by: [1, 2, 3, 4] } => column <@ ARRAY[1, 2, 3, 4]
   */
  contained_by?: any[];
  
  /**
   * Verifica se o array tem elementos em comum com outro array
   * @example { overlaps: [2, 3] } => column && ARRAY[2, 3]
   */
  overlaps?: any[];
  
  /**
   * Verifica se o array está vazio
   * @example { is_empty: true } => array_length(column, 1) IS NULL
   */
  is_empty?: boolean;
  
  /**
   * Verifica se o array tem o comprimento especificado
   * @example { length: 3 } => array_length(column, 1) = 3
   */
  length?: number;
  
  /**
   * Verifica se o array contém o elemento específico
   * @example { element: 5 } => 5 = ANY(column)
   */
  element?: any;
}

/**
 * Classe de adaptador para filtros de arrays PostgreSQL
 */
export class ArrayFilterAdapter {
  /**
   * Converte filtros de array JSON para formato interno de filtro
   * 
   * @param field Nome do campo
   * @param options Opções de filtro de array
   * @returns Objeto de filtro no formato interno
   */
  public static adaptArrayFilter(field: string, options: ArrayFilterOptions): any {
    const result: any = {};
    
    if (typeof options !== 'object' || options === null) {
      throw new Error(`Filtro de array inválido para o campo ${field}: ${JSON.stringify(options)}`);
    }
    
    // Processa cada operador de array
    if (options.contains !== undefined) {
      result[`${field}`] = { [FilterOperator.ARRAY_CONTAINS]: options.contains };
    }
    
    if (options.contained_by !== undefined) {
      result[`${field}`] = { 
        ...(result[field] || {}), 
        [FilterOperator.ARRAY_CONTAINED_BY]: options.contained_by 
      };
    }
    
    if (options.overlaps !== undefined) {
      result[`${field}`] = { 
        ...(result[field] || {}), 
        [FilterOperator.ARRAY_OVERLAPS]: options.overlaps 
      };
    }
    
    if (options.is_empty !== undefined) {
      // Para checar se um array está vazio, usamos array_length IS NULL
      if (options.is_empty) {
        result[`array_length(${field}, 1)`] = { [FilterOperator.IS_NULL]: true };
      } else {
        result[`array_length(${field}, 1)`] = { [FilterOperator.IS_NOT_NULL]: true };
      }
    }
    
    if (options.length !== undefined) {
      result[`array_length(${field}, 1)`] = options.length;
    }
    
    if (options.element !== undefined) {
      // Para checar se um elemento está em um array, usamos = ANY()
      result[`${options.element}`] = { [FilterOperator.EQUALS]: `ANY(${field})` };
    }
    
    return result;
  }
  
  /**
   * Verifica se um objeto é um filtro de array válido
   * 
   * @param obj Objeto a ser verificado
   * @returns Verdadeiro se for um filtro de array válido
   */
  public static isArrayFilter(obj: any): boolean {
    if (typeof obj !== 'object' || obj === null) {
      return false;
    }
    
    const arrayFilterKeys = [
      'contains', 
      'contained_by', 
      'overlaps',
      'is_empty',
      'length',
      'element'
    ];
    
    return arrayFilterKeys.some(key => key in obj);
  }
} 