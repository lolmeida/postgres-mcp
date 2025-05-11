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
    ConnectionError, DatabaseError, NotFoundError, QueryError, RepositoryError, TransactionError
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

    async def get_tables(self, schema: str = "public", include_views: bool = False) -> List[str]:
        """
        Obtém a lista de tabelas em um schema.
        
        Args:
            schema: Nome do schema
            include_views: Se deve incluir views nos resultados
            
        Returns:
            Lista de nomes de tabelas
        """
        try:
            # Constrói a consulta SQL para listagem de tabelas
            table_type_filter = ""
            if not include_views:
                table_type_filter = "AND table_type = 'BASE TABLE'"
                
            query = f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1
                {table_type_filter}
                ORDER BY table_name
            """
            
            # Executa a consulta
            results = await self.pool.fetch(query, schema)
            
            # Converte o resultado para uma lista de strings
            tables = [record["table_name"] for record in results]
            
            return tables
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao obter tabelas: {str(e)}")
            raise RepositoryError(f"Erro ao obter tabelas: {str(e)}")

    async def get_views(self, schema: str = "public", include_materialized: bool = True) -> List[str]:
        """
        Obtém a lista de views em um schema.
        
        Args:
            schema: Nome do schema
            include_materialized: Se deve incluir views materializadas
            
        Returns:
            Lista de nomes de views
        """
        try:
            # Consulta para views normais
            regular_views_query = """
                SELECT table_name AS view_name
                FROM information_schema.views
                WHERE table_schema = $1
            """
            
            # Executa a consulta para views normais
            regular_views = await self.pool.fetch(regular_views_query, schema)
            views = [record["view_name"] for record in regular_views]
            
            # Se deve incluir views materializadas
            if include_materialized:
                # Consulta para views materializadas (não estão em information_schema.views)
                materialized_views_query = """
                    SELECT matviewname AS view_name
                    FROM pg_matviews
                    WHERE schemaname = $1
                """
                
                # Executa a consulta para views materializadas
                materialized_views = await self.pool.fetch(materialized_views_query, schema)
                views.extend([record["view_name"] for record in materialized_views])
                
            # Ordena a lista combinada
            views.sort()
            
            return views
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao obter views: {str(e)}")
            raise RepositoryError(f"Erro ao obter views: {str(e)}")

    async def describe_view(self, view: str, schema: str = "public") -> Dict[str, Any]:
        """
        Obtém a descrição detalhada de uma view.
        
        Args:
            view: Nome da view
            schema: Nome do schema
            
        Returns:
            Dicionário com informações da view
        """
        try:
            # Verificar se é uma view normal ou materializada
            view_type_query = """
                SELECT 
                    CASE
                        WHEN EXISTS (
                            SELECT 1 FROM information_schema.views 
                            WHERE table_schema = $1 AND table_name = $2
                        ) THEN 'VIEW'
                        WHEN EXISTS (
                            SELECT 1 FROM pg_matviews 
                            WHERE schemaname = $1 AND matviewname = $2
                        ) THEN 'MATERIALIZED VIEW'
                        ELSE NULL
                    END AS view_type
            """
            
            view_type_result = await self.pool.fetchval(view_type_query, schema, view)
            
            if not view_type_result:
                raise RepositoryError(f"View {schema}.{view} não encontrada")
            
            is_materialized = view_type_result == 'MATERIALIZED VIEW'
            
            # Consulta para obter colunas
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable = 'YES' AS is_nullable,
                    column_default,
                    pg_catalog.col_description(
                        pg_catalog.format('%s.%s', table_schema, table_name)::regclass::oid, 
                        ordinal_position
                    ) AS column_comment
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema = $1 
                    AND table_name = $2
                ORDER BY 
                    ordinal_position
            """
            
            columns_result = await self.pool.fetch(columns_query, schema, view)
            
            # Consulta para obter definição da view
            definition_query = ""
            if is_materialized:
                definition_query = """
                    SELECT pg_get_viewdef(format('%I.%I', $1, $2)::regclass, true) AS view_definition
                """
            else:
                definition_query = """
                    SELECT view_definition 
                    FROM information_schema.views 
                    WHERE table_schema = $1 AND table_name = $2
                """
            
            definition_result = await self.pool.fetchval(definition_query, schema, view)
            
            # Consulta para obter comentário da view
            comment_query = """
                SELECT pg_catalog.obj_description(
                    pg_catalog.format('%s.%s', $1, $2)::regclass::oid, 'pg_class'
                ) AS view_comment
            """
            
            comment_result = await self.pool.fetchval(comment_query, schema, view)
            
            # Consulta para obter tabelas/views dependentes
            depends_query = """
                SELECT DISTINCT
                    d.refobjid::regclass::text AS dependency
                FROM
                    pg_depend d
                JOIN
                    pg_class c ON c.oid = d.objid
                JOIN 
                    pg_namespace n ON n.oid = c.relnamespace
                WHERE
                    n.nspname = $1
                    AND c.relname = $2
                    AND d.deptype = 'n'
                    AND d.refobjid != d.objid
            """
            
            depends_result = await self.pool.fetch(depends_query, schema, view)
            depends_on = [record["dependency"] for record in depends_result]
            
            # Montar estrutura de colunas
            columns = []
            for col in columns_result:
                columns.append({
                    "name": col["column_name"],
                    "data_type": col["data_type"],
                    "nullable": col["is_nullable"],
                    "default": col["column_default"],
                    "comment": col["column_comment"]
                })
            
            # Montar resultado final
            view_info = {
                "name": view,
                "schema": schema,
                "columns": columns,
                "definition": definition_result,
                "is_materialized": is_materialized,
                "comment": comment_result,
                "depends_on": depends_on
            }
            
            return view_info
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao descrever view: {str(e)}")
            raise RepositoryError(f"Erro ao descrever view: {str(e)}")

    async def read_view(
        self,
        view: str,
        schema: str = "public",
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lê registros de uma view.
        
        Args:
            view: Nome da view
            schema: Nome do schema
            filters: Filtros para a consulta
            columns: Colunas específicas a retornar
            order_by: Coluna para ordenação
            ascending: Direção da ordenação
            limit: Limite de registros a retornar
            offset: Número de registros a pular
            
        Returns:
            Lista de registros
        """
        # Reutiliza a implementação de get_records para views
        return await self.get_records(
            table=view,
            schema=schema,
            filters=filters,
            columns=columns,
            order_by=order_by,
            ascending=ascending,
            limit=limit,
            offset=offset
        )
        
    async def create_view(
        self,
        view: str,
        definition: str,
        schema: str = "public",
        is_materialized: bool = False,
        replace: bool = False
    ) -> Dict[str, Any]:
        """
        Cria uma nova view.
        
        Args:
            view: Nome da view
            definition: Definição SQL da view
            schema: Nome do schema
            is_materialized: Se é uma view materializada
            replace: Se deve substituir caso já exista
            
        Returns:
            Informações da view criada
        """
        try:
            # Construir a consulta SQL para criar a view
            create_replace = "CREATE OR REPLACE" if replace else "CREATE"
            materialized = "MATERIALIZED" if is_materialized else ""
            
            query = f"{create_replace} {materialized} VIEW {schema}.{view} AS {definition}"
            
            # Executar a consulta
            await self.pool.execute(query)
            
            # Retornar informações da view criada
            view_info = await self.describe_view(view, schema)
            return view_info
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao criar view: {str(e)}")
            raise RepositoryError(f"Erro ao criar view: {str(e)}")
    
    async def refresh_materialized_view(
        self,
        view: str,
        schema: str = "public",
        concurrently: bool = False
    ) -> bool:
        """
        Atualiza uma view materializada.
        
        Args:
            view: Nome da view materializada
            schema: Nome do schema
            concurrently: Se deve atualizar concurrently
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            # Verificar se é uma view materializada
            is_materialized_query = """
                SELECT EXISTS (
                    SELECT 1 FROM pg_matviews 
                    WHERE schemaname = $1 AND matviewname = $2
                ) AS is_materialized
            """
            
            is_materialized = await self.pool.fetchval(is_materialized_query, schema, view)
            
            if not is_materialized:
                raise RepositoryError(f"{schema}.{view} não é uma view materializada")
            
            # Construir a consulta SQL para atualizar a view materializada
            concurrently_str = "CONCURRENTLY" if concurrently else ""
            query = f"REFRESH MATERIALIZED VIEW {concurrently_str} {schema}.{view}"
            
            # Executar a consulta
            await self.pool.execute(query)
            
            return True
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao atualizar view materializada: {str(e)}")
            raise RepositoryError(f"Erro ao atualizar view materializada: {str(e)}")
    
    async def drop_view(
        self,
        view: str,
        schema: str = "public",
        if_exists: bool = False,
        cascade: bool = False
    ) -> bool:
        """
        Exclui uma view.
        
        Args:
            view: Nome da view
            schema: Nome do schema
            if_exists: Se deve ignorar caso não exista
            cascade: Se deve excluir objetos dependentes
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            # Verificar se é uma view normal ou materializada
            view_type_query = """
                SELECT 
                    CASE
                        WHEN EXISTS (
                            SELECT 1 FROM information_schema.views 
                            WHERE table_schema = $1 AND table_name = $2
                        ) THEN 'VIEW'
                        WHEN EXISTS (
                            SELECT 1 FROM pg_matviews 
                            WHERE schemaname = $1 AND matviewname = $2
                        ) THEN 'MATERIALIZED VIEW'
                        ELSE NULL
                    END AS view_type
            """
            
            view_type = await self.pool.fetchval(view_type_query, schema, view)
            
            if not view_type and not if_exists:
                raise RepositoryError(f"View {schema}.{view} não encontrada")
            
            # Construir a consulta SQL para excluir a view
            if_exists_str = "IF EXISTS" if if_exists else ""
            cascade_str = "CASCADE" if cascade else ""
            
            query = f"DROP {view_type} {if_exists_str} {schema}.{view} {cascade_str}"
            
            # Executar a consulta
            await self.pool.execute(query)
            
            return True
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao excluir view: {str(e)}")
            raise RepositoryError(f"Erro ao excluir view: {str(e)}")

    # Métodos para funções e procedimentos armazenados

    async def get_functions(
        self, 
        schema: str = "public", 
        include_procedures: bool = True,
        include_aggregates: bool = True
    ) -> List[str]:
        """
        Obtém a lista de funções em um schema.
        
        Args:
            schema: Nome do schema
            include_procedures: Se deve incluir procedimentos
            include_aggregates: Se deve incluir funções de agregação
            
        Returns:
            Lista de nomes de funções
        """
        try:
            # Construir a parte da consulta para filtrar por tipo
            proc_filter = ""
            if not include_procedures:
                proc_filter = "AND p.prokind = 'f'"  # Apenas funções
            elif not include_aggregates:
                proc_filter = "AND p.prokind != 'a'"  # Exclui funções de agregação
            
            # Consulta para obter funções
            query = f"""
                SELECT n.nspname as schema_name, p.proname as function_name
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = $1
                {proc_filter}
                ORDER BY p.proname
            """
            
            # Executar a consulta
            result = await self.pool.fetch(query, schema)
            
            # Extrair nomes de funções
            functions = [row["function_name"] for row in result]
            
            return functions
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao obter funções: {str(e)}")
            raise RepositoryError(f"Erro ao obter funções: {str(e)}")

    async def describe_function(self, function: str, schema: str = "public") -> Dict[str, Any]:
        """
        Obtém a descrição detalhada de uma função.
        
        Args:
            function: Nome da função
            schema: Nome do schema
            
        Returns:
            Dicionário com informações da função
        """
        try:
            # Consulta para obter informações da função
            query = """
                SELECT 
                    p.proname as name,
                    n.nspname as schema,
                    pg_get_function_result(p.oid) as return_type,
                    pg_get_function_arguments(p.oid) as arguments,
                    pg_get_functiondef(p.oid) as definition,
                    l.lanname as language,
                    p.prokind = 'p' as is_procedure,
                    p.prokind = 'a' as is_aggregate,
                    p.proiswindow as is_window,
                    p.prosecdef as is_security_definer,
                    CASE
                        WHEN p.provolatile = 'i' THEN 'immutable'
                        WHEN p.provolatile = 's' THEN 'stable'
                        ELSE 'volatile'
                    END as volatility,
                    obj_description(p.oid, 'pg_proc') as comment,
                    p.pronargs as num_args,
                    p.proargtypes as arg_types,
                    p.proallargtypes as all_arg_types,
                    p.proargmodes as arg_modes,
                    p.proargnames as arg_names,
                    p.proargdefaults as arg_defaults
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                JOIN pg_language l ON p.prolang = l.oid
                WHERE p.proname = $1 AND n.nspname = $2
                LIMIT 1
            """
            
            # Executar a consulta
            row = await self.pool.fetchrow(query, function, schema)
            
            if not row:
                raise RepositoryError(f"Função {schema}.{function} não encontrada")
            
            # Processar os argumentos
            arg_types = []
            arg_names = []
            arg_defaults = []
            
            # Função para processar argumentos baseado nos metadados
            if row["all_arg_types"] is not None:
                # Processar informações completas de argumentos
                all_arg_types = row["all_arg_types"]
                arg_modes = row["arg_modes"]
                arg_names_raw = row["arg_names"]
                
                # Mapear tipos de OIDs para tipos de dados
                for i, type_oid in enumerate(all_arg_types):
                    arg_type_query = "SELECT format_type($1, NULL) as type_name"
                    type_name = await self.pool.fetchval(arg_type_query, type_oid)
                    arg_types.append(type_name)
                    
                    # Coletar nomes se disponíveis
                    if arg_names_raw and i < len(arg_names_raw):
                        arg_names.append(arg_names_raw[i])
                    else:
                        arg_names.append(f"arg{i+1}")
            
            # Consulta adicional para obter valores padrão dos argumentos, que não são facilmente acessíveis
            if row["num_args"] > 0:
                defaults_query = """
                    SELECT unnest(string_to_array(
                        pg_get_function_arguments(p.oid), ', '
                    )) as arg_with_default
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE p.proname = $1 AND n.nspname = $2
                """
                
                default_rows = await self.pool.fetch(defaults_query, function, schema)
                for arg_row in default_rows:
                    arg_with_default = arg_row["arg_with_default"]
                    if " DEFAULT " in arg_with_default:
                        default_value = arg_with_default.split(" DEFAULT ")[1]
                        arg_defaults.append(default_value)
                    else:
                        arg_defaults.append(None)
            
            # Construir resultado
            function_info = {
                "name": row["name"],
                "schema": row["schema"],
                "return_type": row["return_type"],
                "argument_types": arg_types,
                "argument_names": arg_names,
                "argument_defaults": arg_defaults,
                "definition": row["definition"],
                "language": row["language"],
                "is_procedure": row["is_procedure"],
                "is_aggregate": row["is_aggregate"],
                "is_window": row["is_window"],
                "is_security_definer": row["is_security_definer"],
                "volatility": row["volatility"],
                "comment": row["comment"]
            }
            
            return function_info
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao descrever função: {str(e)}")
            raise RepositoryError(f"Erro ao descrever função: {str(e)}")

    async def execute_function(
        self, 
        function: str, 
        schema: str = "public", 
        args: Optional[List[Any]] = None,
        named_args: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Executa uma função armazenada.
        
        Args:
            function: Nome da função
            schema: Nome do schema
            args: Argumentos posicionais para a função
            named_args: Argumentos nomeados para a função
            
        Returns:
            Resultado da função
        """
        try:
            # Primeiro, descrevemos a função para verificar se ela existe e suas características
            function_info = await self.describe_function(function, schema)
            
            # Construir a parte de argumentos da consulta
            arg_values = []
            
            if named_args:
                # Para argumentos nomeados, construímos uma string no formato 'nome => valor'
                arg_parts = []
                for name, value in named_args.items():
                    arg_parts.append(f"{name} => ${len(arg_values) + 1}")
                    arg_values.append(value)
                
                args_string = ", ".join(arg_parts)
            elif args:
                # Para argumentos posicionais, usamos placeholders $1, $2, etc.
                arg_parts = [f"${i + 1}" for i in range(len(args))]
                args_string = ", ".join(arg_parts)
                arg_values = args
            else:
                args_string = ""
            
            # Construir a consulta SQL baseada no tipo (função ou procedimento)
            if function_info["is_procedure"]:
                # Para procedimentos (PostgreSQL 11+)
                query = f"CALL {schema}.{function}({args_string})"
                await self.pool.execute(query, *arg_values)
                # Procedimentos não retornam valores
                return None
            else:
                # Para funções
                query = f"SELECT {schema}.{function}({args_string})"
                
                # Executar a consulta
                result = await self.pool.fetchval(query, *arg_values)
                return result
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao executar função: {str(e)}")
            raise RepositoryError(f"Erro ao executar função: {str(e)}")

    async def create_function(
        self,
        function: str,
        definition: str,
        return_type: str,
        schema: str = "public",
        argument_definitions: Optional[List[Dict[str, Any]]] = None,
        language: str = "plpgsql",
        is_procedure: bool = False,
        replace: bool = False,
        security_definer: bool = False,
        volatility: str = "volatile"
    ) -> Dict[str, Any]:
        """
        Cria uma nova função ou procedimento.
        
        Args:
            function: Nome da função
            definition: Definição SQL da função
            return_type: Tipo de retorno da função
            schema: Nome do schema
            argument_definitions: Definições dos argumentos
            language: Linguagem da função
            is_procedure: Se é um procedimento
            replace: Se deve substituir caso já exista
            security_definer: Se é executada com permissões do criador
            volatility: Volatilidade da função
            
        Returns:
            Informações da função criada
        """
        try:
            # Construir a parte de argumentos
            args_string = ""
            if argument_definitions:
                arg_parts = []
                for arg in argument_definitions:
                    # Cada argumento deve ter pelo menos nome e tipo
                    arg_name = arg.get("name", "").strip()
                    arg_type = arg.get("type", "").strip()
                    
                    if not arg_name or not arg_type:
                        raise ValueError("Todos os argumentos devem ter nome e tipo")
                    
                    arg_str = f"{arg_name} {arg_type}"
                    
                    # Adicionar valor padrão, se fornecido
                    if "default" in arg and arg["default"] is not None:
                        arg_str += f" DEFAULT {arg['default']}"
                    
                    # Adicionar modo, se fornecido (IN, OUT, INOUT)
                    if "mode" in arg and arg["mode"] is not None:
                        mode = arg["mode"].upper()
                        if mode not in ["IN", "OUT", "INOUT", "VARIADIC"]:
                            raise ValueError(f"Modo de argumento inválido: {mode}")
                        
                        # Modos posicionais antes do nome
                        arg_str = f"{mode} {arg_str}"
                    
                    arg_parts.append(arg_str)
                
                args_string = ", ".join(arg_parts)
            
            # Construir a consulta SQL para criar a função
            create_replace = "CREATE OR REPLACE" if replace else "CREATE"
            func_or_proc = "PROCEDURE" if is_procedure else "FUNCTION"
            
            # Para funções normais, precisamos do tipo de retorno
            returns_clause = "" if is_procedure else f"RETURNS {return_type}"
            
            # Definir características da função
            security_clause = "SECURITY DEFINER" if security_definer else "SECURITY INVOKER"
            volatility_clause = volatility.upper()
            
            # Construir a consulta SQL completa
            query = f"""
                {create_replace} {func_or_proc} {schema}.{function}({args_string})
                {returns_clause}
                LANGUAGE {language}
                {security_clause}
                {volatility_clause}
                AS $function$
                {definition}
                $function$;
            """
            
            # Executar a consulta
            await self.pool.execute(query)
            
            # Retornar informações da função criada
            function_info = await self.describe_function(function, schema)
            return function_info
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao criar função: {str(e)}")
            raise RepositoryError(f"Erro ao criar função: {str(e)}")

    async def drop_function(
        self,
        function: str,
        schema: str = "public",
        if_exists: bool = False,
        cascade: bool = False,
        arg_types: Optional[List[str]] = None
    ) -> bool:
        """
        Exclui uma função.
        
        Args:
            function: Nome da função
            schema: Nome do schema
            if_exists: Se deve ignorar caso não exista
            cascade: Se deve excluir objetos dependentes
            arg_types: Tipos dos argumentos para identificar a função específica
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            # Verificar se a função existe
            if not if_exists:
                exists_query = """
                    SELECT EXISTS (
                        SELECT 1 FROM pg_proc p
                        JOIN pg_namespace n ON p.pronamespace = n.oid
                        WHERE p.proname = $1 AND n.nspname = $2
                    ) AS exists
                """
                
                exists = await self.pool.fetchval(exists_query, function, schema)
                
                if not exists:
                    raise RepositoryError(f"Função {schema}.{function} não encontrada")
            
            # Construir a parte de argumentos, se fornecidos
            args_part = ""
            if arg_types:
                args_part = f"({', '.join(arg_types)})"
            
            # Construir a consulta SQL para excluir a função
            if_exists_str = "IF EXISTS" if if_exists else ""
            cascade_str = "CASCADE" if cascade else ""
            
            query = f"DROP FUNCTION {if_exists_str} {schema}.{function}{args_part} {cascade_str}"
            
            # Executar a consulta
            await self.pool.execute(query)
            
            return True
            
        except asyncpg.PostgresError as e:
            # Loga o erro e relança como exceção específica da aplicação
            self.logger.error(f"Erro ao excluir função: {str(e)}")
            raise RepositoryError(f"Erro ao excluir função: {str(e)}")