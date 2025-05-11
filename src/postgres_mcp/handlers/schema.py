"""
Handlers para operações relacionadas a schemas PostgreSQL
"""

from typing import Any, Dict

from pydantic import ValidationError

from postgres_mcp.core.exceptions import PostgresMCPError
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
            parameters: Parâmetros da requisição (não utilizado para esta operação)
            
        Returns:
            Resposta formatada com a lista de schemas
        """
        try:
            schemas = await self.schema_service.list_schemas()
            return self.success_response(schemas)
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao listar schemas: {str(e)}")


class ListTablesHandler(BaseHandler):
    """Handler para listar tabelas em um schema."""
    
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
                - schema (str, opcional): Nome do schema (default: "public")
                - include_views (bool, opcional): Incluir views nos resultados (default: False)
            
        Returns:
            Resposta formatada com a lista de tabelas
        """
        try:
            # Validar parâmetros
            request = ListTablesRequest(**parameters)
            
            # Processar requisição
            tables = await self.schema_service.list_tables(
                schema=request.schema,
                include_views=request.include_views
            )
            
            return self.success_response(tables)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao listar tabelas: {str(e)}")


class DescribeTableHandler(BaseHandler):
    """Handler para descrever a estrutura de uma tabela."""
    
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
                - table (str): Nome da tabela
                - schema (str, opcional): Nome do schema (default: "public")
            
        Returns:
            Resposta formatada com a descrição da tabela
        """
        try:
            # Validar parâmetros
            request = DescribeTableRequest(**parameters)
            
            # Processar requisição
            table_info = await self.schema_service.describe_table(
                table=request.table,
                schema=request.schema
            )
            
            return self.success_response(table_info)
        except ValidationError as e:
            return self.error_response(
                "Parâmetros inválidos",
                "validation_error",
                {"errors": e.errors()}
            )
        except PostgresMCPError as e:
            return self.error_response(str(e), e.error_type, e.details)
        except Exception as e:
            return self.error_response(f"Erro ao descrever tabela: {str(e)}") 