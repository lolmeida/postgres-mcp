"""
Testes unitários para os handlers de cache do MCP.
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from postgres_mcp.models.requests import (
    GetCacheStatsRequest,
    ClearCacheRequest
)
from postgres_mcp.services.cache import CacheService
from postgres_mcp.handlers.cache import (
    GetCacheStatsHandler,
    ClearCacheHandler
)


@pytest.fixture
def mock_service_container():
    """Fixture que cria um mock do contêiner de serviços."""
    container = MagicMock()
    container.cache_service = MagicMock(spec=CacheService)
    # Os métodos do CacheService não são coroutines, então não precisamos do AsyncMock
    return container


@pytest.mark.asyncio
async def test_get_cache_stats_handler(mock_service_container):
    """Testa o handler de estatísticas do cache."""
    # Configura o mock para retornar estatísticas
    mock_service_container.cache_service.get_stats.return_value = {
        "hits": 100,
        "misses": 25,
        "size": 50,
        "max_size": 1000,
        "hit_ratio": 0.8
    }
    
    # Cria o handler
    handler = GetCacheStatsHandler(mock_service_container)
    
    # Cria uma requisição
    request = GetCacheStatsRequest()
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.cache_service.get_stats.assert_called_once()
    
    # Verifica a resposta
    assert response["success"] is True
    assert "stats" in response
    assert response["stats"]["hits"] == 100
    assert response["stats"]["misses"] == 25
    assert response["stats"]["size"] == 50
    assert response["stats"]["max_size"] == 1000
    assert response["stats"]["hit_ratio"] == 0.8


@pytest.mark.asyncio
async def test_get_cache_stats_handler_error(mock_service_container):
    """Testa o handler de estatísticas do cache quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.cache_service.get_stats.side_effect = Exception("Erro ao obter estatísticas")
    
    # Cria o handler
    handler = GetCacheStatsHandler(mock_service_container)
    
    # Cria uma requisição
    request = GetCacheStatsRequest()
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro ao obter estatísticas" in response["error"]


@pytest.mark.asyncio
async def test_clear_cache_handler_all(mock_service_container):
    """Testa o handler de limpeza de todo o cache."""
    # Cria o handler
    handler = ClearCacheHandler(mock_service_container)
    
    # Cria uma requisição para limpar todo o cache
    request = ClearCacheRequest()
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.cache_service.clear.assert_called_once_with(namespace=None)
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_clear_cache_handler_namespace(mock_service_container):
    """Testa o handler de limpeza de cache para um namespace específico."""
    # Cria o handler
    handler = ClearCacheHandler(mock_service_container)
    
    # Cria uma requisição para limpar um namespace específico
    request = ClearCacheRequest(namespace="functions")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.cache_service.clear.assert_called_once_with(namespace="functions")
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_clear_cache_handler_error(mock_service_container):
    """Testa o handler de limpeza de cache quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.cache_service.clear.side_effect = Exception("Erro ao limpar cache")
    
    # Cria o handler
    handler = ClearCacheHandler(mock_service_container)
    
    # Cria uma requisição
    request = ClearCacheRequest()
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro ao limpar cache" in response["error"] 