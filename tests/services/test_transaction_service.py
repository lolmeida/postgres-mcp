"""
Testes unitários para o serviço de transações.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from postgres_mcp.core.exceptions import ServiceError
from postgres_mcp.services.transaction import TransactionService


@pytest.fixture
def mock_repository():
    """Fixture que cria um mock do repositório PostgreSQL."""
    mock = MagicMock()
    mock.begin_transaction = AsyncMock()
    mock.commit_transaction = AsyncMock()
    mock.rollback_transaction = AsyncMock()
    mock.get_transaction_status = AsyncMock()
    return mock


@pytest.fixture
def transaction_service(mock_repository):
    """Fixture que cria uma instância do serviço de transações com o repositório mockado."""
    return TransactionService(repository=mock_repository)


@pytest.mark.asyncio
async def test_begin_transaction_success(transaction_service, mock_repository):
    """Testa o início de uma transação com sucesso."""
    # Configura o mock para retornar sucesso
    mock_repository.begin_transaction.return_value = "tx_1234"
    
    # Chama o método e verifica o resultado
    transaction_id = await transaction_service.begin_transaction()
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.begin_transaction.assert_called_once()
    
    # Verifica o resultado
    assert transaction_id == "tx_1234"


@pytest.mark.asyncio
async def test_begin_transaction_error(transaction_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao iniciar uma transação."""
    # Configura o mock para lançar uma exceção
    mock_repository.begin_transaction.side_effect = Exception("Erro ao iniciar transação")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await transaction_service.begin_transaction()
    
    # Verifica a mensagem de erro
    assert "Erro ao iniciar transação:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_commit_transaction_success(transaction_service, mock_repository):
    """Testa o commit de uma transação com sucesso."""
    # Configura o mock para retornar sucesso
    mock_repository.commit_transaction.return_value = True
    
    # Chama o método e verifica o resultado
    result = await transaction_service.commit_transaction("tx_1234")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.commit_transaction.assert_called_once_with("tx_1234")
    
    # Verifica o resultado
    assert result is True


@pytest.mark.asyncio
async def test_commit_transaction_error(transaction_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao fazer commit de uma transação."""
    # Configura o mock para lançar uma exceção
    mock_repository.commit_transaction.side_effect = Exception("Transação não existe")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await transaction_service.commit_transaction("tx_invalid")
    
    # Verifica a mensagem de erro
    assert "Erro ao fazer commit da transação tx_invalid:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_rollback_transaction_success(transaction_service, mock_repository):
    """Testa o rollback de uma transação com sucesso."""
    # Configura o mock para retornar sucesso
    mock_repository.rollback_transaction.return_value = True
    
    # Chama o método e verifica o resultado
    result = await transaction_service.rollback_transaction("tx_1234")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.rollback_transaction.assert_called_once_with("tx_1234")
    
    # Verifica o resultado
    assert result is True


@pytest.mark.asyncio
async def test_rollback_transaction_error(transaction_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao fazer rollback de uma transação."""
    # Configura o mock para lançar uma exceção
    mock_repository.rollback_transaction.side_effect = Exception("Transação já finalizada")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await transaction_service.rollback_transaction("tx_finished")
    
    # Verifica a mensagem de erro
    assert "Erro ao fazer rollback da transação tx_finished:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_transaction_status_success(transaction_service, mock_repository):
    """Testa a obtenção do status de uma transação com sucesso."""
    # Configura o mock para retornar um status
    mock_repository.get_transaction_status.return_value = {
        "id": "tx_1234",
        "status": "active",
        "started_at": "2023-01-01T12:00:00Z",
        "query_count": 5
    }
    
    # Chama o método e verifica o resultado
    result = await transaction_service.get_transaction_status("tx_1234")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.get_transaction_status.assert_called_once_with("tx_1234")
    
    # Verifica o resultado
    assert result["id"] == "tx_1234"
    assert result["status"] == "active"
    assert result["started_at"] == "2023-01-01T12:00:00Z"
    assert result["query_count"] == 5


@pytest.mark.asyncio
async def test_get_transaction_status_error(transaction_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao obter o status de uma transação."""
    # Configura o mock para lançar uma exceção
    mock_repository.get_transaction_status.side_effect = Exception("Transação não encontrada")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await transaction_service.get_transaction_status("tx_unknown")
    
    # Verifica a mensagem de erro
    assert "Erro ao obter status da transação tx_unknown:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_transaction_context_manager_success():
    """Testa o uso do gerenciador de contexto para transações com sucesso."""
    # Cria um mock para o repositório
    mock_repo = MagicMock()
    mock_repo.begin_transaction = AsyncMock(return_value="tx_1234")
    mock_repo.commit_transaction = AsyncMock(return_value=True)
    
    # Cria o serviço
    service = TransactionService(repository=mock_repo)
    
    # Usa o gerenciador de contexto
    async with service.transaction() as tx_id:
        assert tx_id == "tx_1234"
    
    # Verifica se begin e commit foram chamados
    mock_repo.begin_transaction.assert_called_once()
    mock_repo.commit_transaction.assert_called_once_with("tx_1234")
    # Rollback não deve ter sido chamado
    mock_repo.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_transaction_context_manager_error():
    """Testa o gerenciador de contexto para transações quando ocorre um erro."""
    # Cria um mock para o repositório
    mock_repo = MagicMock()
    mock_repo.begin_transaction = AsyncMock(return_value="tx_1234")
    mock_repo.rollback_transaction = AsyncMock(return_value=True)
    
    # Cria o serviço
    service = TransactionService(repository=mock_repo)
    
    # Usa o gerenciador de contexto com uma exceção
    with pytest.raises(ValueError):
        async with service.transaction() as tx_id:
            assert tx_id == "tx_1234"
            raise ValueError("Erro durante a transação")
    
    # Verifica se begin e rollback foram chamados
    mock_repo.begin_transaction.assert_called_once()
    mock_repo.rollback_transaction.assert_called_once_with("tx_1234")
    # Commit não deve ter sido chamado
    mock_repo.commit_transaction.assert_not_called() 