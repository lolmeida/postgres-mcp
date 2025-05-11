"""
Testes para filtros geométricos
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.filters import GeometricFilter


class TestGeometricFilters(unittest.TestCase):
    """Testes para os filtros geométricos."""
    
    def test_valid_point_near(self):
        """Testa filtro 'near' com ponto válido."""
        # Formato simples
        filter_obj = GeometricFilter(near="(10,20)")
        self.assertEqual(filter_obj.near, "(10,20)")
        
        # Com distância
        filter_obj = GeometricFilter(near="(10,20),5.5")
        self.assertEqual(filter_obj.near, "(10,20),5.5")
        
        # Com espaços
        filter_obj = GeometricFilter(near="( 10.5 , 20.75 )")
        self.assertEqual(filter_obj.near, "( 10.5 , 20.75 )")
    
    def test_invalid_point_near(self):
        """Testa filtro 'near' com ponto inválido."""
        # Formato incorreto
        with self.assertRaises(ValidationError):
            GeometricFilter(near="10,20")
        
        with self.assertRaises(ValidationError):
            GeometricFilter(near="[10,20]")
        
        with self.assertRaises(ValidationError):
            GeometricFilter(near="(10,20,30)")
    
    def test_valid_distance(self):
        """Testa filtro 'distance' com valor válido."""
        # Valor numérico
        filter_obj = GeometricFilter(distance=10.5)
        self.assertEqual(filter_obj.distance, 10.5)
        
        # String com ponto e distância
        filter_obj = GeometricFilter(distance="(10,20),5.5")
        self.assertEqual(filter_obj.distance, "(10,20),5.5")
    
    def test_valid_contains_point(self):
        """Testa filtro 'contains_point' com valor válido."""
        filter_obj = GeometricFilter(contains_point="(10,20)")
        self.assertEqual(filter_obj.contains_point, "(10,20)")
    
    def test_invalid_contains_point(self):
        """Testa filtro 'contains_point' com valor inválido."""
        with self.assertRaises(ValidationError):
            GeometricFilter(contains_point="10,20")
    
    def test_valid_bounding_box(self):
        """Testa filtro 'bounding_box' com valor válido."""
        filter_obj = GeometricFilter(bounding_box="((0,0),(10,10))")
        self.assertEqual(filter_obj.bounding_box, "((0,0),(10,10))")
        
        filter_obj = GeometricFilter(bounding_box="((0.5,0.5),(10.5,10.5))")
        self.assertEqual(filter_obj.bounding_box, "((0.5,0.5),(10.5,10.5))")
    
    def test_invalid_bounding_box(self):
        """Testa filtro 'bounding_box' com valor inválido."""
        with self.assertRaises(ValidationError):
            GeometricFilter(bounding_box="(0,0),(10,10)")
        
        with self.assertRaises(ValidationError):
            GeometricFilter(bounding_box="((0,0),(10,10,5))")
        
        with self.assertRaises(ValidationError):
            GeometricFilter(bounding_box="((0,0)))")
    
    def test_valid_within(self):
        """Testa filtro 'within' com valor válido."""
        filter_obj = GeometricFilter(within="((0,0),(10,10))")
        self.assertEqual(filter_obj.within, "((0,0),(10,10))")
        
        filter_obj = GeometricFilter(within="((0,0),(5,5),(10,0),(0,0))")
        self.assertEqual(filter_obj.within, "((0,0),(5,5),(10,0),(0,0))")
    
    def test_valid_intersects(self):
        """Testa filtro 'intersects' com valor válido."""
        filter_obj = GeometricFilter(intersects="((0,0),(10,10))")
        self.assertEqual(filter_obj.intersects, "((0,0),(10,10))")
        
        filter_obj = GeometricFilter(intersects="(5,5)")
        self.assertEqual(filter_obj.intersects, "(5,5)")
    
    def test_filter_requires_at_least_one_operator(self):
        """Testa se o filtro requer pelo menos um operador."""
        with self.assertRaises(ValidationError):
            GeometricFilter()


if __name__ == "__main__":
    unittest.main() 