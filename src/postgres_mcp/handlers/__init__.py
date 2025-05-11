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
    'RollbackTransactionHandler'
] 