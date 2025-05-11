"""
Testes para filtros de array
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import ArrayFilter


class TestArrayFilters(unittest.TestCase):
    """Testes para os filtros de array."""
    
    def test_valid_contains(self):
        """Testa filtro 'contains' com valores válidos."""
        filter_obj = ArrayFilter(contains=[1, 2, 3])
        self.assertEqual(filter_obj.contains, [1, 2, 3])
        
        filter_obj = ArrayFilter(contains=["a", "b", "c"])
        self.assertEqual(filter_obj.contains, ["a", "b", "c"])
        
        filter_obj = ArrayFilter(contains=[1, "a", True])
        self.assertEqual(filter_obj.contains, [1, "a", True])
    
    def test_valid_contained_by(self):
        """Testa filtro 'contained_by' com valores válidos."""
        filter_obj = ArrayFilter(contained_by=[1, 2, 3, 4, 5])
        self.assertEqual(filter_obj.contained_by, [1, 2, 3, 4, 5])
        
        filter_obj = ArrayFilter(contained_by=["a", "b", "c", "d"])
        self.assertEqual(filter_obj.contained_by, ["a", "b", "c", "d"])
    
    def test_valid_overlap(self):
        """Testa filtro 'overlap' com valores válidos."""
        filter_obj = ArrayFilter(overlap=[1, 2, 3])
        self.assertEqual(filter_obj.overlap, [1, 2, 3])
        
        filter_obj = ArrayFilter(overlap=["a", "b", "c"])
        self.assertEqual(filter_obj.overlap, ["a", "b", "c"])
    
    def test_valid_array_length(self):
        """Testa filtro 'array_length' com valores válidos."""
        filter_obj = ArrayFilter(array_length=3)
        self.assertEqual(filter_obj.array_length, 3)
        
        filter_obj = ArrayFilter(array_length=0)
        self.assertEqual(filter_obj.array_length, 0)
    
    def test_valid_array_length_gt(self):
        """Testa filtro 'array_length_gt' com valores válidos."""
        filter_obj = ArrayFilter(array_length_gt=3)
        self.assertEqual(filter_obj.array_length_gt, 3)
        
        filter_obj = ArrayFilter(array_length_gt=0)
        self.assertEqual(filter_obj.array_length_gt, 0)
    
    def test_valid_array_length_lt(self):
        """Testa filtro 'array_length_lt' com valores válidos."""
        filter_obj = ArrayFilter(array_length_lt=10)
        self.assertEqual(filter_obj.array_length_lt, 10)
        
        filter_obj = ArrayFilter(array_length_lt=1)
        self.assertEqual(filter_obj.array_length_lt, 1)
    
    def test_multiple_operators(self):
        """Testa filtro com múltiplos operadores."""
        filter_obj = ArrayFilter(contains=[1, 2], array_length_gt=1)
        self.assertEqual(filter_obj.contains, [1, 2])
        self.assertEqual(filter_obj.array_length_gt, 1)
        
        filter_obj = ArrayFilter(overlap=["a", "b"], array_length_lt=5)
        self.assertEqual(filter_obj.overlap, ["a", "b"])
        self.assertEqual(filter_obj.array_length_lt, 5)
        
        filter_obj = ArrayFilter(array_length=3, contained_by=[1, 2, 3, 4, 5])
        self.assertEqual(filter_obj.array_length, 3)
        self.assertEqual(filter_obj.contained_by, [1, 2, 3, 4, 5])
    
    def test_empty_array(self):
        """Testa filtro com array vazio."""
        filter_obj = ArrayFilter(contains=[])
        self.assertEqual(filter_obj.contains, [])
        
        filter_obj = ArrayFilter(contained_by=[])
        self.assertEqual(filter_obj.contained_by, [])
        
        filter_obj = ArrayFilter(overlap=[])
        self.assertEqual(filter_obj.overlap, [])
    
    def test_filter_requires_at_least_one_operator(self):
        """Testa se o filtro requer pelo menos um operador."""
        with self.assertRaises(ValidationError):
            ArrayFilter()


if __name__ == "__main__":
    unittest.main() 