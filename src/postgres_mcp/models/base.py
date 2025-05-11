"""
Modelos base para requisições e respostas MCP
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class MCPRequest(BaseModel):
    """
    Modelo base para requisições MCP.
    
    Atributos:
        tool (str): Nome da ferramenta a ser executada
        parameters (dict): Parâmetros para a ferramenta
    """
    
    tool: str = Field(..., description="Nome da ferramenta a ser executada")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros para a ferramenta")
    
    @validator("tool")
    def validate_tool(cls, v: str) -> str:
        """Valida o nome da ferramenta."""
        if not v or not isinstance(v, str):
            raise ValueError("tool deve ser uma string não vazia")
        return v


class MCPResponse(BaseModel):
    """
    Modelo base para respostas MCP.
    
    Atributos:
        success (bool): Indica se a operação foi bem-sucedida
        data (Any, opcional): Dados retornados pela operação
        count (int, opcional): Contagem de itens retornados
        error (dict, opcional): Informações de erro, se houver
    """
    
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    data: Optional[Any] = Field(None, description="Dados retornados pela operação")
    count: Optional[int] = Field(None, description="Contagem de itens retornados")
    error: Optional[Dict[str, Any]] = Field(None, description="Informações de erro, se houver")
    
    @classmethod
    def success_response(cls, data: Any = None, count: Optional[int] = None) -> "MCPResponse":
        """
        Cria uma resposta de sucesso.
        
        Args:
            data: Dados a serem retornados
            count: Contagem de itens (opcional)
            
        Returns:
            Resposta MCP de sucesso
        """
        if isinstance(data, list) and count is None:
            count = len(data)
        
        return cls(success=True, data=data, count=count)
    
    @classmethod
    def error_response(
        cls, message: str, error_type: str = "internal_error", details: Optional[Dict[str, Any]] = None
    ) -> "MCPResponse":
        """
        Cria uma resposta de erro.
        
        Args:
            message: Mensagem de erro
            error_type: Tipo do erro
            details: Detalhes adicionais do erro
            
        Returns:
            Resposta MCP de erro
        """
        error = {
            "message": message,
            "type": error_type
        }
        
        if details:
            error["details"] = details
            
        return cls(success=False, error=error)


class TableReference(BaseModel):
    """
    Referência a uma tabela PostgreSQL.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
    """
    
    table: str = Field(..., description="Nome da tabela")
    schema: str = Field("public", description="Nome do schema")
    
    @validator("table")
    def validate_table(cls, v: str) -> str:
        """Valida o nome da tabela."""
        if not v:
            raise ValueError("nome da tabela não pode ser vazio")
        return v
    
    @validator("schema")
    def validate_schema(cls, v: str) -> str:
        """Valida o nome do schema."""
        if not v:
            raise ValueError("nome do schema não pode ser vazio")
        return v 