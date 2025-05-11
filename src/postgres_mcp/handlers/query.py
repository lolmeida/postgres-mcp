"""
Handler para execução de consultas SQL personalizadas
"""

from typing import Any, Dict

from pydantic import ValidationError

from postgres_mcp.core.exceptions import PostgresMCPError
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.models.requests import ExecuteQueryRequest
from postgres_mcp.services.query import QueryService


class ExecuteQueryHandler(BaseHandler):
    """Handler para execução de consultas SQL personalizadas."""
    
    def __init__(self, query_service: QueryService):
        """
        Inicializa o handler.
        
        Args:
            query_service: Serviço de consulta
        """
        self.query_service = query_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para executar uma consulta SQL personalizada.
        
        Args:
            parameters: Parâmetros da requisição
                - query (str): Consulta SQL a ser executada
                - params (dict, opcional): Parâmetros para a consulta
                - transaction_id (str, opcional): ID da transação
            
        Returns:
            Resposta formatada com os resultados da consulta
        """
        try:
            # Validar parâmetros
            request = ExecuteQueryRequest(**parameters)
            
            # Processar requisição
            result = await self.query_service.execute_query(
                query=request.query,
                params=request.params,
                transaction_id=request.transaction_id
            )
            
            return self.success_response(result)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao executar consulta: {str(e)}") 