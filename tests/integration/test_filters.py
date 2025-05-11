"""
Testes de integração para filtros do PostgreSQL MCP com banco de dados real.
"""
import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

class TestComparisonFilters:
    """Testes para filtros de comparação."""
    
    async def test_equal_filter(self, mcp_client):
        """Testa filtro de igualdade."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "id": 1
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) == 1
        assert result["records"][0]["id"] == 1
    
    async def test_not_equal_filter(self, mcp_client):
        """Testa filtro de desigualdade."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "id": {"neq": 1}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert record["id"] != 1
    
    async def test_greater_than_filter(self, mcp_client):
        """Testa filtro maior que."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"gt": 20.00}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["price"] > 20.00
    
    async def test_less_than_filter(self, mcp_client):
        """Testa filtro menor que."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"lt": 20.00}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["price"] < 20.00
    
    async def test_greater_than_equal_filter(self, mcp_client):
        """Testa filtro maior ou igual a."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"gte": 19.99}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["price"] >= 19.99
    
    async def test_less_than_equal_filter(self, mcp_client):
        """Testa filtro menor ou igual a."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"lte": 19.99}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["price"] <= 19.99
    
    async def test_between_filter(self, mcp_client):
        """Testa filtro entre valores."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"between": [10.00, 30.00]}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert 10.00 <= record["price"] <= 30.00


class TestTextFilters:
    """Testes para filtros de texto."""
    
    async def test_like_filter(self, mcp_client):
        """Testa filtro LIKE."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "name": {"like": "Test User%"}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert record["name"].startswith("Test User")
    
    async def test_ilike_filter(self, mcp_client):
        """Testa filtro ILIKE (case-insensitive)."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "name": {"ilike": "test user%"}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert record["name"].upper().startswith("TEST USER")
    
    async def test_starts_with_filter(self, mcp_client):
        """Testa filtro starts_with."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "name": {"starts_with": "Product"}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert record["name"].startswith("Product")
    
    async def test_ends_with_filter(self, mcp_client):
        """Testa filtro ends_with."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "name": {"ends_with": "1"}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert record["name"].endswith("1")
    
    async def test_contains_filter(self, mcp_client):
        """Testa filtro contains."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "description": {"contains": "product"}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert "product" in record["description"].lower()


class TestListFilters:
    """Testes para filtros de lista."""
    
    async def test_in_filter(self, mcp_client):
        """Testa filtro IN."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "id": {"in": [1, 2, 3]}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) <= 3
        for record in result["records"]:
            assert record["id"] in [1, 2, 3]
    
    async def test_not_in_filter(self, mcp_client):
        """Testa filtro NOT IN."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "id": {"not_in": [1, 2, 3]}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["id"] not in [1, 2, 3]


class TestNullFilters:
    """Testes para filtros de valores nulos."""
    
    async def test_is_null_filter(self, mcp_client):
        """Testa filtro IS NULL."""
        # Primeiro criar um registro com valor nulo
        await mcp_client.execute_tool(
            "update_records",
            {
                "table": "products",
                "filters": {"id": 1},
                "data": {"description": None}
            }
        )
        
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "description": {"is": None}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["description"] is None
    
    async def test_is_not_null_filter(self, mcp_client):
        """Testa filtro IS NOT NULL."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "description": {"is_not": None}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["description"] is not None


class TestArrayFilters:
    """Testes para filtros de arrays."""
    
    async def test_array_contains_filter(self, mcp_client):
        """Testa filtro contains para arrays."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "categories": {"contains": "electronics"}
                }
            }
        )
        
        assert result["success"] is True
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert "electronics" in record["categories"]
    
    async def test_array_contained_by_filter(self, mcp_client):
        """Testa filtro contained_by para arrays."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "categories": {"contained_by": ["electronics", "gadgets", "computers"]}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            # Todos os elementos do array de categorias devem estar na lista especificada
            assert all(cat in ["electronics", "gadgets", "computers"] for cat in record["categories"])
    
    async def test_array_overlaps_filter(self, mcp_client):
        """Testa filtro overlaps para arrays."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "categories": {"overlaps": ["home", "kitchen"]}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            # Pelo menos um elemento em comum
            assert any(cat in ["home", "kitchen"] for cat in record["categories"])


class TestJSONBFilters:
    """Testes para filtros de JSONB."""
    
    async def test_jsonb_contains_filter(self, mcp_client):
        """Testa filtro contains para JSONB."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "attributes": {"jsonb_contains": {"color": "black"}}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["attributes"].get("color") == "black"
    
    async def test_jsonb_has_key_filter(self, mcp_client):
        """Testa filtro has_key para JSONB."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "attributes": {"has_key": "material"}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert "material" in record["attributes"]
    
    async def test_jsonb_path_filter(self, mcp_client):
        """Testa filtro de caminho para JSONB."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "attributes->color": "black"
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["attributes"].get("color") == "black"
    
    async def test_jsonb_path_nested_filter(self, mcp_client):
        """Testa filtro de caminho aninhado para JSONB."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "attributes->dimensions->width": 10
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert "dimensions" in record["attributes"]
            assert record["attributes"]["dimensions"].get("width") == 10


class TestComplexFilters:
    """Testes para filtros complexos combinados."""
    
    async def test_and_filters(self, mcp_client):
        """Testa filtros combinados com AND implícito."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"gte": 10.00},
                    "active": True,
                    "inventory": {"gt": 0}
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["price"] >= 10.00
            assert record["active"] is True
            assert record["inventory"] > 0
    
    async def test_or_filters(self, mcp_client):
        """Testa filtros combinados com OR explícito."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "or": [
                        {"price": {"lt": 10.00}},
                        {"price": {"gt": 40.00}}
                    ]
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["price"] < 10.00 or record["price"] > 40.00
    
    async def test_and_or_combined_filters(self, mcp_client):
        """Testa filtros combinados com AND e OR aninhados."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "active": True,
                    "or": [
                        {"categories": {"contains": "electronics"}},
                        {"price": {"gte": 25.00}}
                    ]
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["active"] is True
            assert "electronics" in record["categories"] or record["price"] >= 25.00
    
    async def test_not_filter(self, mcp_client):
        """Testa o operador NOT."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "not": {
                        "active": False
                    }
                }
            }
        )
        
        assert result["success"] is True
        for record in result["records"]:
            assert record["active"] is not False 