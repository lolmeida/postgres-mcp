"""
Handlers MCP para operações com views PostgreSQL
"""

import logging
from typing import Any, Dict

from postgres_mcp.core.exceptions import HandlerError
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.models.requests import (
    CreateViewRequest, DescribeViewRequest, DropViewRequest,
    ListViewsRequest, ReadViewRequest, RefreshMaterializedViewRequest
)
from postgres_mcp.models.response import DataResponse, ErrorResponse


class ListViewsHandler(BaseHandler):
    """Handler para listagem de views."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de listagem de views.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = ListViewsRequest(**params)
            
            # Busca as views
            views = await self.services.view_service.list_views(
                schema=request.schema,
                include_materialized=request.include_materialized
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=views,
                count=len(views)
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao listar views: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class DescribeViewHandler(BaseHandler):
    """Handler para descrição de view."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de descrição de view.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = DescribeViewRequest(**params)
            
            # Busca a descrição da view
            view_info = await self.services.view_service.describe_view(
                view=request.view,
                schema=request.schema
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=view_info.model_dump(),
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao descrever view: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class ReadViewHandler(BaseHandler):
    """Handler para leitura de view."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de leitura de view.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = ReadViewRequest(**params)
            
            # Busca os registros
            records = await self.services.view_service.read_view(
                view=request.view,
                schema=request.schema,
                filters=request.filters,
                columns=request.columns,
                order_by=request.order_by,
                ascending=request.ascending,
                limit=request.limit,
                offset=request.offset
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=records,
                count=len(records)
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao ler view: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class CreateViewHandler(BaseHandler):
    """Handler para criação de view."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de criação de view.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = CreateViewRequest(**params)
            
            # Cria a view
            view_info = await self.services.view_service.create_view(
                view=request.view,
                definition=request.definition,
                schema=request.schema,
                is_materialized=request.is_materialized,
                replace=request.replace
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=view_info.model_dump(),
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao criar view: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class RefreshMaterializedViewHandler(BaseHandler):
    """Handler para atualizar view materializada."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de atualização de view materializada.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = RefreshMaterializedViewRequest(**params)
            
            # Atualiza a view materializada
            result = await self.services.view_service.refresh_materialized_view(
                view=request.view,
                schema=request.schema,
                concurrently=request.concurrently
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data={"view": f"{request.schema}.{request.view}", "refreshed": result},
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao atualizar view materializada: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class DropViewHandler(BaseHandler):
    """Handler para excluir view."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de exclusão de view.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = DropViewRequest(**params)
            
            # Exclui a view
            result = await self.services.view_service.drop_view(
                view=request.view,
                schema=request.schema,
                is_materialized=request.is_materialized,
                if_exists=request.if_exists,
                cascade=request.cascade
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data={"view": f"{request.schema}.{request.view}", "dropped": result},
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao excluir view: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump() 