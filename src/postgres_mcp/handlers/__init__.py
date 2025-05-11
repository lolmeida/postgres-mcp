"""
Pacote de handlers para processamento de requisições MCP
"""

from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.handlers.schema import (
    ListSchemasHandler, ListTablesHandler, DescribeTableHandler
)
from postgres_mcp.handlers.table import (
    ReadTableHandler, CreateRecordHandler, CreateBatchHandler, 
    UpdateRecordsHandler, DeleteRecordsHandler
)
from postgres_mcp.handlers.query import ExecuteQueryHandler
from postgres_mcp.handlers.transaction import (
    BeginTransactionHandler, CommitTransactionHandler, RollbackTransactionHandler
)
from postgres_mcp.handlers.cache import (
    GetCacheStatsHandler, ClearCacheHandler
)
from postgres_mcp.handlers.metrics import (
    GetMetricsHandler, ResetMetricsHandler
)
from postgres_mcp.handlers.views import (
    CreateViewHandler, DescribeViewHandler, DropViewHandler,
    ListViewsHandler, ReadViewHandler, RefreshMaterializedViewHandler
)

__all__ = [
    'BaseHandler',
    'ListSchemasHandler',
    'ListTablesHandler',
    'DescribeTableHandler',
    'ReadTableHandler',
    'CreateRecordHandler',
    'CreateBatchHandler',
    'UpdateRecordsHandler',
    'DeleteRecordsHandler',
    'ExecuteQueryHandler',
    'BeginTransactionHandler',
    'CommitTransactionHandler',
    'RollbackTransactionHandler',
    'GetCacheStatsHandler',
    'ClearCacheHandler',
    'GetMetricsHandler',
    'ResetMetricsHandler',
    'CreateViewHandler',
    'DescribeViewHandler',
    'DropViewHandler',
    'ListViewsHandler',
    'ReadViewHandler',
    'RefreshMaterializedViewHandler'
]

# Mapeamento de ferramentas para handlers
TOOL_HANDLERS = {
    # Ferramentas de schema
    "list_schemas": ListSchemasHandler,
    
    # Ferramentas de tabela
    "list_tables": ListTablesHandler,
    "describe_table": DescribeTableHandler,
    "read_table": ReadTableHandler,
    "create_record": CreateRecordHandler,
    "create_batch": CreateBatchHandler,
    "update_records": UpdateRecordsHandler,
    "delete_records": DeleteRecordsHandler,
    
    # Ferramentas de consulta
    "execute_query": ExecuteQueryHandler,
    
    # Ferramentas de transação
    "begin_transaction": BeginTransactionHandler,
    "commit_transaction": CommitTransactionHandler,
    "rollback_transaction": RollbackTransactionHandler,
    
    # Ferramentas de cache
    "get_cache_stats": GetCacheStatsHandler,
    "clear_cache": ClearCacheHandler,
    
    # Ferramentas de métricas
    "get_metrics": GetMetricsHandler,
    "reset_metrics": ResetMetricsHandler,
    
    # Ferramentas de views
    "list_views": ListViewsHandler,
    "describe_view": DescribeViewHandler,
    "read_view": ReadViewHandler,
    "create_view": CreateViewHandler,
    "refresh_materialized_view": RefreshMaterializedViewHandler,
    "drop_view": DropViewHandler
} 