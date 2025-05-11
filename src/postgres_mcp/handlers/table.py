"""
Handlers para operações relacionadas a tabelas PostgreSQL
"""

from typing import Any, Dict

from pydantic import ValidationError

from postgres_mcp.core.exceptions import PostgresMCPError
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.models.requests import (
    CreateBatchRequest, CreateRecordRequest, DeleteRecordsRequest,
    ReadTableRequest, UpdateRecordsRequest
)
from postgres_mcp.services.table import TableService


class ReadTableHandler(BaseHandler):
    """Handler para leitura de registros em tabelas."""
    
    def __init__(self, table_service: TableService):
        """
        Inicializa o handler.
        
        Args:
            table_service: Serviço de tabela
        """
        self.table_service = table_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para ler registros de uma tabela.
        
        Args:
            parameters: Parâmetros da requisição
                - table (str): Nome da tabela
                - schema (str, opcional): Nome do schema (default: "public")
                - filters (dict, opcional): Filtros para a consulta
                - columns (list, opcional): Colunas específicas a retornar
                - order_by (str, opcional): Coluna para ordenação
                - ascending (bool, opcional): Direção da ordenação (default: True)
                - limit (int, opcional): Limite de registros a retornar
                - offset (int, opcional): Número de registros a pular
            
        Returns:
            Resposta formatada com os registros encontrados
        """
        try:
            # Validar parâmetros
            request = ReadTableRequest(**parameters)
            
            # Processar requisição
            result = await self.table_service.read_table(
                table=request.table,
                filters=request.filters,
                columns=request.columns,
                order_by=request.order_by,
                ascending=request.ascending,
                limit=request.limit,
                offset=request.offset,
                schema=request.schema
            )
            
            return self.success_response(
                data=result["data"],
                count=result["count"]
            )
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao ler registros: {str(e)}")


class CreateRecordHandler(BaseHandler):
    """Handler para criação de registros em tabelas."""
    
    def __init__(self, table_service: TableService):
        """
        Inicializa o handler.
        
        Args:
            table_service: Serviço de tabela
        """
        self.table_service = table_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para criar um registro em uma tabela.
        
        Args:
            parameters: Parâmetros da requisição
                - table (str): Nome da tabela
                - schema (str, opcional): Nome do schema (default: "public")
                - data (dict): Dados do registro a ser criado
                - returning (list, opcional): Colunas a serem retornadas após a criação
            
        Returns:
            Resposta formatada com o registro criado
        """
        try:
            # Validar parâmetros
            request = CreateRecordRequest(**parameters)
            
            # Processar requisição
            result = await self.table_service.create_record(
                table=request.table,
                data=request.data,
                returning=request.returning,
                schema=request.schema
            )
            
            return self.success_response(result)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao criar registro: {str(e)}")


class CreateBatchHandler(BaseHandler):
    """Handler para criação em lote de registros em tabelas."""
    
    def __init__(self, table_service: TableService):
        """
        Inicializa o handler.
        
        Args:
            table_service: Serviço de tabela
        """
        self.table_service = table_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para criar múltiplos registros em uma tabela.
        
        Args:
            parameters: Parâmetros da requisição
                - table (str): Nome da tabela
                - schema (str, opcional): Nome do schema (default: "public")
                - data (list): Lista de registros a serem criados
                - returning (list, opcional): Colunas a serem retornadas após a criação
            
        Returns:
            Resposta formatada com os registros criados
        """
        try:
            # Validar parâmetros
            request = CreateBatchRequest(**parameters)
            
            # Processar requisição
            result = await self.table_service.create_batch(
                table=request.table,
                data=request.data,
                returning=request.returning,
                schema=request.schema
            )
            
            return self.success_response(result)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao criar registros em lote: {str(e)}")


class UpdateRecordsHandler(BaseHandler):
    """Handler para atualização de registros em tabelas."""
    
    def __init__(self, table_service: TableService):
        """
        Inicializa o handler.
        
        Args:
            table_service: Serviço de tabela
        """
        self.table_service = table_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para atualizar registros em uma tabela.
        
        Args:
            parameters: Parâmetros da requisição
                - table (str): Nome da tabela
                - schema (str, opcional): Nome do schema (default: "public")
                - filters (dict): Filtros para selecionar registros a serem atualizados
                - data (dict): Dados a serem atualizados
                - returning (list, opcional): Colunas a serem retornadas após a atualização
            
        Returns:
            Resposta formatada com os registros atualizados
        """
        try:
            # Validar parâmetros
            request = UpdateRecordsRequest(**parameters)
            
            # Processar requisição
            result = await self.table_service.update_records(
                table=request.table,
                filters=request.filters,
                data=request.data,
                returning=request.returning,
                schema=request.schema
            )
            
            return self.success_response(result)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao atualizar registros: {str(e)}")


class DeleteRecordsHandler(BaseHandler):
    """Handler para exclusão de registros em tabelas."""
    
    def __init__(self, table_service: TableService):
        """
        Inicializa o handler.
        
        Args:
            table_service: Serviço de tabela
        """
        self.table_service = table_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para excluir registros de uma tabela.
        
        Args:
            parameters: Parâmetros da requisição
                - table (str): Nome da tabela
                - schema (str, opcional): Nome do schema (default: "public")
                - filters (dict): Filtros para selecionar registros a serem excluídos
                - returning (list, opcional): Colunas a serem retornadas dos registros excluídos
            
        Returns:
            Resposta formatada com os registros excluídos
        """
        try:
            # Validar parâmetros
            request = DeleteRecordsRequest(**parameters)
            
            # Processar requisição
            result = await self.table_service.delete_records(
                table=request.table,
                filters=request.filters,
                returning=request.returning,
                schema=request.schema
            )
            
            return self.success_response(result)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao excluir registros: {str(e)}") 