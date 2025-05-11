"""
Sistema de filtros para consultas SQL
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, root_validator


class FilterOperator(str, Enum):
    """Operadores suportados para filtros."""
    # Operadores de comparação
    EQ = "eq"  # Equal
    GT = "gt"  # Greater than
    LT = "lt"  # Less than
    GTE = "gte"  # Greater than or equal
    LTE = "lte"  # Less than or equal
    NE = "ne"  # Not equal
    
    # Operadores de texto
    LIKE = "like"  # LIKE case sensitive
    ILIKE = "ilike"  # LIKE case insensitive
    MATCH = "match"  # Regex match case sensitive
    IMATCH = "imatch"  # Regex match case insensitive
    
    # Operadores de lista
    IN = "in"  # In list
    NIN = "nin"  # Not in list
    
    # Operadores para valores nulos
    IS = "is"  # IS NULL or IS NOT NULL
    
    # Operadores para arrays
    CONTAINS = "contains"  # Array contains
    CONTAINED_BY = "contained_by"  # Array is contained by
    OVERLAP = "overlap"  # Arrays overlap
    ARRAY_LENGTH = "array_length"  # Array length
    ARRAY_LENGTH_GT = "array_length_gt"  # Array length greater than
    ARRAY_LENGTH_LT = "array_length_lt"  # Array length less than
    
    # Operadores para JSON/JSONB
    JSONB_CONTAINS = "jsonb_contains"  # JSONB contains
    JSONB_CONTAINED_BY = "jsonb_contained_by"  # JSONB is contained by
    HAS_KEY = "has_key"  # JSONB has key
    HAS_ANY_KEYS = "has_any_keys"  # JSONB has any keys
    HAS_ALL_KEYS = "has_all_keys"  # JSONB has all keys
    JSONB_PATH = "jsonb_path"  # JSONB path query
    
    # Operadores para tipos geométricos
    DISTANCE = "distance"  # Distância entre pontos
    NEAR = "near"  # Ponto próximo (dentro de determinada distância)
    CONTAINS_POINT = "contains_point"  # Polígono contém ponto
    WITHIN = "within"  # Ponto/objeto está dentro de outro
    INTERSECTS = "intersects"  # Objetos se interceptam
    BOUNDING_BOX = "bounding_box"  # Dentro da caixa delimitadora


class ComparisonFilter(BaseModel):
    """
    Filtro de comparação.
    
    Suporta operadores de comparação como eq, gt, lt, gte, lte, ne.
    """
    
    eq: Optional[Any] = Field(None, description="Igual a")
    gt: Optional[Any] = Field(None, description="Maior que")
    lt: Optional[Any] = Field(None, description="Menor que")
    gte: Optional[Any] = Field(None, description="Maior ou igual a")
    lte: Optional[Any] = Field(None, description="Menor ou igual a")
    ne: Optional[Any] = Field(None, description="Diferente de")
    
    @root_validator(pre=True)
    def check_at_least_one_operator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se pelo menos um operador foi fornecido."""
        if not any(op in values for op in ["eq", "gt", "lt", "gte", "lte", "ne"]):
            raise ValueError("Pelo menos um operador de comparação deve ser fornecido")
        return values


class TextFilter(BaseModel):
    """
    Filtro de texto.
    
    Suporta operadores de texto como like, ilike, match, imatch.
    """
    
    like: Optional[str] = Field(None, description="LIKE case sensitive")
    ilike: Optional[str] = Field(None, description="LIKE case insensitive")
    match: Optional[str] = Field(None, description="Regex match case sensitive")
    imatch: Optional[str] = Field(None, description="Regex match case insensitive")
    
    @root_validator(pre=True)
    def check_at_least_one_operator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se pelo menos um operador foi fornecido."""
        if not any(op in values for op in ["like", "ilike", "match", "imatch"]):
            raise ValueError("Pelo menos um operador de texto deve ser fornecido")
        return values


class ListFilter(BaseModel):
    """
    Filtro de lista.
    
    Suporta operadores de lista como in, nin.
    """
    
    in_: Optional[List[Any]] = Field(None, alias="in", description="In list")
    nin: Optional[List[Any]] = Field(None, description="Not in list")
    
    @root_validator(pre=True)
    def check_at_least_one_operator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se pelo menos um operador foi fornecido."""
        if not any(op in values for op in ["in", "nin"]):
            raise ValueError("Pelo menos um operador de lista deve ser fornecido")
        return values


class NullFilter(BaseModel):
    """
    Filtro para valores nulos.
    
    Suporta operador is (null/not null).
    """
    
    is_: Optional[str] = Field(..., alias="is", description="IS NULL ou IS NOT NULL")
    
    @root_validator(pre=True)
    def validate_is_value(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Valida o valor do operador is."""
        is_value = values.get("is")
        if is_value is not None and is_value != "null" and is_value != "not null":
            raise ValueError("Valor de 'is' deve ser 'null' ou 'not null'")
        return values


class ArrayFilter(BaseModel):
    """
    Filtro para arrays.
    
    Suporta operadores de array como contains, contained_by, overlap, array_length.
    """
    
    contains: Optional[List[Any]] = Field(None, description="Array contém elementos")
    contained_by: Optional[List[Any]] = Field(None, description="Array está contido em")
    overlap: Optional[List[Any]] = Field(None, description="Arrays têm elementos em comum")
    array_length: Optional[int] = Field(None, description="Comprimento do array")
    array_length_gt: Optional[int] = Field(None, description="Comprimento do array maior que")
    array_length_lt: Optional[int] = Field(None, description="Comprimento do array menor que")
    
    @root_validator(pre=True)
    def check_at_least_one_operator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se pelo menos um operador foi fornecido."""
        if not any(op in values for op in [
            "contains", "contained_by", "overlap", 
            "array_length", "array_length_gt", "array_length_lt"
        ]):
            raise ValueError("Pelo menos um operador de array deve ser fornecido")
        return values


class JsonbFilter(BaseModel):
    """
    Filtro para JSONB.
    
    Suporta operadores JSONB como jsonb_contains, jsonb_contained_by, has_key, 
    has_any_keys, has_all_keys, jsonb_path.
    """
    
    jsonb_contains: Optional[Dict[str, Any]] = Field(None, description="JSONB contém")
    jsonb_contained_by: Optional[Dict[str, Any]] = Field(None, description="JSONB está contido em")
    has_key: Optional[str] = Field(None, description="JSONB tem a chave")
    has_any_keys: Optional[List[str]] = Field(None, description="JSONB tem qualquer uma das chaves")
    has_all_keys: Optional[List[str]] = Field(None, description="JSONB tem todas as chaves")
    jsonb_path: Optional[str] = Field(None, description="Consulta caminho JSONB")
    
    @root_validator(pre=True)
    def check_at_least_one_operator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se pelo menos um operador foi fornecido."""
        if not any(op in values for op in [
            "jsonb_contains", "jsonb_contained_by", "has_key", 
            "has_any_keys", "has_all_keys", "jsonb_path"
        ]):
            raise ValueError("Pelo menos um operador JSONB deve ser fornecido")
        return values


class GeometricFilter(BaseModel):
    """
    Filtro para tipos geométricos do PostgreSQL.
    
    Suporta operações com point, line, circle, polygon e outros tipos geométricos.
    """
    
    distance: Optional[Union[float, str]] = Field(None, description="Distância entre pontos")
    near: Optional[str] = Field(None, description="Ponto próximo (formato: (x,y))")
    contains_point: Optional[str] = Field(None, description="Polígono contém ponto (formato: (x,y))")
    within: Optional[str] = Field(None, description="Dentro de outro objeto geométrico")
    intersects: Optional[str] = Field(None, description="Intercepta outro objeto geométrico")
    bounding_box: Optional[str] = Field(None, description="Dentro da caixa delimitadora (formato: ((x1,y1),(x2,y2)))")
    
    @root_validator(pre=True)
    def check_at_least_one_operator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica se pelo menos um operador foi fornecido."""
        if not any(op in values for op in [
            "distance", "near", "contains_point", "within", "intersects", "bounding_box"
        ]):
            raise ValueError("Pelo menos um operador geométrico deve ser fornecido")
        return values
    
    @root_validator
    def validate_geometric_format(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Valida o formato dos valores geométricos."""
        # Validar formato de ponto (x,y)
        for field in ["near", "contains_point"]:
            value = values.get(field)
            if value is not None:
                if not cls._is_valid_point_format(value):
                    raise ValueError(f"Formato inválido para {field}. Deve ser '(x,y)'")
        
        # Validar formato de caixa delimitadora ((x1,y1),(x2,y2))
        if "bounding_box" in values and values["bounding_box"] is not None:
            if not cls._is_valid_box_format(values["bounding_box"]):
                raise ValueError("Formato inválido para bounding_box. Deve ser '((x1,y1),(x2,y2))'")
        
        return values
    
    @staticmethod
    def _is_valid_point_format(value: str) -> bool:
        """Verifica se o valor está no formato de ponto (x,y)."""
        if not isinstance(value, str):
            return False
        
        # Formato básico (x,y)
        if not (value.startswith("(") and value.endswith(")")):
            return False
        
        try:
            # Remover parênteses e dividir pelas coordenadas
            coords = value[1:-1].split(",")
            if len(coords) != 2:
                return False
            
            # Tentar converter para float
            float(coords[0].strip())
            float(coords[1].strip())
            return True
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def _is_valid_box_format(value: str) -> bool:
        """Verifica se o valor está no formato de caixa ((x1,y1),(x2,y2))."""
        if not isinstance(value, str):
            return False
        
        # Formato básico ((x1,y1),(x2,y2))
        if not (value.startswith("((") and value.endswith("))")):
            return False
        
        try:
            # Remover parênteses externos
            inner_value = value[1:-1]
            
            # Dividir pelos dois pontos
            points = inner_value.split("),(")
            if len(points) != 2:
                return False
            
            # Validar cada ponto
            point1 = "(" + points[0] + ")"
            point2 = "(" + points[1] + ")"
            
            return GeometricFilter._is_valid_point_format(point1) and GeometricFilter._is_valid_point_format(point2)
        except (ValueError, IndexError):
            return False


# Tipo complexo para filtros
FilterType = Union[
    Any,  # Valor direto (igualdade simples)
    ComparisonFilter,
    TextFilter,
    ListFilter,
    NullFilter,
    ArrayFilter,
    JsonbFilter,
    GeometricFilter,  # Novo tipo de filtro para geometria
    Dict[str, Any]  # Dicionário genérico para outros filtros
]

# Tipo recursivo para filtros aninhados
FiltersType = Dict[str, Union[FilterType, "FiltersType"]] 