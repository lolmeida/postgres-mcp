"""
Testes de integração para operações CRUD do PostgreSQL MCP.
"""
import pytest
import uuid

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

class TestReadOperations:
    """Testes para operações de leitura."""
    
    async def test_read_table_all_records(self, mcp_client):
        """Testa a leitura de todos os registros de uma tabela."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "limit": 100
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        assert len(result["records"]) == 5  # Número de usuários inseridos no sample_data.sql
        
        # Verifica os campos esperados
        for record in result["records"]:
            assert "id" in record
            assert "name" in record
            assert "email" in record
            assert "active" in record
    
    async def test_read_table_with_filters(self, mcp_client):
        """Testa a leitura de registros filtrados."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {
                    "active": True
                }
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        assert len(result["records"]) == 3  # Número de usuários ativos
        
        for record in result["records"]:
            assert record["active"] is True
    
    async def test_read_table_with_limit_offset(self, mcp_client):
        """Testa a leitura com limit e offset."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "limit": 2,
                "offset": 1
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        assert len(result["records"]) == 2
        
        # O primeiro registro deve ser o ID 2 (considerando o offset 1)
        assert result["records"][0]["id"] == 2
    
    async def test_read_table_with_order_by(self, mcp_client):
        """Testa a leitura com ordenação."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "order_by": [{"field": "name", "direction": "desc"}]
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        
        # Verifica se a ordenação está correta (ordem decrescente por nome)
        names = [record["name"] for record in result["records"]]
        assert names == sorted(names, reverse=True)
    
    async def test_read_table_with_complex_filters(self, mcp_client):
        """Testa a leitura com filtros complexos."""
        result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "products",
                "filters": {
                    "price": {"gte": 20.00},
                    "active": True,
                    "categories": {"contains": "electronics"}
                }
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        
        for record in result["records"]:
            assert record["price"] >= 20.00
            assert record["active"] is True
            assert "electronics" in record["categories"]


class TestCreateOperations:
    """Testes para operações de criação."""
    
    async def test_create_record(self, mcp_client):
        """Testa a criação de um registro."""
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "New Test User",
                    "email": email,
                    "active": True
                }
            }
        )
        
        assert result["success"] is True
        assert "record" in result
        assert result["record"]["name"] == "New Test User"
        assert result["record"]["email"] == email
        assert result["record"]["active"] is True
        assert "id" in result["record"]
    
    async def test_create_record_with_returning(self, mcp_client):
        """Testa a criação de um registro com retorno de campos específicos."""
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "New Test User",
                    "email": email,
                    "active": True
                },
                "returning": ["id", "name"]
            }
        )
        
        assert result["success"] is True
        assert "record" in result
        assert "id" in result["record"]
        assert "name" in result["record"]
        assert "email" not in result["record"]  # Não solicitado em returning
    
    async def test_create_batch(self, mcp_client):
        """Testa a criação em lote de registros."""
        emails = [f"batch_{uuid.uuid4().hex[:8]}@example.com" for _ in range(3)]
        
        result = await mcp_client.execute_tool(
            "create_batch",
            {
                "table": "users",
                "data": [
                    {"name": "Batch User 1", "email": emails[0], "active": True},
                    {"name": "Batch User 2", "email": emails[1], "active": False},
                    {"name": "Batch User 3", "email": emails[2], "active": True}
                ]
            }
        )
        
        assert result["success"] is True
        assert "records" in result
        assert len(result["records"]) == 3
        
        # Verificar cada registro inserido
        for i, record in enumerate(result["records"]):
            assert record["name"] == f"Batch User {i+1}"
            assert record["email"] == emails[i]
            assert "id" in record


class TestUpdateOperations:
    """Testes para operações de atualização."""
    
    async def test_update_records(self, mcp_client):
        """Testa a atualização de registros."""
        # Primeiro insere um registro para teste
        email = f"update_{uuid.uuid4().hex[:8]}@example.com"
        create_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Update Test User",
                    "email": email,
                    "active": True
                }
            }
        )
        
        record_id = create_result["record"]["id"]
        
        # Atualiza o registro
        update_result = await mcp_client.execute_tool(
            "update_records",
            {
                "table": "users",
                "filters": {"id": record_id},
                "data": {
                    "name": "Updated User",
                    "active": False
                }
            }
        )
        
        assert update_result["success"] is True
        assert update_result["count"] == 1
        
        # Verifica se o registro foi atualizado corretamente
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"id": record_id}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 1
        assert read_result["records"][0]["name"] == "Updated User"
        assert read_result["records"][0]["active"] is False
        assert read_result["records"][0]["email"] == email  # Este campo não foi alterado
    
    async def test_update_multiple_records(self, mcp_client):
        """Testa a atualização de múltiplos registros."""
        # Atualiza todos os registros inativos para ativos
        update_result = await mcp_client.execute_tool(
            "update_records",
            {
                "table": "users",
                "filters": {"active": False},
                "data": {
                    "active": True
                }
            }
        )
        
        assert update_result["success"] is True
        assert update_result["count"] > 0
        
        # Verifica se todos os registros estão ativos
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"active": False}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 0


class TestDeleteOperations:
    """Testes para operações de exclusão."""
    
    async def test_delete_records(self, mcp_client):
        """Testa a exclusão de registros."""
        # Primeiro insere um registro para teste
        email = f"delete_{uuid.uuid4().hex[:8]}@example.com"
        create_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Delete Test User",
                    "email": email,
                    "active": True
                }
            }
        )
        
        record_id = create_result["record"]["id"]
        
        # Exclui o registro
        delete_result = await mcp_client.execute_tool(
            "delete_records",
            {
                "table": "users",
                "filters": {"id": record_id}
            }
        )
        
        assert delete_result["success"] is True
        assert delete_result["count"] == 1
        
        # Verifica se o registro foi excluído
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"id": record_id}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 0
    
    async def test_delete_multiple_records(self, mcp_client):
        """Testa a exclusão de múltiplos registros."""
        # Cria alguns registros para teste
        emails = [f"multi_delete_{uuid.uuid4().hex[:8]}@example.com" for _ in range(3)]
        
        await mcp_client.execute_tool(
            "create_batch",
            {
                "table": "users",
                "data": [
                    {"name": "Delete Test 1", "email": emails[0], "active": True},
                    {"name": "Delete Test 2", "email": emails[1], "active": True},
                    {"name": "Delete Test 3", "email": emails[2], "active": True}
                ]
            }
        )
        
        # Exclui os registros
        delete_result = await mcp_client.execute_tool(
            "delete_records",
            {
                "table": "users",
                "filters": {"email": {"in": emails}}
            }
        )
        
        assert delete_result["success"] is True
        assert delete_result["count"] == 3
        
        # Verifica se todos os registros foram excluídos
        for email in emails:
            read_result = await mcp_client.execute_tool(
                "read_table",
                {
                    "table": "users",
                    "filters": {"email": email}
                }
            )
            
            assert read_result["success"] is True
            assert len(read_result["records"]) == 0 