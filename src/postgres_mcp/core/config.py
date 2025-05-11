"""
Configurações para o PostgreSQL MCP
"""

import os
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


class LogLevel(str, Enum):
    """Níveis de log suportados."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SSLMode(str, Enum):
    """Modos SSL suportados pelo PostgreSQL."""
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class MCPMode(str, Enum):
    """Modos de transporte MCP suportados."""
    STDIO = "stdio"
    HTTP = "http"


class PostgresMCPConfig(BaseModel):
    """Configuração para o PostgreSQL MCP."""
    
    # Database settings
    db_host: str = Field(default="localhost", description="Host do PostgreSQL")
    db_port: int = Field(default=5432, description="Porta do PostgreSQL")
    db_name: str = Field(default="postgres", description="Nome do banco de dados PostgreSQL")
    db_user: str = Field(default="postgres", description="Usuário do PostgreSQL")
    db_password: str = Field(default="postgres", description="Senha do PostgreSQL")
    db_ssl: SSLMode = Field(default=SSLMode.PREFER, description="Modo SSL para conexão PostgreSQL")
    
    # Server settings
    mode: MCPMode = Field(default=MCPMode.STDIO, description="Modo de transporte MCP")
    port: int = Field(default=8000, description="Porta para servidor HTTP")
    host: str = Field(default="0.0.0.0", description="Host para servidor HTTP")
    
    # Pool settings
    pool_min_size: int = Field(default=5, description="Tamanho mínimo do pool de conexões")
    pool_max_size: int = Field(default=20, description="Tamanho máximo do pool de conexões")
    
    # Logging settings
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Nível de log")
    log_sql_queries: bool = Field(default=False, description="Log de consultas SQL")
    
    # Timeout settings
    command_timeout: int = Field(default=60, description="Timeout para comandos em segundos")
    transaction_timeout: int = Field(default=300, description="Timeout para transações em segundos")
    
    # Security settings
    max_query_rows: int = Field(default=10000, description="Limite máximo de linhas para consultas")
    enable_execute_query: bool = Field(default=True, description="Habilitar ferramenta execute_query")
    
    # Test mode
    test_mode: bool = Field(default=False, description="Modo de teste (não conecta ao banco)")
    
    @validator("pool_min_size")
    def validate_min_pool_size(cls, v, values):
        """Valida que o tamanho mínimo do pool é maior que 0."""
        if v < 1:
            raise ValueError("pool_min_size deve ser maior que 0")
        return v
    
    @validator("pool_max_size")
    def validate_max_pool_size(cls, v, values):
        """Valida que o tamanho máximo do pool é maior que o mínimo."""
        min_size = values.get("pool_min_size", 5)
        if v < min_size:
            raise ValueError(f"pool_max_size deve ser maior ou igual a pool_min_size ({min_size})")
        return v
    
    @classmethod
    def from_env(cls) -> "PostgresMCPConfig":
        """Carrega configuração das variáveis de ambiente."""
        return cls(
            # Database settings
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "postgres"),
            db_user=os.getenv("DB_USER", "postgres"),
            db_password=os.getenv("DB_PASSWORD", "postgres"),
            db_ssl=os.getenv("DB_SSL", "prefer"),
            
            # Server settings
            mode=os.getenv("MCP_MODE", "stdio"),
            port=int(os.getenv("MCP_PORT", "8000")),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            
            # Pool settings
            pool_min_size=int(os.getenv("POOL_MIN_SIZE", "5")),
            pool_max_size=int(os.getenv("POOL_MAX_SIZE", "20")),
            
            # Logging settings
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_sql_queries=os.getenv("LOG_SQL_QUERIES", "").lower() == "true",
            
            # Timeout settings
            command_timeout=int(os.getenv("COMMAND_TIMEOUT", "60")),
            transaction_timeout=int(os.getenv("TRANSACTION_TIMEOUT", "300")),
            
            # Security settings
            max_query_rows=int(os.getenv("MAX_QUERY_ROWS", "10000")),
            enable_execute_query=os.getenv("ENABLE_EXECUTE_QUERY", "").lower() != "false",
        ) 