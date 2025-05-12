/**
 * Validation schemas for MCP operations
 * 
 * This file contains Joi schemas for validating request parameters 
 * for all MCP operations. Each schema corresponds to a specific MCP tool.
 */

import Joi from 'joi';

/**
 * Base schema for MCP requests
 */
export const mcpRequestSchema = Joi.object({
  tool: Joi.string().required(),
  parameters: Joi.object().default({})
});

/**
 * Schema for list_schemas operation
 */
export const listSchemasSchema = Joi.object({
  includeSystemSchemas: Joi.boolean().default(false),
  limit: Joi.number().integer().min(1).max(1000).default(100),
  offset: Joi.number().integer().min(0).default(0)
});

/**
 * Schema for list_tables operation
 */
export const listTablesSchema = Joi.object({
  schema: Joi.string().default('public'),
  includeViews: Joi.boolean().default(true),
  limit: Joi.number().integer().min(1).max(1000).default(100),
  offset: Joi.number().integer().min(0).default(0)
});

/**
 * Schema for describe_table operation
 */
export const describeTableSchema = Joi.object({
  schema: Joi.string().default('public'),
  table: Joi.string().required(),
  includeRelations: Joi.boolean().default(true)
});

/**
 * Filter operator schema for read operations
 */
const filterOperatorSchema = Joi.alternatives().try(
  Joi.string(),
  Joi.number(),
  Joi.boolean(),
  Joi.array().items(Joi.any()),
  Joi.object({
    eq: Joi.any(),
    neq: Joi.any(),
    gt: Joi.any(),
    gte: Joi.any(),
    lt: Joi.any(),
    lte: Joi.any(),
    like: Joi.string(),
    ilike: Joi.string(),
    in: Joi.array().items(Joi.any()),
    notIn: Joi.array().items(Joi.any()),
    isNull: Joi.boolean(),
    between: Joi.array().length(2).items(Joi.any())
  })
);

/**
 * Schema for read_table operation
 */
export const readTableSchema = Joi.object({
  schema: Joi.string().default('public'),
  table: Joi.string().required(),
  columns: Joi.array().items(Joi.string()).default([]),
  filter: Joi.object().pattern(Joi.string(), filterOperatorSchema).default({}),
  limit: Joi.number().integer().min(1).max(5000).default(100),
  offset: Joi.number().integer().min(0).default(0),
  orderBy: Joi.alternatives().try(
    Joi.string(),
    Joi.array().items(
      Joi.alternatives().try(
        Joi.string(),
        Joi.object({
          column: Joi.string().required(),
          direction: Joi.string().valid('asc', 'desc').default('asc')
        })
      )
    )
  ).default([])
});

/**
 * Schema for create_record operation
 */
export const createRecordSchema = Joi.object({
  schema: Joi.string().default('public'),
  table: Joi.string().required(),
  data: Joi.object().required(),
  returnRecord: Joi.boolean().default(true)
});

/**
 * Schema for create_batch operation
 */
export const createBatchSchema = Joi.object({
  schema: Joi.string().default('public'),
  table: Joi.string().required(),
  data: Joi.array().items(Joi.object()).min(1).required(),
  returnRecords: Joi.boolean().default(true)
});

/**
 * Schema for update_records operation
 */
export const updateRecordsSchema = Joi.object({
  schema: Joi.string().default('public'),
  table: Joi.string().required(),
  data: Joi.object().required(),
  filter: Joi.object().pattern(Joi.string(), filterOperatorSchema).required(),
  returnRecords: Joi.boolean().default(true)
});

/**
 * Schema for delete_records operation
 */
export const deleteRecordsSchema = Joi.object({
  schema: Joi.string().default('public'),
  table: Joi.string().required(),
  filter: Joi.object().pattern(Joi.string(), filterOperatorSchema).required(),
  returnRecords: Joi.boolean().default(true)
});

/**
 * Schema for execute_query operation
 */
export const executeQuerySchema = Joi.object({
  query: Joi.string().required(),
  parameters: Joi.array().items(Joi.any()).default([]),
  limit: Joi.number().integer().min(1).max(5000).default(100),
  offset: Joi.number().integer().min(0).default(0)
});

/**
 * Schema for transaction operations
 */
export const transactionSchema = Joi.object({
  transactionId: Joi.string().uuid()
});

/**
 * Schema for cache operations
 */
export const cacheSchema = Joi.object({
  tableName: Joi.string(),
  schemaName: Joi.string(),
  all: Joi.boolean().default(false)
}); 