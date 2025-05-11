"""
Classe base para serviços MCP
"""

import abc
import logging
from typing import Any, Dict, List, Optional, TypeVar, Union

from postgres_mcp.repository.base import BaseRepository

T = TypeVar('T')


class BaseService(abc.ABC):
    """
    Classe base para todos os serviços.
    
    Os serviços contêm a lógica de negócios da aplicação e são responsáveis
    por orquestrar operações entre repositórios e outros serviços.
    """
    
    def __init__(self, repository: BaseRepository, logger: logging.Logger):
        """
        Inicializa o serviço.
        
        Args:
            repository: Repositório para acesso a dados
            logger: Logger configurado
        """
        self.repository = repository
        self.logger = logger 