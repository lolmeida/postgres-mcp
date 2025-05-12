/**
 * PostgreSQL MCP - Model Context Protocol implementation for PostgreSQL in JavaScript/TypeScript
 * 
 * This is the main entry point of the library, exporting all public classes and interfaces
 * that can be used by library consumers.
 */

// Core
export * from './core/MCPConfig';
export * from './core/PostgresMCPServer';
export * from './core/MCPRouter';
export * from './core/types';

// Database
export * from './database/PostgresConfig';
export * from './database/PostgresConnection';
export * from './database/PostgresConnectionManager';

// Export PostgresSchemaManager but avoid re-exporting its types that conflict with core/types
export { 
  PostgresSchemaManager 
} from './database/PostgresSchemaManager';

export * from './database/PostgresQueryBuilder';
export * from './database/PostgresSchemaQueries';

// Interfaces
export * from './handlers/HandlerBase';
export * from './services/ServiceBase';
export * from './repositories/RepositoryBase';

// Export PostgresRepository but avoid re-exporting TransactionCallback which conflicts with TransactionService
export {
  PostgresRepository
} from './repositories/PostgresRepository';

// Services
export * from './services/TableService';
export * from './services/QueryService';
export * from './services/ValidationService';
export * from './services/SchemaService';

// Export TransactionService but avoid re-exporting TransactionCallback
export {
  TransactionService,
  TransactionInfo,
  IsolationLevel,
  TransactionStatus
} from './services/TransactionService';

// Export other services
export * from './services/LoggingService';

// Export CacheService but avoid re-exporting CacheStats which conflicts
export {
  CacheService,
  CacheOptions,
  SetOptions
} from './services/CacheService';

export * from './services/MetricsService';
export * from './services/SecurityService';

// Utils
export * from './utils/exceptions';
export * from './utils/logger';
export * from './models/ValidationSchemas';

// Default export for easier usage
import { PostgresMCPServer } from './core/PostgresMCPServer';
export default PostgresMCPServer;