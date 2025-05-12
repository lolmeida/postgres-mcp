/**
 * ViewInfo Model
 * 
 * Modelo para representar informações sobre views no PostgreSQL.
 * Suporta tanto views regulares quanto views materializadas.
 */

import { ColumnInfo } from '../core/types';

/**
 * Tipos de views suportados
 */
export enum ViewType {
  REGULAR = 'VIEW',
  MATERIALIZED = 'MATERIALIZED_VIEW'
}

/**
 * Interface para informações sobre views
 */
export interface ViewInfo {
  /**
   * Nome da view
   */
  viewName: string;
  
  /**
   * Nome do schema onde a view está localizada
   */
  schemaName: string;
  
  /**
   * Tipo da view (regular ou materializada)
   */
  viewType: ViewType;
  
  /**
   * Definição SQL da view
   */
  definition: string;
  
  /**
   * Dono da view
   */
  owner: string;
  
  /**
   * Descrição da view, se houver
   */
  description?: string;
  
  /**
   * Colunas da view
   * Observação: Pode ser null se as colunas não foram carregadas
   */
  columns?: ColumnInfo[];
  
  /**
   * Para views materializadas, indica se possui um índice para refresh rápido
   */
  hasIndexForRefresh?: boolean;
  
  /**
   * Para views materializadas, indica quando foi a última atualização
   */
  lastRefreshed?: Date;
}

/**
 * Opções para listagem de views
 */
export interface ViewListOptions {
  /**
   * Incluir views regulares
   * Default: true
   */
  includeRegularViews?: boolean;
  
  /**
   * Incluir views materializadas
   * Default: true
   */
  includeMaterializedViews?: boolean;
  
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
 * Opções para detalhes de views
 */
export interface ViewDetailOptions {
  /**
   * Incluir informações detalhadas das colunas
   * Default: true
   */
  includeColumns?: boolean;
  
  /**
   * Incluir a definição SQL da view
   * Default: true
   */
  includeDefinition?: boolean;
}

/**
 * Opções para refreshing de views materializadas
 */
export interface MaterializedViewRefreshOptions {
  /**
   * Realizar refresh concorrente (requer índice para chave única)
   * Default: false
   */
  concurrently?: boolean;
  
  /**
   * Refresh com novos dados apenas (não recomputa a view inteira)
   * Default: false
   */
  withData?: boolean;
} 