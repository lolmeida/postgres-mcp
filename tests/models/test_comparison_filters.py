"""
Testes para filtros de comparação
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import ComparisonFilter


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
    
    def test_valid_less_than_filter(self):
        """Testa filtro menor que (lt) com valor válido."""
        filter_obj = ComparisonFilter(lt=10)
        self.assertEqual(filter_obj.lt, 10)
        
        filter_obj = ComparisonFilter(lt=10.5)
        self.assertEqual(filter_obj.lt, 10.5)
    
    def test_valid_greater_than_or_equal_filter(self):
        """Testa filtro maior ou igual a (gte) com valor válido."""
        filter_obj = ComparisonFilter(gte=10)
        self.assertEqual(filter_obj.gte, 10)
        
        filter_obj = ComparisonFilter(gte=10.5)
        self.assertEqual(filter_obj.gte, 10.5)
    
    def test_valid_less_than_or_equal_filter(self):
        """Testa filtro menor ou igual a (lte) com valor válido."""
        filter_obj = ComparisonFilter(lte=10)
        self.assertEqual(filter_obj.lte, 10)
        
        filter_obj = ComparisonFilter(lte=10.5)
        self.assertEqual(filter_obj.lte, 10.5)
    
    def test_valid_not_equal_filter(self):
        """Testa filtro diferente de (ne) com valor válido."""
        filter_obj = ComparisonFilter(ne=10)
        self.assertEqual(filter_obj.ne, 10)
        
        filter_obj = ComparisonFilter(ne="test")
        self.assertEqual(filter_obj.ne, "test")
        
        filter_obj = ComparisonFilter(ne=True)
        self.assertEqual(filter_obj.ne, True)
    
    def test_multiple_operators(self):
        """Testa filtro com múltiplos operadores."""
        filter_obj = ComparisonFilter(gt=10, lt=20)
        self.assertEqual(filter_obj.gt, 10)
        self.assertEqual(filter_obj.lt, 20)
        
        filter_obj = ComparisonFilter(gte=10, lte=20)
        self.assertEqual(filter_obj.gte, 10)
        self.assertEqual(filter_obj.lte, 20)
        
        filter_obj = ComparisonFilter(eq=10, ne=20)
        self.assertEqual(filter_obj.eq, 10)
        self.assertEqual(filter_obj.ne, 20)
    
    def test_filter_requires_at_least_one_operator(self):
        """Testa se o filtro requer pelo menos um operador."""
        with self.assertRaises(ValidationError):
            ComparisonFilter()


if __name__ == "__main__":
    unittest.main() 