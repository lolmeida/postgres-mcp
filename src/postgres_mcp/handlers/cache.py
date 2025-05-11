"""
Handlers para operações de cache
"""

from typing import Any, Dict, Optional

from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.services.cache import CacheService


class GetCacheStatsHandler(BaseHandler):
    """
    Handler para obter estatísticas do cache.
    """
    
    def __init__(self, cache_service: CacheService):
        """
        Inicializa o handler.
        
        Args:
            cache_service: Serviço de cache
        """
        self.cache_service = cache_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retorna estatísticas do uso de cache.
        
        Args:
            parameters: Não utiliza parâmetros
            
        Returns:
            Resposta com estatísticas de cache
        """
        stats = self.cache_service.get_stats()
        return self.success_response(stats)


class ClearCacheHandler(BaseHandler):
    """
    Handler para limpar o cache.
    """
    
    def __init__(self, cache_service: CacheService):
        """
        Inicializa o handler.
        
        Args:
            cache_service: Serviço de cache
        """
        self.cache_service = cache_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpa o cache.
        
        Args:
            parameters: Parâmetros da requisição
                - scope (str, opcional): Escopo da limpeza ('all', 'table', 'schema')
                - table (str, opcional): Nome da tabela (quando scope='table')
                - schema (str, opcional): Nome do schema (quando scope='schema' ou 'table')
            
        Returns:
            Resposta indicando sucesso
        """
        scope = parameters.get("scope", "all")
        
        if scope == "all":
            self.cache_service.clear_all()
            message = "Cache completamente limpo"
        elif scope == "table":
            table = parameters.get("table")
            schema = parameters.get("schema", "public")
            
            if not table:
                return self.error_response(
                    "Parâmetro 'table' obrigatório quando scope='table'",
                    "validation_error"
                )
                
            self.cache_service.invalidate_table(table, schema)
            message = f"Cache da tabela {schema}.{table} limpo"
        elif scope == "schema":
            schema = parameters.get("schema")
            
            if not schema:
                return self.error_response(
                    "Parâmetro 'schema' obrigatório quando scope='schema'",
                    "validation_error"
                )
                
            self.cache_service.invalidate_schema(schema)
            message = f"Cache do schema {schema} limpo"
        else:
            return self.error_response(
                f"Valor inválido para 'scope': {scope}. Valores válidos: 'all', 'table', 'schema'",
                "validation_error"
            )
            
        return self.success_response({"message": message}) 