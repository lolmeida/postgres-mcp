"""
Testes para filtros de valores nulos
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import NullFilter


class TestNullFilters(unittest.TestCase):
    """Testes para os filtros de valores nulos."""
    
    def test_valid_is_null(self):
        """Testa filtro IS NULL."""
        filter_obj = NullFilter(is_="null")
        self.assertEqual(filter_obj.is_, "null")
    
    def test_valid_is_not_null(self):
        """Testa filtro IS NOT NULL."""
        filter_obj = NullFilter(is_="not null")
        self.assertEqual(filter_obj.is_, "not null")
    
    def test_invalid_is_value(self):
        """Testa filtro IS com valor inválido."""
        with self.assertRaises(ValidationError):
            NullFilter(is_="invalid")
        
        with self.assertRaises(ValidationError):
            NullFilter(is_="NULL")  # Deve ser "null" em minúsculo
        
        with self.assertRaises(ValidationError):
            NullFilter(is_="NOT NULL")  # Deve ser "not null" em minúsculo
    
    def test_filter_requires_is_operator(self):
        """Testa se o filtro requer o operador is."""
        with self.assertRaises(ValidationError):
            NullFilter()


if __name__ == "__main__":
    unittest.main() 