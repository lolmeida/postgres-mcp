"""
Base service para serviços da aplicação
"""

import logging
from typing import Any, Optional

from postgres_mcp.repository.postgres import PostgresRepository


class BaseService:
    """
    Classe base para todos os serviços da aplicação.
    
    Fornece funcionalidades comuns e acesso ao repositório.
    """
    
    def __init__(self, repository: Optional[PostgresRepository] = None, logger: Optional[logging.Logger] = None):
        """
        Inicializa o serviço base.
        
        Args:
            repository: Repositório PostgreSQL
            logger: Logger para registrar atividades do serviço
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__) 