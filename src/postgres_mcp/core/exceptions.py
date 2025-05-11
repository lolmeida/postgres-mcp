"""
Exceções personalizadas para o PostgreSQL MCP
"""

from typing import Any, Dict, Optional


class PostgresMCPError(Exception):
    """Classe base para todas as exceções do PostgreSQL MCP."""
    
    def __init__(
        self, 
        message: str, 
        error_type: str = "internal_error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a exceção para um dicionário para resposta."""
        return {
            "message": self.message,
            "type": self.error_type,
            "details": self.details
        }


class ValidationError(PostgresMCPError):
    """Erro de validação dos parâmetros da requisição."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "validation_error", details)


class DatabaseError(PostgresMCPError):
    """Erro do banco de dados ao processar a operação."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "database_error", details)


class SecurityError(PostgresMCPError):
    """Erro relacionado a permissões ou políticas de segurança."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "security_error", details)


class TransactionError(PostgresMCPError):
    """Erro relacionado a transações."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "transaction_error", details)


class QueryError(PostgresMCPError):
    """Erro na execução de consulta SQL personalizada."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "query_error", details)


class NotFoundError(PostgresMCPError):
    """Erro quando um recurso não é encontrado."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "not_found_error", details)


class ConnectionError(PostgresMCPError):
    """Erro de conexão com o banco de dados."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "connection_error", details)


class ConfigurationError(PostgresMCPError):
    """Erro de configuração."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "configuration_error", details) 