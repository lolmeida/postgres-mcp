"""
Serviço para gerenciamento de views PostgreSQL
"""

import logging
from typing import Any, Dict, List, Optional

from postgres_mcp.core.exceptions import ServiceError
from postgres_mcp.models.base import ViewInfo
from postgres_mcp.repository.postgres import PostgresRepository
from postgres_mcp.services.base import BaseService


class ViewService(BaseService):
    """
    Serviço para gerenciamento de views PostgreSQL.
    
    Este serviço fornece operações para listar, descrever, criar, ler, atualizar e excluir views.
    """
    
    def __init__(self, repository: PostgresRepository):
        """
        Inicializa o serviço de views.
        
        Args:
            repository: Repositório PostgreSQL
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def list_views(self, schema: str = "public", include_materialized: bool = True) -> List[str]:
        """
        Lista todas as views em um schema.
        
        Args:
            schema: Nome do schema
            include_materialized: Se deve incluir views materializadas
            
        Returns:
            Lista de nomes de views
        """
        try:
            views = await self.repository.get_views(schema, include_materialized)
            return views
        except Exception as e:
            self.logger.error(f"Erro ao listar views: {str(e)}")
            raise ServiceError(f"Erro ao listar views: {str(e)}")
    
    async def describe_view(self, view: str, schema: str = "public") -> ViewInfo:
        """
        Obtém a descrição detalhada de uma view.
        
        Args:
            view: Nome da view
            schema: Nome do schema
            
        Returns:
            Informações detalhadas da view
        """
        try:
            view_data = await self.repository.describe_view(view, schema)
            return ViewInfo(**view_data)
        except Exception as e:
            self.logger.error(f"Erro ao descrever view {schema}.{view}: {str(e)}")
            raise ServiceError(f"Erro ao descrever view {schema}.{view}: {str(e)}")
    
    async def read_view(
        self,
        view: str,
        schema: str = "public",
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lê registros de uma view.
        
        Args:
            view: Nome da view
            schema: Nome do schema
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            order_by: Coluna para ordenação
            ascending: Direção da ordenação
            limit: Limite de registros a retornar
            offset: Número de registros a pular
            
        Returns:
            Lista de registros
        """
        try:
            records = await self.repository.read_view(
                view=view,
                schema=schema,
                filters=filters,
                columns=columns,
                order_by=order_by,
                ascending=ascending,
                limit=limit,
                offset=offset
            )
            return records
        except Exception as e:
            self.logger.error(f"Erro ao ler view {schema}.{view}: {str(e)}")
            raise ServiceError(f"Erro ao ler view {schema}.{view}: {str(e)}")
    
    async def create_view(
        self,
        view: str,
        definition: str,
        schema: str = "public",
        is_materialized: bool = False,
        replace: bool = False
    ) -> ViewInfo:
        """
        Cria uma nova view.
        
        Args:
            view: Nome da view
            definition: Definição SQL da view
            schema: Nome do schema
            is_materialized: Se é uma view materializada
            replace: Se deve substituir caso já exista
            
        Returns:
            Informações da view criada
        """
        try:
            view_data = await self.repository.create_view(
                view=view,
                definition=definition,
                schema=schema,
                is_materialized=is_materialized,
                replace=replace
            )
            return ViewInfo(**view_data)
        except Exception as e:
            self.logger.error(f"Erro ao criar view {schema}.{view}: {str(e)}")
            raise ServiceError(f"Erro ao criar view {schema}.{view}: {str(e)}")
    
    async def refresh_materialized_view(
        self,
        view: str,
        schema: str = "public",
        concurrently: bool = False
    ) -> bool:
        """
        Atualiza uma view materializada.
        
        Args:
            view: Nome da view materializada
            schema: Nome do schema
            concurrently: Se deve atualizar concurrently
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            success = await self.repository.refresh_materialized_view(
                view=view,
                schema=schema,
                concurrently=concurrently
            )
            return success
        except Exception as e:
            self.logger.error(f"Erro ao atualizar view materializada {schema}.{view}: {str(e)}")
            raise ServiceError(f"Erro ao atualizar view materializada {schema}.{view}: {str(e)}")
    
    async def drop_view(
        self,
        view: str,
        schema: str = "public",
        if_exists: bool = False,
        cascade: bool = False
    ) -> bool:
        """
        Exclui uma view.
        
        Args:
            view: Nome da view
            schema: Nome do schema
            if_exists: Se deve ignorar caso não exista
            cascade: Se deve excluir objetos dependentes
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            success = await self.repository.drop_view(
                view=view,
                schema=schema,
                if_exists=if_exists,
                cascade=cascade
            )
            return success
        except Exception as e:
            self.logger.error(f"Erro ao excluir view {schema}.{view}: {str(e)}")
            raise ServiceError(f"Erro ao excluir view {schema}.{view}: {str(e)}") 