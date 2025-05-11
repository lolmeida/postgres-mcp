"""
Testes para serialização e deserialização de mensagens MCP
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastmcp import Request as MCPRequest

from postgres_mcp.core.server import PostgresMCP


class TestMCPSerialization(unittest.TestCase):
    """Testes para serialização e deserialização de mensagens MCP."""
    
    @patch('postgres_mcp.core.server.FastMCPServer')
    @patch('postgres_mcp.core.server.PostgresRepository')
    @patch('postgres_mcp.core.server.configure_logging')
    async def test_request_deserialization(self, mock_logging, mock_repo, mock_server):
        """Testa a deserialização de requisições MCP."""
        # Configurar mocks
        mock_logging.return_value = MagicMock()
        mock_repo.return_value = MagicMock()
        mock_repo.return_value.connect = AsyncMock()
        
        # Criar servidor PostgresMCP em modo de teste
        mcp = PostgresMCP(test_mode=True)
        
        # Criar um router mock com método route
        mcp.router.route = AsyncMock()
        mcp.router.route.return_value = {"success": True, "data": "test"}
        
        # Criar requisição MCP
        request_data = {
            "tool": "list_tables",
            "parameters": {
                "schema": "public"
            }
        }
        request = MCPRequest(json_data=json.dumps(request_data))
        
        # Chamar o método de processamento de requisição
        response = await mcp._handle_request(request)
        
        # Verificar se a requisição foi deserializada corretamente
        mcp.router.route.assert_called_once()
        args, _ = mcp.router.route.call_args
        self.assertEqual(args[0], request_data)
        
        # Verificar se a resposta foi serializada corretamente
        response_data = json.loads(response.json_data)
        self.assertEqual(response_data, {"success": True, "data": "test"})
    
    @patch('postgres_mcp.core.server.FastMCPServer')
    @patch('postgres_mcp.core.server.PostgresRepository')
    @patch('postgres_mcp.core.server.configure_logging')
    async def test_request_deserialization_invalid_json(self, mock_logging, mock_repo, mock_server):
        """Testa a deserialização de requisições MCP com JSON inválido."""
        # Configurar mocks
        mock_logging.return_value = MagicMock()
        mock_repo.return_value = MagicMock()
        mock_repo.return_value.connect = AsyncMock()
        
        # Criar servidor PostgresMCP em modo de teste
        mcp = PostgresMCP(test_mode=True)
        
        # Criar requisição MCP com JSON inválido
        request = MCPRequest(json_data="invalid json")
        
        # Chamar o método de processamento de requisição
        response = await mcp._handle_request(request)
        
        # Verificar se a resposta contém o erro esperado
        response_data = json.loads(response.json_data)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["error"]["type"], "validation_error")
    
    @patch('postgres_mcp.core.server.FastMCPServer')
    @patch('postgres_mcp.core.server.PostgresRepository')
    @patch('postgres_mcp.core.server.configure_logging')
    async def test_response_serialization(self, mock_logging, mock_repo, mock_server):
        """Testa a serialização de respostas MCP."""
        # Configurar mocks
        mock_logging.return_value = MagicMock()
        mock_repo.return_value = MagicMock()
        mock_repo.return_value.connect = AsyncMock()
        
        # Criar servidor PostgresMCP em modo de teste
        mcp = PostgresMCP(test_mode=True)
        
        # Criar um router mock com método route
        mcp.router.route = AsyncMock()
        
        # Testar vários tipos de resposta
        test_cases = [
            # Resposta de sucesso simples
            {
                "success": True
            },
            # Resposta com dados
            {
                "success": True,
                "data": {"id": 1, "name": "Test"}
            },
            # Resposta com lista
            {
                "success": True,
                "results": [{"id": 1}, {"id": 2}]
            },
            # Resposta com valores nulos
            {
                "success": True,
                "data": {"id": 1, "value": None}
            },
            # Resposta de erro
            {
                "success": False,
                "error": {
                    "message": "Erro de teste",
                    "type": "test_error"
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Configurar mock para retornar o caso de teste
            mcp.router.route.return_value = test_case
            
            # Criar requisição MCP
            request_data = {
                "tool": f"test_{i}",
                "parameters": {}
            }
            request = MCPRequest(json_data=json.dumps(request_data))
            
            # Chamar o método de processamento de requisição
            response = await mcp._handle_request(request)
            
            # Verificar se a resposta foi serializada corretamente
            response_data = json.loads(response.json_data)
            self.assertEqual(response_data, test_case)


if __name__ == "__main__":
    unittest.main() 