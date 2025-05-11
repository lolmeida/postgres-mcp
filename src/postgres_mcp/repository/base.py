"""
Interface base para repositórios
"""

import abc
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from postgres_mcp.models.filters import FiltersType

T = TypeVar("T")


class BaseRepository(abc.ABC):
    """Interface base para todos os repositórios."""
    
    @abc.abstractmethod
    async def find_one(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        columns: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """
        Busca um único registro.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            schema: Nome do schema (default: "public")
            
        Returns:
            Registro encontrado ou None
        """
        pass
    
    @abc.abstractmethod
    async def find_many(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Busca múltiplos registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            order_by: Coluna para ordenação
            ascending: Direção da ordenação
            limit: Limite de registros a retornar
            offset: Número de registros a pular
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros encontrados
        """
        pass
    
    @abc.abstractmethod
    async def count(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        schema: str = "public",
    ) -> int:
        """
        Conta registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            schema: Nome do schema (default: "public")
            
        Returns:
            Contagem de registros
        """
        pass
    
    @abc.abstractmethod
    async def create(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um registro.
        
        Args:
            table: Nome da tabela
            data: Dados do registro a ser criado
            returning: Colunas a serem retornadas após a criação
            schema: Nome do schema (default: "public")
            
        Returns:
            Registro criado (se returning fornecido) ou None
        """
        pass
    
    @abc.abstractmethod
    async def create_many(
        self,
        table: str,
        data: List[Dict[str, Any]],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Cria múltiplos registros.
        
        Args:
            table: Nome da tabela
            data: Lista de registros a serem criados
            returning: Colunas a serem retornadas após a criação
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros criados (se returning fornecido) ou lista vazia
        """
        pass
    
    @abc.abstractmethod
    async def update(
        self,
        table: str,
        filters: FiltersType,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Atualiza registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem atualizados
            data: Dados a serem atualizados
            returning: Colunas a serem retornadas após a atualização
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros atualizados (se returning fornecido) ou lista vazia
        """
        pass
    
    @abc.abstractmethod
    async def delete(
        self,
        table: str,
        filters: FiltersType,
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Exclui registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem excluídos
            returning: Colunas a serem retornadas dos registros excluídos
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros excluídos (se returning fornecido) ou lista vazia
        """
        pass
    
    @abc.abstractmethod
    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        fetch: bool = True,
    ) -> Union[List[Dict[str, Any]], int]:
        """
        Executa uma consulta SQL arbitrária.
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta
            fetch: Se deve buscar resultados (True) ou apenas executar (False)
            
        Returns:
            Lista de registros (se fetch=True) ou número de linhas afetadas (se fetch=False)
        """
        pass
    
    @abc.abstractmethod
    async def list_schemas(self) -> List[str]:
        """
        Lista schemas disponíveis.
        
        Returns:
            Lista de nomes de schemas
        """
        pass
    
    @abc.abstractmethod
    async def list_tables(self, schema: str = "public", include_views: bool = False) -> List[Dict[str, str]]:
        """
        Lista tabelas disponíveis em um schema.
        
        Args:
            schema: Nome do schema
            include_views: Incluir views nos resultados
            
        Returns:
            Lista de informações de tabelas
        """
        pass
    
    @abc.abstractmethod
    async def describe_table(self, table: str, schema: str = "public") -> Dict[str, Any]:
        """
        Descreve a estrutura de uma tabela.
        
        Args:
            table: Nome da tabela
            schema: Nome do schema
            
        Returns:
            Informações detalhadas da tabela
        """
        pass
    
    @abc.abstractmethod
    async def begin_transaction(self, isolation_level: str = "read_committed") -> str:
        """
        Inicia uma transação.
        
        Args:
            isolation_level: Nível de isolamento da transação
            
        Returns:
            ID da transação
        """
        pass
    
    @abc.abstractmethod
    async def commit_transaction(self, transaction_id: str) -> None:
        """
        Confirma uma transação.
        
        Args:
            transaction_id: ID da transação a ser confirmada
        """
        pass
    
    @abc.abstractmethod
    async def rollback_transaction(self, transaction_id: str, savepoint: Optional[str] = None) -> None:
        """
        Reverte uma transação.
        
        Args:
            transaction_id: ID da transação a ser revertida
            savepoint: Nome do savepoint para o qual reverter (opcional)
        """
        pass
    
    @abc.abstractmethod
    async def get_pool_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pool de conexões.
        
        Returns:
            Dicionário com estatísticas como:
            - total_connections: Total de conexões no pool
            - used_connections: Conexões em uso
            - idle_connections: Conexões ociosas
            - min_size: Tamanho mínimo do pool
            - max_size: Tamanho máximo do pool
        """
        pass
