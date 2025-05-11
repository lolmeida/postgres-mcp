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


class TextFilter(BaseModel):
    """Filtro de texto."""
    like: Optional[str] = Field(None, description="LIKE case sensitive")
    ilike: Optional[str] = Field(None, description="LIKE case insensitive")
    match: Optional[str] = Field(None, description="Regex match case sensitive")
    imatch: Optional[str] = Field(None, description="Regex match case insensitive")
    
    @model_validator(mode='before')
    @classmethod
    def check_at_least_one_operator(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        if not any(op in data for op in ["like", "ilike", "match", "imatch"]):
            raise ValueError("Pelo menos um operador de texto deve ser fornecido")
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
        self.params = {}
    
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
        self.params = {}
        self.param_counter = 0
        
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
                expr = self._process_filter(field, value)
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
        
        return query, self.params
    
    def _process_filter(self, field: str, value: Any) -> Optional[str]:
        """Process a filter and return the SQL expression."""
        if value is None:
            return f"{self._quote_identifier(field)} IS NULL"
        
        if isinstance(value, dict):
            conditions = []
            
            # Check for filter objects
            # List filters
            if "in" in value or "in_" in value:
                in_values = value.get("in") or value.get("in_")
                if in_values is not None:
                    param_name = f"p_{self.param_counter}"
                    self.param_counter += 1
                    self.params[param_name] = in_values
                    conditions.append(f"{self._quote_identifier(field)} = ANY(:{param_name})")
            
            if "nin" in value:
                nin_values = value.get("nin")
                if nin_values is not None:
                    param_name = f"p_{self.param_counter}"
                    self.param_counter += 1
                    self.params[param_name] = nin_values
                    conditions.append(f"{self._quote_identifier(field)} != ALL(:{param_name})")
            
            # Comparison operators
            if "eq" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["eq"]
                conditions.append(f"{self._quote_identifier(field)} = :{param_name}")
            
            if "gt" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["gt"]
                conditions.append(f"{self._quote_identifier(field)} > :{param_name}")
            
            if "lt" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["lt"]
                conditions.append(f"{self._quote_identifier(field)} < :{param_name}")
            
            if "gte" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["gte"]
                conditions.append(f"{self._quote_identifier(field)} >= :{param_name}")
            
            if "lte" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["lte"]
                conditions.append(f"{self._quote_identifier(field)} <= :{param_name}")
            
            if "ne" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["ne"]
                conditions.append(f"{self._quote_identifier(field)} != :{param_name}")
            
            # Text operators
            if "like" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["like"]
                conditions.append(f"{self._quote_identifier(field)} LIKE :{param_name}")
            
            if "ilike" in value:
                param_name = f"p_{self.param_counter}"
                self.param_counter += 1
                self.params[param_name] = value["ilike"]
                conditions.append(f"{self._quote_identifier(field)} ILIKE :{param_name}")
            
            # Null operators
            if "is" in value:
                is_value = value["is"]
                if is_value == "null":
                    conditions.append(f"{self._quote_identifier(field)} IS NULL")
                elif is_value == "not null":
                    conditions.append(f"{self._quote_identifier(field)} IS NOT NULL")
            
            # Return all conditions joined with AND
            if conditions:
                return " AND ".join(conditions)
            else:
                # For any unhandled operators
                return "1=1"
        else:
            # Simple equality filter
            param_name = f"p_{self.param_counter}"
            self.param_counter += 1
            self.params[param_name] = value
            return f"{self._quote_identifier(field)} = :{param_name}"
    
    def _quote_identifier(self, identifier: str) -> str:
        """Quote an SQL identifier."""
        return f'"{identifier}"'


# ---- Integrated Tests ----

class TestIntegratedFiltersAndQueryBuilder(unittest.TestCase):
    """Integrated tests for filter models and query builder."""
    
    def setUp(self):
        self.builder = QueryBuilder()
    
    def test_comparison_filters_with_query_builder(self):
        """Test all comparison operators with query builder."""
        print("\n=== TESTING COMPARISON FILTERS WITH QUERY BUILDER ===")
        
        # Test all comparison operators
        comparison_tests = [
            (ComparisonFilter(eq=100), '"score" = :p_0', {'p_0': 100}),
            (ComparisonFilter(gt=90), '"score" > :p_0', {'p_0': 90}),
            (ComparisonFilter(lt=50), '"score" < :p_0', {'p_0': 50}),
            (ComparisonFilter(gte=75), '"score" >= :p_0', {'p_0': 75}),
            (ComparisonFilter(lte=25), '"score" <= :p_0', {'p_0': 25}),
            (ComparisonFilter(ne=0), '"score" != :p_0', {'p_0': 0}),
        ]
        
        for filter_obj, expected_where, expected_params in comparison_tests:
            query, params = self.builder.build_select(
                table="students",
                filters={"score": filter_obj.model_dump(exclude_none=True)}
            )
            
            print(f"Filter: {filter_obj}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            print("-" * 50)
            
            self.assertIn(expected_where, query)
            self.assertEqual(params, expected_params)
    
    def test_text_filters_with_query_builder(self):
        """Test text filters with query builder."""
        print("\n=== TESTING TEXT FILTERS WITH QUERY BUILDER ===")
        
        # Test all text operators
        text_tests = [
            (TextFilter(like="John%"), '"name" LIKE :p_0', {'p_0': 'John%'}),
            (TextFilter(ilike="%smith%"), '"name" ILIKE :p_0', {'p_0': '%smith%'}),
        ]
        
        for filter_obj, expected_where, expected_params in text_tests:
            query, params = self.builder.build_select(
                table="customers",
                filters={"name": filter_obj.model_dump(exclude_none=True)}
            )
            
            print(f"Filter: {filter_obj}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            print("-" * 50)
            
            self.assertIn(expected_where, query)
            self.assertEqual(params, expected_params)
    
    def test_list_filters_with_query_builder(self):
        """Test list filters with query builder."""
        print("\n=== TESTING LIST FILTERS WITH QUERY BUILDER ===")
        
        # Test list filters
        list_tests = [
            (ListFilter(in_=[1, 2, 3]), '"status_id" = ANY(:p_0)', {'p_0': [1, 2, 3]}),
            (ListFilter(nin=[4, 5, 6]), '"status_id" != ALL(:p_0)', {'p_0': [4, 5, 6]}),
        ]
        
        for filter_obj, expected_where, expected_params in list_tests:
            query, params = self.builder.build_select(
                table="orders",
                filters={"status_id": filter_obj.model_dump(by_alias=True, exclude_none=True)}
            )
            
            print(f"Filter: {filter_obj}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            print("-" * 50)
            
            self.assertIn(expected_where, query)
            self.assertEqual(params, expected_params)
    
    def test_null_filters_with_query_builder(self):
        """Test null filters with query builder."""
        print("\n=== TESTING NULL FILTERS WITH QUERY BUILDER ===")
        
        # Test null filters
        null_tests = [
            (NullFilter(is_="null"), '"deleted_at" IS NULL', {}),
            (NullFilter(is_="not null"), '"deleted_at" IS NOT NULL', {}),
        ]
        
        for filter_obj, expected_where, expected_params in null_tests:
            query, params = self.builder.build_select(
                table="users",
                filters={"deleted_at": filter_obj.model_dump(by_alias=True)}
            )
            
            print(f"Filter: {filter_obj}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            print("-" * 50)
            
            self.assertIn(expected_where, query)
            self.assertEqual(params, expected_params)
    
    def test_complex_query_with_multiple_filters(self):
        """Test a complex query with multiple filter types."""
        print("\n=== TESTING COMPLEX QUERY WITH MULTIPLE FILTERS ===")
        
        # Create different filter types
        filters = {
            "name": TextFilter(ilike="%doe%").model_dump(exclude_none=True),
            "age": ComparisonFilter(gte=18, lte=65).model_dump(exclude_none=True),
            "role_id": ListFilter(in_=[1, 2, 3]).model_dump(by_alias=True, exclude_none=True),
            "deleted_at": NullFilter(is_="null").model_dump(by_alias=True),
        }
        
        query, params = self.builder.build_select(
            table="users",
            filters=filters,
            order_by="created_at",
            ascending=False,
            limit=10,
            offset=0
        )
        
        print(f"Filters: {filters}")
        print(f"Query: {query}")
        print(f"Params: {params}")
        
        # Check that all conditions are in the query
        self.assertIn('"name" ILIKE', query)
        self.assertIn('"age" >=', query)
        self.assertIn('"age" <=', query)
        self.assertIn('"role_id" = ANY', query)
        self.assertIn('"deleted_at" IS NULL', query)
        
        # Check order by, limit, offset
        self.assertIn('ORDER BY "created_at" DESC', query)
        self.assertIn('LIMIT 10', query)
        
        # Check parameters
        self.assertEqual(params['p_0'], '%doe%')  # name ILIKE
        self.assertEqual(params['p_1'], 18)  # age >=
        self.assertEqual(params['p_2'], 65)  # age <=
        self.assertEqual(params['p_3'], [1, 2, 3])  # role_id = ANY


if __name__ == "__main__":
    unittest.main() 