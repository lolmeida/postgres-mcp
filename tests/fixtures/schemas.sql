-- Schemas SQL for PostgreSQL MCP integration tests

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS test_schema;

-- Set search path
SET search_path TO public, test_schema; 