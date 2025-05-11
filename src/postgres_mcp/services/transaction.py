"""
Serviço para gerenciamento de transações PostgreSQL
"""

import logging
from typing import Optional

from postgres_mcp.core.exceptions import TransactionError
from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.services.base import BaseService


class TransactionService(BaseService):
    """
    Serviço para gerenciamento de transações PostgreSQL.
    
    Este serviço gerencia operações transacionais como início, confirmação
    e reversão de transações.
    """
    
    async def begin_transaction(self, isolation_level: str = "read_committed") -> str:
        """
        Inicia uma nova transação.
        
        Args:
            isolation_level: Nível de isolamento da transação
            
        Returns:
            ID da transação
            
        Raises:
            TransactionError: Se houver erro ao iniciar a transação
        """
        self.logger.debug("Iniciando transação com isolamento: %s", isolation_level)
        return await self.repository.begin_transaction(isolation_level)
    
    async def commit_transaction(self, transaction_id: str) -> None:
        """
        Confirma uma transação.
        
        Args:
            transaction_id: ID da transação a ser confirmada
            
        Raises:
            TransactionError: Se a transação não existir ou houver erro ao confirmar
        """
        self.logger.debug("Confirmando transação: %s", transaction_id)
        await self.repository.commit_transaction(transaction_id)
    
    async def rollback_transaction(self, transaction_id: str, savepoint: Optional[str] = None) -> None:
        """
        Reverte uma transação.
        
        Args:
            transaction_id: ID da transação a ser revertida
            savepoint: Nome do savepoint para reversão parcial
            
        Raises:
            TransactionError: Se a transação não existir ou houver erro ao reverter
        """
        if savepoint:
            self.logger.debug("Revertendo transação %s para savepoint %s", transaction_id, savepoint)
        else:
            self.logger.debug("Revertendo transação: %s", transaction_id)
            
        await self.repository.rollback_transaction(transaction_id, savepoint) 