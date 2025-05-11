"""
Testes para as funções de conversão de tipos geométricos
"""

import unittest

from postgres_mcp.utils.pg_types import (
    PostgresTypeConverter, prepare_point, prepare_point_from_string,
    prepare_box_from_string, prepare_polygon_from_string
)


class TestGeometricTypeConversions(unittest.TestCase):
    """Testes para conversões de tipos geométricos."""
    
    def test_validate_point(self):
        """Testa a validação de pontos."""
        # Pontos válidos
        self.assertTrue(PostgresTypeConverter.validate_point("(0,0)"))
        self.assertTrue(PostgresTypeConverter.validate_point("(10,20)"))
        self.assertTrue(PostgresTypeConverter.validate_point("(-10.5,20.75)"))
        self.assertTrue(PostgresTypeConverter.validate_point("( 10 , 20 )"))
        
        # Pontos inválidos
        self.assertFalse(PostgresTypeConverter.validate_point("0,0"))
        self.assertFalse(PostgresTypeConverter.validate_point("[10,20]"))
        self.assertFalse(PostgresTypeConverter.validate_point("(10,20,30)"))
        self.assertFalse(PostgresTypeConverter.validate_point("(a,b)"))
        self.assertFalse(PostgresTypeConverter.validate_point(123))
    
    def test_validate_box(self):
        """Testa a validação de boxes."""
        # Boxes válidas
        self.assertTrue(PostgresTypeConverter.validate_box("((0,0),(10,10))"))
        self.assertTrue(PostgresTypeConverter.validate_box("((-10.5,-20.5),(30.5,40.5))"))
        self.assertTrue(PostgresTypeConverter.validate_box("(( 0 , 0 ),( 10 , 10 ))"))
        
        # Boxes inválidas
        self.assertFalse(PostgresTypeConverter.validate_box("(0,0),(10,10)"))
        self.assertFalse(PostgresTypeConverter.validate_box("((0,0))"))
        self.assertFalse(PostgresTypeConverter.validate_box("((0,0),(10,10,5))"))
        self.assertFalse(PostgresTypeConverter.validate_box("(a,b),(c,d)"))
        self.assertFalse(PostgresTypeConverter.validate_box(123))
    
    def test_validate_polygon(self):
        """Testa a validação de polígonos."""
        # Polígonos válidos (triângulo)
        self.assertTrue(PostgresTypeConverter.validate_polygon("((0,0),(10,10),(20,0))"))
        # Polígono fechado (quadrado)
        self.assertTrue(PostgresTypeConverter.validate_polygon("((0,0),(0,10),(10,10),(10,0),(0,0))"))
        
        # Polígonos inválidos
        self.assertFalse(PostgresTypeConverter.validate_polygon("(0,0),(10,10)"))  # Faltam parênteses externos
        self.assertFalse(PostgresTypeConverter.validate_polygon("((0,0),(10,10))"))  # Apenas dois pontos
        self.assertFalse(PostgresTypeConverter.validate_polygon("(a,b),(c,d),(e,f)"))  # Caracteres inválidos
    
    def test_prepare_point(self):
        """Testa a preparação de pontos."""
        # Verificar formato POINT(x y)
        result = prepare_point(10, 20)
        self.assertEqual(result, "POINT(10 20)")
        
        result = prepare_point(-10.5, 20.75)
        self.assertEqual(result, "POINT(-10.5 20.75)")
    
    def test_prepare_point_from_string(self):
        """Testa a preparação de pontos a partir de strings."""
        # Formato simples
        result = prepare_point_from_string("(10,20)")
        self.assertEqual(result, "POINT(10.0 20.0)")
        
        # Com espaços
        result = prepare_point_from_string("( 10.5 , 20.75 )")
        self.assertEqual(result, "POINT(10.5 20.75)")
        
        # Valores negativos
        result = prepare_point_from_string("(-10,-20)")
        self.assertEqual(result, "POINT(-10.0 -20.0)")
        
        # Formato inválido
        with self.assertRaises(ValueError):
            prepare_point_from_string("10,20")
    
    def test_prepare_box_from_string(self):
        """Testa a preparação de boxes a partir de strings."""
        # Formato simples
        result = prepare_box_from_string("((0,0),(10,10))")
        self.assertEqual(result, "BOX(0.0 0.0, 10.0 10.0)")
        
        # Com espaços e valores decimais
        result = prepare_box_from_string("(( 0.5 , 0.5 ),( 10.5 , 10.5 ))")
        self.assertEqual(result, "BOX(0.5 0.5, 10.5 10.5)")
        
        # Valores negativos
        result = prepare_box_from_string("((-10,-10),(10,10))")
        self.assertEqual(result, "BOX(-10.0 -10.0, 10.0 10.0)")
        
        # Formato inválido
        with self.assertRaises(ValueError):
            prepare_box_from_string("(0,0),(10,10)")
    
    def test_prepare_polygon_from_string(self):
        """Testa a preparação de polígonos a partir de strings."""
        # Triângulo
        result = prepare_polygon_from_string("((0,0),(10,10),(20,0))")
        self.assertEqual(result, "POLYGON((0 0, 10 10, 20 0))")
        
        # Quadrado fechado
        result = prepare_polygon_from_string("((0,0),(0,10),(10,10),(10,0),(0,0))")
        self.assertEqual(result, "POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))")
        
        # Com valores decimais
        result = prepare_polygon_from_string("((0.5,0.5),(10.5,10.5),(20.5,0.5))")
        self.assertEqual(result, "POLYGON((0.5 0.5, 10.5 10.5, 20.5 0.5))")
        
        # Formato inválido
        with self.assertRaises(ValueError):
            prepare_polygon_from_string("(0,0),(10,10)")


if __name__ == "__main__":
    unittest.main() 