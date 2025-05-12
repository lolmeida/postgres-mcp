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
export * from './database/PostgresSchemaManager';
export * from './database/PostgresQueryBuilder';
export * from './database/PostgresSchemaQueries';

// Interfaces
export * from './handlers/HandlerBase';
export * from './services/ServiceBase';
export * from './repositories/RepositoryBase';

// Implementations
export * from './repositories/PostgresRepository';

// Services
export * from './services/TableService';
export * from './services/QueryService';
export * from './services/ValidationService';
export * from './services/SchemaService';
export * from './services/TransactionService';

// Utils
export * from './utils/exceptions';
export * from './utils/logger';
export * from './models/ValidationSchemas';

// Default export for easier usage
import { PostgresMCPServer } from './core/PostgresMCPServer';
export default PostgresMCPServer; 