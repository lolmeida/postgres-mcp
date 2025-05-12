/**
 * View Service Implementation
 * 
 * Este serviço gerencia operações relacionadas a views no PostgreSQL,
 * incluindo listar, obter detalhes e atualizar views materializadas.
 */

import { AbstractService } from './ServiceBase';
import { PostgresConnection } from '../database/PostgresConnection';
import { PostgresSchemaManager, ViewRow } from '../database/PostgresSchemaManager';
import { createComponentLogger } from '../utils/logger';
import { ViewInfo, ViewType, ViewListOptions, ViewDetailOptions, MaterializedViewRefreshOptions } from '../models/ViewInfo';
import { ColumnInfo } from '../core/types';
import { QueryException } from '../utils/exceptions';

/**
 * Serviço para gerenciamento de views
 */
export class ViewService extends AbstractService {
  private logger = createComponentLogger('ViewService');
  private schemaManager: PostgresSchemaManager;

  /**
   * Cria uma nova instância do serviço de views
   * 
   * @param connection Conexão PostgreSQL
   */
  constructor(connection: PostgresConnection) {
    super();
    this.schemaManager = new PostgresSchemaManager(connection);
    this.logger.debug('View service initialized');
  }

  /**
   * Lista views em um schema
   * 
   * @param schemaName Nome do schema
   * @param options Opções de listagem
   * @returns Lista de views
   */
  async listViews(
    schemaName: string = 'public',
    options: ViewListOptions = {}
  ): Promise<ViewInfo[]> {
    try {
      const includeRegularViews = options.includeRegularViews ?? true;
      const includeMaterializedViews = options.includeMaterializedViews ?? true;
      const limit = options.limit || 100;
      const offset = options.offset || 0;
      
      this.logger.debug(`Listing views in schema ${schemaName}`, options);
      
      // Busca as views no banco de dados
      const viewRows = await this.schemaManager.listViews(
        schemaName, 
        includeRegularViews,
        includeMaterializedViews
      );
      
      // Mapeia as rows para o modelo ViewInfo
      const views = viewRows.map(row => this.mapToViewInfo(row));
      
      // Aplica paginação
      return views.slice(offset, offset + limit);
    } catch (error: any) {
      this.logger.error(`Failed to list views in schema: ${schemaName}`, error);
      throw this.createError(
        `Failed to list views: ${error.message}`,
        'database_error',
        { schemaName, cause: error }
      );
    }
  }

  /**
   * Obtém detalhes de uma view específica
   * 
   * @param viewName Nome da view
   * @param schemaName Nome do schema
   * @param options Opções de detalhes
   * @returns Informações da view
   */
  async getViewDetails(
    viewName: string,
    schemaName: string = 'public',
    options: ViewDetailOptions = {}
  ): Promise<ViewInfo> {
    try {
      const includeColumns = options.includeColumns ?? true;
      const includeDefinition = options.includeDefinition ?? true;
      
      this.logger.debug(`Getting view details: ${schemaName}.${viewName}`, options);
      
      // Busca informações básicas da view
      const viewRow = await this.schemaManager.getViewInfo(viewName, schemaName);
      
      // Mapeia para o modelo ViewInfo
      const view = this.mapToViewInfo(viewRow);
      
      // Se solicitado, adiciona a definição SQL
      if (includeDefinition) {
        view.definition = await this.schemaManager.getViewDefinition(viewName, schemaName);
      }
      
      // Se solicitado, adiciona informações sobre colunas
      if (includeColumns) {
        const columns = await this.schemaManager.getTableColumns(viewName, schemaName);
        view.columns = columns.map(col => ({
          name: col.columnName,
          type: col.dataType,
          description: col.description,
          isNullable: col.isNullable,
          isPrimaryKey: false,
          isForeignKey: false,
          isUnique: false,
          defaultValue: col.columnDefault
        }));
      }
      
      return view;
    } catch (error: any) {
      this.logger.error(`Failed to get view details: ${schemaName}.${viewName}`, error);
      throw this.createError(
        `Failed to get view details: ${error.message}`,
        'database_error',
        { schemaName, viewName, cause: error }
      );
    }
  }

  /**
   * Atualiza uma view materializada
   * 
   * @param viewName Nome da view materializada
   * @param schemaName Nome do schema
   * @param options Opções de atualização
   * @returns Flag de sucesso
   */
  async refreshMaterializedView(
    viewName: string,
    schemaName: string = 'public',
    options: MaterializedViewRefreshOptions = {}
  ): Promise<boolean> {
    try {
      const concurrently = options.concurrently ?? false;
      const withData = options.withData ?? true;
      
      this.logger.debug(`Refreshing materialized view: ${schemaName}.${viewName}`, options);
      
      return await this.schemaManager.refreshMaterializedView(
        viewName,
        schemaName,
        concurrently,
        withData
      );
    } catch (error: any) {
      this.logger.error(`Failed to refresh materialized view: ${schemaName}.${viewName}`, error);
      throw this.createError(
        `Failed to refresh materialized view: ${error.message}`,
        'database_error',
        { schemaName, viewName, cause: error }
      );
    }
  }

  /**
   * Mapeia uma linha de tabela para o modelo ViewInfo
   * 
   * @param row Linha do resultado da consulta
   * @returns Modelo ViewInfo
   */
  private mapToViewInfo(row: ViewRow): ViewInfo {
    return {
      viewName: row.view_name,
      schemaName: row.schema_name,
      viewType: row.view_type === 'VIEW' ? ViewType.REGULAR : ViewType.MATERIALIZED,
      definition: '',  // Será preenchido sob demanda
      owner: row.owner,
      description: row.description || undefined,
      hasIndexForRefresh: row.has_index_for_refresh,
      lastRefreshed: row.last_refreshed || undefined
    };
  }
} 