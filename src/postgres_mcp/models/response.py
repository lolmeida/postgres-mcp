"""
Modelos de resposta específicos para o protocolo MCP
"""

from typing import Any, Dict, Optional

from pydantic import Field

from postgres_mcp.models.base import MCPResponse


class DataResponse(MCPResponse):
    """
    Resposta de sucesso com dados.
    
    Atributos:
        success (bool): Sempre True para esta classe
        data (Any): Dados retornados pela operação
        count (int, opcional): Contagem de itens retornados
    """
    
    success: bool = Field(True, description="Indica que a operação foi bem-sucedida")
    data: Any = Field(..., description="Dados retornados pela operação")
    count: Optional[int] = Field(None, description="Contagem de itens retornados")
    error: None = None
    
    def __init__(self, **data):
        """
        Inicializa a resposta de dados.
        
        Se data['data'] for uma lista e count não for fornecido, 
        count será definido automaticamente como o tamanho da lista.
        """
        if "data" in data and isinstance(data["data"], list) and "count" not in data:
            data["count"] = len(data["data"])
            
        super().__init__(**data)


class ErrorResponse(MCPResponse):
    """
    Resposta de erro.
    
    Atributos:
        success (bool): Sempre False para esta classe
        error (dict): Informações detalhadas sobre o erro
    """
    
    success: bool = Field(False, description="Indica que a operação falhou")
    data: None = None
    count: None = None
    error: Dict[str, Any] = Field(..., description="Informações detalhadas sobre o erro")
    
    @classmethod
    def create(
        cls, message: str, error_type: str = "internal_error", details: Optional[Dict[str, Any]] = None
    ) -> "ErrorResponse":
        """
        Método de fábrica para criar uma resposta de erro.
        
        Args:
            message: Mensagem descritiva do erro
            error_type: Tipo do erro (categoria)
            details: Detalhes adicionais específicos do erro
            
        Returns:
            Instância de ErrorResponse
        """
        error = {
            "message": message,
            "type": error_type
        }
        
        if details:
            error["details"] = details
            
        return cls(error=error) 