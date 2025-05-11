"""
Modelos para requisições específicas das ferramentas MCP
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from postgres_mcp.models.base import TableReference
from postgres_mcp.models.filters import FiltersType


class ListSchemasRequest(BaseModel):
    """Modelo para requisição de listagem de schemas."""
    pass


class ListTablesRequest(BaseModel):
    """
    Modelo para requisição de listagem de tabelas.
    
    Atributos:
        schema (str, opcional): Nome do schema (default: "public")
        include_views (bool, opcional): Incluir views nos resultados (default: False)
    """
    
    schema: str = Field("public", description="Nome do schema")
    include_views: bool = Field(False, description="Incluir views nos resultados")


class DescribeTableRequest(TableReference):
    """
    Modelo para requisição de descrição de tabela.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
    """
    pass


class ReadTableRequest(TableReference):
    """
    Modelo para requisição de leitura de tabela.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
        filters (dict, opcional): Filtros para a consulta
        columns (list, opcional): Colunas específicas a retornar
        order_by (str, opcional): Coluna para ordenação
        ascending (bool, opcional): Direção da ordenação (default: True)
        limit (int, opcional): Limite de registros a retornar
        offset (int, opcional): Número de registros a pular
    """
    
    filters: Optional[FiltersType] = Field(None, description="Filtros para a consulta")
    columns: Optional[List[str]] = Field(None, description="Colunas específicas a retornar")
    order_by: Optional[str] = Field(None, description="Coluna para ordenação")
    ascending: bool = Field(True, description="Direção da ordenação (True=ASC, False=DESC)")
    limit: Optional[int] = Field(None, description="Limite de registros a retornar")
    offset: Optional[int] = Field(None, description="Número de registros a pular")
    
    @validator("limit")
    def validate_limit(cls, v: Optional[int]) -> Optional[int]:
        """Valida o limite de registros."""
        if v is not None and v <= 0:
            raise ValueError("limit deve ser maior que 0")
        return v
    
    @validator("offset")
    def validate_offset(cls, v: Optional[int]) -> Optional[int]:
        """Valida o offset de registros."""
        if v is not None and v < 0:
            raise ValueError("offset deve ser maior ou igual a 0")
        return v


class CreateRecordRequest(TableReference):
    """
    Modelo para requisição de criação de registro.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
        data (dict): Dados do registro a ser criado
        returning (list, opcional): Colunas a serem retornadas após a criação
    """
    
    data: Dict[str, Any] = Field(..., description="Dados do registro a ser criado")
    returning: Optional[List[str]] = Field(None, description="Colunas a serem retornadas após a criação")


class CreateBatchRequest(TableReference):
    """
    Modelo para requisição de criação em lote.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
        data (list): Lista de registros a serem criados
        returning (list, opcional): Colunas a serem retornadas após a criação
    """
    
    data: List[Dict[str, Any]] = Field(..., description="Lista de registros a serem criados")
    returning: Optional[List[str]] = Field(None, description="Colunas a serem retornadas após a criação")
    
    @validator("data")
    def validate_data(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida a lista de dados."""
        if not v:
            raise ValueError("data não pode ser uma lista vazia")
        return v


class UpdateRecordsRequest(TableReference):
    """
    Modelo para requisição de atualização de registros.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
        filters (dict): Filtros para selecionar registros a serem atualizados
        data (dict): Dados a serem atualizados
        returning (list, opcional): Colunas a serem retornadas após a atualização
    """
    
    filters: FiltersType = Field(..., description="Filtros para selecionar registros a serem atualizados")
    data: Dict[str, Any] = Field(..., description="Dados a serem atualizados")
    returning: Optional[List[str]] = Field(None, description="Colunas a serem retornadas após a atualização")


class DeleteRecordsRequest(TableReference):
    """
    Modelo para requisição de exclusão de registros.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
        filters (dict): Filtros para selecionar registros a serem excluídos
        returning (list, opcional): Colunas a serem retornadas dos registros excluídos
    """
    
    filters: FiltersType = Field(..., description="Filtros para selecionar registros a serem excluídos")
    returning: Optional[List[str]] = Field(None, description="Colunas a serem retornadas dos registros excluídos")


class ExecuteQueryRequest(BaseModel):
    """
    Modelo para requisição de execução de consulta SQL personalizada.
    
    Atributos:
        query (str): Consulta SQL a ser executada
        params (dict, opcional): Parâmetros para a consulta
        transaction_id (str, opcional): ID da transação
    """
    
    query: str = Field(..., description="Consulta SQL a ser executada")
    params: Optional[Dict[str, Any]] = Field(None, description="Parâmetros para a consulta")
    transaction_id: Optional[str] = Field(None, description="ID da transação")
    
    @validator("query")
    def validate_query(cls, v: str) -> str:
        """Valida a consulta SQL."""
        if not v:
            raise ValueError("query não pode ser vazia")
        return v


class BeginTransactionRequest(BaseModel):
    """
    Modelo para requisição de início de transação.
    
    Atributos:
        isolation_level (str, opcional): Nível de isolamento (default: "read_committed")
    """
    
    isolation_level: str = Field("read_committed", description="Nível de isolamento")


class CommitTransactionRequest(BaseModel):
    """
    Modelo para requisição de confirmação de transação.
    
    Atributos:
        transaction_id (str): ID da transação
    """
    
    transaction_id: str = Field(..., description="ID da transação")


class RollbackTransactionRequest(BaseModel):
    """
    Modelo para requisição de rollback de transação.
    
    Atributos:
        transaction_id (str): ID da transação
        savepoint (str, opcional): Nome do savepoint para rollback parcial
    """
    
    transaction_id: str = Field(..., description="ID da transação")
    savepoint: Optional[str] = Field(None, description="Nome do savepoint para rollback parcial")


class GetCacheStatsRequest(BaseModel):
    """Modelo para requisição de estatísticas de cache."""
    pass


class ClearCacheRequest(BaseModel):
    """
    Modelo para requisição de limpeza de cache.
    
    Atributos:
        scope (str, opcional): Escopo da limpeza (all, table, schema) (default: "all")
        table (str, opcional): Nome da tabela (obrigatório quando scope="table")
        schema (str, opcional): Nome do schema (obrigatório quando scope=table ou schema)
    """
    
    scope: str = Field("all", description="Escopo da limpeza (all, table, schema)")
    table: Optional[str] = Field(None, description="Nome da tabela")
    schema: Optional[str] = Field(None, description="Nome do schema")
    
    @validator("scope")
    def validate_scope(cls, v: str) -> str:
        """Valida o escopo da limpeza."""
        if v not in ["all", "table", "schema"]:
            raise ValueError("scope deve ser 'all', 'table' ou 'schema'")
        return v
    
    @validator("table")
    def validate_table(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Valida se o nome da tabela está presente quando necessário."""
        if values.get("scope") == "table" and not v:
            raise ValueError("table é obrigatório quando scope='table'")
        return v
    
    @validator("schema")
    def validate_schema(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Valida se o nome do schema está presente quando necessário."""
        if values.get("scope") in ["table", "schema"] and not v:
            raise ValueError("schema é obrigatório quando scope='table' ou scope='schema'")
        return v


class GetMetricsRequest(BaseModel):
    """
    Modelo para requisição de métricas de desempenho.
    
    Atributos:
        metric_type (str, opcional): Tipo específico de métrica
        operation (str, opcional): Nome da operação para filtrar
        window_seconds (int, opcional): Janela de tempo em segundos
    """
    
    metric_type: Optional[str] = Field(None, description="Tipo específico de métrica")
    operation: Optional[str] = Field(None, description="Nome da operação para filtrar")
    window_seconds: int = Field(60, description="Janela de tempo em segundos")


class ResetMetricsRequest(BaseModel):
    """Modelo para requisição de reset de métricas."""
    pass


# Novos modelos para suporte a views

class ViewReference(BaseModel):
    """
    Referência a uma view PostgreSQL.
    
    Atributos:
        view (str): Nome da view
        schema (str, opcional): Nome do schema (default: "public")
    """
    
    view: str = Field(..., description="Nome da view")
    schema: str = Field("public", description="Nome do schema")
    
    @validator("view")
    def validate_view(cls, v: str) -> str:
        """Valida o nome da view."""
        if not v:
            raise ValueError("nome da view não pode ser vazio")
        return v
    
    @validator("schema")
    def validate_schema(cls, v: str) -> str:
        """Valida o nome do schema."""
        if not v:
            raise ValueError("nome do schema não pode ser vazio")
        return v


class ListViewsRequest(BaseModel):
    """
    Modelo para requisição de listagem de views.
    
    Atributos:
        schema (str, opcional): Nome do schema (default: "public")
        include_materialized (bool, opcional): Incluir views materializadas (default: True)
    """
    
    schema: str = Field("public", description="Nome do schema")
    include_materialized: bool = Field(True, description="Incluir views materializadas")


class DescribeViewRequest(ViewReference):
    """
    Modelo para requisição de descrição de view.
    
    Atributos:
        view (str): Nome da view
        schema (str, opcional): Nome do schema (default: "public")
    """
    pass


class ReadViewRequest(ViewReference):
    """
    Modelo para requisição de leitura de view.
    
    Atributos:
        view (str): Nome da view
        schema (str, opcional): Nome do schema (default: "public")
        filters (dict, opcional): Filtros para a consulta
        columns (list, opcional): Colunas específicas a retornar
        order_by (str, opcional): Coluna para ordenação
        ascending (bool, opcional): Direção da ordenação (default: True)
        limit (int, opcional): Limite de registros a retornar
        offset (int, opcional): Número de registros a pular
    """
    
    filters: Optional[FiltersType] = Field(None, description="Filtros para a consulta")
    columns: Optional[List[str]] = Field(None, description="Colunas específicas a retornar")
    order_by: Optional[str] = Field(None, description="Coluna para ordenação")
    ascending: bool = Field(True, description="Direção da ordenação (True=ASC, False=DESC)")
    limit: Optional[int] = Field(None, description="Limite de registros a retornar")
    offset: Optional[int] = Field(None, description="Número de registros a pular")
    
    @validator("limit")
    def validate_limit(cls, v: Optional[int]) -> Optional[int]:
        """Valida o limite de registros."""
        if v is not None and v <= 0:
            raise ValueError("limit deve ser maior que 0")
        return v
    
    @validator("offset")
    def validate_offset(cls, v: Optional[int]) -> Optional[int]:
        """Valida o offset de registros."""
        if v is not None and v < 0:
            raise ValueError("offset deve ser maior ou igual a 0")
        return v


class CreateViewRequest(ViewReference):
    """
    Modelo para requisição de criação de view.
    
    Atributos:
        view (str): Nome da view
        schema (str, opcional): Nome do schema (default: "public")
        definition (str): Definição SQL da view
        is_materialized (bool, opcional): Se é uma view materializada (default: False)
        replace (bool, opcional): Se deve substituir caso já exista (default: False)
    """
    
    definition: str = Field(..., description="Definição SQL da view")
    is_materialized: bool = Field(False, description="Se é uma view materializada")
    replace: bool = Field(False, description="Se deve substituir caso já exista")
    
    @validator("definition")
    def validate_definition(cls, v: str) -> str:
        """Valida a definição SQL."""
        if not v:
            raise ValueError("definition não pode ser vazia")
        return v


class RefreshMaterializedViewRequest(ViewReference):
    """
    Modelo para requisição de atualização de view materializada.
    
    Atributos:
        view (str): Nome da view materializada
        schema (str, opcional): Nome do schema (default: "public")
        concurrently (bool, opcional): Se deve atualizar concurrently (default: False)
    """
    
    concurrently: bool = Field(False, description="Se deve atualizar concurrently")


class DropViewRequest(ViewReference):
    """
    Modelo para requisição de exclusão de view.
    
    Atributos:
        view (str): Nome da view
        schema (str, opcional): Nome do schema (default: "public")
        if_exists (bool, opcional): Se deve ignorar caso não exista (default: False)
        cascade (bool, opcional): Se deve excluir objetos dependentes (default: False)
    """
    
    if_exists: bool = Field(False, description="Se deve ignorar caso não exista")
    cascade: bool = Field(False, description="Se deve excluir objetos dependentes")


# Modelos para suporte a funções e procedimentos armazenados

class FunctionReference(BaseModel):
    """
    Referência a uma função PostgreSQL.
    
    Atributos:
        function (str): Nome da função
        schema (str, opcional): Nome do schema (default: "public")
    """
    
    function: str = Field(..., description="Nome da função")
    schema: str = Field("public", description="Nome do schema")
    
    @validator("function")
    def validate_function(cls, v: str) -> str:
        """Valida o nome da função."""
        if not v:
            raise ValueError("nome da função não pode ser vazio")
        return v
    
    @validator("schema")
    def validate_schema(cls, v: str) -> str:
        """Valida o nome do schema."""
        if not v:
            raise ValueError("nome do schema não pode ser vazio")
        return v


class ListFunctionsRequest(BaseModel):
    """
    Modelo para requisição de listagem de funções.
    
    Atributos:
        schema (str, opcional): Nome do schema (default: "public")
        include_procedures (bool, opcional): Incluir procedimentos nos resultados (default: True)
        include_aggregates (bool, opcional): Incluir funções de agregação (default: True)
    """
    
    schema: str = Field("public", description="Nome do schema")
    include_procedures: bool = Field(True, description="Incluir procedimentos nos resultados")
    include_aggregates: bool = Field(True, description="Incluir funções de agregação")


class DescribeFunctionRequest(FunctionReference):
    """
    Modelo para requisição de descrição de função.
    
    Atributos:
        function (str): Nome da função
        schema (str, opcional): Nome do schema (default: "public")
    """
    pass


class ExecuteFunctionRequest(FunctionReference):
    """
    Modelo para requisição de execução de função.
    
    Atributos:
        function (str): Nome da função
        schema (str, opcional): Nome do schema (default: "public")
        args (list, opcional): Argumentos posicionais para a função
        named_args (dict, opcional): Argumentos nomeados para a função
    """
    
    args: Optional[List[Any]] = Field(None, description="Argumentos posicionais para a função")
    named_args: Optional[Dict[str, Any]] = Field(None, description="Argumentos nomeados para a função")


class CreateFunctionRequest(FunctionReference):
    """
    Modelo para requisição de criação de função.
    
    Atributos:
        function (str): Nome da função
        schema (str, opcional): Nome do schema (default: "public")
        definition (str): Definição SQL da função
        return_type (str): Tipo de retorno da função
        argument_definitions (list, opcional): Definições dos argumentos
        language (str, opcional): Linguagem da função (default: "plpgsql")
        is_procedure (bool, opcional): Se é um procedimento (default: False)
        replace (bool, opcional): Se deve substituir caso já exista (default: False)
        security_definer (bool, opcional): Se é executada com permissões do criador (default: False)
        volatility (str, opcional): Volatilidade da função (default: "volatile")
    """
    
    definition: str = Field(..., description="Definição SQL da função")
    return_type: str = Field(..., description="Tipo de retorno da função")
    argument_definitions: Optional[List[Dict[str, Any]]] = Field(None, description="Definições dos argumentos")
    language: str = Field("plpgsql", description="Linguagem da função")
    is_procedure: bool = Field(False, description="Se é um procedimento")
    replace: bool = Field(False, description="Se deve substituir caso já exista")
    security_definer: bool = Field(False, description="Se é executada com permissões do criador")
    volatility: str = Field("volatile", description="Volatilidade da função (volatile, stable, immutable)")
    
    @validator("definition")
    def validate_definition(cls, v: str) -> str:
        """Valida a definição SQL."""
        if not v:
            raise ValueError("definition não pode ser vazia")
        return v
    
    @validator("volatility")
    def validate_volatility(cls, v: str) -> str:
        """Valida a volatilidade da função."""
        if v not in ["volatile", "stable", "immutable"]:
            raise ValueError("volatility deve ser 'volatile', 'stable' ou 'immutable'")
        return v


class DropFunctionRequest(FunctionReference):
    """
    Modelo para requisição de exclusão de função.
    
    Atributos:
        function (str): Nome da função
        schema (str, opcional): Nome do schema (default: "public")
        if_exists (bool, opcional): Se deve ignorar caso não exista (default: False)
        cascade (bool, opcional): Se deve excluir objetos dependentes (default: False)
        arg_types (list, opcional): Tipos dos argumentos para identificar a função específica
    """
    
    if_exists: bool = Field(False, description="Se deve ignorar caso não exista")
    cascade: bool = Field(False, description="Se deve excluir objetos dependentes")
    arg_types: Optional[List[str]] = Field(None, description="Tipos dos argumentos para identificar a função específica") 