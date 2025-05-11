"""
PostgreSQL MCP - Model Context Protocol para PostgreSQL
"""

__version__ = "0.1.0"

from postgres_mcp.core.server import PostgresMCP, run_mcp
from postgres_mcp.core.config import PostgresMCPConfig
from postgres_mcp.core.exceptions import (
    PostgresMCPError, DatabaseError, ValidationError, NotFoundError,
    SecurityError, ConnectionError, QueryError, TransactionError
)

__all__ = [
    '__version__',
    'PostgresMCP',
    'run_mcp',
    'PostgresMCPConfig',
    'PostgresMCPError',
    'DatabaseError',
    'ValidationError',
    'NotFoundError',
    'SecurityError',
    'ConnectionError',
    'QueryError',
    'TransactionError'
] 