"""
Implementação do repositório PostgreSQL
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import asyncpg
from asyncpg import Connection, Pool
from asyncpg.transaction import Transaction

from postgres_mcp.core.config import PostgresMCPConfig, SSLMode
from postgres_mcp.core.exceptions import (
    ConnectionError, DatabaseError, NotFoundError, QueryError, TransactionError
)
from postgres_mcp.core.logging import SQLLogger
from postgres_mcp.models.filters import FiltersType
from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.repository.query_builder import QueryBuilder
from postgres_mcp.utils.pg_types import PostgresTypeConverter

logger = logging.getLogger(__name__)


class PostgresRepository(BaseRepository):
    """
    Implementação do repositório para PostgreSQL usando asyncpg.
    """
    
    def __init__(self, config: PostgresMCPConfig, logger: logging.Logger):
        """
        Inicializa o repositório PostgreSQL.
        
        Args:
            config: Configuração do PostgreSQL MCP
            logger: Logger configurado
        """
        self.config = config
        self.logger = logger
        self.pool: Optional[Pool] = None
        self.sql_logger = SQLLogger(logger, config.log_sql_queries)
        self.query_builder = QueryBuilder()
        self._transactions: Dict[str, Transaction] = {}
    
    async def initialize(self) -> None:
        """
        Inicializa o pool de conexões.
        
        Raises:
            ConnectionError: Se não for possível conectar ao banco de dados
        """
        if self.pool:
            return
            
        if self.config.test_mode:
            self.logger.info("Inicializando em modo de teste (sem conexão)")
            return
            
        try:
            # Configuração de SSL
            ssl = None
            if self.config.db_ssl != SSLMode.DISABLE:
                ssl = self.config.db_ssl.value
                
            self.logger.info(
                "Conectando ao PostgreSQL em %s:%s/%s (SSL: %s)",
                self.config.db_host,
                self.config.db_port,
                self.config.db_name,
                self.config.db_ssl.value
            )
            
            # Criar pool de conexões
            self.pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_name,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size,
                command_timeout=self.config.command_timeout,
                ssl=ssl,
            )
            
            # Registra manipuladores de tipos personalizados
            if self.pool:
                PostgresTypeConverter.register_type_handlers(self.pool)
            
            self.logger.info("Conexão com PostgreSQL estabelecida com sucesso")
            
        except (asyncpg.PostgresError, OSError) as err:
            self.logger.error("Falha ao conectar ao PostgreSQL: %s", str(err))
            raise ConnectionError(f"Falha ao conectar ao PostgreSQL: {str(err)}")
    
    async def close(self) -> None:
        """Fecha o pool de conexões."""
        if self.pool:
            # Fechar todas as transações
            for transaction_id, conn in list(self._transactions.items()):
                self.logger.warning("Revertendo transação pendente: %s", transaction_id)
                try:
                    await conn.execute("ROLLBACK")
                    await self._release_connection(conn)
                    del self._transactions[transaction_id]
                except Exception as e:
                    self.logger.error("Erro ao reverter transação pendente %s: %s", transaction_id, str(e))
            
            # Fechar o pool
            await self.pool.close()
            self.pool = None
            self.logger.info("Conexão com PostgreSQL fechada")
    
    async def find_one(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        columns: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """
        Busca um único registro.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            schema: Nome do schema (default: "public")
            
        Returns:
            Registro encontrado ou None
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Construir a consulta
            query, params = self.query_builder.build_select(
                table=table,
                filters=filters,
                columns=columns,
                limit=1,
                schema=schema
            )
            
            # Executar a consulta
            records = await self._execute_query(query, params)
            
            # Retornar o primeiro registro, se houver
            return records[0] if records else None
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao buscar registro em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao buscar registro: {str(e)}")
    
    async def find_many(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Busca múltiplos registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            order_by: Coluna para ordenação
            ascending: Direção da ordenação
            limit: Limite de registros a retornar
            offset: Número de registros a pular
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros encontrados
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Aplicar limite máximo de registros se configurado
            if self.config.max_query_rows and (limit is None or limit > self.config.max_query_rows):
                self.logger.info(
                    "Limitando consulta a %s registros (max_query_rows)",
                    self.config.max_query_rows
                )
                limit = self.config.max_query_rows
            
            # Construir a consulta
            query, params = self.query_builder.build_select(
                table=table,
                filters=filters,
                columns=columns,
                order_by=order_by,
                ascending=ascending,
                limit=limit,
                offset=offset,
                schema=schema
            )
            
            # Executar a consulta
            return await self._execute_query(query, params)
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao buscar registros em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao buscar registros: {str(e)}")
    
    async def count(
        self,
        table: str,
        filters: Optional[FiltersType] = None,
        schema: str = "public",
    ) -> int:
        """
        Conta registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para a consulta
            schema: Nome do schema (default: "public")
            
        Returns:
            Contagem de registros
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Construir a consulta
            query, params = self.query_builder.build_count(
                table=table,
                filters=filters,
                schema=schema
            )
            
            # Executar a consulta
            records = await self._execute_query(query, params)
            
            # Extrair o valor de contagem
            if records and len(records) > 0:
                count_value = records[0].get("count")
                return int(count_value) if count_value is not None else 0
                
            return 0
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao contar registros em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao contar registros: {str(e)}")
    
    async def create(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um registro.
        
        Args:
            table: Nome da tabela
            data: Dados do registro a ser criado
            returning: Colunas a serem retornadas após a criação
            schema: Nome do schema (default: "public")
            
        Returns:
            Registro criado (se returning fornecido) ou None
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Construir a consulta
            query, params = self.query_builder.build_insert(
                table=table,
                data=data,
                returning=returning,
                schema=schema
            )
            
            # Executar a consulta
            records = await self._execute_query(query, params)
            
            # Retornar o registro criado, se houver
            return records[0] if records else None
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao criar registro em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao criar registro: {str(e)}")
    
    async def create_many(
        self,
        table: str,
        data: List[Dict[str, Any]],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Cria múltiplos registros.
        
        Args:
            table: Nome da tabela
            data: Lista de registros a serem criados
            returning: Colunas a serem retornadas após a criação
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros criados (se returning fornecido) ou lista vazia
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Construir a consulta
            query, params = self.query_builder.build_insert(
                table=table,
                data=data,
                returning=returning,
                schema=schema
            )
            
            # Executar a consulta
            return await self._execute_query(query, params)
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao criar registros em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao criar registros: {str(e)}")
    
    async def update(
        self,
        table: str,
        filters: FiltersType,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Atualiza registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem atualizados
            data: Dados a serem atualizados
            returning: Colunas a serem retornadas após a atualização
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros atualizados (se returning fornecido) ou lista vazia
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Verificar se há dados para atualizar
            if not data:
                self.logger.warning("Nenhum dado fornecido para atualização em %s.%s", schema, table)
                return []
            
            # Construir a consulta
            query, params = self.query_builder.build_update(
                table=table,
                filters=filters,
                data=data,
                returning=returning,
                schema=schema
            )
            
            # Executar a consulta
            return await self._execute_query(query, params)
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao atualizar registros em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao atualizar registros: {str(e)}")
    
    async def delete(
        self,
        table: str,
        filters: FiltersType,
        returning: Optional[List[str]] = None,
        schema: str = "public",
    ) -> List[Dict[str, Any]]:
        """
        Exclui registros.
        
        Args:
            table: Nome da tabela
            filters: Filtros para selecionar registros a serem excluídos
            returning: Colunas a serem retornadas dos registros excluídos
            schema: Nome do schema (default: "public")
            
        Returns:
            Lista de registros excluídos (se returning fornecido) ou lista vazia
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Verificar se há filtros (evitar exclusão acidental de todos os registros)
            if not filters:
                raise QueryError("Nenhum filtro fornecido para exclusão (proteção contra exclusão acidental)")
            
            # Construir a consulta
            query, params = self.query_builder.build_delete(
                table=table,
                filters=filters,
                returning=returning,
                schema=schema
            )
            
            # Executar a consulta
            return await self._execute_query(query, params)
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao excluir registros em %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao excluir registros: {str(e)}")
    
    async def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        fetch: bool = True,
    ) -> Union[List[Dict[str, Any]], int]:
        """
        Executa uma consulta SQL arbitrária.
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta
            fetch: Se deve buscar resultados (True) ou apenas executar (False)
            
        Returns:
            Lista de registros (se fetch=True) ou número de linhas afetadas (se fetch=False)
            
        Raises:
            QueryError: Se a execução da consulta falhar
            SecurityError: Se a execução de consultas não estiver habilitada
        """
        if not self.config.enable_execute_query:
            raise SecurityError("Execução de consultas SQL personalizadas está desabilitada")
        
        try:
            # Log da consulta
            self.sql_logger.log_query(query, params)
            
            # Adquirir conexão do pool
            async with self.pool.acquire() as conn:
                if fetch:
                    # Executar consulta e buscar resultados
                    result = await conn.fetch(query, *(params or {}).values())
                    return [dict(r) for r in result]
                else:
                    # Executar consulta sem buscar resultados
                    result = await conn.execute(query, *(params or {}).values())
                    
                    # Extrair o número de linhas afetadas
                    if result:
                        try:
                            # Formato: "UPDATE/INSERT/DELETE N"
                            return int(result.split(" ")[-1])
                        except (ValueError, IndexError):
                            return 0
                    return 0
                    
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao executar consulta SQL: %s", str(e))
            raise QueryError(f"Erro ao executar consulta SQL: {str(e)}")
    
    async def list_schemas(self) -> List[str]:
        """
        Lista schemas disponíveis.
        
        Returns:
            Lista de nomes de schemas
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        query = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT LIKE 'pg_%'
              AND schema_name != 'information_schema'
            ORDER BY schema_name;
        """
        
        try:
            # Executar a consulta
            result = await self._execute_query(query)
            
            # Extrair os nomes dos schemas
            return [record["schema_name"] for record in result]
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao listar schemas: %s", str(e))
            raise DatabaseError(f"Erro ao listar schemas: {str(e)}")
    
    async def list_tables(self, schema: str = "public", include_views: bool = False) -> List[Dict[str, str]]:
        """
        Lista tabelas disponíveis em um schema.
        
        Args:
            schema: Nome do schema
            include_views: Incluir views nos resultados
            
        Returns:
            Lista de informações de tabelas
            
        Raises:
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        table_types = ["'BASE TABLE'"]
        if include_views:
            table_types.append("'VIEW'")
        
        query = f"""
            SELECT 
                table_name,
                table_type,
                obj_description(
                    (quote_ident($1) || '.' || quote_ident(table_name))::regclass, 
                    'pg_class'
                ) as description
            FROM information_schema.tables
            WHERE table_schema = $1
              AND table_type IN ({', '.join(table_types)})
            ORDER BY table_name;
        """
        
        try:
            # Executar a consulta
            async with self.pool.acquire() as conn:
                result = await conn.fetch(query, schema)
                
            # Converter para dicionários
            return [dict(r) for r in result]
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao listar tabelas em %s: %s", schema, str(e))
            raise DatabaseError(f"Erro ao listar tabelas: {str(e)}")
    
    async def _get_connection(self, transaction_id: Optional[str] = None) -> Connection:
        """
        Obtém uma conexão do pool, ou usa uma conexão existente de uma transação.
        
        Args:
            transaction_id: ID da transação (opcional)
            
        Returns:
            Conexão com o banco de dados
        """
        if transaction_id and transaction_id in self._transactions:
            return self._transactions[transaction_id]
        
        if not self.pool:
            raise ConnectionError("Pool de conexões não inicializado")
        
        return await self.pool.acquire()
    
    async def _release_connection(self, conn: Connection, transaction_id: Optional[str] = None) -> None:
        """
        Libera uma conexão de volta para o pool, a menos que seja de uma transação.
        
        Args:
            conn: Conexão a ser liberada
            transaction_id: ID da transação (opcional)
        """
        if transaction_id and transaction_id in self._transactions:
            # Não liberar conexões de transações ativas
            return
        
        await self.pool.release(conn)
    
    async def _execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executa uma consulta SQL e retorna os resultados como dicionários.
        
        Args:
            query: Consulta SQL a ser executada
            params: Parâmetros para a consulta
            transaction_id: ID da transação (opcional)
            
        Returns:
            Lista de registros como dicionários
        """
        # Log da consulta
        self.sql_logger.log_query(query, params)
        
        # Adquirir conexão
        conn = await self._get_connection(transaction_id)
        
        try:
            # Converter parâmetros nomeados para posicionais
            query_args = []
            if params:
                # Substituir referências de parâmetros nomeados por posicionais
                param_keys = list(params.keys())
                for i, key in enumerate(param_keys):
                    query = query.replace(f":{key}", f"${i+1}")
                    query_args.append(params[key])
            
            # Executar a consulta
            result = await conn.fetch(query, *query_args)
            
            # Converter para dicionários
            return [dict(r) for r in result]
            
        finally:
            # Liberar conexão se não estiver em uma transação
            if not transaction_id:
                await self._release_connection(conn)
    
    async def describe_table(self, table: str, schema: str = "public") -> Dict[str, Any]:
        """
        Descreve a estrutura de uma tabela.
        
        Args:
            table: Nome da tabela
            schema: Nome do schema
            
        Returns:
            Informações detalhadas da tabela
            
        Raises:
            NotFoundError: Se a tabela não existir
            DatabaseError: Se ocorrer um erro de banco de dados
        """
        try:
            # Verificar se a tabela existe
            check_query = """
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = $1 
                    AND table_name = $2
                ) as exists;
            """
            
            async with self.pool.acquire() as conn:
                exists = await conn.fetchval(check_query, schema, table)
                
            if not exists:
                raise NotFoundError(f"Tabela {schema}.{table} não encontrada")
            
            # Consulta para obter informações das colunas
            columns_query = """
                SELECT 
                    column_name as name,
                    data_type as type,
                    is_nullable = 'YES' as nullable,
                    column_default as default,
                    character_maximum_length as char_length,
                    numeric_precision as precision,
                    numeric_scale as scale,
                    col_description(
                        (quote_ident($1) || '.' || quote_ident($2))::regclass, 
                        ordinal_position
                    ) as description
                FROM information_schema.columns
                WHERE table_schema = $1
                AND table_name = $2
                ORDER BY ordinal_position;
            """
            
            # Consulta para obter chave primária
            pk_query = """
                SELECT 
                    c.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage AS ccu 
                    ON ccu.constraint_schema = tc.constraint_schema
                    AND ccu.constraint_name = tc.constraint_name
                JOIN information_schema.columns AS c 
                    ON c.table_schema = tc.constraint_schema
                    AND tc.table_name = c.table_name 
                    AND ccu.column_name = c.column_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = $1
                    AND tc.table_name = $2
                ORDER BY c.ordinal_position;
            """
            
            # Consulta para obter chaves estrangeiras
            fk_query = """
                SELECT
                    tc.constraint_name as name,
                    ccu.column_name as column_name,
                    ccu2.table_schema as foreign_table_schema,
                    ccu2.table_name as foreign_table_name,
                    ccu2.column_name as foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage AS ccu 
                    ON ccu.constraint_schema = tc.constraint_schema
                    AND ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints rc
                    ON rc.constraint_schema = tc.constraint_schema
                    AND rc.constraint_name = tc.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu2
                    ON ccu2.constraint_schema = rc.unique_constraint_schema
                    AND ccu2.constraint_name = rc.unique_constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = $1
                    AND tc.table_name = $2;
            """
            
            # Consulta para obter índices
            indexes_query = """
                SELECT
                    i.relname as name,
                    array_agg(a.attname) as columns,
                    ix.indisunique as unique,
                    ix.indisprimary as primary,
                    pg_get_indexdef(ix.indexrelid) as definition
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relkind = 'r'
                    AND n.nspname = $1
                    AND t.relname = $2
                GROUP BY i.relname, ix.indisunique, ix.indisprimary, ix.indexrelid
                ORDER BY i.relname;
            """
            
            # Executar todas as consultas
            async with self.pool.acquire() as conn:
                columns = await conn.fetch(columns_query, schema, table)
                primary_key = await conn.fetch(pk_query, schema, table)
                foreign_keys = await conn.fetch(fk_query, schema, table)
                indexes = await conn.fetch(indexes_query, schema, table)
                
                # Obter comentário da tabela
                table_comment_query = """
                    SELECT 
                        obj_description((quote_ident($1) || '.' || quote_ident($2))::regclass, 'pg_class') as description;
                """
                table_comment = await conn.fetchval(table_comment_query, schema, table)
            
            # Formatar resultados
            result = {
                "name": table,
                "schema": schema,
                "description": table_comment,
                "columns": [dict(col) for col in columns],
                "primary_key": [col["column_name"] for col in primary_key],
                "foreign_keys": [dict(fk) for fk in foreign_keys],
                "indexes": [dict(idx) for idx in indexes]
            }
            
            return result
            
        except NotFoundError:
            raise
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao descrever tabela %s.%s: %s", schema, table, str(e))
            raise DatabaseError(f"Erro ao descrever tabela: {str(e)}")
    
    async def begin_transaction(self, isolation_level: str = "read_committed") -> str:
        """
        Inicia uma transação.
        
        Args:
            isolation_level: Nível de isolamento da transação
            
        Returns:
            ID da transação
            
        Raises:
            ConnectionError: Se não for possível obter uma conexão
            TransactionError: Se houver erro ao iniciar a transação
        """
        try:
            # Validar nível de isolamento
            valid_levels = {
                "read_uncommitted": "READ UNCOMMITTED",
                "read_committed": "READ COMMITTED",
                "repeatable_read": "REPEATABLE READ",
                "serializable": "SERIALIZABLE"
            }
            
            if isolation_level not in valid_levels:
                valid_options = ", ".join(valid_levels.keys())
                raise TransactionError(
                    f"Nível de isolamento inválido: {isolation_level}. Opções válidas: {valid_options}"
                )
            
            # Obter conexão do pool
            conn = await self.pool.acquire()
            
            # Gerar ID único para a transação
            transaction_id = str(uuid.uuid4())
            
            try:
                # Definir nível de isolamento e iniciar transação
                begin_command = f"BEGIN ISOLATION LEVEL {valid_levels[isolation_level]}"
                await conn.execute(begin_command)
                
                # Configurar timeout
                if self.config.transaction_timeout > 0:
                    timeout_ms = self.config.transaction_timeout * 1000
                    await conn.execute(f"SET LOCAL statement_timeout = {timeout_ms}")
                
                # Armazenar conexão para uso futuro
                self._transactions[transaction_id] = conn
                
                self.logger.debug(
                    "Transação iniciada: %s (isolamento: %s)", 
                    transaction_id, 
                    valid_levels[isolation_level]
                )
                
                return transaction_id
                
            except asyncpg.PostgresError as e:
                # Em caso de erro, liberar conexão e propagar exceção
                await self.pool.release(conn)
                raise TransactionError(f"Erro ao iniciar transação: {str(e)}")
                
        except (asyncpg.PostgresError, asyncio.TimeoutError) as e:
            self.logger.error("Erro ao iniciar transação: %s", str(e))
            raise TransactionError(f"Erro ao iniciar transação: {str(e)}")
    
    async def commit_transaction(self, transaction_id: str) -> None:
        """
        Confirma uma transação.
        
        Args:
            transaction_id: ID da transação a ser confirmada
            
        Raises:
            TransactionError: Se a transação não existir ou houver erro ao confirmar
        """
        if transaction_id not in self._transactions:
            raise TransactionError(f"Transação não encontrada: {transaction_id}")
        
        conn = self._transactions[transaction_id]
        
        try:
            # Confirmar a transação
            await conn.execute("COMMIT")
            self.logger.debug("Transação confirmada: %s", transaction_id)
            
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao confirmar transação %s: %s", transaction_id, str(e))
            
            # Tentar reverter em caso de erro
            try:
                await conn.execute("ROLLBACK")
                self.logger.warning("Transação revertida após erro no commit: %s", transaction_id)
            except Exception:
                pass
                
            raise TransactionError(f"Erro ao confirmar transação: {str(e)}")
            
        finally:
            # Remover do dicionário e liberar conexão
            del self._transactions[transaction_id]
            await self.pool.release(conn)
    
    async def rollback_transaction(self, transaction_id: str, savepoint: Optional[str] = None) -> None:
        """
        Reverte uma transação.
        
        Args:
            transaction_id: ID da transação a ser revertida
            savepoint: Nome do savepoint para o qual reverter (opcional)
            
        Raises:
            TransactionError: Se a transação não existir ou ocorrer um erro
        """
        if transaction_id not in self._transactions:
            raise TransactionError(f"Transação não encontrada: {transaction_id}")
            
        conn = self._transactions[transaction_id]
        
        try:
            self.logger.debug("Revertendo transação: %s", transaction_id)
            
            if savepoint:
                # Reverter para um savepoint específico
                await conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                self.logger.debug("Transação revertida para savepoint: %s", savepoint)
            else:
                # Reverter a transação inteira
                await conn.execute("ROLLBACK")
                
                # Liberar a conexão
                await self._release_connection(conn)
                del self._transactions[transaction_id]
                
                self.logger.debug("Transação revertida: %s", transaction_id)
                
        except asyncpg.PostgresError as e:
            self.logger.error("Erro ao reverter transação %s: %s", transaction_id, str(e))
            raise TransactionError(f"Erro ao reverter transação: {str(e)}")
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pool de conexões.
        
        Returns:
            Dicionário com estatísticas como:
            - total_connections: Total de conexões no pool
            - used_connections: Conexões em uso
            - idle_connections: Conexões ociosas
            - min_size: Tamanho mínimo do pool
            - max_size: Tamanho máximo do pool
        """
        if not self.pool or self.config.test_mode:
            # Retornar valores padrão em modo de teste
            return {
                "total_connections": 0,
                "used_connections": 0,
                "idle_connections": 0,
                "min_size": self.config.pool_min_size,
                "max_size": self.config.pool_max_size
            }
            
        try:
            # Obter estatísticas do pool
            stats = {
                "total_connections": len(self.pool._holders),  # Total de conexões gerenciadas
                "used_connections": len([c for c in self.pool._holders if c._con and c._in_use]),  # Conexões em uso
                "idle_connections": len(self.pool._queue._queue),  # Conexões ociosas
                "min_size": self.pool._minsize,
                "max_size": self.pool._maxsize
            }
            
            # Adicionar métricas de transações
            stats["active_transactions"] = len(self._transactions)
            
            return stats
            
        except Exception as e:
            self.logger.warning("Erro ao obter estatísticas do pool: %s", str(e))
            # Retornar valores padrão em caso de erro
            return {
                "total_connections": 0,
                "used_connections": 0,
                "idle_connections": 0,
                "min_size": self.config.pool_min_size,
                "max_size": self.config.pool_max_size,
                "active_transactions": len(self._transactions)
            }

    async def get_table_structure(self, table: str, schema: str = "public") -> List[Dict[str, Any]]:
        """
        Obtém a estrutura de uma tabela.
        
        Args:
            table: Nome da tabela
            schema: Schema da tabela (padrão: 'public')
            
        Returns:
            Lista de colunas com seus tipos e outras propriedades
            
        Raises:
            DatabaseError: Se ocorrer um erro ao obter a estrutura
        """
        query = """
        SELECT 
            c.column_name, 
            c.data_type, 
            c.is_nullable::boolean,
            c.column_default,
            CASE 
                WHEN c.data_type = 'ARRAY' THEN c.udt_name
                WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
                ELSE NULL
            END AS array_type,
            CASE 
                WHEN c.data_type = 'character varying' THEN c.character_maximum_length
                WHEN c.data_type = 'character' THEN c.character_maximum_length
                WHEN c.data_type = 'numeric' THEN c.numeric_precision
                ELSE NULL
            END AS max_length,
            pk.is_primary_key
        FROM 
            information_schema.columns c
        LEFT JOIN (
            SELECT 
                kcu.column_name,
                TRUE as is_primary_key
            FROM 
                information_schema.key_column_usage kcu
            JOIN 
                information_schema.table_constraints tc
            ON 
                kcu.constraint_name = tc.constraint_name
            WHERE 
                tc.constraint_type = 'PRIMARY KEY' AND
                kcu.table_schema = $1 AND
                kcu.table_name = $2
        ) pk ON c.column_name = pk.column_name
        WHERE 
            c.table_schema = $1 AND
            c.table_name = $2
        ORDER BY 
            c.ordinal_position
        """
        try:
            async with self._get_connection() as conn:
                rows = await conn.fetch(query, schema, table)
                
                result = []
                for row in rows:
                    # Converter asyncpg.Record para dicionário
                    column_info = dict(row)
                    
                    # Adicionar informações extras para tipos específicos
                    data_type = column_info["data_type"].lower()
                    
                    # Processar tipos de array
                    if data_type == "array":
                        array_type = column_info.get("array_type")
                        if array_type and array_type.startswith("_"):
                            # Extrair o tipo base do array (remove o underscore inicial)
                            base_type = array_type[1:]
                            column_info["array_element_type"] = base_type
                    
                    # Processar tipos JSON/JSONB
                    elif data_type in ("json", "jsonb"):
                        column_info["is_json"] = True
                    
                    # Processar tipos geométricos
                    elif data_type in ("point", "line", "circle", "polygon"):
                        column_info["is_geometric"] = True
                    
                    result.append(column_info)
                
                return result
                
        except asyncpg.PostgresError as e:
            logger.error(f"Erro ao obter estrutura da tabela {schema}.{table}: {str(e)}")
            raise DatabaseError(f"Falha ao obter estrutura da tabela: {str(e)}")