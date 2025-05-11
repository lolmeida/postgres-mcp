"""
Testes para o QueryBuilder, com foco na conversão de filtros para SQL
"""

import unittest
from unittest.mock import patch

from postgres_mcp.repository.query_builder import QueryBuilder


class TestQueryBuilder(unittest.TestCase):
    """Testes para o QueryBuilder."""
    
    def setUp(self):
        """Configuração dos testes."""
        self.builder = QueryBuilder()
    
    def test_build_simple_select(self):
        """Testa a construção de uma consulta SELECT simples."""
        query, params = self.builder.build_select(
            table="users",
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\""
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {})
    
    def test_build_select_with_columns(self):
        """Testa a construção de uma consulta SELECT com colunas específicas."""
        query, params = self.builder.build_select(
            table="users",
            columns=["id", "name", "email"],
            schema="public"
        )
        
        expected_query = "SELECT \"id\", \"name\", \"email\" FROM public.\"users\""
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {})
    
    def test_build_select_with_simple_filter(self):
        """Testa a construção de uma consulta SELECT com filtro simples."""
        query, params = self.builder.build_select(
            table="users",
            filters={"id": 1},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE \"id\" = :p_0"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {"p_0": 1})
    
    def test_build_select_with_null_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de valor nulo."""
        query, params = self.builder.build_select(
            table="users",
            filters={"email": None},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE \"email\" IS NULL"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {})
    
    def test_build_select_with_multiple_simple_filters(self):
        """Testa a construção de uma consulta SELECT com múltiplos filtros simples."""
        query, params = self.builder.build_select(
            table="users",
            filters={"active": True, "age": 30},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE \"active\" = :p_0 AND \"age\" = :p_1"
        self.assertEqual(query, expected_query)
        self.assertEqual(len(params), 2)
        self.assertEqual(params["p_0"], True)
        self.assertEqual(params["p_1"], 30)
    
    def test_build_select_with_comparison_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de comparação."""
        query, params = self.builder.build_select(
            table="users",
            filters={"age": {"gt": 18, "lte": 65}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"age\" > :p_0 AND \"age\" <= :p_1)"
        self.assertEqual(query, expected_query)
        self.assertEqual(len(params), 2)
        self.assertEqual(params["p_0"], 18)
        self.assertEqual(params["p_1"], 65)
    
    def test_build_select_with_text_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de texto."""
        query, params = self.builder.build_select(
            table="users",
            filters={"name": {"like": "John%"}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"name\" LIKE :p_0)"
        self.assertEqual(query, expected_query)
        self.assertEqual(len(params), 1)
        self.assertEqual(params["p_0"], "John%")
    
    def test_build_select_with_list_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de lista."""
        query, params = self.builder.build_select(
            table="users",
            filters={"role": {"in": ["admin", "manager"]}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"role\" = ANY(:p_0))"
        self.assertEqual(query, expected_query)
        self.assertEqual(len(params), 1)
        self.assertEqual(params["p_0"], ["admin", "manager"])
    
    def test_build_select_with_null_operator_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de valor nulo usando operador."""
        query, params = self.builder.build_select(
            table="users",
            filters={"email": {"is": "null"}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"email\" IS NULL)"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {})
    
    def test_build_select_with_not_null_operator_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de valor não nulo usando operador."""
        query, params = self.builder.build_select(
            table="users",
            filters={"email": {"is": "not null"}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"email\" IS NOT NULL)"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {})
    
    def test_build_select_with_array_filter(self):
        """Testa a construção de uma consulta SELECT com filtro de array."""
        query, params = self.builder.build_select(
            table="users",
            filters={"tags": {"contains": ["active", "premium"]}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"tags\" @> :p_0)"
        self.assertEqual(query, expected_query)
        self.assertEqual(len(params), 1)
        # O tipo exato do parâmetro pode variar dependendo da implementação de prepare_array
    
    def test_build_select_with_jsonb_filter(self):
        """Testa a construção de uma consulta SELECT com filtro JSONB."""
        query, params = self.builder.build_select(
            table="users",
            filters={"data": {"jsonb_contains": {"settings": {"theme": "dark"}}}},
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" WHERE (\"data\" @> :p_0)"
        self.assertEqual(query, expected_query)
        self.assertEqual(len(params), 1)
        # O tipo exato do parâmetro pode variar dependendo da implementação de prepare_jsonb
    
    def test_build_select_with_order_limit_offset(self):
        """Testa a construção de uma consulta SELECT com ordenação, limite e offset."""
        query, params = self.builder.build_select(
            table="users",
            order_by="created_at",
            ascending=False,
            limit=10,
            offset=20,
            schema="public"
        )
        
        expected_query = "SELECT * FROM public.\"users\" ORDER BY \"created_at\" DESC LIMIT 10 OFFSET 20"
        self.assertEqual(query, expected_query)
        self.assertEqual(params, {})


if __name__ == "__main__":
    unittest.main() 