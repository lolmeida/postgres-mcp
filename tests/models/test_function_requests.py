"""
Testes para os modelos de requisição relacionados a funções.
"""

import unittest
from pydantic import ValidationError

from postgres_mcp.models.requests import (
    FunctionReference, ListFunctionsRequest, DescribeFunctionRequest,
    ExecuteFunctionRequest, CreateFunctionRequest, DropFunctionRequest
)


class TestFunctionReference(unittest.TestCase):
    """Testes para o modelo FunctionReference."""
    
    def test_create_function_reference(self):
        """Teste de criação do modelo FunctionReference com valores válidos."""
        
        reference = FunctionReference(
            function="test_function",
            schema="public"
        )
        
        self.assertEqual(reference.function, "test_function")
        self.assertEqual(reference.schema, "public")
    
    def test_invalid_function_reference(self):
        """Teste de falha na criação do modelo FunctionReference com valores inválidos."""
        
        # Testar função vazia
        with self.assertRaises(ValueError):
            FunctionReference(
                function="",
                schema="public"
            )
        
        # Testar schema vazio
        with self.assertRaises(ValueError):
            FunctionReference(
                function="test_function",
                schema=""
            )
        
        # Testar função ausente
        with self.assertRaises(ValidationError):
            FunctionReference(
                schema="public"
            )


class TestListFunctionsRequest(unittest.TestCase):
    """Testes para o modelo ListFunctionsRequest."""
    
    def test_create_list_functions_request(self):
        """Teste de criação do modelo ListFunctionsRequest com valores válidos."""
        
        request = ListFunctionsRequest(
            schema="public",
            include_procedures=True,
            include_aggregates=True
        )
        
        self.assertEqual(request.schema, "public")
        self.assertTrue(request.include_procedures)
        self.assertTrue(request.include_aggregates)
    
    def test_create_list_functions_request_with_defaults(self):
        """Teste de criação do modelo ListFunctionsRequest com valores padrão."""
        
        request = ListFunctionsRequest()
        
        self.assertEqual(request.schema, "public")
        self.assertTrue(request.include_procedures)
        self.assertTrue(request.include_aggregates)
    
    def test_create_list_functions_request_with_filters(self):
        """Teste de criação do modelo ListFunctionsRequest com filtros específicos."""
        
        request = ListFunctionsRequest(
            schema="custom_schema",
            include_procedures=False,
            include_aggregates=False
        )
        
        self.assertEqual(request.schema, "custom_schema")
        self.assertFalse(request.include_procedures)
        self.assertFalse(request.include_aggregates)


class TestDescribeFunctionRequest(unittest.TestCase):
    """Testes para o modelo DescribeFunctionRequest."""
    
    def test_create_describe_function_request(self):
        """Teste de criação do modelo DescribeFunctionRequest com valores válidos."""
        
        request = DescribeFunctionRequest(
            function="test_function",
            schema="public"
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
    
    def test_describe_function_request_inheritance(self):
        """Teste de herança do modelo DescribeFunctionRequest."""
        
        request = DescribeFunctionRequest(
            function="test_function",
            schema="custom_schema"
        )
        
        self.assertIsInstance(request, FunctionReference)
        self.assertEqual(request.schema, "custom_schema")


class TestExecuteFunctionRequest(unittest.TestCase):
    """Testes para o modelo ExecuteFunctionRequest."""
    
    def test_create_execute_function_request(self):
        """Teste de criação do modelo ExecuteFunctionRequest com valores válidos."""
        
        request = ExecuteFunctionRequest(
            function="test_function",
            schema="public",
            args=[1, 2, 3],
            named_args={"param1": "value1", "param2": "value2"}
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
        self.assertEqual(request.args, [1, 2, 3])
        self.assertEqual(request.named_args, {"param1": "value1", "param2": "value2"})
    
    def test_create_execute_function_request_with_defaults(self):
        """Teste de criação do modelo ExecuteFunctionRequest com valores padrão."""
        
        request = ExecuteFunctionRequest(
            function="test_function"
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
        self.assertIsNone(request.args)
        self.assertIsNone(request.named_args)
    
    def test_execute_function_request_inheritance(self):
        """Teste de herança do modelo ExecuteFunctionRequest."""
        
        request = ExecuteFunctionRequest(
            function="test_function",
            schema="custom_schema"
        )
        
        self.assertIsInstance(request, FunctionReference)
        self.assertEqual(request.schema, "custom_schema")


class TestCreateFunctionRequest(unittest.TestCase):
    """Testes para o modelo CreateFunctionRequest."""
    
    def test_create_function_request(self):
        """Teste de criação do modelo CreateFunctionRequest com valores válidos."""
        
        request = CreateFunctionRequest(
            function="test_function",
            schema="public",
            definition="BEGIN RETURN 1; END;",
            return_type="integer",
            argument_definitions=[
                {"name": "a", "type": "integer"},
                {"name": "b", "type": "integer", "default": "5"}
            ],
            language="plpgsql",
            is_procedure=False,
            replace=False,
            security_definer=False,
            volatility="volatile"
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
        self.assertEqual(request.definition, "BEGIN RETURN 1; END;")
        self.assertEqual(request.return_type, "integer")
        self.assertEqual(len(request.argument_definitions), 2)
        self.assertEqual(request.argument_definitions[0]["name"], "a")
        self.assertEqual(request.argument_definitions[1]["default"], "5")
        self.assertEqual(request.language, "plpgsql")
        self.assertFalse(request.is_procedure)
        self.assertFalse(request.replace)
        self.assertFalse(request.security_definer)
        self.assertEqual(request.volatility, "volatile")
    
    def test_create_function_request_with_defaults(self):
        """Teste de criação do modelo CreateFunctionRequest com valores padrão."""
        
        request = CreateFunctionRequest(
            function="test_function",
            definition="BEGIN RETURN 1; END;",
            return_type="integer"
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
        self.assertEqual(request.definition, "BEGIN RETURN 1; END;")
        self.assertEqual(request.return_type, "integer")
        self.assertIsNone(request.argument_definitions)
        self.assertEqual(request.language, "plpgsql")
        self.assertFalse(request.is_procedure)
        self.assertFalse(request.replace)
        self.assertFalse(request.security_definer)
        self.assertEqual(request.volatility, "volatile")
    
    def test_create_procedure_request(self):
        """Teste de criação do modelo CreateFunctionRequest para um procedimento."""
        
        request = CreateFunctionRequest(
            function="test_procedure",
            schema="public",
            definition="BEGIN PERFORM 1; END;",
            return_type="void",
            is_procedure=True,
            language="plpgsql"
        )
        
        self.assertEqual(request.function, "test_procedure")
        self.assertEqual(request.return_type, "void")
        self.assertTrue(request.is_procedure)
    
    def test_invalid_create_function_request(self):
        """Teste de falha na criação do modelo CreateFunctionRequest com valores inválidos."""
        
        # Testar definição vazia
        with self.assertRaises(ValueError):
            CreateFunctionRequest(
                function="test_function",
                definition="",
                return_type="integer"
            )
        
        # Testar volatilidade inválida
        with self.assertRaises(ValueError):
            CreateFunctionRequest(
                function="test_function",
                definition="BEGIN RETURN 1; END;",
                return_type="integer",
                volatility="invalid"
            )
        
        # Testar return_type ausente
        with self.assertRaises(ValidationError):
            CreateFunctionRequest(
                function="test_function",
                definition="BEGIN RETURN 1; END;"
            )


class TestDropFunctionRequest(unittest.TestCase):
    """Testes para o modelo DropFunctionRequest."""
    
    def test_create_drop_function_request(self):
        """Teste de criação do modelo DropFunctionRequest com valores válidos."""
        
        request = DropFunctionRequest(
            function="test_function",
            schema="public",
            if_exists=True,
            cascade=True,
            arg_types=["integer", "integer"]
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
        self.assertTrue(request.if_exists)
        self.assertTrue(request.cascade)
        self.assertEqual(request.arg_types, ["integer", "integer"])
    
    def test_create_drop_function_request_with_defaults(self):
        """Teste de criação do modelo DropFunctionRequest com valores padrão."""
        
        request = DropFunctionRequest(
            function="test_function"
        )
        
        self.assertEqual(request.function, "test_function")
        self.assertEqual(request.schema, "public")
        self.assertFalse(request.if_exists)
        self.assertFalse(request.cascade)
        self.assertIsNone(request.arg_types)
    
    def test_drop_function_request_inheritance(self):
        """Teste de herança do modelo DropFunctionRequest."""
        
        request = DropFunctionRequest(
            function="test_function",
            schema="custom_schema"
        )
        
        self.assertIsInstance(request, FunctionReference)
        self.assertEqual(request.schema, "custom_schema")


if __name__ == "__main__":
    unittest.main() 