"""
Base classe para handlers MCP
"""

import abc
from typing import Any, Dict, Type

from postgres_mcp.models.base import MCPResponse


class BaseHandler(abc.ABC):
    """
    Classe base para todos os handlers MCP.
    
    Esta classe define a interface comum para todos os handlers de ferramentas MCP.
    Todos os handlers devem validar os parâmetros de entrada, executar a lógica
    de negócios e retornar uma resposta formatada.
    """
    
    @abc.abstractmethod
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma requisição para a ferramenta.
        
        Args:
            parameters: Parâmetros da requisição
            
        Returns:
            Resposta formatada para o cliente
            
        Raises:
            Exceções específicas da ferramenta
        """
        pass
    
    def success_response(self, data: Any = None, count: int = None) -> Dict[str, Any]:
        """
        Cria uma resposta de sucesso.
        
        Args:
            data: Dados a serem retornados
            count: Contagem de itens
            
        Returns:
            Resposta formatada
        """
        response = {"success": True}
        
        if data is not None:
            response["data"] = data
            
            # Se for uma lista e count não for especificado, usar o tamanho da lista
            if isinstance(data, list) and count is None:
                response["count"] = len(data)
        
        if count is not None:
            response["count"] = count
            
        return response
    
    def error_response(self, message: str, error_type: str = "internal_error", details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Cria uma resposta de erro.
        
        Args:
            message: Mensagem de erro
            error_type: Tipo do erro
            details: Detalhes adicionais do erro
            
        Returns:
            Resposta formatada
        """
        error = {
            "message": message,
            "type": error_type
        }
        
        if details:
            error["details"] = details
            
        return {
            "success": False,
            "error": error
        }

class HandlerRegistry:
    """
    Registro de handlers MCP.
    
    Esta classe armazena e permite o acesso aos handlers disponíveis.
    """
    
    def __init__(self):
        """Inicializa o registro de handlers."""
        self._handlers: Dict[str, Type[BaseHandler]] = {}
    
    def register(self, tool_name: str, handler_class: Type[BaseHandler]) -> None:
        """
        Registra um handler para uma ferramenta.
        
        Args:
            tool_name: Nome da ferramenta
            handler_class: Classe do handler
            
        Raises:
            ValueError: Se a ferramenta já estiver registrada
        """
        if tool_name in self._handlers:
            raise ValueError(f"Ferramenta '{tool_name}' já está registrada")
        
        self._handlers[tool_name] = handler_class
    
    def get_handler(self, tool_name: str) -> Type[BaseHandler]:
        """
        Retorna a classe do handler para uma ferramenta.
        
        Args:
            tool_name: Nome da ferramenta
            
        Returns:
            Classe do handler
            
        Raises:
            KeyError: Se a ferramenta não estiver registrada
        """
        if tool_name not in self._handlers:
            raise KeyError(f"Ferramenta '{tool_name}' não está registrada")
        
        return self._handlers[tool_name]
    
    def has_handler(self, tool_name: str) -> bool:
        """
        Verifica se uma ferramenta está registrada.
        
        Args:
            tool_name: Nome da ferramenta
            
        Returns:
            True se a ferramenta estiver registrada, False caso contrário
        """
        return tool_name in self._handlers
    
    def list_tools(self) -> Dict[str, Type[BaseHandler]]:
        """
        Lista todas as ferramentas registradas.
        
        Returns:
            Dicionário com os nomes das ferramentas e suas classes de handler
        """
        return self._handlers.copy() 