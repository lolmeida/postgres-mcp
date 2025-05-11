"""
Testes para filtros de JSONB
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import JsonbFilter


class TestJsonbFilters(unittest.TestCase):
    """Testes para os filtros de JSONB."""
    
    def test_valid_jsonb_contains(self):
        """Testa filtro 'jsonb_contains' com valores válidos."""
        filter_obj = JsonbFilter(jsonb_contains={"name": "John"})
        self.assertEqual(filter_obj.jsonb_contains, {"name": "John"})
        
        filter_obj = JsonbFilter(jsonb_contains={"name": "John", "age": 30})
        self.assertEqual(filter_obj.jsonb_contains, {"name": "John", "age": 30})
        
        filter_obj = JsonbFilter(jsonb_contains={"tags": ["tag1", "tag2"]})
        self.assertEqual(filter_obj.jsonb_contains, {"tags": ["tag1", "tag2"]})
        
        filter_obj = JsonbFilter(jsonb_contains={"nested": {"field": "value"}})
        self.assertEqual(filter_obj.jsonb_contains, {"nested": {"field": "value"}})
    
    def test_valid_jsonb_contained_by(self):
        """Testa filtro 'jsonb_contained_by' com valores válidos."""
        filter_obj = JsonbFilter(jsonb_contained_by={"name": "John", "age": 30, "active": True})
        self.assertEqual(filter_obj.jsonb_contained_by, {"name": "John", "age": 30, "active": True})
    
    def test_valid_has_key(self):
        """Testa filtro 'has_key' com valores válidos."""
        filter_obj = JsonbFilter(has_key="name")
        self.assertEqual(filter_obj.has_key, "name")
        
        filter_obj = JsonbFilter(has_key="nested.field")
        self.assertEqual(filter_obj.has_key, "nested.field")
    
    def test_valid_has_any_keys(self):
        """Testa filtro 'has_any_keys' com valores válidos."""
        filter_obj = JsonbFilter(has_any_keys=["name", "age"])
        self.assertEqual(filter_obj.has_any_keys, ["name", "age"])
        
        filter_obj = JsonbFilter(has_any_keys=["nested.field", "tags"])
        self.assertEqual(filter_obj.has_any_keys, ["nested.field", "tags"])
    
    def test_valid_has_all_keys(self):
        """Testa filtro 'has_all_keys' com valores válidos."""
        filter_obj = JsonbFilter(has_all_keys=["name", "age"])
        self.assertEqual(filter_obj.has_all_keys, ["name", "age"])
        
        filter_obj = JsonbFilter(has_all_keys=["nested.field", "tags"])
        self.assertEqual(filter_obj.has_all_keys, ["nested.field", "tags"])
    
    def test_valid_jsonb_path(self):
        """Testa filtro 'jsonb_path' com valores válidos."""
        filter_obj = JsonbFilter(jsonb_path="$.name")
        self.assertEqual(filter_obj.jsonb_path, "$.name")
        
        filter_obj = JsonbFilter(jsonb_path="$.nested.field")
        self.assertEqual(filter_obj.jsonb_path, "$.nested.field")
        
        filter_obj = JsonbFilter(jsonb_path="$.tags[0]")
        self.assertEqual(filter_obj.jsonb_path, "$.tags[0]")
    
    def test_multiple_operators(self):
        """Testa filtro com múltiplos operadores."""
        filter_obj = JsonbFilter(has_key="name", has_all_keys=["age", "active"])
        self.assertEqual(filter_obj.has_key, "name")
        self.assertEqual(filter_obj.has_all_keys, ["age", "active"])
        
        filter_obj = JsonbFilter(jsonb_contains={"name": "John"}, jsonb_path="$.age")
        self.assertEqual(filter_obj.jsonb_contains, {"name": "John"})
        self.assertEqual(filter_obj.jsonb_path, "$.age")
    
    def test_empty_objects_and_arrays(self):
        """Testa filtro com objetos e arrays vazios."""
        filter_obj = JsonbFilter(jsonb_contains={})
        self.assertEqual(filter_obj.jsonb_contains, {})
        
        filter_obj = JsonbFilter(has_any_keys=[])
        self.assertEqual(filter_obj.has_any_keys, [])
        
        filter_obj = JsonbFilter(has_all_keys=[])
        self.assertEqual(filter_obj.has_all_keys, [])
    
    def test_filter_requires_at_least_one_operator(self):
        """Testa se o filtro requer pelo menos um operador."""
        with self.assertRaises(ValidationError):
            JsonbFilter()


if __name__ == "__main__":
    unittest.main() 