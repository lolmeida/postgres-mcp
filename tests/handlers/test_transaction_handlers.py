"""
Testes unitários para os handlers de transações do MCP.
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Usar os modelos mockados em vez dos reais
from tests.mock_models import (
    BeginTransactionRequest,
    CommitTransactionRequest,
    RollbackTransactionRequest,
    GetTransactionStatusRequest
)


@pytest.fixture
def mock_service_container():
    """Fixture que cria um mock do contêiner de serviços."""
    container = MagicMock()
    container.transaction_service = MagicMock()
    # Transformar os métodos em coroutines
    container.transaction_service.begin_transaction = AsyncMock()
    container.transaction_service.commit_transaction = AsyncMock()
    container.transaction_service.rollback_transaction = AsyncMock()
    container.transaction_service.get_transaction_status = AsyncMock()
    return container


@pytest.mark.asyncio
async def test_begin_transaction_handler(mock_service_container):
    """Testa o handler de início de transação."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import BeginTransactionHandler
    
    # Configura o mock para retornar um ID de transação
    mock_service_container.transaction_service.begin_transaction.return_value = "tx_1234"
    
    # Cria o handler
    handler = BeginTransactionHandler(mock_service_container)
    
    # Cria uma requisição
    request = BeginTransactionRequest()
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.transaction_service.begin_transaction.assert_called_once()
    
    # Verifica a resposta
    assert response["success"] is True
    assert "transaction_id" in response
    assert response["transaction_id"] == "tx_1234"


@pytest.mark.asyncio
async def test_begin_transaction_handler_error(mock_service_container):
    """Testa o handler de início de transação quando ocorre um erro."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import BeginTransactionHandler
    
    # Configura o mock para lançar uma exceção
    mock_service_container.transaction_service.begin_transaction.side_effect = Exception("Erro ao iniciar transação")
    
    # Cria o handler
    handler = BeginTransactionHandler(mock_service_container)
    
    # Cria uma requisição
    request = BeginTransactionRequest()
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro ao iniciar transação" in response["error"]


@pytest.mark.asyncio
async def test_commit_transaction_handler(mock_service_container):
    """Testa o handler de commit de transação."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import CommitTransactionHandler
    
    # Configura o mock para retornar sucesso
    mock_service_container.transaction_service.commit_transaction.return_value = True
    
    # Cria o handler
    handler = CommitTransactionHandler(mock_service_container)
    
    # Cria uma requisição
    request = CommitTransactionRequest(transaction_id="tx_1234")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.transaction_service.commit_transaction.assert_called_once_with("tx_1234")
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_commit_transaction_handler_error(mock_service_container):
    """Testa o handler de commit de transação quando ocorre um erro."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import CommitTransactionHandler
    
    # Configura o mock para lançar uma exceção
    mock_service_container.transaction_service.commit_transaction.side_effect = Exception("Transação não existe")
    
    # Cria o handler
    handler = CommitTransactionHandler(mock_service_container)
    
    # Cria uma requisição
    request = CommitTransactionRequest(transaction_id="tx_invalid")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Transação não existe" in response["error"]


@pytest.mark.asyncio
async def test_rollback_transaction_handler(mock_service_container):
    """Testa o handler de rollback de transação."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import RollbackTransactionHandler
    
    # Configura o mock para retornar sucesso
    mock_service_container.transaction_service.rollback_transaction.return_value = True
    
    # Cria o handler
    handler = RollbackTransactionHandler(mock_service_container)
    
    # Cria uma requisição
    request = RollbackTransactionRequest(transaction_id="tx_1234")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.transaction_service.rollback_transaction.assert_called_once_with("tx_1234")
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_rollback_transaction_handler_error(mock_service_container):
    """Testa o handler de rollback de transação quando ocorre um erro."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import RollbackTransactionHandler
    
    # Configura o mock para lançar uma exceção
    mock_service_container.transaction_service.rollback_transaction.side_effect = Exception("Transação já finalizada")
    
    # Cria o handler
    handler = RollbackTransactionHandler(mock_service_container)
    
    # Cria uma requisição
    request = RollbackTransactionRequest(transaction_id="tx_finished")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Transação já finalizada" in response["error"]


@pytest.mark.asyncio
async def test_get_transaction_status_handler(mock_service_container):
    """Testa o handler de status de transação."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import GetTransactionStatusHandler
    
    # Configura o mock para retornar um status
    mock_service_container.transaction_service.get_transaction_status.return_value = {
        "id": "tx_1234",
        "status": "active",
        "started_at": "2023-01-01T12:00:00Z",
        "query_count": 5
    }
    
    # Cria o handler
    handler = GetTransactionStatusHandler(mock_service_container)
    
    # Cria uma requisição
    request = GetTransactionStatusRequest(transaction_id="tx_1234")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.transaction_service.get_transaction_status.assert_called_once_with("tx_1234")
    
    # Verifica a resposta
    assert response["success"] is True
    assert "status" in response
    assert response["status"]["id"] == "tx_1234"
    assert response["status"]["status"] == "active"
    assert response["status"]["started_at"] == "2023-01-01T12:00:00Z"
    assert response["status"]["query_count"] == 5


@pytest.mark.asyncio
async def test_get_transaction_status_handler_error(mock_service_container):
    """Testa o handler de status de transação quando ocorre um erro."""
    # Importar localmente para garantir que estamos usando o mock
    from postgres_mcp.handlers.transaction import GetTransactionStatusHandler
    
    # Configura o mock para lançar uma exceção
    mock_service_container.transaction_service.get_transaction_status.side_effect = Exception("Transação não encontrada")
    
    # Cria o handler
    handler = GetTransactionStatusHandler(mock_service_container)
    
    # Cria uma requisição
    request = GetTransactionStatusRequest(transaction_id="tx_unknown")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Transação não encontrada" in response["error"] 