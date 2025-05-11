"""
Testes para o modelo FunctionInfo.
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.base import FunctionInfo


class TestFunctionInfo(unittest.TestCase):
    """Testes para o modelo FunctionInfo."""
    
    def test_create_function_info(self):
        """Teste de criação do modelo FunctionInfo com valores válidos."""
        
        function_info = FunctionInfo(
            name="test_function",
            schema="public",
            return_type="integer",
            definition="BEGIN RETURN 1; END;",
            language="plpgsql",
        )
        
        self.assertEqual(function_info.name, "test_function")
        self.assertEqual(function_info.schema, "public")
        self.assertEqual(function_info.return_type, "integer")
        self.assertEqual(function_info.definition, "BEGIN RETURN 1; END;")
        self.assertEqual(function_info.language, "plpgsql")
        self.assertFalse(function_info.is_procedure)
        self.assertFalse(function_info.is_aggregate)
        self.assertFalse(function_info.is_window)
        self.assertFalse(function_info.is_security_definer)
        self.assertEqual(function_info.volatility, "volatile")
        self.assertIsNone(function_info.comment)
        self.assertEqual(function_info.argument_types, [])
        self.assertEqual(function_info.argument_names, [])
        self.assertEqual(function_info.argument_defaults, [])
    
    def test_create_function_info_with_arguments(self):
        """Teste de criação do modelo FunctionInfo com argumentos."""
        
        function_info = FunctionInfo(
            name="test_function",
            schema="public",
            return_type="integer",
            definition="BEGIN RETURN $1 + $2; END;",
            language="plpgsql",
            argument_types=["integer", "integer"],
            argument_names=["a", "b"],
            argument_defaults=[None, "5"]
        )
        
        self.assertEqual(function_info.name, "test_function")
        self.assertEqual(function_info.argument_types, ["integer", "integer"])
        self.assertEqual(function_info.argument_names, ["a", "b"])
        self.assertEqual(function_info.argument_defaults, [None, "5"])
    
    def test_create_procedure_info(self):
        """Teste de criação do modelo FunctionInfo para um procedimento."""
        
        procedure_info = FunctionInfo(
            name="test_procedure",
            schema="public",
            return_type="void",
            definition="BEGIN PERFORM 1; END;",
            language="plpgsql",
            is_procedure=True
        )
        
        self.assertEqual(procedure_info.name, "test_procedure")
        self.assertEqual(procedure_info.return_type, "void")
        self.assertTrue(procedure_info.is_procedure)
    
    def test_create_function_info_with_other_attributes(self):
        """Teste de criação do modelo FunctionInfo com atributos adicionais."""
        
        function_info = FunctionInfo(
            name="test_function",
            schema="custom_schema",
            return_type="integer",
            definition="BEGIN RETURN 1; END;",
            language="plpgsql",
            is_aggregate=True,
            is_window=True,
            is_security_definer=True,
            volatility="immutable",
            comment="Test function"
        )
        
        self.assertEqual(function_info.schema, "custom_schema")
        self.assertTrue(function_info.is_aggregate)
        self.assertTrue(function_info.is_window)
        self.assertTrue(function_info.is_security_definer)
        self.assertEqual(function_info.volatility, "immutable")
        self.assertEqual(function_info.comment, "Test function")
    
    def test_invalid_function_info(self):
        """Teste de falha na criação do modelo FunctionInfo com valores inválidos."""
        
        # Testar nome vazio
        with self.assertRaises(ValidationError):
            FunctionInfo(
                name="",
                schema="public",
                return_type="integer",
                definition="BEGIN RETURN 1; END;",
                language="plpgsql",
            )
        
        # Testar schema vazio
        with self.assertRaises(ValidationError):
            FunctionInfo(
                name="test_function",
                schema="",
                return_type="integer",
                definition="BEGIN RETURN 1; END;",
                language="plpgsql",
            )
        
        # Testar return_type vazio
        with self.assertRaises(ValidationError):
            FunctionInfo(
                name="test_function",
                schema="public",
                return_type="",
                definition="BEGIN RETURN 1; END;",
                language="plpgsql",
            )
        
        # Testar definition vazio
        with self.assertRaises(ValidationError):
            FunctionInfo(
                name="test_function",
                schema="public",
                return_type="integer",
                definition="",
                language="plpgsql",
            )
        
        # Testar language vazio
        with self.assertRaises(ValidationError):
            FunctionInfo(
                name="test_function",
                schema="public",
                return_type="integer",
                definition="BEGIN RETURN 1; END;",
                language="",
            )


if __name__ == "__main__":
    unittest.main() 