"""
Handlers para operações de banco de dados.
"""

import logging
from typing import Any, Dict, List

from postgres_mcp.core.exceptions import HandlerError, DatabaseError
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.models.base import MCPResponse


class ListDatabasesHandler(BaseHandler):
    """Handler para listagem de bancos de dados."""
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de listagem de bancos de dados.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Implementação básica para permitir que a aplicação carregue
            # Em uma implementação real, consultaria o repositório para obter a lista
            databases = ["postgres", "template0", "template1"]
            
            return self.success_response(data=databases)
        except Exception as e:
            return self.error_response(
                message=f"Erro ao listar bancos de dados: {str(e)}",
                error_type="database_error"
            )


class ConnectDatabaseHandler(BaseHandler):
    """Handler para conexão com banco de dados."""
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de conexão com banco de dados.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Validação de parâmetros
            if "database" not in parameters:
                raise HandlerError("Parâmetro 'database' é obrigatório")
            
            database_name = parameters["database"]
            
            # Implementação básica para permitir que a aplicação carregue
            # Em uma implementação real, estabeleceria uma conexão real
            connection_info = {
                "database": database_name,
                "connected": True,
                "version": "PostgreSQL 15.3"
            }
            
            return self.success_response(data=connection_info)
        except HandlerError as e:
            return self.error_response(
                message=str(e),
                error_type="validation_error"
            )
        except Exception as e:
            return self.error_response(
                message=f"Erro ao conectar ao banco de dados: {str(e)}",
                error_type="database_error"
            )


class GetConnectionHandler(BaseHandler):
    """Handler para obter informações de conexão atual."""
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de informações da conexão atual.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Implementação básica para permitir que a aplicação carregue
            # Em uma implementação real, retornaria informações reais da conexão
            connection_info = {
                "database": "postgres",
                "user": "postgres",
                "connected": True,
                "server_version": "15.3",
                "client_encoding": "UTF8",
                "application_name": "postgres_mcp"
            }
            
            return self.success_response(data=connection_info)
        except Exception as e:
            return self.error_response(
                message=f"Erro ao obter informações de conexão: {str(e)}",
                error_type="database_error"
            ) 