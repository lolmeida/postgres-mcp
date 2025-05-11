"""
Handlers MCP para operações com funções e procedimentos armazenados PostgreSQL
"""

import logging
from typing import Any, Dict

from postgres_mcp.core.exceptions import HandlerError
from postgres_mcp.handlers.base import HandlerBase
from postgres_mcp.models.requests import (
    CreateFunctionRequest, DescribeFunctionRequest, DropFunctionRequest,
    ExecuteFunctionRequest, ListFunctionsRequest
)
from postgres_mcp.models.response import DataResponse, ErrorResponse


class ListFunctionsHandler(HandlerBase):
    """Handler para listagem de funções."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de listagem de funções.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = ListFunctionsRequest(**params)
            
            # Busca as funções
            functions = await self.services.function_service.list_functions(
                schema=request.schema,
                include_procedures=request.include_procedures,
                include_aggregates=request.include_aggregates
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=functions,
                count=len(functions)
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao listar funções: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class DescribeFunctionHandler(HandlerBase):
    """Handler para descrição de função."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de descrição de função.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = DescribeFunctionRequest(**params)
            
            # Busca a descrição da função
            function_info = await self.services.function_service.describe_function(
                function=request.function,
                schema=request.schema
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=function_info.model_dump(),
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao descrever função: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class ExecuteFunctionHandler(HandlerBase):
    """Handler para execução de função."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de execução de função.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = ExecuteFunctionRequest(**params)
            
            # Executa a função
            result = await self.services.function_service.execute_function(
                function=request.function,
                schema=request.schema,
                args=request.args,
                named_args=request.named_args
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=result,
                count=1 if result is not None else 0
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao executar função: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class CreateFunctionHandler(HandlerBase):
    """Handler para criação de função."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de criação de função.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = CreateFunctionRequest(**params)
            
            # Cria a função
            function_info = await self.services.function_service.create_function(
                function=request.function,
                definition=request.definition,
                return_type=request.return_type,
                schema=request.schema,
                argument_definitions=request.argument_definitions,
                language=request.language,
                is_procedure=request.is_procedure,
                replace=request.replace,
                security_definer=request.security_definer,
                volatility=request.volatility
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data=function_info.model_dump(),
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao criar função: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump()


class DropFunctionHandler(HandlerBase):
    """Handler para exclusão de função."""
    
    async def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa a requisição de exclusão de função.
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            # Valida parâmetros
            request = DropFunctionRequest(**params)
            
            # Exclui a função
            success = await self.services.function_service.drop_function(
                function=request.function,
                schema=request.schema,
                if_exists=request.if_exists,
                cascade=request.cascade,
                arg_types=request.arg_types
            )
            
            # Retorna resposta de sucesso
            return DataResponse(
                success=True,
                data={"success": success},
                count=1
            ).model_dump()
            
        except Exception as e:
            # Loga o erro
            self.logger.error(f"Erro ao excluir função: {str(e)}")
            
            # Retorna resposta de erro
            return ErrorResponse(
                success=False,
                error={
                    "message": str(e),
                    "type": type(e).__name__
                }
            ).model_dump() 