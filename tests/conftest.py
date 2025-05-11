"""
Configuração de testes para o projeto PostgreSQL MCP.
"""

import sys
import pytest
from unittest.mock import MagicMock, AsyncMock

from mock_models import FunctionInfo, ViewInfo, ColumnInfo
from mock_services import CacheService, TransactionService
from mock_handlers import (
    BaseHandler,
    GetCacheStatsHandler, ClearCacheHandler,
    BeginTransactionHandler, CommitTransactionHandler,
    RollbackTransactionHandler, GetTransactionStatusHandler
)


# Classe base para exceções mockadas
class MockBaseError(Exception):
    """Classe base para exceções do PostgreSQL MCP."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
    
    def to_dict(self):
        return {"message": self.message, "type": self.__class__.__name__}


# Exceções mockadas
class MockPostgresMCPError(MockBaseError):
    """Exceção base mockada para o PostgreSQL MCP."""
    pass


class MockValidationError(MockPostgresMCPError):
    """Exceção de validação mockada."""
    pass


class MockHandlerError(MockPostgresMCPError):
    """Exceção de handler mockada."""
    pass


class MockRepositoryError(MockPostgresMCPError):
    """Exceção de repositório mockada."""
    pass


class MockServiceError(MockPostgresMCPError):
    """Exceção de serviço mockada."""
    pass


# Serviços mockados - criamos mock modules para os serviços
mock_cache_module = MagicMock()
mock_cache_module.CacheService = CacheService

mock_transaction_module = MagicMock()
mock_transaction_module.TransactionService = TransactionService

# Handler base mockado
mock_base_handler_module = MagicMock()
mock_base_handler_module.BaseHandler = BaseHandler

# Cache handlers mockados
mock_cache_handler_module = MagicMock()
mock_cache_handler_module.GetCacheStatsHandler = GetCacheStatsHandler
mock_cache_handler_module.ClearCacheHandler = ClearCacheHandler

# Transaction handlers mockados
mock_transaction_handler_module = MagicMock()
mock_transaction_handler_module.BeginTransactionHandler = BeginTransactionHandler
mock_transaction_handler_module.CommitTransactionHandler = CommitTransactionHandler
mock_transaction_handler_module.RollbackTransactionHandler = RollbackTransactionHandler
mock_transaction_handler_module.GetTransactionStatusHandler = GetTransactionStatusHandler


# Criar mocks para os modelos base
mock_base_models = MagicMock()
mock_base_models.FunctionInfo = FunctionInfo
mock_base_models.ViewInfo = ViewInfo
mock_base_models.ColumnInfo = ColumnInfo

# Criar mock para módulo de exceções
mock_exceptions = MagicMock()
mock_exceptions.PostgresMCPError = MockPostgresMCPError
mock_exceptions.ValidationError = MockValidationError
mock_exceptions.HandlerError = MockHandlerError
mock_exceptions.RepositoryError = MockRepositoryError
mock_exceptions.ServiceError = MockServiceError

# Criar mocks para os módulos externos
class MockMCPServer:
    def __init__(self, *args, **kwargs):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass


class MockRequest:
    def __init__(self, *args, **kwargs):
        self.json = {}


class MockResponse:
    def __init__(self, *args, **kwargs):
        self.json = {}


# Criar mocks para os módulos que são importados no código
mock_fastmcp = MagicMock()
mock_fastmcp.MCPServer = MockMCPServer
mock_fastmcp.Request = MockRequest
mock_fastmcp.Response = MockResponse

# Adicionar os mocks ao sys.modules para que sejam importados pelo código
sys.modules['fastmcp'] = mock_fastmcp
sys.modules['postgres_mcp.models.base'] = mock_base_models
sys.modules['postgres_mcp.core.exceptions'] = mock_exceptions
sys.modules['postgres_mcp.services.cache'] = mock_cache_module
sys.modules['postgres_mcp.services.transaction'] = mock_transaction_module
sys.modules['postgres_mcp.handlers.base'] = mock_base_handler_module
sys.modules['postgres_mcp.handlers.cache'] = mock_cache_handler_module
sys.modules['postgres_mcp.handlers.transaction'] = mock_transaction_handler_module


# Configuração para testes assíncronos
@pytest.fixture
def event_loop():
    """Cria um loop de eventos compartilhado para os testes."""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close() 