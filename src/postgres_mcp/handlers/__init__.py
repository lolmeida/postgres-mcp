"""
Pacote de handlers MCP para processamento de requisições
"""

from postgres_mcp.handlers.base import BaseHandler, HandlerRegistry
from postgres_mcp.handlers.database import (
    ListDatabasesHandler, ConnectDatabaseHandler, GetConnectionHandler
)
from postgres_mcp.handlers.schema import (
    ListSchemasHandler, CreateSchemaHandler, DescribeSchemaHandler, DropSchemaHandler,
    ListTablesHandler, DescribeTableHandler
)
from postgres_mcp.handlers.table import (
    CreateTableHandler, AlterTableHandler, DropTableHandler, TruncateTableHandler
)
from postgres_mcp.handlers.query import (
    QueryHandler, InsertHandler, UpdateHandler, DeleteHandler, 
    CountHandler, ExistsHandler, MetadataHandler
)
from postgres_mcp.handlers.transaction import (
    BeginTransactionHandler, CommitTransactionHandler, 
    RollbackTransactionHandler, TransactionStatusHandler
)
from postgres_mcp.handlers.cache import (
    GetCacheHandler, SetCacheHandler, DeleteCacheHandler, 
    FlushCacheHandler, GetCacheStatsHandler
)
from postgres_mcp.handlers.metrics import (
    GetMetricsHandler, ResetMetricsHandler, GetPerformanceHandler
)
from postgres_mcp.handlers.views import (
    ListViewsHandler, DescribeViewHandler, CreateViewHandler,
    RefreshMaterializedViewHandler, DropViewHandler
)
from postgres_mcp.handlers.functions import (
    ListFunctionsHandler, DescribeFunctionHandler, ExecuteFunctionHandler,
    CreateFunctionHandler, DropFunctionHandler
)

__all__ = [
    'BaseHandler',
    'HandlerRegistry',
    # Database Handlers
    'ListDatabasesHandler',
    'ConnectDatabaseHandler',
    'GetConnectionHandler',
    # Schema Handlers
    'ListSchemasHandler',
    'CreateSchemaHandler',
    'DescribeSchemaHandler',
    'DropSchemaHandler',
    'ListTablesHandler',
    'DescribeTableHandler',
    # Table Handlers
    'CreateTableHandler',
    'AlterTableHandler',
    'DropTableHandler',
    'TruncateTableHandler',
    # Query Handlers
    'QueryHandler',
    'InsertHandler',
    'UpdateHandler',
    'DeleteHandler',
    'CountHandler',
    'ExistsHandler',
    'MetadataHandler',
    # Transaction Handlers
    'BeginTransactionHandler',
    'CommitTransactionHandler',
    'RollbackTransactionHandler',
    'TransactionStatusHandler',
    # Cache Handlers
    'GetCacheHandler',
    'SetCacheHandler',
    'DeleteCacheHandler',
    'FlushCacheHandler',
    'GetCacheStatsHandler',
    # Metrics Handlers
    'GetMetricsHandler',
    'ResetMetricsHandler',
    'GetPerformanceHandler',
    # View Handlers
    'ListViewsHandler',
    'DescribeViewHandler',
    'CreateViewHandler',
    'RefreshMaterializedViewHandler',
    'DropViewHandler',
    # Function Handlers
    'ListFunctionsHandler',
    'DescribeFunctionHandler',
    'ExecuteFunctionHandler',
    'CreateFunctionHandler',
    'DropFunctionHandler',
]

def register_handlers(registry: HandlerRegistry) -> HandlerRegistry:
    """
    Registra todos os handlers disponíveis.
    
    Args:
        registry: Registro de handlers
        
    Returns:
        Registro atualizado
    """
    # Database Handlers
    registry.register("list_databases", ListDatabasesHandler)
    registry.register("connect_database", ConnectDatabaseHandler)
    registry.register("get_connection", GetConnectionHandler)
    
    # Schema Handlers
    registry.register("list_schemas", ListSchemasHandler)
    registry.register("create_schema", CreateSchemaHandler)
    registry.register("describe_schema", DescribeSchemaHandler)
    registry.register("drop_schema", DropSchemaHandler)
    
    # Table Handlers
    registry.register("list_tables", ListTablesHandler)
    registry.register("describe_table", DescribeTableHandler)
    registry.register("create_table", CreateTableHandler)
    registry.register("alter_table", AlterTableHandler)
    registry.register("drop_table", DropTableHandler)
    registry.register("truncate_table", TruncateTableHandler)
    
    # Query Handlers
    registry.register("query", QueryHandler)
    registry.register("insert", InsertHandler)
    registry.register("update", UpdateHandler)
    registry.register("delete", DeleteHandler)
    registry.register("count", CountHandler)
    registry.register("exists", ExistsHandler)
    registry.register("metadata", MetadataHandler)
    
    # Transaction Handlers
    registry.register("begin_transaction", BeginTransactionHandler)
    registry.register("commit_transaction", CommitTransactionHandler)
    registry.register("rollback_transaction", RollbackTransactionHandler)
    registry.register("transaction_status", TransactionStatusHandler)
    
    # Cache Handlers
    registry.register("get_cache", GetCacheHandler)
    registry.register("set_cache", SetCacheHandler)
    registry.register("delete_cache", DeleteCacheHandler)
    registry.register("flush_cache", FlushCacheHandler)
    registry.register("get_cache_stats", GetCacheStatsHandler)
    
    # Metrics Handlers
    registry.register("get_metrics", GetMetricsHandler)
    registry.register("reset_metrics", ResetMetricsHandler)
    registry.register("get_performance", GetPerformanceHandler)
    
    # View Handlers
    registry.register("list_views", ListViewsHandler)
    registry.register("describe_view", DescribeViewHandler)
    registry.register("create_view", CreateViewHandler)
    registry.register("refresh_materialized_view", RefreshMaterializedViewHandler)
    registry.register("drop_view", DropViewHandler)
    
    # Function Handlers
    registry.register("list_functions", ListFunctionsHandler)
    registry.register("describe_function", DescribeFunctionHandler)
    registry.register("execute_function", ExecuteFunctionHandler)
    registry.register("create_function", CreateFunctionHandler)
    registry.register("drop_function", DropFunctionHandler)
    
    return registry 