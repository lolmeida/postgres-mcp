"""
Serviço para gerenciamento de cache
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

from cachetools import TTLCache, LRUCache, cached

from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.services.base import BaseService

T = TypeVar('T')
CacheKeyType = Union[str, Tuple[Any, ...]]


class CacheService(BaseService):
    """
    Serviço para gerenciamento de cache nas operações MCP.
    
    Implementa estratégias de cache para otimizar consultas frequentes
    e reduzir a carga no banco de dados.
    """
    
    def __init__(
        self, 
        repository: BaseRepository, 
        logger: logging.Logger,
        max_size: int = 1000,
        ttl: int = 300  # 5 minutes default TTL
    ):
        """
        Inicializa o serviço de cache.
        
        Args:
            repository: Repositório para acesso a dados
            logger: Logger configurado
            max_size: Tamanho máximo do cache (número de itens)
            ttl: Tempo de vida dos itens em cache (segundos)
        """
        super().__init__(repository, logger)
        self.logger.info("Inicializando serviço de cache: max_size=%d, ttl=%d", max_size, ttl)
        
        # Cache principal com TTL para dados de tabelas e consultas
        self.table_cache = TTLCache(maxsize=max_size, ttl=ttl)
        
        # Cache de esquemas (menor e com TTL mais longo)
        self.schema_cache = TTLCache(maxsize=100, ttl=ttl * 2)
        
        # Cache para metadados de tabelas (estrutura, colunas, etc.)
        self.metadata_cache = TTLCache(maxsize=200, ttl=ttl * 3)
        
        # Estatísticas de uso do cache
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0
        }
    
    def get_table_key(self, table: str, schema: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Gera uma chave única para cache de dados de tabela.
        
        Args:
            table: Nome da tabela
            schema: Nome do schema
            filters: Filtros aplicados (opcional)
            
        Returns:
            Chave de cache
        """
        if filters:
            # Convertemos os filtros para uma representação estável para usar como chave
            filters_str = str(sorted([(k, str(v)) for k, v in filters.items()]))
            return f"table:{schema}.{table}:{filters_str}"
        return f"table:{schema}.{table}"
    
    def get_query_key(self, query: str, params: Optional[List[Any]] = None) -> str:
        """
        Gera uma chave única para cache de consultas SQL.
        
        Args:
            query: Consulta SQL
            params: Parâmetros da consulta (opcional)
            
        Returns:
            Chave de cache
        """
        if params:
            return f"query:{query}:{str(params)}"
        return f"query:{query}"
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Recupera um valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se não encontrado
        """
        try:
            if key.startswith("table:"):
                value = self.table_cache.get(key)
            elif key.startswith("schema:"):
                value = self.schema_cache.get(key)
            elif key.startswith("metadata:"):
                value = self.metadata_cache.get(key)
            else:
                value = None
                
            if value is not None:
                self.stats["hits"] += 1
                self.logger.debug("Cache hit: %s", key)
            else:
                self.stats["misses"] += 1
                self.logger.debug("Cache miss: %s", key)
                
            return value
        except Exception as e:
            self.logger.warning("Erro ao acessar cache: %s", str(e))
            return None
    
    def set_in_cache(self, key: str, value: Any) -> None:
        """
        Armazena um valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
        """
        try:
            if key.startswith("table:"):
                self.table_cache[key] = value
            elif key.startswith("schema:"):
                self.schema_cache[key] = value
            elif key.startswith("metadata:"):
                self.metadata_cache[key] = value
                
            self.logger.debug("Cache set: %s", key)
        except Exception as e:
            self.logger.warning("Erro ao armazenar em cache: %s", str(e))
    
    def invalidate(self, key: str) -> None:
        """
        Invalida uma entrada específica do cache.
        
        Args:
            key: Chave do cache a ser invalidada
        """
        try:
            if key.startswith("table:"):
                if key in self.table_cache:
                    del self.table_cache[key]
            elif key.startswith("schema:"):
                if key in self.schema_cache:
                    del self.schema_cache[key]
            elif key.startswith("metadata:"):
                if key in self.metadata_cache:
                    del self.metadata_cache[key]
                    
            self.stats["invalidations"] += 1
            self.logger.debug("Cache invalidado: %s", key)
        except Exception as e:
            self.logger.warning("Erro ao invalidar cache: %s", str(e))
    
    def invalidate_table(self, table: str, schema: str = "public") -> None:
        """
        Invalida todas as entradas de cache relacionadas a uma tabela.
        
        Args:
            table: Nome da tabela
            schema: Nome do schema
        """
        prefix = f"table:{schema}.{table}"
        for key in list(self.table_cache.keys()):
            if key.startswith(prefix):
                self.invalidate(key)
                
        # Também invalidamos o metadado da tabela
        metadata_key = f"metadata:{schema}.{table}"
        self.invalidate(metadata_key)
        
        self.logger.info("Cache invalidado para tabela %s.%s", schema, table)
    
    def invalidate_schema(self, schema: str) -> None:
        """
        Invalida todas as entradas de cache relacionadas a um schema.
        
        Args:
            schema: Nome do schema
        """
        # Invalidar tabelas do schema
        for key in list(self.table_cache.keys()):
            if f"table:{schema}." in key:
                self.invalidate(key)
                
        # Invalidar metadados do schema
        for key in list(self.metadata_cache.keys()):
            if f"metadata:{schema}." in key:
                self.invalidate(key)
                
        # Invalidar a lista de tabelas/schemas
        schema_key = f"schema:{schema}"
        self.invalidate(schema_key)
        
        self.logger.info("Cache invalidado para schema %s", schema)
    
    def clear_all(self) -> None:
        """
        Limpa todo o cache.
        """
        self.table_cache.clear()
        self.schema_cache.clear()
        self.metadata_cache.clear()
        self.logger.info("Cache completamente limpo")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de uso do cache.
        
        Returns:
            Estatísticas do cache
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_ratio = (self.stats["hits"] / total) * 100 if total > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "invalidations": self.stats["invalidations"],
            "hit_ratio": f"{hit_ratio:.2f}%",
            "table_cache_size": len(self.table_cache),
            "schema_cache_size": len(self.schema_cache),
            "metadata_cache_size": len(self.metadata_cache),
            "table_cache_capacity": self.table_cache.maxsize,
            "schema_cache_capacity": self.schema_cache.maxsize,
            "metadata_cache_capacity": self.metadata_cache.maxsize,
        }

    async def cache_table_data(
        self, 
        table: str, 
        data: List[Dict[str, Any]], 
        filters: Optional[Dict[str, Any]] = None,
        schema: str = "public"
    ) -> None:
        """
        Armazena dados de tabela em cache.
        
        Args:
            table: Nome da tabela
            data: Dados a serem armazenados
            filters: Filtros utilizados para obter os dados
            schema: Nome do schema
        """
        key = self.get_table_key(table, schema, filters)
        self.set_in_cache(key, data)
    
    async def get_cached_table_data(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None,
        schema: str = "public"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Recupera dados de tabela do cache.
        
        Args:
            table: Nome da tabela
            filters: Filtros utilizados para obter os dados
            schema: Nome do schema
            
        Returns:
            Dados armazenados ou None se não encontrados
        """
        key = self.get_table_key(table, schema, filters)
        return self.get_from_cache(key)
    
    async def cache_query_result(
        self, 
        query: str, 
        result: Any, 
        params: Optional[List[Any]] = None
    ) -> None:
        """
        Armazena resultado de consulta em cache.
        
        Args:
            query: Consulta SQL
            result: Resultado da consulta
            params: Parâmetros da consulta
        """
        key = self.get_query_key(query, params)
        self.set_in_cache(key, result)
    
    async def get_cached_query_result(
        self, 
        query: str, 
        params: Optional[List[Any]] = None
    ) -> Optional[Any]:
        """
        Recupera resultado de consulta do cache.
        
        Args:
            query: Consulta SQL
            params: Parâmetros da consulta
            
        Returns:
            Resultado armazenado ou None se não encontrado
        """
        key = self.get_query_key(query, params)
        return self.get_from_cache(key)
    
    async def cache_table_metadata(
        self, 
        table: str, 
        metadata: Dict[str, Any], 
        schema: str = "public"
    ) -> None:
        """
        Armazena metadados de tabela em cache.
        
        Args:
            table: Nome da tabela
            metadata: Metadados da tabela
            schema: Nome do schema
        """
        key = f"metadata:{schema}.{table}"
        self.set_in_cache(key, metadata)
    
    async def get_cached_table_metadata(
        self, 
        table: str, 
        schema: str = "public"
    ) -> Optional[Dict[str, Any]]:
        """
        Recupera metadados de tabela do cache.
        
        Args:
            table: Nome da tabela
            schema: Nome do schema
            
        Returns:
            Metadados armazenados ou None se não encontrados
        """
        key = f"metadata:{schema}.{table}"
        return self.get_from_cache(key) 