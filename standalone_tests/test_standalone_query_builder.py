#!/usr/bin/env python3

import unittest
import pytest
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator

# Marcar todos os testes neste módulo como standalone
pytestmark = pytest.mark.standalone

# ---- Filter Models Implementation ----

class ComparisonFilter(BaseModel):
    """Filtro de comparação."""
    eq: Optional[Any] = Field(None, description="Igual a")
    gt: Optional[Any] = Field(None, description="Maior que")
    lt: Optional[Any] = Field(None, description="Menor que")
    gte: Optional[Any] = Field(None, description="Maior ou igual a")
    lte: Optional[Any] = Field(None, description="Menor ou igual a")
    ne: Optional[Any] = Field(None, description="Diferente de")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in ["eq", "gt", "lt", "gte", "lte", "ne"]):
            raise ValueError("Pelo menos um operador de comparação deve ser fornecido")
        return data


class ListFilter(BaseModel):
    """Filtro de lista."""
    in_: Optional[List[Any]] = Field(None, alias="in", description="In list")
    nin: Optional[List[Any]] = Field(None, description="Not in list")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        
        # Check for 'in_' field as well as 'in' for direct instantiation
        has_in = "in" in data or "in_" in data
        has_nin = "nin" in data
        
        if not (has_in or has_nin):
            raise ValueError("Pelo menos um operador de lista deve ser fornecido")
        
        # Handle 'in_' to 'in' conversion for direct instantiation
        if "in_" in data and "in" not in data:
            data["in"] = data.pop("in_")
        
        return data


class NullFilter(BaseModel):
    """Filtro para valores nulos."""
    is_: str = Field(alias="is", description="IS NULL ou IS NOT NULL")
    
    @model_validator(mode='before')
    @classmethod
    def validate_is_value(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        
        # Handle 'is_' to 'is' conversion for direct instantiation
        if "is_" in data and "is" not in data:
            data["is"] = data.pop("is_")
        
        is_value = data.get("is")
        if is_value is not None and is_value != "null" and is_value != "not null":
            raise ValueError("Valor de 'is' deve ser 'null' ou 'not null'")
        
        return data


# ---- Query Builder Implementation ----

class QueryBuilder:
    """Simplified QueryBuilder for testing."""
    
    def __init__(self):
        self.param_counter = 0
    
    def build_select(
        self,
        table: str,
        schema: str = "public",
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Builds a SELECT query.
        
        Args:
            table: Table name
            schema: Schema name
            columns: Columns to select
            filters: Query filters
            order_by: Column to order by
            ascending: Order direction
            limit: Result limit
            offset: Result offset
            
        Returns:
            Tuple of (query_string, params)
        """
        params = {}
        
        # Build SELECT clause
        if columns:
            select_clause = f"SELECT {', '.join([self._quote_identifier(col) for col in columns])}"
        else:
            select_clause = "SELECT *"
        
        # Build FROM clause
        from_clause = f"FROM {schema}.{self._quote_identifier(table)}"
        
        # Build WHERE clause
        where_clause = ""
        if filters:
            filter_expressions = []
            for field, value in filters.items():
                expr = self._process_filter(field, value, params)
                if expr:
                    filter_expressions.append(expr)
            
            if filter_expressions:
                where_clause = f"WHERE {' AND '.join(filter_expressions)}"
        
        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            direction = "ASC" if ascending else "DESC"
            order_clause = f"ORDER BY {self._quote_identifier(order_by)} {direction}"
        
        # Build LIMIT and OFFSET clauses
        limit_clause = f"LIMIT {limit}" if limit is not None else ""
        offset_clause = f"OFFSET {offset}" if offset is not None else ""
        
        # Combine all clauses
        query_parts = [
            select_clause,
            from_clause,
            where_clause,
            order_clause,
            limit_clause,
            offset_clause
        ]
        
        # Remove empty clauses and join with spaces
        query = " ".join([part for part in query_parts if part])
        
        return query, params
    
    def _process_filter(self, field: str, value: Any, params: Dict[str, Any]) -> Optional[str]:
        """Process a filter and return the SQL expression."""
        if value is None:
            return f"{self._quote_identifier(field)} IS NULL"
        
        if isinstance(value, dict):
            # Check for filter objects
            if "in" in value or "in_" in value:
                # Handle ListFilter
                in_values = value.get("in") or value.get("in_")
                if in_values is not None:
                    param_name = f"p_{self.param_counter}"
                    self.param_counter += 1
                    params[param_name] = in_values
                    return f"{self._quote_identifier(field)} = ANY(:{param_name})"
            
            if "eq" in value:
                # Handle ComparisonFilter with eq
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                params[param_name] = value["eq"]
                return f"{self._quote_identifier(field)} = :{param_name}"
            
            if "is" in value:
                # Handle NullFilter
                is_value = value["is"]
                if is_value == "null":
                    return f"{self._quote_identifier(field)} IS NULL"
                elif is_value == "not null":
                    return f"{self._quote_identifier(field)} IS NOT NULL"
            
            # For simplicity, we're just handling a few key filter types here
            return "1=1"  # Default to true if we don't handle the filter
        else:
            # Simple equality filter
            param_name = f"p_{self.param_counter}"
            self.param_counter += 1
            params[param_name] = value
            return f"{self._quote_identifier(field)} = :{param_name}"
    
    def _quote_identifier(self, identifier: str) -> str:
        """Quote an SQL identifier."""
        return f'"{identifier}"'


# ---- Tests ----

class TestQueryBuilderWithFilters(unittest.TestCase):
    """Test QueryBuilder with filter models."""
    
    def setUp(self):
        self.builder = QueryBuilder()
    
    def test_comparison_filter(self):
        """Test QueryBuilder with ComparisonFilter."""
        print("\n=== TESTING QUERY BUILDER WITH COMPARISON FILTER ===")
        
        # Using direct filter object
        filter_obj = ComparisonFilter(eq=10)
        query, params = self.builder.build_select(
            table="users",
            filters={"age": filter_obj.model_dump(exclude_none=True)}
        )
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        self.assertIn('"age" = :p_0', query)
        self.assertEqual(params["p_0"], 10)
        
        # Using dictionary representation
        query, params = self.builder.build_select(
            table="users",
            filters={"age": {"eq": 10}}
        )
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        self.assertIn('"age" = :p_1', query)
        self.assertEqual(params["p_1"], 10)
    
    def test_list_filter_direct(self):
        """Test QueryBuilder with ListFilter using direct object."""
        print("\n=== TESTING QUERY BUILDER WITH LIST FILTER (DIRECT) ===")
        
        # Using direct filter object with in_
        filter_obj = ListFilter(in_=[1, 2, 3])
        print(f"Filter object: {filter_obj}")
        print(f"Model dump: {filter_obj.model_dump()}")
        print(f"Model dump (exclude_none): {filter_obj.model_dump(exclude_none=True)}")
        print(f"Model dump (by_alias): {filter_obj.model_dump(by_alias=True)}")
        print(f"Model dump (by_alias, exclude_none): {filter_obj.model_dump(by_alias=True, exclude_none=True)}")
        
        query, params = self.builder.build_select(
            table="users",
            filters={"role_id": filter_obj.model_dump(by_alias=True, exclude_none=True)}
        )
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        self.assertIn('"role_id" = ANY(:p_0)', query)
        self.assertEqual(params["p_0"], [1, 2, 3])
    
    def test_list_filter_dict(self):
        """Test QueryBuilder with ListFilter using dictionary."""
        print("\n=== TESTING QUERY BUILDER WITH LIST FILTER (DICT) ===")
        
        # Using dictionary representation
        query, params = self.builder.build_select(
            table="users",
            filters={"role_id": {"in": [1, 2, 3]}}
        )
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        self.assertIn('"role_id" = ANY(:p_0)', query)
        self.assertEqual(params["p_0"], [1, 2, 3])
    
    def test_null_filter(self):
        """Test QueryBuilder with NullFilter."""
        print("\n=== TESTING QUERY BUILDER WITH NULL FILTER ===")
        
        # Using direct filter object
        filter_obj = NullFilter(is_="null")
        query, params = self.builder.build_select(
            table="users",
            filters={"last_login": filter_obj.model_dump(by_alias=True)}
        )
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        self.assertIn('"last_login" IS NULL', query)
        
        # Using dictionary representation
        query, params = self.builder.build_select(
            table="users",
            filters={"last_login": {"is": "not null"}}
        )
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        self.assertIn('"last_login" IS NOT NULL', query)


if __name__ == "__main__":
    unittest.main() 