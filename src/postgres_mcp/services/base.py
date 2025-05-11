"""
Base service para serviços da aplicação
"""

from typing import Any, Optional

from postgres_mcp.repository.postgres import PostgresRepository


class BaseService:
    """
    Classe base para todos os serviços da aplicação.
    
    Fornece funcionalidades comuns e acesso ao repositório.
    """
    
    def __init__(self, repository: Optional[PostgresRepository] = None):
        """
        Inicializa o serviço base.
        
        Args:
            repository: Repositório PostgreSQL
        """
        self.repository = repository 