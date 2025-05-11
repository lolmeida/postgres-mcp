"""
Serviço para gerenciamento de funções e procedimentos armazenados PostgreSQL
"""

import logging
from typing import Any, Dict, List, Optional

from postgres_mcp.core.exceptions import ServiceError
from postgres_mcp.models.base import FunctionInfo
from postgres_mcp.repository.postgres import PostgresRepository
from postgres_mcp.services.base import ServiceBase


class FunctionService(ServiceBase):
    """
    Serviço para gerenciamento de funções e procedimentos armazenados PostgreSQL.
    
    Este serviço fornece operações para listar, descrever, criar, executar e excluir funções e procedimentos.
    """
    
    def __init__(self, repository: PostgresRepository):
        """
        Inicializa o serviço de funções.
        
        Args:
            repository: Repositório PostgreSQL
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def list_functions(
        self, 
        schema: str = "public", 
        include_procedures: bool = True,
        include_aggregates: bool = True
    ) -> List[str]:
        """
        Lista todas as funções em um schema.
        
        Args:
            schema: Nome do schema
            include_procedures: Se deve incluir procedimentos
            include_aggregates: Se deve incluir funções de agregação
            
        Returns:
            Lista de nomes de funções
        """
        try:
            functions = await self.repository.get_functions(
                schema=schema,
                include_procedures=include_procedures,
                include_aggregates=include_aggregates
            )
            return functions
        except Exception as e:
            self.logger.error(f"Erro ao listar funções: {str(e)}")
            raise ServiceError(f"Erro ao listar funções: {str(e)}")
    
    async def describe_function(self, function: str, schema: str = "public") -> FunctionInfo:
        """
        Obtém a descrição detalhada de uma função.
        
        Args:
            function: Nome da função
            schema: Nome do schema
            
        Returns:
            Informações detalhadas da função
        """
        try:
            function_data = await self.repository.describe_function(function, schema)
            return FunctionInfo(**function_data)
        except Exception as e:
            self.logger.error(f"Erro ao descrever função {schema}.{function}: {str(e)}")
            raise ServiceError(f"Erro ao descrever função {schema}.{function}: {str(e)}")
    
    async def execute_function(
        self, 
        function: str, 
        schema: str = "public", 
        args: Optional[List[Any]] = None,
        named_args: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Executa uma função armazenada.
        
        Args:
            function: Nome da função
            schema: Nome do schema
            args: Argumentos posicionais para a função
            named_args: Argumentos nomeados para a função
            
        Returns:
            Resultado da função
        """
        try:
            result = await self.repository.execute_function(
                function=function,
                schema=schema,
                args=args,
                named_args=named_args
            )
            return result
        except Exception as e:
            self.logger.error(f"Erro ao executar função {schema}.{function}: {str(e)}")
            raise ServiceError(f"Erro ao executar função {schema}.{function}: {str(e)}")
    
    async def create_function(
        self,
        function: str,
        definition: str,
        return_type: str,
        schema: str = "public",
        argument_definitions: Optional[List[Dict[str, Any]]] = None,
        language: str = "plpgsql",
        is_procedure: bool = False,
        replace: bool = False,
        security_definer: bool = False,
        volatility: str = "volatile"
    ) -> FunctionInfo:
        """
        Cria uma nova função ou procedimento.
        
        Args:
            function: Nome da função
            definition: Definição SQL da função
            return_type: Tipo de retorno da função
            schema: Nome do schema
            argument_definitions: Definições dos argumentos
            language: Linguagem da função
            is_procedure: Se é um procedimento
            replace: Se deve substituir caso já exista
            security_definer: Se é executada com permissões do criador
            volatility: Volatilidade da função
            
        Returns:
            Informações da função criada
        """
        try:
            function_data = await self.repository.create_function(
                function=function,
                definition=definition,
                return_type=return_type,
                schema=schema,
                argument_definitions=argument_definitions,
                language=language,
                is_procedure=is_procedure,
                replace=replace,
                security_definer=security_definer,
                volatility=volatility
            )
            return FunctionInfo(**function_data)
        except Exception as e:
            self.logger.error(f"Erro ao criar função {schema}.{function}: {str(e)}")
            raise ServiceError(f"Erro ao criar função {schema}.{function}: {str(e)}")
    
    async def drop_function(
        self,
        function: str,
        schema: str = "public",
        if_exists: bool = False,
        cascade: bool = False,
        arg_types: Optional[List[str]] = None
    ) -> bool:
        """
        Exclui uma função.
        
        Args:
            function: Nome da função
            schema: Nome do schema
            if_exists: Se deve ignorar caso não exista
            cascade: Se deve excluir objetos dependentes
            arg_types: Tipos dos argumentos para identificar a função específica
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            success = await self.repository.drop_function(
                function=function,
                schema=schema,
                if_exists=if_exists,
                cascade=cascade,
                arg_types=arg_types
            )
            return success
        except Exception as e:
            self.logger.error(f"Erro ao excluir função {schema}.{function}: {str(e)}")
            raise ServiceError(f"Erro ao excluir função {schema}.{function}: {str(e)}") 