"""
Modelos mockados para testes de handlers.
"""

from typing import Dict, Any, List, Optional


# Modelos base
class FunctionInfo:
    """Informações sobre uma função do PostgreSQL."""
    def __init__(
        self,
        name: str,
        schema: str,
        return_type: Optional[str] = None,
        definition: str = "",
        language: str = "plpgsql",
        argument_types: Optional[List[str]] = None,
        argument_names: Optional[List[str]] = None,
        argument_defaults: Optional[List[Any]] = None,
        is_procedure: bool = False,
        is_aggregate: bool = False,
        is_window: bool = False,
        is_security_definer: bool = False,
        volatility: str = "volatile",
        comment: Optional[str] = None
    ):
        self.name = name
        self.schema = schema
        self.return_type = return_type
        self.definition = definition
        self.language = language
        self.argument_types = argument_types or []
        self.argument_names = argument_names or []
        self.argument_defaults = argument_defaults or []
        self.is_procedure = is_procedure
        self.is_aggregate = is_aggregate
        self.is_window = is_window
        self.is_security_definer = is_security_definer
        self.volatility = volatility
        self.comment = comment


class ColumnInfo:
    """Informações sobre uma coluna de tabela ou view."""
    def __init__(
        self,
        name: str,
        data_type: str,
        nullable: bool = True,
        is_primary: bool = False,
        default: Optional[str] = None,
        comment: Optional[str] = None
    ):
        self.name = name
        self.data_type = data_type
        self.nullable = nullable
        self.is_primary = is_primary
        self.default = default
        self.comment = comment


class ViewInfo:
    """Informações sobre uma view."""
    def __init__(
        self,
        name: str,
        schema: str,
        columns: List[ColumnInfo],
        definition: str,
        is_materialized: bool = False,
        comment: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ):
        self.name = name
        self.schema = schema
        self.columns = columns
        self.definition = definition
        self.is_materialized = is_materialized
        self.comment = comment
        self.depends_on = depends_on or []


# Modelos para requisições de cache
class GetCacheStatsRequest:
    """Request para obter estatísticas do cache."""
    pass


class ClearCacheRequest:
    """Request para limpar o cache."""
    def __init__(self, namespace: Optional[str] = None):
        self.namespace = namespace


# Modelos para requisições de transação
class BeginTransactionRequest:
    """Request para iniciar uma transação."""
    pass


class CommitTransactionRequest:
    """Request para fazer commit de uma transação."""
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id


class RollbackTransactionRequest:
    """Request para fazer rollback de uma transação."""
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id


class GetTransactionStatusRequest:
    """Request para obter o status de uma transação."""
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id


# Modelos para referências de objetos
class FunctionReference:
    """Referência a uma função do PostgreSQL."""
    def __init__(self, name: str, schema: str = "public", arg_types: Optional[List[str]] = None):
        self.name = name
        self.schema = schema
        self.arg_types = arg_types


class ViewReference:
    """Referência a uma view do PostgreSQL."""
    def __init__(self, name: str, schema: str = "public"):
        self.name = name
        self.schema = schema


# Modelos para requisições de funções
class ListFunctionsRequest:
    """Request para listar funções."""
    def __init__(
        self, 
        schema: str = "public", 
        include_procedures: bool = True,
        include_aggregates: bool = True
    ):
        self.schema = schema
        self.include_procedures = include_procedures
        self.include_aggregates = include_aggregates


class DescribeFunctionRequest:
    """Request para descrever uma função."""
    def __init__(self, function: FunctionReference):
        self.function = function


class ExecuteFunctionRequest:
    """Request para executar uma função."""
    def __init__(
        self, 
        function: FunctionReference, 
        args: Optional[List[Any]] = None,
        named_args: Optional[Dict[str, Any]] = None
    ):
        self.function = function
        self.args = args
        self.named_args = named_args


class CreateFunctionRequest:
    """Request para criar uma função."""
    def __init__(
        self,
        function: FunctionReference,
        definition: str,
        return_type: Optional[str] = None,
        argument_definitions: Optional[List[str]] = None,
        language: str = "plpgsql",
        is_procedure: bool = False,
        replace: bool = False,
        security_definer: bool = False,
        volatility: Optional[str] = None
    ):
        self.function = function
        self.definition = definition
        self.return_type = return_type
        self.argument_definitions = argument_definitions
        self.language = language
        self.is_procedure = is_procedure
        self.replace = replace
        self.security_definer = security_definer
        self.volatility = volatility


class DropFunctionRequest:
    """Request para excluir uma função."""
    def __init__(
        self,
        function: FunctionReference,
        if_exists: bool = False,
        cascade: bool = False
    ):
        self.function = function
        self.if_exists = if_exists
        self.cascade = cascade


# Modelos para requisições de views
class ListViewsRequest:
    """Request para listar views."""
    def __init__(
        self, 
        schema: str = "public", 
        include_materialized: bool = True
    ):
        self.schema = schema
        self.include_materialized = include_materialized


class DescribeViewRequest:
    """Request para descrever uma view."""
    def __init__(self, view: ViewReference):
        self.view = view


class CreateViewRequest:
    """Request para criar uma view."""
    def __init__(
        self,
        view: ViewReference,
        definition: str,
        replace: bool = False,
        is_materialized: bool = False,
        columns: Optional[List[Dict[str, Any]]] = None,
        with_data: bool = True,
        comment: Optional[str] = None
    ):
        self.view = view
        self.definition = definition
        self.replace = replace
        self.is_materialized = is_materialized
        self.columns = columns
        self.with_data = with_data
        self.comment = comment


class RefreshViewRequest:
    """Request para atualizar uma view materializada."""
    def __init__(
        self,
        view: ViewReference,
        concurrently: bool = False
    ):
        self.view = view
        self.concurrently = concurrently


class DropViewRequest:
    """Request para excluir uma view."""
    def __init__(
        self,
        view: ViewReference,
        if_exists: bool = False,
        cascade: bool = False
    ):
        self.view = view
        self.if_exists = if_exists
        self.cascade = cascade 