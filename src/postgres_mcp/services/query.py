"""
Serviço para execução de consultas SQL personalizadas
"""

import logging
import re
from typing import Any, Dict, List, Optional

from postgres_mcp.core.config import PostgresMCPConfig
from postgres_mcp.core.exceptions import SecurityError
from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.services.base import BaseService


class QueryService(BaseService):
    """
    Serviço para execução de consultas SQL personalizadas.
    
    Este serviço gerencia a execução segura de consultas SQL personalizadas,
    aplicando validações e restrições de segurança conforme configurado.
    """
    
    def __init__(
        self,
        repository: BaseRepository,
        logger: logging.Logger,
        config: PostgresMCPConfig,
        cache_service: Optional["CacheService"] = None
    ):
        """
        Inicializa o serviço.
        
        Args:
            repository: Repositório para acesso a dados
            logger: Logger configurado
            config: Configuração do PostgreSQL MCP
            cache_service: Serviço de cache (opcional)
        """
        super().__init__(repository, logger)
        self.config = config
        self.cache_service = cache_service
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executa uma consulta SQL personalizada.
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta
            transaction_id: ID da transação (opcional)
            
        Returns:
            Resultados da consulta como lista de dicionários
            
        Raises:
            SecurityError: Se a consulta contiver comandos não permitidos
        """
        # Verificar se a execução de consultas está habilitada
        if not self.config.enable_execute_query:
            raise SecurityError(
                "Execução de consultas SQL personalizadas está desabilitada"
            )
        
        # Sanitizar e validar a consulta
        self._validate_query(query)
        
        # Determinar se é uma consulta SELECT (somente leitura)
        is_select_query = query.strip().upper().startswith("SELECT")
        
        # Verificar cache se for uma consulta SELECT e se não estiver em uma transação
        if is_select_query and not transaction_id and self.cache_service:
            # Converter parâmetros para lista se necessário
            param_list = list(params.values()) if params else None
            
            # Tentar obter resultados do cache
            cached_result = await self.cache_service.get_cached_query_result(query, param_list)
            if cached_result is not None:
                self.logger.debug("Retornando resultado do cache para consulta SQL")
                return cached_result
        
        # Executar a consulta
        self.logger.debug("Executando consulta personalizada")
        result = await self.repository.execute(query, params, True)
        
        # Armazenar em cache se for uma consulta SELECT
        if is_select_query and not transaction_id and self.cache_service:
            # Converter parâmetros para lista se necessário
            param_list = list(params.values()) if params else None
            
            await self.cache_service.cache_query_result(query, result, param_list)
        
        return result
    
    def _validate_query(self, query: str) -> None:
        """
        Valida uma consulta SQL para segurança.
        
        Args:
            query: Consulta SQL a ser validada
            
        Raises:
            SecurityError: Se a consulta contiver comandos não permitidos
        """
        # Verificar se a consulta está vazia
        if not query or not query.strip():
            raise SecurityError("Consulta SQL vazia")
        
        # Lista de comandos SQL bloqueados (se restrict_dangerous_queries estiver habilitado)
        if self.config.restrict_dangerous_queries:
            dangerous_commands = [
                r"\bDROP\s+", r"\bTRUNCATE\s+", r"\bALTER\s+", r"\bCREATE\s+",
                r"\bRENAME\s+", r"\bCOMMENT\s+", r"\bGRANT\s+", r"\bREVOKE\s+",
                r"\bVACUUM\s+", r"\bANALYZE\s+", r"\bCLUSTER\s+", r"\bEXPLAIN\s+",
                r"\bCOPY\s+", r"\bREINDEX\s+"
            ]
            
            # Verificar cada comando perigoso
            for command in dangerous_commands:
                if re.search(command, query, re.IGNORECASE):
                    raise SecurityError(
                        f"Comando SQL não permitido: {command.strip()}"
                    )
        
        # Limite de tamanho da consulta
        if self.config.max_query_length > 0 and len(query) > self.config.max_query_length:
            raise SecurityError(
                f"Consulta SQL excede o tamanho máximo permitido ({self.config.max_query_length} caracteres)"
            ) 