"""
Testes de integração para operações de transação do PostgreSQL MCP.
"""
import pytest
import uuid

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

class TestTransactions:
    """Testes para operações de transação."""
    
    async def test_transaction_commit(self, mcp_client):
        """Testa a execução de uma transação com commit."""
        # Iniciar transação
        tx_result = await mcp_client.execute_tool(
            "begin_transaction",
            {}
        )
        
        assert tx_result["success"] is True
        assert "transaction_id" in tx_result
        
        tx_id = tx_result["transaction_id"]
        
        # Inserir um usuário na transação
        email = f"tx_commit_{uuid.uuid4().hex[:8]}@example.com"
        create_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Transaction User",
                    "email": email,
                    "active": True
                },
                "transaction_id": tx_id
            }
        )
        
        assert create_result["success"] is True
        assert "id" in create_result["record"]
        
        user_id = create_result["record"]["id"]
        
        # Commit da transação
        commit_result = await mcp_client.execute_tool(
            "commit_transaction",
            {
                "transaction_id": tx_id
            }
        )
        
        assert commit_result["success"] is True
        
        # Verificar se o registro foi persistido
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"id": user_id}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 1
        assert read_result["records"][0]["email"] == email
    
    async def test_transaction_rollback(self, mcp_client):
        """Testa a execução de uma transação com rollback."""
        # Iniciar transação
        tx_result = await mcp_client.execute_tool(
            "begin_transaction",
            {}
        )
        
        assert tx_result["success"] is True
        tx_id = tx_result["transaction_id"]
        
        # Inserir um usuário na transação
        email = f"tx_rollback_{uuid.uuid4().hex[:8]}@example.com"
        create_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Rollback User",
                    "email": email,
                    "active": True
                },
                "transaction_id": tx_id
            }
        )
        
        assert create_result["success"] is True
        user_id = create_result["record"]["id"]
        
        # Rollback da transação
        rollback_result = await mcp_client.execute_tool(
            "rollback_transaction",
            {
                "transaction_id": tx_id
            }
        )
        
        assert rollback_result["success"] is True
        
        # Verificar que o registro não foi persistido
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"email": email}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 0
    
    async def test_transaction_isolation(self, mcp_client, postgres_connection):
        """Testa o isolamento de transações."""
        # Iniciar transação
        tx_result = await mcp_client.execute_tool(
            "begin_transaction",
            {}
        )
        
        assert tx_result["success"] is True
        tx_id = tx_result["transaction_id"]
        
        # Inserir um usuário na transação
        email = f"tx_isolation_{uuid.uuid4().hex[:8]}@example.com"
        create_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Isolation User",
                    "email": email,
                    "active": True
                },
                "transaction_id": tx_id
            }
        )
        
        assert create_result["success"] is True
        
        # Verificar que o registro é visível dentro da transação
        tx_read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"email": email},
                "transaction_id": tx_id
            }
        )
        
        assert tx_read_result["success"] is True
        assert len(tx_read_result["records"]) == 1
        
        # Verificar que o registro não é visível fora da transação
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"email": email}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 0
        
        # Commit da transação
        await mcp_client.execute_tool(
            "commit_transaction",
            {
                "transaction_id": tx_id
            }
        )
        
        # Agora o registro deve ser visível
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"email": email}
            }
        )
        
        assert read_result["success"] is True
        assert len(read_result["records"]) == 1
    
    async def test_multiple_operations_in_transaction(self, mcp_client):
        """Testa a execução de múltiplas operações em uma única transação."""
        # Iniciar transação
        tx_result = await mcp_client.execute_tool(
            "begin_transaction",
            {}
        )
        
        assert tx_result["success"] is True
        tx_id = tx_result["transaction_id"]
        
        # 1. Inserir um usuário
        email = f"tx_multi_{uuid.uuid4().hex[:8]}@example.com"
        user_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Multi Op User",
                    "email": email,
                    "active": True
                },
                "transaction_id": tx_id
            }
        )
        
        user_id = user_result["record"]["id"]
        
        # 2. Inserir um pedido para este usuário
        order_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "orders",
                "data": {
                    "user_id": user_id,
                    "total_amount": 99.99,
                    "status": "pending",
                    "items": [
                        {"product_id": 1, "quantity": 1, "price": 19.99},
                        {"product_id": 2, "quantity": 2, "price": 29.99}
                    ]
                },
                "transaction_id": tx_id
            }
        )
        
        order_id = order_result["record"]["id"]
        
        # 3. Atualizar o status do pedido
        await mcp_client.execute_tool(
            "update_records",
            {
                "table": "orders",
                "filters": {"id": order_id},
                "data": {"status": "confirmed"},
                "transaction_id": tx_id
            }
        )
        
        # Commit da transação
        await mcp_client.execute_tool(
            "commit_transaction",
            {
                "transaction_id": tx_id
            }
        )
        
        # Verificar se todas as operações foram persistidas
        order_read = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "orders",
                "filters": {"id": order_id}
            }
        )
        
        assert order_read["success"] is True
        assert len(order_read["records"]) == 1
        assert order_read["records"][0]["user_id"] == user_id
        assert order_read["records"][0]["status"] == "confirmed"
    
    async def test_transaction_error_handling(self, mcp_client):
        """Testa o tratamento de erros em transações."""
        # Iniciar transação
        tx_result = await mcp_client.execute_tool(
            "begin_transaction",
            {}
        )
        
        tx_id = tx_result["transaction_id"]
        
        # Operação 1: inserir usuário (sucesso)
        email = f"tx_error_{uuid.uuid4().hex[:8]}@example.com"
        await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Error Test User",
                    "email": email,
                    "active": True
                },
                "transaction_id": tx_id
            }
        )
        
        # Operação 2: tentativa de violar restrição de unicidade (deve falhar)
        error_result = await mcp_client.execute_tool(
            "create_record",
            {
                "table": "users",
                "data": {
                    "name": "Error Duplicate User",
                    "email": email,  # Mesmo email, deve violar restrição
                    "active": True
                },
                "transaction_id": tx_id
            }
        )
        
        assert error_result["success"] is False
        
        # Fazer rollback da transação
        await mcp_client.execute_tool(
            "rollback_transaction",
            {
                "transaction_id": tx_id
            }
        )
        
        # Verificar que nenhum dos registros foi persistido
        read_result = await mcp_client.execute_tool(
            "read_table",
            {
                "table": "users",
                "filters": {"email": email}
            }
        )
        
        assert len(read_result["records"]) == 0 