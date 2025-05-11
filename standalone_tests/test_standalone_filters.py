#!/usr/bin/env python3

import unittest
import pytest
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator

# Marcar todos os testes neste módulo como standalone
pytestmark = pytest.mark.standalone

# ---- Filter Models Implementation ----

class ComparisonFilter(BaseModel):
    """Filtro de comparação."""
    eq: Optional[Any] = Field(None, description="Igual a")
    gt: Optional[Any] = Field(None, description="Maior que")
    lt: Optional[Any] = Field(None, description="Menor que")
    gte: Optional[Any] = Field(None, description="Maior ou igual a")
    lte: Optional[Any] = Field(None, description="Menor ou igual a")
    ne: Optional[Any] = Field(None, description="Diferente de")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in ["eq", "gt", "lt", "gte", "lte", "ne"]):
            raise ValueError("Pelo menos um operador de comparação deve ser fornecido")
        return data


class TextFilter(BaseModel):
    """Filtro de texto."""
    like: Optional[str] = Field(None, description="LIKE case sensitive")
    ilike: Optional[str] = Field(None, description="LIKE case insensitive")
    match: Optional[str] = Field(None, description="Regex match case sensitive")
    imatch: Optional[str] = Field(None, description="Regex match case insensitive")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in ["like", "ilike", "match", "imatch"]):
            raise ValueError("Pelo menos um operador de texto deve ser fornecido")
        return data


class ListFilter(BaseModel):
    """Filtro de lista."""
    in_: Optional[List[Any]] = Field(None, alias="in", description="In list")
    nin: Optional[List[Any]] = Field(None, description="Not in list")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        
        # Check for 'in_' field as well as 'in' for direct instantiation
        has_in = "in" in data or "in_" in data
        has_nin = "nin" in data
        
        if not (has_in or has_nin):
            raise ValueError("Pelo menos um operador de lista deve ser fornecido")
        
        # Handle 'in_' to 'in' conversion for direct instantiation
        if "in_" in data and "in" not in data:
            data["in"] = data.pop("in_")
        
        return data


class NullFilter(BaseModel):
    """Filtro para valores nulos."""
    is_: str = Field(alias="is", description="IS NULL ou IS NOT NULL")
    
    @model_validator(mode='before')
    @classmethod
    def validate_is_value(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        
        # Handle 'is_' to 'is' conversion for direct instantiation
        if "is_" in data and "is" not in data:
            data["is"] = data.pop("is_")
        
        is_value = data.get("is")
        if is_value is not None and is_value != "null" and is_value != "not null":
            raise ValueError("Valor de 'is' deve ser 'null' ou 'not null'")
        
        return data


class ArrayFilter(BaseModel):
    """Filtro para arrays."""
    contains: Optional[List[Any]] = Field(None, description="Array contém elementos")
    contained_by: Optional[List[Any]] = Field(None, description="Array está contido em")
    overlap: Optional[List[Any]] = Field(None, description="Arrays têm elementos em comum")
    array_length: Optional[int] = Field(None, description="Comprimento do array")
    array_length_gt: Optional[int] = Field(None, description="Comprimento do array maior que")
    array_length_lt: Optional[int] = Field(None, description="Comprimento do array menor que")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in [
            "contains", "contained_by", "overlap", 
            "array_length", "array_length_gt", "array_length_lt"
        ]):
            raise ValueError("Pelo menos um operador de array deve ser fornecido")
        return data


class JsonbFilter(BaseModel):
    """Filtro para JSONB."""
    jsonb_contains: Optional[Dict[str, Any]] = Field(None, description="JSONB contém")
    jsonb_contained_by: Optional[Dict[str, Any]] = Field(None, description="JSONB está contido em")
    has_key: Optional[str] = Field(None, description="JSONB tem a chave")
    has_any_keys: Optional[List[str]] = Field(None, description="JSONB tem qualquer uma das chaves")
    has_all_keys: Optional[List[str]] = Field(None, description="JSONB tem todas as chaves")
    jsonb_path: Optional[str] = Field(None, description="Consulta caminho JSONB")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in [
            "jsonb_contains", "jsonb_contained_by", "has_key", 
            "has_any_keys", "has_all_keys", "jsonb_path"
        ]):
            raise ValueError("Pelo menos um operador JSONB deve ser fornecido")
        return data


class GeometricFilter(BaseModel):
    """Filtro para tipos geométricos."""
    distance: Optional[Union[float, str]] = Field(None, description="Distância entre pontos")
    near: Optional[str] = Field(None, description="Ponto próximo (formato: (x,y))")
    contains_point: Optional[str] = Field(None, description="Polígono contém ponto (formato: (x,y))")
    within: Optional[str] = Field(None, description="Dentro de outro objeto geométrico")
    intersects: Optional[str] = Field(None, description="Intercepta outro objeto geométrico")
    bounding_box: Optional[str] = Field(None, description="Dentro da caixa delimitadora (formato: ((x1,y1),(x2,y2)))")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in [
            "distance", "near", "contains_point", 
            "within", "intersects", "bounding_box"
        ]):
            raise ValueError("Pelo menos um operador geométrico deve ser fornecido")
        return data
    
    @model_validator(mode='after')
    def validate_geometric_format(self) -> 'GeometricFilter':
        """Valida formatos de valores para operadores geométricos."""
        if self.near and not self._is_valid_point_format(self.near):
            raise ValueError(f"Formato inválido para 'near'. Esperado: '(x,y)', recebido: '{self.near}'")
        
        if self.contains_point and not self._is_valid_point_format(self.contains_point):
            raise ValueError(f"Formato inválido para 'contains_point'. Esperado: '(x,y)', recebido: '{self.contains_point}'")
        
        if self.bounding_box and not self._is_valid_box_format(self.bounding_box):
            raise ValueError(f"Formato inválido para 'bounding_box'. Esperado: '((x1,y1),(x2,y2))', recebido: '{self.bounding_box}'")
        
        return self
    
    @staticmethod
    def _is_valid_point_format(value: str) -> bool:
        """Verifica se o formato do ponto é válido."""
        if not (value.startswith("(") and value.endswith(")")):
            return False
        
        # Remove parênteses
        point_content = value[1:-1]
        
        # Verifica se contém uma vírgula
        if "," not in point_content:
            return False
        
        # Divide em coordenadas x e y
        coords = point_content.split(",")
        if len(coords) != 2:
            return False
        
        # Tenta converter para float
        try:
            float(coords[0].strip())
            float(coords[1].strip())
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_valid_box_format(value: str) -> bool:
        """Verifica se o formato da caixa é válido."""
        if not (value.startswith("((") and value.endswith("))")):
            return False
        
        try:
            # Remove parênteses externos
            box_content = value[2:-2]
            
            # Verifica se tem dois pontos separados por "),("
            if "),(" not in box_content:
                return False
                
            points = box_content.split("),(")
            if len(points) != 2:
                return False
            
            # Testa cada coordenada
            coords1 = points[0].split(",")
            coords2 = points[1].split(",")
            
            if len(coords1) != 2 or len(coords2) != 2:
                return False
                
            # Tenta converter para float
            float(coords1[0].strip())
            float(coords1[1].strip())
            float(coords2[0].strip())
            float(coords2[1].strip())
            
            return True
        except (ValueError, IndexError):
            return False


# ---- Tests ----

class TestComparisonFilters(unittest.TestCase):
    """Testes para os filtros de comparação."""
    
    def test_valid_equal_filter(self):
        """Testa filtro de igualdade (eq) com valor válido."""
        filter_obj = ComparisonFilter(eq=10)
        self.assertEqual(filter_obj.eq, 10)
        
        filter_obj = ComparisonFilter(eq="test")
        self.assertEqual(filter_obj.eq, "test")
        
        filter_obj = ComparisonFilter(eq=True)
        self.assertEqual(filter_obj.eq, True)
    
    def test_valid_greater_than_filter(self):
        """Testa filtro maior que (gt) com valor válido."""
        filter_obj = ComparisonFilter(gt=10)
        self.assertEqual(filter_obj.gt, 10)
        
        filter_obj = ComparisonFilter(gt=10.5)
        self.assertEqual(filter_obj.gt, 10.5)
    
    def test_multiple_operators(self):
        """Testa filtro com múltiplos operadores."""
        filter_obj = ComparisonFilter(gt=10, lt=20)
        self.assertEqual(filter_obj.gt, 10)
        self.assertEqual(filter_obj.lt, 20)
    
    def test_invalid_no_operator(self):
        """Testa filtro sem operador."""
        with self.assertRaises(ValueError):
            ComparisonFilter()


class TestTextFilters(unittest.TestCase):
    """Testes para os filtros de texto."""
    
    def test_valid_like_filter(self):
        """Testa filtro LIKE com valor válido."""
        filter_obj = TextFilter(like="test%")
        self.assertEqual(filter_obj.like, "test%")
        
        filter_obj = TextFilter(like="%test%")
        self.assertEqual(filter_obj.like, "%test%")
    
    def test_valid_ilike_filter(self):
        """Testa filtro ILIKE com valor válido."""
        filter_obj = TextFilter(ilike="test%")
        self.assertEqual(filter_obj.ilike, "test%")
        
        filter_obj = TextFilter(ilike="%TEST%")
        self.assertEqual(filter_obj.ilike, "%TEST%")
    
    def test_empty_string_valid(self):
        """Testa se string vazia é um valor válido."""
        filter_obj = TextFilter(like="")
        self.assertEqual(filter_obj.like, "")


class TestListFilters(unittest.TestCase):
    """Testes para os filtros de lista."""
    
    def test_valid_in_filter_direct_assign(self):
        """Testa filtro IN com atribuição direta."""
        filter_obj = ListFilter(in_=[1, 2, 3])
        self.assertEqual(filter_obj.in_, [1, 2, 3])
    
    def test_valid_in_filter_dict_assign(self):
        """Testa filtro IN com atribuição via dicionário."""
        data = {"in": [1, 2, 3]}
        filter_obj = ListFilter.model_validate(data)
        self.assertEqual(filter_obj.in_, [1, 2, 3])
    
    def test_valid_nin_filter(self):
        """Testa filtro NOT IN com valor válido."""
        filter_obj = ListFilter(nin=[1, 2, 3])
        self.assertEqual(filter_obj.nin, [1, 2, 3])
    
    def test_valid_empty_list(self):
        """Testa filtro com lista vazia."""
        filter_obj = ListFilter(in_=[])
        self.assertEqual(filter_obj.in_, [])
        
        filter_obj = ListFilter(nin=[])
        self.assertEqual(filter_obj.nin, [])


class TestNullFilters(unittest.TestCase):
    """Testes para os filtros de valores nulos."""
    
    def test_valid_is_null_direct(self):
        """Testa filtro IS NULL com atribuição direta."""
        filter_obj = NullFilter(is_="null")
        self.assertEqual(filter_obj.is_, "null")
    
    def test_valid_is_null_dict(self):
        """Testa filtro IS NULL com atribuição via dicionário."""
        data = {"is": "null"}
        filter_obj = NullFilter.model_validate(data)
        self.assertEqual(filter_obj.is_, "null")
    
    def test_valid_is_not_null(self):
        """Testa filtro IS NOT NULL."""
        filter_obj = NullFilter(is_="not null")
        self.assertEqual(filter_obj.is_, "not null")
    
    def test_invalid_is_value(self):
        """Testa valor inválido para IS."""
        with self.assertRaises(ValueError):
            NullFilter(is_="invalid")


class TestArrayFilters(unittest.TestCase):
    """Testes para os filtros de array."""
    
    def test_valid_contains(self):
        """Testa filtro 'contains' com valores válidos."""
        filter_obj = ArrayFilter(contains=[1, 2, 3])
        self.assertEqual(filter_obj.contains, [1, 2, 3])
    
    def test_valid_contained_by(self):
        """Testa filtro 'contained_by' com valores válidos."""
        filter_obj = ArrayFilter(contained_by=[1, 2, 3, 4, 5])
        self.assertEqual(filter_obj.contained_by, [1, 2, 3, 4, 5])
    
    def test_valid_array_length(self):
        """Testa filtro 'array_length' com valores válidos."""
        filter_obj = ArrayFilter(array_length=3)
        self.assertEqual(filter_obj.array_length, 3)
    
    def test_invalid_no_operator(self):
        """Testa filtro sem operador."""
        with self.assertRaises(ValueError):
            ArrayFilter()


class TestJsonbFilters(unittest.TestCase):
    """Testes para os filtros de JSONB."""
    
    def test_valid_jsonb_contains(self):
        """Testa filtro 'jsonb_contains' com valores válidos."""
        filter_obj = JsonbFilter(jsonb_contains={"name": "John"})
        self.assertEqual(filter_obj.jsonb_contains, {"name": "John"})
    
    def test_valid_has_key(self):
        """Testa filtro 'has_key' com valores válidos."""
        filter_obj = JsonbFilter(has_key="name")
        self.assertEqual(filter_obj.has_key, "name")
    
    def test_valid_has_any_keys(self):
        """Testa filtro 'has_any_keys' com valores válidos."""
        filter_obj = JsonbFilter(has_any_keys=["name", "age"])
        self.assertEqual(filter_obj.has_any_keys, ["name", "age"])
    
    def test_invalid_no_operator(self):
        """Testa filtro sem operador."""
        with self.assertRaises(ValueError):
            JsonbFilter()


class TestGeometricFilters(unittest.TestCase):
    """Testes para os filtros geométricos."""
    
    def test_valid_distance(self):
        """Testa filtro 'distance' com valores válidos."""
        filter_obj = GeometricFilter(distance=10.5)
        self.assertEqual(filter_obj.distance, 10.5)
    
    def test_valid_near(self):
        """Testa filtro 'near' com valores válidos."""
        filter_obj = GeometricFilter(near="(10.5,20.3)")
        self.assertEqual(filter_obj.near, "(10.5,20.3)")
    
    def test_valid_bounding_box(self):
        """Testa filtro 'bounding_box' com valores válidos."""
        filter_obj = GeometricFilter(bounding_box="((0,0),(10,10))")
        self.assertEqual(filter_obj.bounding_box, "((0,0),(10,10))")
    
    def test_invalid_point_format(self):
        """Testa formato inválido para ponto."""
        with self.assertRaises(ValueError):
            GeometricFilter(near="10.5,20.3")
    
    def test_invalid_box_format(self):
        """Testa formato inválido para caixa."""
        with self.assertRaises(ValueError):
            GeometricFilter(bounding_box="(0,0),(10,10)")


if __name__ == "__main__":
    unittest.main(verbosity=2) 