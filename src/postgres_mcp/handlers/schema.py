"""
Handlers para operações relacionadas a schemas PostgreSQL
"""

from typing import Any, Dict

from pydantic import ValidationError

from postgres_mcp.core.exceptions import PostgresMCPError, HandlerError
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.models.requests import DescribeTableRequest, ListTablesRequest
from postgres_mcp.services.schema import SchemaService


class ListSchemasHandler(BaseHandler):
    """Handler para listar schemas disponíveis."""
    
    def __init__(self, schema_service: SchemaService):
        """
        Inicializa o handler.
        
        Args:
            schema_service: Serviço de schema
        """
        self.schema_service = schema_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para listar schemas.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            schemas = await self.schema_service.list_schemas()
            return self.success_response(data=schemas)
        except PostgresMCPError as e:
            return self.error_response(message=str(e), error_type=e.error_type, details=e.details)
        except Exception as e:
            return self.error_response(message=f"Erro ao listar schemas: {str(e)}")


class ListTablesHandler(BaseHandler):
    """Handler para listar tabelas de um schema."""
    
    def __init__(self, schema_service: SchemaService):
        """
        Inicializa o handler.
        
        Args:
            schema_service: Serviço de schema
        """
        self.schema_service = schema_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para listar tabelas.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            request = ListTablesRequest(**parameters)
            tables = await self.schema_service.list_tables(request.schema)
            return self.success_response(data=tables)
        except ValidationError as e:
            return self.error_response(
                message="Parâmetros inválidos",
                error_type="validation_error",
                details={"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(message=str(e), error_type=e.error_type, details=e.details)
        except Exception as e:
            return self.error_response(message=f"Erro ao listar tabelas: {str(e)}")


class DescribeTableHandler(BaseHandler):
    """Handler para descrever uma tabela."""
    
    def __init__(self, schema_service: SchemaService):
        """
        Inicializa o handler.
        
        Args:
            schema_service: Serviço de schema
        """
        self.schema_service = schema_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para descrever uma tabela.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            request = DescribeTableRequest(**parameters)
            table_info = await self.schema_service.describe_table(request.schema, request.table)
            return self.success_response(data=table_info)
        except ValidationError as e:
            return self.error_response(
                message="Parâmetros inválidos",
                error_type="validation_error",
                details={"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(message=str(e), error_type=e.error_type, details=e.details)
        except Exception as e:
            return self.error_response(message=f"Erro ao descrever tabela: {str(e)}")


class CreateSchemaHandler(BaseHandler):
    """Handler para criar um schema."""
    
    def __init__(self, schema_service: SchemaService):
        """
        Inicializa o handler.
        
        Args:
            schema_service: Serviço de schema
        """
        self.schema_service = schema_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para criar um schema.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            if "schema" not in parameters:
                raise HandlerError("O parâmetro 'schema' é obrigatório")
            
            schema_name = parameters["schema"]
            
            # Parâmetro opcional
            if_not_exists = parameters.get("if_not_exists", False)
            
            result = await self.schema_service.create_schema(schema_name, if_not_exists)
            return self.success_response(data={"schema": schema_name, "created": result})
        except PostgresMCPError as e:
            return self.error_response(message=str(e), error_type=e.error_type, details=e.details)
        except Exception as e:
            return self.error_response(message=f"Erro ao criar schema: {str(e)}")


class DescribeSchemaHandler(BaseHandler):
    """Handler para descrever um schema."""
    
    def __init__(self, schema_service: SchemaService):
        """
        Inicializa o handler.
        
        Args:
            schema_service: Serviço de schema
        """
        self.schema_service = schema_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para descrever um schema.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            if "schema" not in parameters:
                raise HandlerError("O parâmetro 'schema' é obrigatório")
                
            schema_name = parameters["schema"]
            
            schema_info = await self.schema_service.describe_schema(schema_name)
            return self.success_response(data=schema_info)
        except PostgresMCPError as e:
            return self.error_response(message=str(e), error_type=e.error_type, details=e.details)
        except Exception as e:
            return self.error_response(message=f"Erro ao descrever schema: {str(e)}")


class DropSchemaHandler(BaseHandler):
    """Handler para excluir um schema."""
    
    def __init__(self, schema_service: SchemaService):
        """
        Inicializa o handler.
        
        Args:
            schema_service: Serviço de schema
        """
        self.schema_service = schema_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para excluir um schema.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada
        """
        try:
            if "schema" not in parameters:
                raise HandlerError("O parâmetro 'schema' é obrigatório")
                
            schema_name = parameters["schema"]
            
            # Parâmetros opcionais
            cascade = parameters.get("cascade", False)
            if_exists = parameters.get("if_exists", False)
            
            result = await self.schema_service.drop_schema(schema_name, cascade, if_exists)
            return self.success_response(data={"schema": schema_name, "dropped": result})
        except PostgresMCPError as e:
            return self.error_response(message=str(e), error_type=e.error_type, details=e.details)
        except Exception as e:
            return self.error_response(message=f"Erro ao excluir schema: {str(e)}") 