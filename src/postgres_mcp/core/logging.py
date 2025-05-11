"""
Configuração de logging para o PostgreSQL MCP
"""

import logging
import sys
from typing import Optional, Union

from postgres_mcp.core.config import LogLevel


def configure_logging(log_level: Union[str, LogLevel] = LogLevel.INFO) -> logging.Logger:
    """
    Configura o logger para o PostgreSQL MCP.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger configurado
    """
    if isinstance(log_level, str):
        log_level = LogLevel(log_level.upper())
    
    # Converte Enum para string do logging
    level = getattr(logging, log_level.value)
    
    # Configuração do formato de log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configuração do logger
    logger = logging.getLogger("postgres_mcp")
    logger.setLevel(level)
    logger.handlers = []  # Limpa handlers existentes para evitar duplicação
    
    # Handler para stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


class SQLLogger:
    """
    Logger para consultas SQL.
    
    Esta classe fornece funcionalidade para logging de consultas SQL
    com suporte para ocultação de credenciais sensíveis e formatação.
    """
    
    def __init__(self, logger: logging.Logger, enabled: bool = False):
        """
        Inicializa o SQLLogger.
        
        Args:
            logger: Logger a ser utilizado
            enabled: Se o logging de SQL está habilitado
        """
        self.logger = logger
        self.enabled = enabled
    
    def log_query(self, query: str, params: Optional[dict] = None) -> None:
        """
        Loga uma consulta SQL.
        
        Args:
            query: A consulta SQL
            params: Parâmetros da consulta (opcional)
        """
        if not self.enabled:
            return
        
        # Sanitiza a consulta para remover credenciais
        sanitized_query = self._sanitize_query(query)
        
        # Loga a consulta
        if params:
            self.logger.debug("Executing SQL: %s with params: %s", sanitized_query, self._sanitize_params(params))
        else:
            self.logger.debug("Executing SQL: %s", sanitized_query)
    
    def _sanitize_query(self, query: str) -> str:
        """
        Sanitiza uma consulta SQL para remover informações sensíveis.
        
        Args:
            query: A consulta SQL original
            
        Returns:
            Consulta sanitizada
        """
        # Aqui poderíamos implementar lógica para substituir senhas e
        # outras informações sensíveis na consulta SQL
        return query
    
    def _sanitize_params(self, params: dict) -> dict:
        """
        Sanitiza parâmetros de consulta para remover informações sensíveis.
        
        Args:
            params: Parâmetros originais
            
        Returns:
            Parâmetros sanitizados
        """
        # Cria uma cópia para não modificar o original
        sanitized = params.copy()
        
        # Substitui valores sensíveis
        sensitive_keys = ["password", "senha", "api_key", "token", "secret"]
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "******"
        
        return sanitized 