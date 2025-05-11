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
    
    def __init__(
        self, 
        repository: BaseRepository, 
        logger: logging.Logger,
        cache_service: Optional["CacheService"] = None
    ):
        """
        Inicializa o serviço.
        
        Args:
            repository: Repositório para acesso a dados
            logger: Logger configurado
            cache_service: Serviço de cache (opcional)
        """
        super().__init__(repository, logger)
        self.cache_service = cache_service
    
    async def list_schemas(self) -> List[str]:
        """
        Lista todos os schemas disponíveis.
        
        Returns:
            Lista de nomes de schemas
        """
        self.logger.debug("Listando schemas")
        
        # Verificar cache se disponível
        if self.cache_service:
            cached_schemas = await self.cache_service.get_from_cache("schema:list")
            if cached_schemas is not None:
                self.logger.debug("Retornando schemas do cache")
                return cached_schemas
        
        # Obter schemas do repositório
        schemas = await self.repository.list_schemas()
        
        # Armazenar em cache se disponível
        if self.cache_service:
            await self.cache_service.set_in_cache("schema:list", schemas)
        
        return schemas
    
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
        
        # Criar chave de cache
        cache_key = f"schema:{schema}:tables:{include_views}"
        
        # Verificar cache se disponível
        if self.cache_service:
            cached_tables = await self.cache_service.get_from_cache(cache_key)
            if cached_tables is not None:
                self.logger.debug("Retornando tabelas do cache para schema: %s", schema)
                return cached_tables
        
        # Obter tabelas do repositório
        tables = await self.repository.list_tables(schema, include_views)
        
        # Armazenar em cache se disponível
        if self.cache_service:
            await self.cache_service.set_in_cache(cache_key, tables)
        
        return tables
    
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
        
        # Verificar cache se disponível
        if self.cache_service:
            cached_metadata = await self.cache_service.get_cached_table_metadata(table, schema)
            if cached_metadata is not None:
                self.logger.debug("Retornando metadados do cache para tabela: %s.%s", schema, table)
                return cached_metadata
        
        # Obter metadados do repositório
        metadata = await self.repository.describe_table(table, schema)
        
        # Armazenar em cache se disponível
        if self.cache_service:
            await self.cache_service.cache_table_metadata(table, metadata, schema)
        
        return metadata 