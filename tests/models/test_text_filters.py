"""
Testes para filtros de texto
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import TextFilter


class TestTextFilters(unittest.TestCase):
    """Testes para os filtros de texto."""
    
    def test_valid_like_filter(self):
        """Testa filtro LIKE com valor válido."""
        filter_obj = TextFilter(like="test%")
        self.assertEqual(filter_obj.like, "test%")
        
        filter_obj = TextFilter(like="%test%")
        self.assertEqual(filter_obj.like, "%test%")
        
        filter_obj = TextFilter(like="_est")
        self.assertEqual(filter_obj.like, "_est")
    
    def test_valid_ilike_filter(self):
        """Testa filtro ILIKE com valor válido."""
        filter_obj = TextFilter(ilike="test%")
        self.assertEqual(filter_obj.ilike, "test%")
        
        filter_obj = TextFilter(ilike="%TEST%")
        self.assertEqual(filter_obj.ilike, "%TEST%")
    
    def test_valid_match_filter(self):
        """Testa filtro de regex match com valor válido."""
        filter_obj = TextFilter(match="^test$")
        self.assertEqual(filter_obj.match, "^test$")
        
        filter_obj = TextFilter(match="test[0-9]+")
        self.assertEqual(filter_obj.match, "test[0-9]+")
    
    def test_valid_imatch_filter(self):
        """Testa filtro de regex imatch com valor válido."""
        filter_obj = TextFilter(imatch="^test$")
        self.assertEqual(filter_obj.imatch, "^test$")
        
        filter_obj = TextFilter(imatch="TEST[0-9]+")
        self.assertEqual(filter_obj.imatch, "TEST[0-9]+")
    
    def test_multiple_operators(self):
        """Testa filtro com múltiplos operadores."""
        filter_obj = TextFilter(like="test%", match="^test")
        self.assertEqual(filter_obj.like, "test%")
        self.assertEqual(filter_obj.match, "^test")
        
        filter_obj = TextFilter(ilike="%test%", imatch="test.*")
        self.assertEqual(filter_obj.ilike, "%test%")
        self.assertEqual(filter_obj.imatch, "test.*")
    
    def test_filter_requires_at_least_one_operator(self):
        """Testa se o filtro requer pelo menos um operador."""
        with self.assertRaises(ValidationError):
            TextFilter()
    
    def test_empty_string_valid(self):
        """Testa se string vazia é um valor válido."""
        filter_obj = TextFilter(like="")
        self.assertEqual(filter_obj.like, "")
        
        filter_obj = TextFilter(ilike="")
        self.assertEqual(filter_obj.ilike, "")


if __name__ == "__main__":
    unittest.main() 