"""
Serviço para operações relacionadas a tabelas PostgreSQL
"""

import logging
from typing import Any, Dict, List, Optional

from postgres_mcp.models.filters import FiltersType
from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.services.base import BaseService


class TableService(BaseService):
    """
    Serviço para operações relacionadas a tabelas PostgreSQL.
    
    Este serviço gerencia operações como leitura, criação, atualização e exclusão
    de registros em tabelas PostgreSQL.
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
    
    async def read_table(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        schema: str = "public",
    ) -> Dict[str, Any]:
        """
        Lê registros de uma tabela.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            order_by: Coluna para ordenação
            ascending: Direção da ordenação
            limit: Limite de registros a retornar
            offset: Número de registros a pular
            schema: Nome do schema
            
        Returns:
            Dicionário com registros e contagem
        """
        self.logger.debug(
            "Lendo tabela %s.%s (filters=%s, columns=%s, order_by=%s, ascending=%s, limit=%s, offset=%s)",
            schema, table, filters, columns, order_by, ascending, limit, offset
        )
        
        # Se tiver offset ou limit, não usamos cache para evitar inconsistências na paginação
        use_cache = self.cache_service is not None and offset is None
        
        # Tentar obter do cache se não tiver offset (paginação)
        if use_cache:
            cached_data = await self.cache_service.get_cached_table_data(table, filters, schema)
            if cached_data is not None:
                self.logger.debug("Retornando dados do cache para tabela: %s.%s", schema, table)
                
                # Aplicar filtros adicionais em memória (order_by, limit) se necessário
                result_data = cached_data
                
                # Se tiver limit, aplicamos aqui
                if limit is not None:
                    result_data = result_data[:limit]
                
                return {
                    "data": result_data,
                    "count": len(cached_data)
                }
        
        # Obter contagem total (sem limit/offset) para paginação
        count = await self.repository.count(table, filters, schema)
        
        # Buscar registros conforme parâmetros
        data = await self.repository.find_many(
            table=table,
            filters=filters,
            columns=columns,
            order_by=order_by,
            ascending=ascending,
            limit=limit,
            offset=offset,
            schema=schema
        )
        
        # Armazenar em cache se necessário e se não tiver limit ou offset
        if use_cache and offset is None and (limit is None or limit >= count):
            await self.cache_service.cache_table_data(table, data, filters, schema)
        
        return {
            "data": data,
            "count": count
        }
    
    async def create_record(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um registro em uma tabela.
        
        Args:
            table: Nome da tabela
            data: Dados do registro a ser criado
            returning: Colunas a serem retornadas após a criação
            schema: Nome do schema
            
        Returns:
            Registro criado (se returning fornecido) ou None
        """
        self.logger.debug(
            "Criando registro em %s.%s (data=%s, returning=%s)",
            schema, table, data, returning
        )
        
        result = await self.repository.create(
            table=table,
            data=data,
            returning=returning,
            schema=schema
        )
        
        # Invalidar cache para a tabela modificada
        if self.cache_service:
            self.cache_service.invalidate_table(table, schema)
        
        return result
    
    async def create_batch(
        self,
        table: str,
        data: List[Dict[str, Any]],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Cria múltiplos registros em uma tabela.
        
        Args:
            table: Nome da tabela
            data: Lista de registros a serem criados
            returning: Colunas a serem retornadas após a criação
            schema: Nome do schema
            
        Returns:
            Lista de registros criados (se returning fornecido) ou lista vazia
        """
        self.logger.debug(
            "Criando registros em lote em %s.%s (%d registros, returning=%s)",
            schema, table, len(data), returning
        )
        
        result = await self.repository.create_many(
            table=table,
            data=data,
            returning=returning,
            schema=schema
        )
        
        # Invalidar cache para a tabela modificada
        if self.cache_service:
            self.cache_service.invalidate_table(table, schema)
        
        return result
    
    async def update_records(
        self,
        table: str,
        filters: FiltersType,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Atualiza registros em uma tabela.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem atualizados
            data: Dados a serem atualizados
            returning: Colunas a serem retornadas após a atualização
            schema: Nome do schema
            
        Returns:
            Lista de registros atualizados (se returning fornecido) ou lista vazia
        """
        self.logger.debug(
            "Atualizando registros em %s.%s (filters=%s, data=%s, returning=%s)",
            schema, table, filters, data, returning
        )
        
        result = await self.repository.update(
            table=table,
            filters=filters,
            data=data,
            returning=returning,
            schema=schema
        )
        
        # Invalidar cache para a tabela modificada
        if self.cache_service:
            self.cache_service.invalidate_table(table, schema)
        
        return result
    
    async def delete_records(
        self,
        table: str,
        filters: FiltersType,
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Exclui registros de uma tabela.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem excluídos
            returning: Colunas a serem retornadas dos registros excluídos
            schema: Nome do schema
            
        Returns:
            Lista de registros excluídos (se returning fornecido) ou lista vazia
        """
        self.logger.debug(
            "Excluindo registros de %s.%s (filters=%s, returning=%s)",
            schema, table, filters, returning
        )
        
        result = await self.repository.delete(
            table=table,
            filters=filters,
            returning=returning,
            schema=schema
        )
        
        # Invalidar cache para a tabela modificada
        if self.cache_service:
            self.cache_service.invalidate_table(table, schema)
        
        return result 