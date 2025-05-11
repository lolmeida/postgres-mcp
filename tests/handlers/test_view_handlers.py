"""
Testes unitários para os handlers de views do MCP.
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from postgres_mcp.models.base import ViewInfo, ColumnInfo
from postgres_mcp.models.requests import (
    ViewReference, 
    ListViewsRequest,
    DescribeViewRequest,
    CreateViewRequest,
    RefreshViewRequest,
    DropViewRequest
)
from postgres_mcp.services.views import ViewService
from postgres_mcp.handlers.views import (
    ListViewsHandler,
    DescribeViewHandler,
    CreateViewHandler,
    RefreshViewHandler,
    DropViewHandler
)


@pytest.fixture
def mock_service_container():
    """Fixture que cria um mock do contêiner de serviços."""
    container = MagicMock()
    container.view_service = MagicMock(spec=ViewService)
    # Transformar os métodos em coroutines
    container.view_service.list_views = AsyncMock()
    container.view_service.describe_view = AsyncMock()
    container.view_service.create_view = AsyncMock()
    container.view_service.refresh_view = AsyncMock()
    container.view_service.drop_view = AsyncMock()
    return container


@pytest.mark.asyncio
async def test_list_views_handler(mock_service_container):
    """Testa o handler de listagem de views."""
    # Configura o mock para retornar views
    mock_service_container.view_service.list_views.return_value = [
        "view1", "view2", "view3"
    ]
    
    # Cria o handler
    handler = ListViewsHandler(mock_service_container)
    
    # Cria uma requisição
    request = ListViewsRequest(schema="public")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.list_views.assert_called_once_with(
        schema="public", 
        include_materialized=True
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "views" in response
    assert len(response["views"]) == 3
    assert response["views"] == ["view1", "view2", "view3"]


@pytest.mark.asyncio
async def test_list_views_non_materialized(mock_service_container):
    """Testa o handler de listagem de views excluindo views materializadas."""
    # Configura o mock para retornar views
    mock_service_container.view_service.list_views.return_value = ["view1"]
    
    # Cria o handler
    handler = ListViewsHandler(mock_service_container)
    
    # Cria uma requisição com filtros
    request = ListViewsRequest(
        schema="analytics",
        include_materialized=False
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.list_views.assert_called_once_with(
        schema="analytics", 
        include_materialized=False
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert len(response["views"]) == 1
    assert response["views"] == ["view1"]


@pytest.mark.asyncio
async def test_list_views_handler_error(mock_service_container):
    """Testa o handler de listagem de views quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.view_service.list_views.side_effect = Exception("Erro de teste")
    
    # Cria o handler
    handler = ListViewsHandler(mock_service_container)
    
    # Cria uma requisição
    request = ListViewsRequest(schema="public")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro de teste" in response["error"]


@pytest.mark.asyncio
async def test_describe_view_handler(mock_service_container):
    """Testa o handler de descrição de view."""
    # Cria colunas para a view
    columns = [
        ColumnInfo(name="id", data_type="integer", nullable=False, is_primary=True),
        ColumnInfo(name="name", data_type="text", nullable=False)
    ]
    
    # Cria um objeto de view para retorno
    view_info = ViewInfo(
        name="test_view",
        schema="public",
        columns=columns,
        definition="SELECT id, name FROM users",
        is_materialized=False,
        comment="View de teste",
        depends_on=["public.users"]
    )
    
    # Configura o mock para retornar a view
    mock_service_container.view_service.describe_view.return_value = view_info
    
    # Cria o handler
    handler = DescribeViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = DescribeViewRequest(
        view=ViewReference(name="test_view", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.describe_view.assert_called_once_with(
        "test_view", "public"
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "view" in response
    assert response["view"]["name"] == "test_view"
    assert response["view"]["schema"] == "public"
    assert len(response["view"]["columns"]) == 2
    assert response["view"]["columns"][0]["name"] == "id"
    assert response["view"]["definition"] == "SELECT id, name FROM users"
    assert response["view"]["is_materialized"] is False
    assert response["view"]["comment"] == "View de teste"
    assert response["view"]["depends_on"] == ["public.users"]


@pytest.mark.asyncio
async def test_describe_view_handler_materialized(mock_service_container):
    """Testa o handler de descrição de view materializada."""
    # Cria colunas para a view
    columns = [
        ColumnInfo(name="month", data_type="date", nullable=False),
        ColumnInfo(name="total", data_type="numeric", nullable=True)
    ]
    
    # Cria um objeto de view materializada para retorno
    view_info = ViewInfo(
        name="monthly_stats",
        schema="analytics",
        columns=columns,
        definition="SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        is_materialized=True,
        depends_on=["public.orders"]
    )
    
    # Configura o mock para retornar a view
    mock_service_container.view_service.describe_view.return_value = view_info
    
    # Cria o handler
    handler = DescribeViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = DescribeViewRequest(
        view=ViewReference(name="monthly_stats", schema="analytics")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta
    assert response["success"] is True
    assert response["view"]["name"] == "monthly_stats"
    assert response["view"]["schema"] == "analytics"
    assert response["view"]["is_materialized"] is True
    assert len(response["view"]["columns"]) == 2
    assert response["view"]["columns"][0]["name"] == "month"
    assert response["view"]["columns"][1]["name"] == "total"
    assert response["view"]["depends_on"] == ["public.orders"]


@pytest.mark.asyncio
async def test_describe_view_handler_error(mock_service_container):
    """Testa o handler de descrição de view quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.view_service.describe_view.side_effect = Exception("View não encontrada")
    
    # Cria o handler
    handler = DescribeViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = DescribeViewRequest(
        view=ViewReference(name="non_existent", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "View não encontrada" in response["error"]


@pytest.mark.asyncio
async def test_create_view_handler(mock_service_container):
    """Testa o handler de criação de view."""
    # Cria colunas para a view
    columns = [
        ColumnInfo(name="id", data_type="integer", nullable=False),
        ColumnInfo(name="name", data_type="text", nullable=False)
    ]
    
    # Cria um objeto de view para retorno
    view_info = ViewInfo(
        name="new_view",
        schema="public",
        columns=columns,
        definition="SELECT id, name FROM users WHERE active = true",
        is_materialized=False
    )
    
    # Configura o mock para retornar a view criada
    mock_service_container.view_service.create_view.return_value = view_info
    
    # Cria o handler
    handler = CreateViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = CreateViewRequest(
        view=ViewReference(name="new_view", schema="public"),
        definition="SELECT id, name FROM users WHERE active = true",
        replace=True
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.create_view.assert_called_once_with(
        view="new_view",
        schema="public",
        definition="SELECT id, name FROM users WHERE active = true",
        replace=True,
        is_materialized=False,
        columns=None,
        with_data=True,
        comment=None
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "view" in response
    assert response["view"]["name"] == "new_view"
    assert response["view"]["schema"] == "public"
    assert len(response["view"]["columns"]) == 2
    assert response["view"]["definition"] == "SELECT id, name FROM users WHERE active = true"
    assert response["view"]["is_materialized"] is False


@pytest.mark.asyncio
async def test_create_materialized_view_handler(mock_service_container):
    """Testa o handler de criação de view materializada."""
    # Cria colunas para a view
    columns = [
        ColumnInfo(name="month", data_type="date", nullable=False),
        ColumnInfo(name="total", data_type="numeric", nullable=True)
    ]
    
    # Cria um objeto de view materializada para retorno
    view_info = ViewInfo(
        name="monthly_stats",
        schema="analytics",
        columns=columns,
        definition="SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        is_materialized=True
    )
    
    # Configura o mock para retornar a view criada
    mock_service_container.view_service.create_view.return_value = view_info
    
    # Cria o handler
    handler = CreateViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = CreateViewRequest(
        view=ViewReference(name="monthly_stats", schema="analytics"),
        definition="SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        is_materialized=True,
        replace=True,
        with_data=True,
        comment="Estatísticas mensais de vendas"
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.create_view.assert_called_once_with(
        view="monthly_stats",
        schema="analytics",
        definition="SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        replace=True,
        is_materialized=True,
        columns=None,
        with_data=True,
        comment="Estatísticas mensais de vendas"
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert response["view"]["name"] == "monthly_stats"
    assert response["view"]["schema"] == "analytics"
    assert response["view"]["is_materialized"] is True


@pytest.mark.asyncio
async def test_create_view_handler_error(mock_service_container):
    """Testa o handler de criação de view quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.view_service.create_view.side_effect = Exception("Erro de sintaxe SQL")
    
    # Cria o handler
    handler = CreateViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = CreateViewRequest(
        view=ViewReference(name="invalid_view", schema="public"),
        definition="INVALID SQL"
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro de sintaxe SQL" in response["error"]


@pytest.mark.asyncio
async def test_refresh_view_handler(mock_service_container):
    """Testa o handler de atualização de view materializada."""
    # Configura o mock para retornar sucesso
    mock_service_container.view_service.refresh_view.return_value = True
    
    # Cria o handler
    handler = RefreshViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = RefreshViewRequest(
        view=ViewReference(name="stats_view", schema="public"),
        concurrently=True
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.refresh_view.assert_called_once_with(
        view="stats_view",
        schema="public",
        concurrently=True
    )
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_refresh_view_handler_error(mock_service_container):
    """Testa o handler de atualização de view quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.view_service.refresh_view.side_effect = Exception("View não é materializada")
    
    # Cria o handler
    handler = RefreshViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = RefreshViewRequest(
        view=ViewReference(name="regular_view", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "View não é materializada" in response["error"]


@pytest.mark.asyncio
async def test_drop_view_handler(mock_service_container):
    """Testa o handler de exclusão de view."""
    # Configura o mock para retornar sucesso
    mock_service_container.view_service.drop_view.return_value = True
    
    # Cria o handler
    handler = DropViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = DropViewRequest(
        view=ViewReference(name="old_view", schema="public"),
        if_exists=True,
        cascade=True
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.drop_view.assert_called_once_with(
        view="old_view",
        schema="public",
        if_exists=True,
        cascade=True
    )
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_drop_materialized_view_handler(mock_service_container):
    """Testa o handler de exclusão de view materializada."""
    # Configura o mock para retornar sucesso
    mock_service_container.view_service.drop_view.return_value = True
    
    # Cria o handler
    handler = DropViewHandler(mock_service_container)
    
    # Cria uma requisição para view materializada
    request = DropViewRequest(
        view=ViewReference(name="materialized_stats", schema="analytics")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.view_service.drop_view.assert_called_once_with(
        view="materialized_stats",
        schema="analytics",
        if_exists=False,
        cascade=False
    )
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_drop_view_handler_error(mock_service_container):
    """Testa o handler de exclusão de view quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.view_service.drop_view.side_effect = Exception("View não existe")
    
    # Cria o handler
    handler = DropViewHandler(mock_service_container)
    
    # Cria uma requisição
    request = DropViewRequest(
        view=ViewReference(name="non_existent", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "View não existe" in response["error"] 