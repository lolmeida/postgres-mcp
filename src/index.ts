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

// Database
export * from './database/PostgresConfig';
export * from './database/PostgresConnection';
export * from './database/PostgresConnectionManager';
export * from './database/PostgresSchemaManager';
export * from './database/PostgresQueryBuilder';

// Interfaces
export * from './handlers/HandlerBase';
export * from './services/ServiceBase';
export * from './repositories/RepositoryBase';
export * from './repositories/PostgresRepository';

// Utils
export * from './utils/exceptions';
export * from './utils/logger';
export * from './utils/ValidationSchemas';

// Default export for easier usage
import { PostgresMCPServer } from './core/PostgresMCPServer';
export default PostgresMCPServer; 