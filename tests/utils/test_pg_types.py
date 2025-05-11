"""
Testes para o módulo utils.pg_types
"""

import json
import unittest

from postgres_mcp.utils.pg_types import PostgresTypeConverter, prepare_array, prepare_jsonb


class TestPostgresTypeConverter(unittest.TestCase):
    """Testes para o conversor de tipos PostgreSQL."""
    
    def test_prepare_array_empty(self):
        """Testa a conversão de um array vazio."""
        result = PostgresTypeConverter.prepare_array_value([])
        self.assertEqual(result, "{}")
    
    def test_prepare_array_simple_types(self):
        """Testa a conversão de arrays com tipos simples."""
        # Inteiros
        result = PostgresTypeConverter.prepare_array_value([1, 2, 3])
        self.assertEqual(result, "{1,2,3}")
        
        # Strings
        result = PostgresTypeConverter.prepare_array_value(["a", "b", "c"])
        self.assertEqual(result, '{\"a\",\"b\",\"c\"}')
        
        # Misturado
        result = PostgresTypeConverter.prepare_array_value([1, "a", None, True])
        self.assertEqual(result, '{1,\"a\",NULL,TRUE}')
    
    def test_prepare_array_escaped_strings(self):
        """Testa a conversão de arrays com strings que precisam escapamento."""
        result = PostgresTypeConverter.prepare_array_value(["quotes\"inside", "back\\slash"])
        self.assertEqual(result, '{\"quotes\\\"inside\",\"back\\\\slash\"}')
    
    def test_prepare_array_nested(self):
        """Testa a conversão de arrays aninhados."""
        result = PostgresTypeConverter.prepare_array_value([[1, 2], [3, 4]])
        self.assertEqual(result, "{{1,2},{3,4}}")
        
        result = PostgresTypeConverter.prepare_array_value([["a", "b"], ["c", "d"]])
        self.assertEqual(result, '{{\"a\",\"b\"},{\"c\",\"d\"}}')
    
    def test_prepare_array_with_objects(self):
        """Testa a conversão de arrays contendo objetos JSON."""
        result = PostgresTypeConverter.prepare_array_value([{"a": 1}, {"b": 2}])
        # Verificar se é um formato válido de array PostgreSQL
        self.assertTrue(result.startswith("{") and result.endswith("}"))
        # Verificar se os objetos foram serializados corretamente
        self.assertIn("{\"a\":1}", result)
        self.assertIn("{\"b\":2}", result)
    
    def test_prepare_jsonb_object(self):
        """Testa a conversão de um objeto para JSONB."""
        result = PostgresTypeConverter.prepare_jsonb_value({"a": 1, "b": "test"})
        # Verificar equivalência usando parsing JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, {"a": 1, "b": "test"})
    
    def test_prepare_jsonb_array(self):
        """Testa a conversão de um array para JSONB."""
        result = PostgresTypeConverter.prepare_jsonb_value([1, 2, {"a": 3}])
        # Verificar equivalência usando parsing JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, [1, 2, {"a": 3}])
    
    def test_prepare_jsonb_complex(self):
        """Testa a conversão de uma estrutura complexa para JSONB."""
        complex_data = {
            "id": 123,
            "name": "Test",
            "active": True,
            "tags": ["a", "b", "c"],
            "metadata": {
                "created_at": "2023-01-01",
                "stats": {
                    "views": 1000,
                    "likes": 50
                }
            }
        }
        result = PostgresTypeConverter.prepare_jsonb_value(complex_data)
        # Verificar equivalência usando parsing JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, complex_data)
    
    def test_prepare_array_helper(self):
        """Testa a função helper prepare_array."""
        result = prepare_array([1, 2, 3])
        self.assertEqual(result, "{1,2,3}")
    
    def test_prepare_jsonb_helper(self):
        """Testa a função helper prepare_jsonb."""
        result = prepare_jsonb({"a": 1})
        parsed = json.loads(result)
        self.assertEqual(parsed, {"a": 1})


if __name__ == "__main__":
    unittest.main() 