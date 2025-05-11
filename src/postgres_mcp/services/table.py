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
        
        return await self.repository.create(
            table=table,
            data=data,
            returning=returning,
            schema=schema
        )
    
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
        
        return await self.repository.create_many(
            table=table,
            data=data,
            returning=returning,
            schema=schema
        )
    
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
        
        return await self.repository.update(
            table=table,
            filters=filters,
            data=data,
            returning=returning,
            schema=schema
        )
    
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
        
        return await self.repository.delete(
            table=table,
            filters=filters,
            returning=returning,
            schema=schema
        ) 