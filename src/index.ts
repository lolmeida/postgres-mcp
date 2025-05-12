/**
 * PostgreSQL MCP - Model Context Protocol implementation for PostgreSQL in JavaScript/TypeScript
 * 
 * This is the main entry point of the library, exporting all public classes and interfaces
 * that can be used by library consumers.
 */

// Core
export * from './core/MCPConfig';
export { PostgresMCPServer } from './mcp/server/PostgresMCPServer';
export { MCPServer, MCPServerOptions, ServerEventCallback } from './mcp/server/MCPServer';
export { MCPRouter, MCPRouterOptions, IMCPHandler } from './mcp/router/MCPRouter';
export * from './core/types';

// MCP Models
export { 
  MCPRequest, 
  IMCPRequest, 
  IMCPRequestWithMetadata 
} from './mcp/models/MCPRequest';

export { 
  MCPResponse, 
  IMCPResponse, 
  IMCPResponseWithMetadata,
  ResponseStatus 
} from './mcp/models/MCPResponse';

// MCP Transport
export { 
  IMCPTransport,
  TransportMode,
  MCPTransportBase,
  MCPStdioTransport,
  MCPHttpTransport,
  HTTPTransportConfig,
  MCPTransportFactory
} from './mcp/transport/MCPTransport';

// Database
export * from './database/PostgresConfig';
export * from './database/PostgresConnection';
export * from './database/PostgresConnectionManager';

// Export PostgresSchemaManager but avoid re-exporting its types that conflict with core/types
export { 
  PostgresSchemaManager 
} from './database/PostgresSchemaManager';

export * from './database/PostgresQueryBuilder';

// Repositories
export * from './repositories/PostgresRepository';
export * from './repositories/RepositoryBase';

// Services
export * from './services/ServiceBase';
export * from './services/SchemaService';
export * from './services/QueryService';
export * from './services/ValidationService';

export {
  TableService,
  TableOperationResult,
  TableFilterOptions
} from './services/TableService';

export {
  TransactionService,
  IsolationLevel,
  TransactionInfo
} from './services/TransactionService';

// Auxiliary Services
export * from './services/LoggingService';
export { 
  CacheService, 
  CacheOptions, 
  SetOptions,
  CacheStats
} from './services/CacheService';
export * from './services/MetricsService';
export * from './services/SecurityService';

// Filters System
export {
  FilterParser,
  FilterParserResult,
  FilterOperator,
  SQLParameter,
  and,
  or,
  not,
  AndFilter,
  OrFilter,
  NotFilter,
  ArrayFilterAdapter,
  ArrayFilterOptions,
  JSONBFilterAdapter,
  JSONBFilterOptions,
  GeoFilterAdapter,
  GeoFilterOptions,
  GeoPoint,
  GeoBoundingBox,
  FilterBuilder,
  FilterBuilderOptions
} from './filters';

// Utils
export * from './utils/logger';
export * from './utils/exceptions';

// Export models
export * from './models/ViewInfo';
export * from './models/FunctionInfo';

// Export services
export * from './services/ViewService';
export * from './services/FunctionService';

// Default export for easier usage
import { PostgresMCPServer } from './core/PostgresMCPServer';
export default PostgresMCPServer;