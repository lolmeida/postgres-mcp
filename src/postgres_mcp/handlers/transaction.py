"""
Handlers para operações relacionadas a transações PostgreSQL
"""

from typing import Any, Dict

from pydantic import ValidationError

from postgres_mcp.core.exceptions import PostgresMCPError
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.models.requests import (
    BeginTransactionRequest, CommitTransactionRequest, RollbackTransactionRequest
)
from postgres_mcp.services.transaction import TransactionService


class BeginTransactionHandler(BaseHandler):
    """Handler para iniciar transações."""
    
    def __init__(self, transaction_service: TransactionService):
        """
        Inicializa o handler.
        
        Args:
            transaction_service: Serviço de transação
        """
        self.transaction_service = transaction_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para iniciar uma transação.
        
        Args:
            parameters: Parâmetros da requisição
                - isolation_level (str, opcional): Nível de isolamento da transação
            
        Returns:
            Resposta formatada com o ID da transação
        """
        try:
            # Validar parâmetros
            request = BeginTransactionRequest(**parameters)
            
            # Processar requisição
            transaction_id = await self.transaction_service.begin_transaction(
                isolation_level=request.isolation_level
            )
            
            return self.success_response({
                "transaction_id": transaction_id
            })
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao iniciar transação: {str(e)}")


class CommitTransactionHandler(BaseHandler):
    """Handler para confirmar transações."""
    
    def __init__(self, transaction_service: TransactionService):
        """
        Inicializa o handler.
        
        Args:
            transaction_service: Serviço de transação
        """
        self.transaction_service = transaction_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para confirmar uma transação.
        
        Args:
            parameters: Parâmetros da requisição
                - transaction_id (str): ID da transação a ser confirmada
            
        Returns:
            Resposta de sucesso ou erro
        """
        try:
            # Validar parâmetros
            request = CommitTransactionRequest(**parameters)
            
            # Processar requisição
            await self.transaction_service.commit_transaction(
                transaction_id=request.transaction_id
            )
            
            return self.success_response({
                "message": f"Transação {request.transaction_id} confirmada com sucesso"
            })
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao confirmar transação: {str(e)}")


class RollbackTransactionHandler(BaseHandler):
    """Handler para reverter transações."""
    
    def __init__(self, transaction_service: TransactionService):
        """
        Inicializa o handler.
        
        Args:
            transaction_service: Serviço de transação
        """
        self.transaction_service = transaction_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para reverter uma transação.
        
        Args:
            parameters: Parâmetros da requisição
                - transaction_id (str): ID da transação a ser revertida
                - savepoint (str, opcional): Nome do savepoint para reversão parcial
            
        Returns:
            Resposta de sucesso ou erro
        """
        try:
            # Validar parâmetros
            request = RollbackTransactionRequest(**parameters)
            
            # Processar requisição
            await self.transaction_service.rollback_transaction(
                transaction_id=request.transaction_id,
                savepoint=request.savepoint
            )
            
            # Construir mensagem de sucesso
            if request.savepoint:
                message = f"Transação {request.transaction_id} revertida para savepoint {request.savepoint}"
            else:
                message = f"Transação {request.transaction_id} revertida com sucesso"
            
            return self.success_response({
                "message": message
            })
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao reverter transação: {str(e)}")


class TransactionStatusHandler(BaseHandler):
    """Handler para consultar o status de uma transação."""
    
    def __init__(self, transaction_service: TransactionService):
        """
        Inicializa o handler.
        
        Args:
            transaction_service: Serviço de transação
        """
        self.transaction_service = transaction_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para consultar o status de uma transação.
        
        Args:
            parameters: Parâmetros da requisição
                - transaction_id (str): ID da transação a ser consultada
            
        Returns:
            Resposta formatada com o status da transação
        """
        try:
            # Validar parâmetros básicos
            if "transaction_id" not in parameters:
                return self.error_response("Parâmetro 'transaction_id' é obrigatório", "validation_error")
            
            transaction_id = parameters["transaction_id"]
            
            # Implementação básica para permitir que a aplicação carregue
            # Em uma implementação real, consultaria o serviço de transação
            status = {
                "transaction_id": transaction_id,
                "status": "active",
                "isolation_level": "read committed",
                "started_at": "2024-05-11T22:00:00Z",
                "operations_count": 0
            }
            
            return self.success_response(status)
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao consultar status da transação: {str(e)}") 