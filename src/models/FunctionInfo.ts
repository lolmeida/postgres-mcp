/**
 * FunctionInfo Model
 * 
 * Modelo para representar informações sobre funções e procedimentos armazenados no PostgreSQL.
 */

/**
 * Tipos de funções suportados
 */
export enum FunctionType {
  FUNCTION = 'FUNCTION',
  PROCEDURE = 'PROCEDURE'
}

/**
 * Volatilidade de função
 */
export enum FunctionVolatility {
  IMMUTABLE = 'IMMUTABLE',    // Sempre retorna o mesmo resultado para os mesmos inputs
  STABLE = 'STABLE',          // Não modifica o banco, mas pode retornar diferentes resultados na mesma transação
  VOLATILE = 'VOLATILE'       // Pode modificar o banco e retornar diferentes resultados
}

/**
 * Argumento de função
 */
export interface FunctionArgument {
  /**
   * Nome do argumento
   */
  name: string;
  
  /**
   * Tipo de dados do argumento
   */
  dataType: string;
  
  /**
   * Valor padrão do argumento, se houver
   */
  defaultValue?: string;
  
  /**
   * Modo do argumento (IN, OUT, INOUT)
   */
  mode?: 'IN' | 'OUT' | 'INOUT';
}

/**
 * Interface para informações sobre funções
 */
export interface FunctionInfo {
  /**
   * Nome da função
   */
  functionName: string;
  
  /**
   * Nome do schema onde a função está localizada
   */
  schemaName: string;
  
  /**
   * Tipo da função (function ou procedure)
   */
  functionType: FunctionType;
  
  /**
   * Tipo de retorno da função (null para procedures)
   */
  returnType: string;
  
  /**
   * Argumentos da função
   */
  arguments: FunctionArgument[];
  
  /**
   * Linguagem da função (sql, plpgsql, etc.)
   */
  language: string;
  
  /**
   * Volatilidade da função
   */
  volatility: FunctionVolatility;
  
  /**
   * Dono da função
   */
  owner: string;
  
  /**
   * Definição da função (corpo SQL)
   */
  definition?: string;
  
  /**
   * Descrição da função, se houver
   */
  description?: string;
}

/**
 * Opções para listagem de funções
 */
export interface FunctionListOptions {
  /**
   * Incluir funções
   * Default: true
   */
  includeFunctions?: boolean;
  
  /**
   * Incluir procedimentos 
   * Default: true
   */
  includeProcedures?: boolean;
  
  /**
   * Filtrar por linguagem
   */
  language?: string;
  
  /**
   * Limite de resultados
   * Default: 100
   */
  limit?: number;
  
  /**
   * Deslocamento para paginação
   * Default: 0
   */
  offset?: number;
}

/**
 * Opções para detalhes de funções
 */
export interface FunctionDetailOptions {
  /**
   * Incluir a definição SQL da função
   * Default: true
   */
  includeDefinition?: boolean;
}

/**
 * Parâmetros para execução de função
 */
export interface FunctionExecutionParams {
  /**
   * Nome da função
   */
  functionName: string;
  
  /**
   * Nome do schema
   */
  schemaName: string;
  
  /**
   * Argumentos para a execução
   */
  args: any[];
} 