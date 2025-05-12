/**
 * PostgreSQL MCP - Implementação JavaScript/TypeScript do Model Context Protocol para PostgreSQL
 * 
 * Este arquivo é o ponto de entrada principal da biblioteca, exportando todas as classes
 * e interfaces públicas que podem ser utilizadas pelos consumidores da biblioteca.
 */

// Core
import { PostgresMCPServer } from './core/PostgresMCPServer';
import { MCPConfig } from './core/MCPConfig';
import { MCPRouter } from './core/MCPRouter';
import { MCPRequest, MCPResponse, MCPError, MCPErrorType, TableInfo, ColumnInfo } from './core/types';

// Handlers
import { HandlerBase, AbstractHandler } from './handlers/HandlerBase';

// Services
import { ServiceBase, AbstractService } from './services/ServiceBase';

// Repositories
import { RepositoryBase, AbstractRepository, DbOperationOptions } from './repositories/RepositoryBase';

// Utils
import { createLogger, createComponentLogger } from './utils/logger';
import { 
  MCPException, ValidationException, DatabaseException, 
  QueryException, SecurityException, TransactionException, 
  InternalException, transformDbError 
} from './utils/exceptions';

// Exportação de componentes públicos
export {
  // Core
  PostgresMCPServer,
  MCPConfig,
  MCPRouter,
  MCPRequest,
  MCPResponse,
  MCPError,
  MCPErrorType,
  TableInfo,
  ColumnInfo,
  
  // Handlers
  HandlerBase,
  AbstractHandler,
  
  // Services
  ServiceBase,
  AbstractService,
  
  // Repositories
  RepositoryBase,
  AbstractRepository,
  DbOperationOptions,
  
  // Utils
  createLogger,
  createComponentLogger,
  MCPException,
  ValidationException,
  DatabaseException,
  QueryException,
  SecurityException,
  TransactionException,
  InternalException,
  transformDbError
};

// Exportação padrão para facilitar o uso
export default PostgresMCPServer; 