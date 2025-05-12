/**
 * JSONBFilterAdapter
 * 
 * Adaptador para operações de filtro com campos JSONB no PostgreSQL.
 * Implementa suporte para operações específicas do JSONB como:
 * - contains (@>): JSONB contém outro JSONB
 * - contained_by (<@): JSONB está contido em outro JSONB
 * - has_key (?): JSONB tem a chave especificada
 * - has_any_keys (?|): JSONB tem qualquer uma das chaves especificadas
 * - has_all_keys (?&): JSONB tem todas as chaves especificadas
 * - path: consulta com JSONPath (PostgreSQL 12+)
 */

import { FilterOperator } from './FilterParser';

/**
 * Interface para representar operações com JSONB no PostgreSQL
 */
export interface JSONBFilterOptions {
  /**
   * Verifica se o JSONB contém outro JSONB (pode ser objeto ou valor primitivo)
   * @example { contains: {"status": "active"} } => column @> '{"status": "active"}'::jsonb
   */
  contains?: any;
  
  /**
   * Verifica se o JSONB está contido em outro JSONB
   * @example { contained_by: {"id": 1, "status": "active"} } => column <@ '{"id": 1, "status": "active"}'::jsonb
   */
  contained_by?: any;
  
  /**
   * Verifica se o JSONB tem a chave especificada no nível superior
   * @example { has_key: "status" } => column ? 'status'
   */
  has_key?: string;
  
  /**
   * Verifica se o JSONB tem qualquer uma das chaves especificadas
   * @example { has_any_keys: ["status", "type"] } => column ?| ARRAY['status', 'type']
   */
  has_any_keys?: string[];
  
  /**
   * Verifica se o JSONB tem todas as chaves especificadas
   * @example { has_all_keys: ["id", "status"] } => column ?& ARRAY['id', 'status']
   */
  has_all_keys?: string[];
  
  /**
   * Consulta usando JSONPath (PostgreSQL 12+)
   * @example { path: "$.status ? (@ == 'active')" } => column @@ '$.status ? (@ == "active")'::jsonpath
   */
  path?: string;
  
  /**
   * Extrai um valor específico do JSONB via caminho
   * @example { extract_path: ["data", "user", "name"] } => column#>>'{data,user,name}'
   * Usado em conjunto com outros operadores padrão para comparação
   */
  extract_path?: string[];
  
  /**
   * Compara um valor extraído de JSONB
   * Só é usado quando extract_path é definido
   */
  equals?: any;
  
  /**
   * Compara se um valor extraído é maior
   * Só é usado quando extract_path é definido
   */
  gt?: any;
  
  /**
   * Compara se um valor extraído é menor
   * Só é usado quando extract_path é definido
   */
  lt?: any;
  
  /**
   * Compara se um valor extraído é maior ou igual
   * Só é usado quando extract_path é definido
   */
  gte?: any;
  
  /**
   * Compara se um valor extraído é menor ou igual
   * Só é usado quando extract_path é definido
   */
  lte?: any;
}

/**
 * Classe de adaptador para filtros JSONB PostgreSQL
 */
export class JSONBFilterAdapter {
  /**
   * Converte filtros JSONB JSON para formato interno de filtro
   * 
   * @param field Nome do campo
   * @param options Opções de filtro JSONB
   * @returns Objeto de filtro no formato interno
   */
  public static adaptJSONBFilter(field: string, options: JSONBFilterOptions): any {
    const result: any = {};
    
    if (typeof options !== 'object' || options === null) {
      throw new Error(`Filtro JSONB inválido para o campo ${field}: ${JSON.stringify(options)}`);
    }
    
    // Verifica se temos um caminho de extração
    let targetField = field;
    if (options.extract_path && Array.isArray(options.extract_path) && options.extract_path.length > 0) {
      // Cria notação de caminho como '{key1,key2,key3}'
      const pathArray = options.extract_path.map(p => p.replace(/"/g, '\\"')).join(',');
      targetField = `${field}#>>'{${pathArray}}'`;
      
      // Aplica operadores de comparação ao valor extraído
      if (options.equals !== undefined) {
        result[targetField] = options.equals;
      }
      
      if (options.gt !== undefined) {
        result[targetField] = { [FilterOperator.GREATER_THAN]: options.gt };
      }
      
      if (options.lt !== undefined) {
        result[targetField] = { [FilterOperator.LESS_THAN]: options.lt };
      }
      
      if (options.gte !== undefined) {
        result[targetField] = { [FilterOperator.GREATER_THAN_EQUALS]: options.gte };
      }
      
      if (options.lte !== undefined) {
        result[targetField] = { [FilterOperator.LESS_THAN_EQUALS]: options.lte };
      }
    } else {
      // Processa operadores JSONB específicos
      if (options.contains !== undefined) {
        result[field] = { [FilterOperator.JSONB_CONTAINS]: options.contains };
      }
      
      if (options.contained_by !== undefined) {
        result[field] = { 
          ...(result[field] || {}), 
          [FilterOperator.JSONB_CONTAINED_BY]: options.contained_by 
        };
      }
      
      if (options.has_key !== undefined) {
        result[field] = { 
          ...(result[field] || {}), 
          [FilterOperator.JSONB_EXISTS]: options.has_key 
        };
      }
      
      if (options.has_any_keys !== undefined && Array.isArray(options.has_any_keys)) {
        // Para ?| operator no PostgreSQL
        result[`${field} ?| array[${options.has_any_keys.map(k => `'${k}'`).join(', ')}]`] = true;
      }
      
      if (options.has_all_keys !== undefined && Array.isArray(options.has_all_keys)) {
        // Para ?& operator no PostgreSQL
        result[`${field} ?& array[${options.has_all_keys.map(k => `'${k}'`).join(', ')}]`] = true;
      }
      
      if (options.path !== undefined) {
        result[field] = { [FilterOperator.JSONB_PATH]: options.path };
      }
    }
    
    return result;
  }
  
  /**
   * Verifica se um objeto é um filtro JSONB válido
   * 
   * @param obj Objeto a ser verificado
   * @returns Verdadeiro se for um filtro JSONB válido
   */
  public static isJSONBFilter(obj: any): boolean {
    if (typeof obj !== 'object' || obj === null) {
      return false;
    }
    
    const jsonbFilterKeys = [
      'contains', 
      'contained_by', 
      'has_key',
      'has_any_keys',
      'has_all_keys',
      'path',
      'extract_path'
    ];
    
    return jsonbFilterKeys.some(key => key in obj);
  }
} 