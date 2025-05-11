"""
Modelos base para requisições e respostas MCP
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class MCPRequest(BaseModel):
    """
    Modelo base para requisições MCP.
    
    Atributos:
        tool (str): Nome da ferramenta a ser executada
        parameters (dict): Parâmetros para a ferramenta
    """
    
    tool: str = Field(..., description="Nome da ferramenta a ser executada")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros para a ferramenta")
    
    @validator("tool")
    def validate_tool(cls, v: str) -> str:
        """Valida o nome da ferramenta."""
        if not v or not isinstance(v, str):
            raise ValueError("tool deve ser uma string não vazia")
        return v


class MCPResponse(BaseModel):
    """
    Modelo base para respostas MCP.
    
    Atributos:
        success (bool): Indica se a operação foi bem-sucedida
        data (Any, opcional): Dados retornados pela operação
        count (int, opcional): Contagem de itens retornados
        error (dict, opcional): Informações de erro, se houver
    """
    
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    data: Optional[Any] = Field(None, description="Dados retornados pela operação")
    count: Optional[int] = Field(None, description="Contagem de itens retornados")
    error: Optional[Dict[str, Any]] = Field(None, description="Informações de erro, se houver")
    
    @classmethod
    def success_response(cls, data: Any = None, count: Optional[int] = None) -> "MCPResponse":
        """
        Cria uma resposta de sucesso.
        
        Args:
            data: Dados a serem retornados
            count: Contagem de itens (opcional)
            
        Returns:
            Resposta MCP de sucesso
        """
        if isinstance(data, list) and count is None:
            count = len(data)
        
        return cls(success=True, data=data, count=count)
    
    @classmethod
    def error_response(
        cls, message: str, error_type: str = "internal_error", details: Optional[Dict[str, Any]] = None
    ) -> "MCPResponse":
        """
        Cria uma resposta de erro.
        
        Args:
            message: Mensagem de erro
            error_type: Tipo do erro
            details: Detalhes adicionais do erro
            
        Returns:
            Resposta MCP de erro
        """
        error = {
            "message": message,
            "type": error_type
        }
        
        if details:
            error["details"] = details
            
        return cls(success=False, error=error)


class TableReference(BaseModel):
    """
    Referência a uma tabela PostgreSQL.
    
    Atributos:
        table (str): Nome da tabela
        schema (str, opcional): Nome do schema (default: "public")
    """
    
    table: str = Field(..., description="Nome da tabela")
    schema: str = Field("public", description="Nome do schema")
    
    @validator("table")
    def validate_table(cls, v: str) -> str:
        """Valida o nome da tabela."""
        if not v:
            raise ValueError("nome da tabela não pode ser vazio")
        return v
    
    @validator("schema")
    def validate_schema(cls, v: str) -> str:
        """Valida o nome do schema."""
        if not v:
            raise ValueError("nome do schema não pode ser vazio")
        return v


class ColumnInfo(BaseModel):
    """Informações de uma coluna."""
    
    name: str = Field(..., description="Nome da coluna")
    data_type: str = Field(..., description="Tipo de dados PostgreSQL")
    nullable: bool = Field(..., description="Se a coluna pode ser nula")
    default: Optional[str] = Field(None, description="Valor padrão, se houver")
    is_primary: bool = Field(False, description="Se é chave primária")
    is_unique: bool = Field(False, description="Se tem restrição de unicidade")
    is_foreign_key: bool = Field(False, description="Se é chave estrangeira")
    references: Optional[str] = Field(None, description="Tabela referenciada se for FK")
    comment: Optional[str] = Field(None, description="Comentário da coluna, se houver")


class TableInfo(BaseModel):
    """Informações de uma tabela."""
    
    name: str = Field(..., description="Nome da tabela")
    schema: str = Field("public", description="Schema da tabela")
    columns: List[ColumnInfo] = Field(..., description="Colunas da tabela")
    primary_keys: List[str] = Field(default_factory=list, description="Colunas de chave primária")
    comment: Optional[str] = Field(None, description="Comentário da tabela, se houver")


class ViewInfo(BaseModel):
    """Informações de uma view PostgreSQL."""
    
    name: str = Field(..., description="Nome da view")
    schema: str = Field("public", description="Schema da view")
    columns: List[ColumnInfo] = Field(..., description="Colunas da view")
    definition: str = Field(..., description="Definição SQL da view")
    is_materialized: bool = Field(False, description="Se é uma view materializada")
    comment: Optional[str] = Field(None, description="Comentário da view, se houver")
    depends_on: List[str] = Field(default_factory=list, description="Tabelas/views das quais esta view depende")


class FunctionInfo(BaseModel):
    """Informações de uma função ou procedimento PostgreSQL."""
    
    name: str = Field(..., description="Nome da função")
    schema: str = Field("public", description="Schema da função")
    return_type: str = Field(..., description="Tipo de retorno da função")
    definition: str = Field(..., description="Definição SQL da função")
    language: str = Field(..., description="Linguagem da função")
    argument_types: List[str] = Field(default_factory=list, description="Tipos dos argumentos")
    argument_names: List[str] = Field(default_factory=list, description="Nomes dos argumentos")
    argument_defaults: List[Optional[str]] = Field(default_factory=list, description="Valores padrão dos argumentos")
    is_procedure: bool = Field(False, description="Se é um procedimento")
    is_aggregate: bool = Field(False, description="Se é uma função de agregação")
    is_window: bool = Field(False, description="Se é uma função de janela")
    is_security_definer: bool = Field(False, description="Se é executada com permissões do criador")
    volatility: str = Field("volatile", description="Volatilidade da função (volatile, stable, immutable)")
    comment: Optional[str] = Field(None, description="Comentário da função, se houver")


class SchemaInfo(BaseModel):
    """Informações de um schema PostgreSQL."""
    
    name: str = Field(..., description="Nome do schema")
    owner: str = Field(..., description="Dono do schema")
    tables: List[str] = Field(default_factory=list, description="Tabelas no schema")
    views: List[str] = Field(default_factory=list, description="Views no schema")
    materialized_views: List[str] = Field(default_factory=list, description="Views materializadas no schema")
    functions: List[str] = Field(default_factory=list, description="Funções no schema")
    procedures: List[str] = Field(default_factory=list, description="Procedimentos no schema")
    comment: Optional[str] = Field(None, description="Comentário do schema, se houver") 