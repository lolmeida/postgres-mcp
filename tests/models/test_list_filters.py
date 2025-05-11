"""
Testes para filtros de lista
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import ListFilter


class TestListFilters(unittest.TestCase):
    """Testes para os filtros de lista."""
    
    def test_valid_in_filter_numbers(self):
        """Testa filtro IN com lista de números válidos."""
        filter_obj = ListFilter(in_=[1, 2, 3])
        self.assertEqual(filter_obj.in_, [1, 2, 3])
        
        filter_obj = ListFilter(in_=[1.5, 2.5, 3.5])
        self.assertEqual(filter_obj.in_, [1.5, 2.5, 3.5])
    
    def test_valid_in_filter_strings(self):
        """Testa filtro IN com lista de strings válidas."""
        filter_obj = ListFilter(in_=["test1", "test2", "test3"])
        self.assertEqual(filter_obj.in_, ["test1", "test2", "test3"])
    
    def test_valid_in_filter_mixed(self):
        """Testa filtro IN com lista de valores mistos."""
        filter_obj = ListFilter(in_=[1, "test", True])
        self.assertEqual(filter_obj.in_, [1, "test", True])
    
    def test_valid_nin_filter_numbers(self):
        """Testa filtro NOT IN com lista de números válidos."""
        filter_obj = ListFilter(nin=[1, 2, 3])
        self.assertEqual(filter_obj.nin, [1, 2, 3])
        
        filter_obj = ListFilter(nin=[1.5, 2.5, 3.5])
        self.assertEqual(filter_obj.nin, [1.5, 2.5, 3.5])
    
    def test_valid_nin_filter_strings(self):
        """Testa filtro NOT IN com lista de strings válidas."""
        filter_obj = ListFilter(nin=["test1", "test2", "test3"])
        self.assertEqual(filter_obj.nin, ["test1", "test2", "test3"])
    
    def test_valid_nin_filter_mixed(self):
        """Testa filtro NOT IN com lista de valores mistos."""
        filter_obj = ListFilter(nin=[1, "test", True])
        self.assertEqual(filter_obj.nin, [1, "test", True])
    
    def test_valid_empty_list(self):
        """Testa filtro com lista vazia."""
        filter_obj = ListFilter(in_=[])
        self.assertEqual(filter_obj.in_, [])
        
        filter_obj = ListFilter(nin=[])
        self.assertEqual(filter_obj.nin, [])
    
    def test_multiple_operators(self):
        """Testa filtro com múltiplos operadores."""
        filter_obj = ListFilter(in_=[1, 2, 3], nin=[4, 5, 6])
        self.assertEqual(filter_obj.in_, [1, 2, 3])
        self.assertEqual(filter_obj.nin, [4, 5, 6])
    
    def test_filter_requires_at_least_one_operator(self):
        """Testa se o filtro requer pelo menos um operador."""
        with self.assertRaises(ValidationError):
            ListFilter()


if __name__ == "__main__":
    unittest.main() 