"""
Pacote de serviços para operações de negócio
"""

from postgres_mcp.services.base import BaseService
from postgres_mcp.services.schema import SchemaService
from postgres_mcp.services.table import TableService
from postgres_mcp.services.query import QueryService
from postgres_mcp.services.transaction import TransactionService
from postgres_mcp.services.cache import CacheService
from postgres_mcp.services.metrics import MetricsService
from postgres_mcp.services.views import ViewService
from postgres_mcp.services.functions import FunctionService

__all__ = [
    'BaseService',
    'SchemaService',
    'TableService',
    'QueryService',
    'TransactionService',
    'CacheService',
    'MetricsService',
    'ViewService',
    'FunctionService'
]

class ServiceContainer:
    """Contêiner para todos os serviços da aplicação."""
    
    def __init__(self, repository: Any):
        """
        Inicializa o contêiner de serviços.
        
        Args:
            repository: Repositório base
        """
        self.schema_service = SchemaService(repository)
        self.table_service = TableService(repository)
        self.query_service = QueryService(repository)
        self.transaction_service = TransactionService(repository)
        self.cache_service = CacheService()
        self.metrics_service = MetricsService()
        self.view_service = ViewService(repository)
        self.function_service = FunctionService(repository)
        
        # Registra o repositório na métrica para monitoramento
        self.metrics_service.register_repository(repository) 