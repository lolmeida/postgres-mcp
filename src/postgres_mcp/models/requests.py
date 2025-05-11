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
        isolation_level (str, opcional): Nível de isolamento da transação (default: "read_committed")
    """
    
    isolation_level: str = Field("read_committed", description="Nível de isolamento da transação")
    
    @validator("isolation_level")
    def validate_isolation_level(cls, v: str) -> str:
        """Valida o nível de isolamento da transação."""
        valid_levels = [
            "read_uncommitted",
            "read_committed",
            "repeatable_read",
            "serializable"
        ]
        if v not in valid_levels:
            raise ValueError(f"isolation_level deve ser um dos: {', '.join(valid_levels)}")
        return v


class CommitTransactionRequest(BaseModel):
    """
    Modelo para requisição de confirmação de transação.
    
    Atributos:
        transaction_id (str): ID da transação a ser confirmada
    """
    
    transaction_id: str = Field(..., description="ID da transação a ser confirmada")


class RollbackTransactionRequest(BaseModel):
    """
    Modelo para requisição de reversão de transação.
    
    Atributos:
        transaction_id (str): ID da transação a ser revertida
        savepoint (str, opcional): Nome do savepoint para reversão parcial
    """
    
    transaction_id: str = Field(..., description="ID da transação a ser revertida")
    savepoint: Optional[str] = Field(None, description="Nome do savepoint para reversão parcial") 