"""
Serviço para operações relacionadas a schemas PostgreSQL
"""

import logging
from typing import Dict, List, Optional, Any

from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.services.base import BaseService


class SchemaService(BaseService):
    """
    Serviço para operações relacionadas a schemas PostgreSQL.
    
    Este serviço gerencia operações como listagem de schemas,
    listagem de tabelas e descrição de tabelas.
    """
    
    async def list_schemas(self) -> List[str]:
        """
        Lista todos os schemas disponíveis.
        
        Returns:
            Lista de nomes de schemas
        """
        self.logger.debug("Listando schemas")
        return await self.repository.list_schemas()
    
    async def list_tables(self, schema: str = "public", include_views: bool = False) -> List[Dict[str, Any]]:
        """
        Lista tabelas em um schema específico.
        
        Args:
            schema: Nome do schema
            include_views: Incluir views nos resultados
            
        Returns:
            Lista de informações de tabelas
        """
        self.logger.debug("Listando tabelas no schema: %s (include_views=%s)", schema, include_views)
        return await self.repository.list_tables(schema, include_views)
    
    async def describe_table(self, table: str, schema: str = "public") -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre uma tabela.
        
        Args:
            table: Nome da tabela
            schema: Nome do schema
            
        Returns:
            Informações detalhadas da tabela
        """
        self.logger.debug("Descrevendo tabela: %s.%s", schema, table)
        return await self.repository.describe_table(table, schema) 