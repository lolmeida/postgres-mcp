"""
Testes de integração para recursos específicos do PostgreSQL.
"""
import pytest
import asyncio

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

class TestViews:
    """Testes para operações com views."""
    
    async def test_create_and_query_view(self, mcp_client, postgres_connection):
        """Testa a criação e consulta de uma view."""
        # Primeiro, cria uma view via SQL direto
        await postgres_connection.execute('''
            CREATE OR REPLACE VIEW public.active_users AS
            SELECT * FROM public.users WHERE active = true;
        ''')
        
        # Agora, consulta a view via MCP
        result = await mcp_client.execute_tool(
            "execute_query",
            {
                "query": "SELECT * FROM active_users",
                "params": []
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        assert len(result["records"]) > 0
        for record in result["records"]:
            assert record["active"] is True
    
    async def test_list_views(self, mcp_client, postgres_connection):
        """Testa a listagem de views."""
        # Primeiro, cria uma segunda view para testar
        await postgres_connection.execute('''
            CREATE OR REPLACE VIEW public.expensive_products AS
            SELECT * FROM public.products WHERE price > 25.00;
        ''')
        
        # Consulta as views via MCP
        result = await mcp_client.execute_tool(
            "list_views",
            {
                "schema": "public"
            }
        )
        
        assert result["success"] is True
        assert "views" in result
        
        # Verifica se as views criadas estão na lista
        view_names = [view["name"] for view in result["views"]]
        assert "active_users" in view_names
        assert "expensive_products" in view_names
    
    async def test_describe_view(self, mcp_client):
        """Testa a descrição de uma view."""
        result = await mcp_client.execute_tool(
            "describe_view",
            {
                "view": "active_users",
                "schema": "public"
            }
        )
        
        assert result["success"] is True
        assert "definition" in result
        assert "columns" in result
        
        # Verifica a definição da view
        assert "SELECT" in result["definition"]
        assert "WHERE active = true" in result["definition"]
        
        # Verifica colunas
        columns = {col["name"]: col for col in result["columns"]}
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns
        assert "active" in columns
    
    async def test_drop_view(self, mcp_client):
        """Testa a exclusão de uma view."""
        result = await mcp_client.execute_tool(
            "drop_view",
            {
                "view": "expensive_products",
                "schema": "public"
            }
        )
        
        assert result["success"] is True
        
        # Verifica se a view foi removida
        list_result = await mcp_client.execute_tool(
            "list_views",
            {
                "schema": "public"
            }
        )
        
        view_names = [view["name"] for view in list_result["views"]]
        assert "expensive_products" not in view_names


class TestFunctions:
    """Testes para funções armazenadas."""
    
    async def test_create_and_execute_function(self, mcp_client, postgres_connection):
        """Testa a criação e execução de uma função."""
        # Primeiro, cria uma função via SQL
        await postgres_connection.execute('''
            CREATE OR REPLACE FUNCTION public.sum_two_numbers(a integer, b integer)
            RETURNS integer AS $$
            BEGIN
                RETURN a + b;
            END;
            $$ LANGUAGE plpgsql;
        ''')
        
        # Executa a função via MCP
        result = await mcp_client.execute_tool(
            "execute_function",
            {
                "function": "sum_two_numbers",
                "schema": "public",
                "args": [10, 20]
            }
        )
        
        assert result["success"] is True
        assert "result" in result
        assert result["result"] == 30
    
    async def test_list_functions(self, mcp_client, postgres_connection):
        """Testa a listagem de funções."""
        # Cria uma segunda função para teste
        await postgres_connection.execute('''
            CREATE OR REPLACE FUNCTION public.multiply_two_numbers(a integer, b integer)
            RETURNS integer AS $$
            BEGIN
                RETURN a * b;
            END;
            $$ LANGUAGE plpgsql;
        ''')
        
        # Lista as funções via MCP
        result = await mcp_client.execute_tool(
            "list_functions",
            {
                "schema": "public"
            }
        )
        
        assert result["success"] is True
        assert "functions" in result
        
        function_names = [func["name"] for func in result["functions"]]
        assert "sum_two_numbers" in function_names
        assert "multiply_two_numbers" in function_names
    
    async def test_drop_function(self, mcp_client):
        """Testa a exclusão de uma função."""
        result = await mcp_client.execute_tool(
            "drop_function",
            {
                "function": "sum_two_numbers",
                "schema": "public",
                "args": ["integer", "integer"]
            }
        )
        
        assert result["success"] is True
        
        # Verifica se a função foi removida
        list_result = await mcp_client.execute_tool(
            "list_functions",
            {
                "schema": "public"
            }
        )
        
        function_names = [func["name"] for func in list_result["functions"]]
        assert "sum_two_numbers" not in function_names


class TestCTEs:
    """Testes para Common Table Expressions (CTEs)."""
    
    async def test_execute_query_with_cte(self, mcp_client):
        """Testa execução de consulta com CTE."""
        result = await mcp_client.execute_tool(
            "execute_query",
            {
                "query": """
                WITH active_products AS (
                    SELECT * FROM products WHERE active = true
                )
                SELECT * FROM active_products WHERE price > 20.00
                ORDER BY price DESC;
                """,
                "params": []
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        
        for record in result["records"]:
            assert record["active"] is True
            assert record["price"] > 20.00


class TestWindowFunctions:
    """Testes para Window Functions."""
    
    async def test_execute_query_with_window_function(self, mcp_client):
        """Testa execução de consulta com Window Function."""
        result = await mcp_client.execute_tool(
            "execute_query",
            {
                "query": """
                SELECT 
                    name, 
                    price,
                    RANK() OVER (ORDER BY price DESC) as price_rank
                FROM products
                WHERE active = true;
                """,
                "params": []
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        
        # Verificar se o ranking está correto
        previous_rank = 0
        previous_price = float('inf')
        
        for record in result["records"]:
            current_rank = record["price_rank"]
            current_price = record["price"]
            
            # Se o preço mudar, o rank deve aumentar
            if current_price < previous_price:
                assert current_rank > previous_rank
            
            previous_rank = current_rank
            previous_price = current_price


class TestSpecialQueries:
    """Testes para consultas especiais do PostgreSQL."""
    
    async def test_subquery(self, mcp_client):
        """Testa consultas com subconsultas."""
        result = await mcp_client.execute_tool(
            "execute_query",
            {
                "query": """
                SELECT u.* 
                FROM users u
                WHERE u.id IN (
                    SELECT DISTINCT o.user_id 
                    FROM orders o
                    WHERE o.status = 'completed'
                );
                """,
                "params": []
            }
        )
        
        assert result["success"] is True
        assert "records" in result
    
    async def test_lateral_join(self, mcp_client, postgres_connection):
        """Testa consultas com LATERAL JOIN."""
        # Esse tipo de consulta é mais avançado - usado para relacionamentos 1:N
        result = await mcp_client.execute_tool(
            "execute_query",
            {
                "query": """
                SELECT 
                    u.name as user_name,
                    o.id as order_id, 
                    o.total_amount
                FROM users u
                LEFT JOIN LATERAL (
                    SELECT * FROM orders 
                    WHERE user_id = u.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) o ON true
                WHERE u.active = true;
                """,
                "params": []
            }
        )
        
        assert result["success"] is True
        assert "records" in result
    
    async def test_json_functions(self, mcp_client):
        """Testa funções para manipulação de JSON/JSONB."""
        result = await mcp_client.execute_tool(
            "execute_query",
            {
                "query": """
                SELECT 
                    id, 
                    name,
                    attributes,
                    attributes->'color' as color,
                    jsonb_object_keys(attributes) as attribute_key
                FROM products
                WHERE attributes ? 'color'
                LIMIT 2;
                """,
                "params": []
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        
        for record in result["records"]:
            assert record["color"] is not None 