"""
Implementação do servidor PostgreSQL MCP
"""

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Any, Dict, List, Optional, Type, Union

from fastmcp import MCPServer as FastMCPServer
from fastmcp import Request as MCPRequest
from fastmcp import Response as MCPResponse
from pydantic import ValidationError as PydanticValidationError

from postgres_mcp.core.config import LogLevel, MCPMode, PostgresMCPConfig
from postgres_mcp.core.exceptions import PostgresMCPError, ValidationError
from postgres_mcp.core.logging import configure_logging
from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.repository.postgres import PostgresRepository
from postgres_mcp.services.base import BaseService


class MCPRouter:
    """
    Roteador para requisições MCP.
    
    Esta classe gerencia o roteamento de requisições MCP para os handlers apropriados.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Inicializa o roteador.
        
        Args:
            logger: Logger configurado
        """
        self.logger = logger
        self.handlers: Dict[str, BaseHandler] = {}
    
    def register_handler(self, tool_name: str, handler: BaseHandler) -> None:
        """
        Registra um handler para uma ferramenta específica.
        
        Args:
            tool_name: Nome da ferramenta
            handler: Handler para a ferramenta
        """
        self.logger.debug("Registrando handler para ferramenta: %s", tool_name)
        self.handlers[tool_name] = handler
    
    async def route(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roteia uma requisição para o handler apropriado.
        
        Args:
            request: Requisição MCP
            
        Returns:
            Resposta do handler
            
        Raises:
            ValidationError: Se a requisição for inválida
            NotImplementedError: Se não houver handler para a ferramenta
        """
        try:
            # Validar formato da requisição
            if not isinstance(request, dict):
                raise ValidationError("Requisição inválida: deve ser um objeto JSON")
            
            # Extrair nome da ferramenta
            tool = request.get("tool")
            if not tool or not isinstance(tool, str):
                raise ValidationError("Requisição inválida: 'tool' ausente ou inválido")
            
            # Extrair parâmetros
            parameters = request.get("parameters", {})
            if not isinstance(parameters, dict):
                raise ValidationError("Requisição inválida: 'parameters' deve ser um objeto")
            
            # Encontrar handler apropriado
            handler = self.handlers.get(tool)
            if not handler:
                raise NotImplementedError(f"Ferramenta não implementada: {tool}")
            
            # Executar handler
            self.logger.debug("Roteando requisição para ferramenta: %s", tool)
            return await handler.handle(parameters)
            
        except PostgresMCPError as e:
            # Erros já formatados para resposta MCP
            self.logger.error("Erro ao processar requisição MCP: %s", str(e))
            return {
                "success": False,
                "error": e.to_dict()
            }
        except PydanticValidationError as e:
            # Erros de validação do Pydantic
            self.logger.error("Erro de validação: %s", str(e))
            return {
                "success": False,
                "error": {
                    "message": "Erro de validação dos parâmetros",
                    "type": "validation_error",
                    "details": {"errors": e.errors()}
                }
            }
        except NotImplementedError as e:
            # Ferramenta não implementada
            self.logger.error("Ferramenta não implementada: %s", str(e))
            return {
                "success": False,
                "error": {
                    "message": str(e),
                    "type": "not_implemented_error"
                }
            }
        except Exception as e:
            # Erros não tratados
            self.logger.exception("Erro não tratado ao processar requisição MCP")
            return {
                "success": False,
                "error": {
                    "message": f"Erro interno: {str(e)}",
                    "type": "internal_error"
                }
            }


class PostgresMCP:
    """
    Implementação principal do servidor PostgreSQL MCP.
    
    Esta classe serve como ponto de entrada para a API MCP PostgreSQL,
    configurando o servidor e gerenciando o ciclo de vida da aplicação.
    """
    
    def __init__(
        self,
        db_host: Optional[str] = None,
        db_port: Optional[int] = None,
        db_name: Optional[str] = None,
        db_user: Optional[str] = None,
        db_password: Optional[str] = None,
        db_ssl: Optional[str] = None,
        mode: Optional[str] = None,
        port: Optional[int] = None,
        host: Optional[str] = None,
        log_level: Optional[str] = None,
        config: Optional[PostgresMCPConfig] = None,
        env_file: Optional[str] = None,
        test_mode: bool = False,
    ):
        """
        Inicializa o servidor PostgreSQL MCP.
        
        Args:
            db_host: Host do PostgreSQL
            db_port: Porta do PostgreSQL
            db_name: Nome do banco de dados PostgreSQL
            db_user: Usuário do PostgreSQL
            db_password: Senha do PostgreSQL
            db_ssl: Modo SSL para conexão PostgreSQL
            mode: Modo de transporte MCP ('stdio' ou 'http')
            port: Porta para servidor HTTP
            host: Host para servidor HTTP
            log_level: Nível de log
            config: Configuração completa (opcional)
            env_file: Arquivo .env para carregar configurações
            test_mode: Modo de teste (não conecta ao banco)
        """
        # Carregar variáveis de ambiente do arquivo .env se especificado
        if env_file:
            self._load_env_file(env_file)
        
        # Inicializar configuração
        self.config = config or self._create_config(
            db_host, db_port, db_name, db_user, db_password, db_ssl,
            mode, port, host, log_level, test_mode
        )
        
        # Configurar logger
        self.logger = configure_logging(self.config.log_level)
        self.logger.info("Inicializando PostgreSQL MCP v%s", self._get_version())
        
        # Inicializar componentes
        self.router = MCPRouter(self.logger)
        self.repository = PostgresRepository(self.config, self.logger)
        self.services: Dict[str, BaseService] = {}
        
        # Flag para controle de estado
        self.running = False
        self.mcp_server: Optional[FastMCPServer] = None
    
    def _get_version(self) -> str:
        """Retorna a versão atual do PostgreSQL MCP."""
        from postgres_mcp import __version__
        return __version__
    
    def _load_env_file(self, env_file: str) -> None:
        """
        Carrega variáveis de ambiente de um arquivo .env.
        
        Args:
            env_file: Caminho para o arquivo .env
        """
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            print("AVISO: pacote python-dotenv não encontrado. Não foi possível carregar o arquivo .env.")
    
    def _create_config(
        self,
        db_host: Optional[str],
        db_port: Optional[int],
        db_name: Optional[str],
        db_user: Optional[str],
        db_password: Optional[str],
        db_ssl: Optional[str],
        mode: Optional[str],
        port: Optional[int],
        host: Optional[str],
        log_level: Optional[str],
        test_mode: bool,
    ) -> PostgresMCPConfig:
        """
        Cria uma configuração combinando parâmetros e variáveis de ambiente.
        
        Args:
            db_host: Host do PostgreSQL
            db_port: Porta do PostgreSQL
            db_name: Nome do banco de dados PostgreSQL
            db_user: Usuário do PostgreSQL
            db_password: Senha do PostgreSQL
            db_ssl: Modo SSL para conexão PostgreSQL
            mode: Modo de transporte MCP ('stdio' ou 'http')
            port: Porta para servidor HTTP
            host: Host para servidor HTTP
            log_level: Nível de log
            test_mode: Modo de teste
            
        Returns:
            Configuração para o PostgreSQL MCP
        """
        # Carregar configuração base das variáveis de ambiente
        config = PostgresMCPConfig.from_env()
        
        # Substituir valores pelos parâmetros fornecidos, se houver
        if db_host is not None:
            config.db_host = db_host
        if db_port is not None:
            config.db_port = db_port
        if db_name is not None:
            config.db_name = db_name
        if db_user is not None:
            config.db_user = db_user
        if db_password is not None:
            config.db_password = db_password
        if db_ssl is not None:
            config.db_ssl = db_ssl
        if mode is not None:
            config.mode = MCPMode(mode)
        if port is not None:
            config.port = port
        if host is not None:
            config.host = host
        if log_level is not None:
            config.log_level = LogLevel(log_level)
        
        # Definir modo de teste
        config.test_mode = test_mode
        
        return config
    
    def _setup_signal_handlers(self) -> None:
        """Configura handlers de sinais para desligamento gracioso."""
        def signal_handler(sig, frame):
            self.logger.info("Sinal recebido, encerrando PostgreSQL MCP...")
            asyncio.create_task(self.stop())
        
        # Registrar handlers para SIGINT e SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _initialize_repository(self) -> None:
        """Inicializa o repositório PostgreSQL."""
        try:
            self.logger.info("Inicializando repositório PostgreSQL...")
            await self.repository.initialize()
        except Exception as e:
            self.logger.error("Falha ao inicializar repositório: %s", str(e))
            raise
    
    def _initialize_services(self) -> None:
        """Inicializa os serviços."""
        from postgres_mcp.services.table import TableService
        from postgres_mcp.services.schema import SchemaService
        from postgres_mcp.services.query import QueryService
        from postgres_mcp.services.transaction import TransactionService
        from postgres_mcp.services.cache import CacheService
        
        # Instanciar serviços
        # O CacheService deve ser instanciado primeiro para ser passado aos outros serviços
        self.services["cache"] = CacheService(self.repository, self.logger)
        cache_service = self.services["cache"]
        
        # Instanciar outros serviços com referência ao CacheService
        self.services["table"] = TableService(self.repository, self.logger, cache_service)
        self.services["schema"] = SchemaService(self.repository, self.logger, cache_service)
        self.services["query"] = QueryService(self.repository, self.logger, self.config, cache_service)
        self.services["transaction"] = TransactionService(self.repository, self.logger)
        
        self.logger.info("Serviços inicializados")
    
    def _initialize_handlers(self) -> None:
        """Inicializa e registra os handlers."""
        from postgres_mcp.handlers.schema import (
            ListSchemasHandler, ListTablesHandler, DescribeTableHandler
        )
        from postgres_mcp.handlers.table import (
            ReadTableHandler, CreateRecordHandler, CreateBatchHandler,
            UpdateRecordsHandler, DeleteRecordsHandler
        )
        from postgres_mcp.handlers.query import ExecuteQueryHandler
        from postgres_mcp.handlers.transaction import (
            BeginTransactionHandler, CommitTransactionHandler, RollbackTransactionHandler
        )
        from postgres_mcp.handlers.cache import (
            GetCacheStatsHandler, ClearCacheHandler
        )
        
        # Extrair serviços
        table_service = self.services["table"]
        schema_service = self.services["schema"]
        query_service = self.services["query"]
        transaction_service = self.services["transaction"]
        cache_service = self.services["cache"]
        
        # Registrar handlers de schema
        self.router.register_handler("list_schemas", ListSchemasHandler(schema_service))
        self.router.register_handler("list_tables", ListTablesHandler(schema_service))
        self.router.register_handler("describe_table", DescribeTableHandler(schema_service))
        
        # Registrar handlers de tabela
        self.router.register_handler("read_table", ReadTableHandler(table_service))
        self.router.register_handler("create_record", CreateRecordHandler(table_service))
        self.router.register_handler("create_batch", CreateBatchHandler(table_service))
        self.router.register_handler("update_records", UpdateRecordsHandler(table_service))
        self.router.register_handler("delete_records", DeleteRecordsHandler(table_service))
        
        # Registrar handler de consulta
        self.router.register_handler("execute_query", ExecuteQueryHandler(query_service))
        
        # Registrar handlers de transação
        self.router.register_handler("begin_transaction", BeginTransactionHandler(transaction_service))
        self.router.register_handler("commit_transaction", CommitTransactionHandler(transaction_service))
        self.router.register_handler("rollback_transaction", RollbackTransactionHandler(transaction_service))
        
        # Registrar handlers de cache
        self.router.register_handler("get_cache_stats", GetCacheStatsHandler(cache_service))
        self.router.register_handler("clear_cache", ClearCacheHandler(cache_service))
        
        self.logger.info("Handlers inicializados e registrados")
    
    async def _handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Processa uma requisição MCP.
        
        Args:
            request: Requisição MCP
            
        Returns:
            Resposta MCP
        """
        try:
            # Converter requisição para dicionário
            request_dict = json.loads(request.json_data)
            
            # Rotear para o handler apropriado
            response_dict = await self.router.route(request_dict)
            
            # Converter resposta para formato MCP
            return MCPResponse(json_data=json.dumps(response_dict))
            
        except json.JSONDecodeError:
            self.logger.error("Requisição inválida: JSON mal-formado")
            error_response = {
                "success": False,
                "error": {
                    "message": "Requisição inválida: JSON mal-formado",
                    "type": "validation_error"
                }
            }
            return MCPResponse(json_data=json.dumps(error_response))
    
    async def start(self) -> None:
        """
        Inicia o servidor PostgreSQL MCP.
        
        Esta função é assíncrona e deve ser chamada em um loop de eventos.
        """
        if self.running:
            self.logger.warning("PostgreSQL MCP já está em execução")
            return
        
        try:
            # Inicializar componentes
            await self._initialize_repository()
            self._initialize_services()
            self._initialize_handlers()
            
            # Configurar handlers de sinais
            self._setup_signal_handlers()
            
            # Iniciar servidor MCP de acordo com o modo
            if self.config.mode == MCPMode.STDIO:
                self.logger.info("Iniciando PostgreSQL MCP em modo STDIO")
                self.mcp_server = FastMCPServer(handler=self._handle_request)
                self.running = True
                await self.mcp_server.start_stdio()
                
            elif self.config.mode == MCPMode.HTTP:
                self.logger.info(
                    "Iniciando PostgreSQL MCP em modo HTTP em %s:%s",
                    self.config.host,
                    self.config.port
                )
                self.mcp_server = FastMCPServer(handler=self._handle_request)
                self.running = True
                await self.mcp_server.start_http(
                    host=self.config.host,
                    port=self.config.port
                )
                
            else:
                raise ValueError(f"Modo de transporte não suportado: {self.config.mode}")
                
        except Exception as e:
            self.logger.exception("Erro ao iniciar PostgreSQL MCP: %s", str(e))
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """
        Para o servidor PostgreSQL MCP.
        
        Esta função é assíncrona e deve ser chamada em um loop de eventos.
        """
        if not self.running:
            return
        
        self.logger.info("Parando PostgreSQL MCP...")
        
        # Parar servidor MCP
        if self.mcp_server:
            await self.mcp_server.stop()
            self.mcp_server = None
        
        # Fechar repositório
        await self.repository.close()
        
        self.running = False
        self.logger.info("PostgreSQL MCP parado")


def run_mcp() -> None:
    """
    Função principal para executar o PostgreSQL MCP a partir da linha de comando.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="PostgreSQL MCP - Model Context Protocol")
    parser.add_argument("--db-host", help="Host do PostgreSQL")
    parser.add_argument("--db-port", type=int, help="Porta do PostgreSQL")
    parser.add_argument("--db-name", help="Nome do banco de dados PostgreSQL")
    parser.add_argument("--db-user", help="Usuário do PostgreSQL")
    parser.add_argument("--db-password", help="Senha do PostgreSQL")
    parser.add_argument("--db-ssl", help="Modo SSL para conexão PostgreSQL")
    parser.add_argument("--mode", choices=["stdio", "http"], help="Modo de transporte MCP")
    parser.add_argument("--port", type=int, help="Porta para servidor HTTP")
    parser.add_argument("--host", help="Host para servidor HTTP")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Nível de log")
    parser.add_argument("--env-file", help="Arquivo .env para carregar configurações")
    parser.add_argument("--test-mode", action="store_true", help="Executar em modo de teste (sem conexão ao banco)")
    
    args = parser.parse_args()
    
    # Criar instância do PostgreSQL MCP
    mcp = PostgresMCP(
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        db_ssl=args.db_ssl,
        mode=args.mode,
        port=args.port,
        host=args.host,
        log_level=args.log_level,
        env_file=args.env_file,
        test_mode=args.test_mode,
    )
    
    # Configurar loop de eventos para execução assíncrona
    loop = asyncio.get_event_loop()
    
    try:
        # Iniciar servidor
        loop.run_until_complete(mcp.start())
        loop.run_forever()
    except KeyboardInterrupt:
        # Parar graciosamente em Ctrl+C
        pass
    finally:
        # Certifique-se de fechar tudo corretamente
        loop.run_until_complete(mcp.stop())
        loop.close()


if __name__ == "__main__":
    run_mcp() 