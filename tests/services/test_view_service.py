"""
Testes unitários para o serviço de views.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from postgres_mcp.core.exceptions import ServiceError
from postgres_mcp.models.base import ViewInfo, ColumnInfo
from postgres_mcp.services.views import ViewService


@pytest.fixture
def mock_repository():
    """Fixture que cria um mock do repositório PostgreSQL."""
    mock = MagicMock()
    # Transformar os métodos em coroutines
    mock.get_views = AsyncMock()
    mock.describe_view = AsyncMock()
    mock.create_view = AsyncMock()
    mock.refresh_view = AsyncMock()
    mock.drop_view = AsyncMock()
    return mock


@pytest.fixture
def view_service(mock_repository):
    """Fixture que cria uma instância do serviço de views com o repositório mockado."""
    return ViewService(repository=mock_repository)


@pytest.mark.asyncio
async def test_list_views_success(view_service, mock_repository):
    """Testa a listagem de views com sucesso."""
    # Configura o mock para retornar uma lista de views
    mock_repository.get_views.return_value = ["view1", "view2", "view3"]
    
    # Chama o método e verifica o resultado
    result = await view_service.list_views("public")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.get_views.assert_called_once_with(
        schema="public", 
        include_materialized=True
    )
    
    # Verifica o resultado
    assert result == ["view1", "view2", "view3"]
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_views_non_materialized(view_service, mock_repository):
    """Testa a listagem de views excluindo views materializadas."""
    # Configura o mock para retornar uma lista de views
    mock_repository.get_views.return_value = ["view1"]
    
    # Chama o método com filtros e verifica o resultado
    result = await view_service.list_views(
        schema="analytics",
        include_materialized=False
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.get_views.assert_called_once_with(
        schema="analytics", 
        include_materialized=False
    )
    
    # Verifica o resultado
    assert result == ["view1"]
    assert len(result) == 1


@pytest.mark.asyncio
async def test_list_views_error(view_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao listar views."""
    # Configura o mock para lançar uma exceção
    mock_repository.get_views.side_effect = Exception("Erro de teste")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await view_service.list_views("public")
    
    # Verifica a mensagem de erro
    assert "Erro ao listar views: Erro de teste" in str(excinfo.value)


@pytest.mark.asyncio
async def test_describe_view_success(view_service, mock_repository):
    """Testa a descrição de uma view com sucesso."""
    # Configura o mock para retornar dados da view
    mock_view_data = {
        "name": "test_view",
        "schema": "public",
        "columns": [
            {
                "name": "id",
                "data_type": "integer",
                "nullable": False,
                "is_primary": True
            },
            {
                "name": "name",
                "data_type": "text",
                "nullable": False
            }
        ],
        "definition": "SELECT id, name FROM users",
        "is_materialized": False,
        "comment": "View de teste",
        "depends_on": ["public.users"]
    }
    mock_repository.describe_view.return_value = mock_view_data
    
    # Chama o método e verifica o resultado
    result = await view_service.describe_view("test_view", "public")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.describe_view.assert_called_once_with("test_view", "public")
    
    # Verifica o resultado
    assert isinstance(result, ViewInfo)
    assert result.name == "test_view"
    assert result.schema == "public"
    assert len(result.columns) == 2
    assert isinstance(result.columns[0], ColumnInfo)
    assert result.columns[0].name == "id"
    assert result.columns[0].data_type == "integer"
    assert result.columns[0].nullable is False
    assert result.columns[0].is_primary is True
    assert result.columns[1].name == "name"
    assert result.definition == "SELECT id, name FROM users"
    assert result.is_materialized is False
    assert result.comment == "View de teste"
    assert result.depends_on == ["public.users"]


@pytest.mark.asyncio
async def test_describe_materialized_view(view_service, mock_repository):
    """Testa a descrição de uma view materializada."""
    # Configura o mock para retornar dados da view materializada
    mock_view_data = {
        "name": "test_materialized",
        "schema": "public",
        "columns": [
            {
                "name": "id",
                "data_type": "integer",
                "nullable": False
            },
            {
                "name": "count",
                "data_type": "bigint",
                "nullable": True
            }
        ],
        "definition": "SELECT id, COUNT(*) FROM orders GROUP BY id",
        "is_materialized": True,
        "depends_on": ["public.orders"]
    }
    mock_repository.describe_view.return_value = mock_view_data
    
    # Chama o método e verifica o resultado
    result = await view_service.describe_view("test_materialized", "public")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.describe_view.assert_called_once_with("test_materialized", "public")
    
    # Verifica o resultado
    assert isinstance(result, ViewInfo)
    assert result.name == "test_materialized"
    assert result.is_materialized is True
    assert len(result.columns) == 2
    assert result.columns[1].name == "count"
    assert result.columns[1].data_type == "bigint"


@pytest.mark.asyncio
async def test_describe_view_error(view_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao descrever uma view."""
    # Configura o mock para lançar uma exceção
    mock_repository.describe_view.side_effect = Exception("View não encontrada")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await view_service.describe_view("non_existent_view", "public")
    
    # Verifica a mensagem de erro
    assert "Erro ao descrever view public.non_existent_view:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_view_success(view_service, mock_repository):
    """Testa a criação de uma view com sucesso."""
    # Configura o mock para retornar dados da view criada
    mock_view_data = {
        "name": "new_view",
        "schema": "public",
        "columns": [
            {
                "name": "id",
                "data_type": "integer",
                "nullable": False
            },
            {
                "name": "name",
                "data_type": "text",
                "nullable": False
            }
        ],
        "definition": "SELECT id, name FROM users WHERE active = true",
        "is_materialized": False
    }
    mock_repository.create_view.return_value = mock_view_data
    
    # Chama o método e verifica o resultado
    result = await view_service.create_view(
        view="new_view",
        definition="SELECT id, name FROM users WHERE active = true",
        schema="public",
        replace=True
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.create_view.assert_called_once_with(
        view="new_view",
        definition="SELECT id, name FROM users WHERE active = true",
        schema="public",
        replace=True,
        is_materialized=False,
        columns=None,
        with_data=True,
        comment=None
    )
    
    # Verifica o resultado
    assert isinstance(result, ViewInfo)
    assert result.name == "new_view"
    assert result.schema == "public"
    assert len(result.columns) == 2
    assert result.definition == "SELECT id, name FROM users WHERE active = true"
    assert result.is_materialized is False


@pytest.mark.asyncio
async def test_create_materialized_view(view_service, mock_repository):
    """Testa a criação de uma view materializada."""
    # Configura o mock para retornar dados da view materializada
    mock_view_data = {
        "name": "monthly_stats",
        "schema": "analytics",
        "columns": [
            {
                "name": "month",
                "data_type": "date",
                "nullable": False
            },
            {
                "name": "total",
                "data_type": "numeric",
                "nullable": True
            }
        ],
        "definition": "SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        "is_materialized": True
    }
    mock_repository.create_view.return_value = mock_view_data
    
    # Chama o método e verifica o resultado
    result = await view_service.create_view(
        view="monthly_stats",
        definition="SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        schema="analytics",
        is_materialized=True,
        replace=True,
        with_data=True,
        comment="Estatísticas mensais de vendas"
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.create_view.assert_called_once_with(
        view="monthly_stats",
        definition="SELECT date_trunc('month', created_at) as month, SUM(amount) as total FROM orders GROUP BY 1",
        schema="analytics",
        replace=True,
        is_materialized=True,
        columns=None,
        with_data=True,
        comment="Estatísticas mensais de vendas"
    )
    
    # Verifica o resultado
    assert isinstance(result, ViewInfo)
    assert result.name == "monthly_stats"
    assert result.schema == "analytics"
    assert result.is_materialized is True


@pytest.mark.asyncio
async def test_create_view_error(view_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao criar uma view."""
    # Configura o mock para lançar uma exceção
    mock_repository.create_view.side_effect = Exception("Erro de sintaxe SQL")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await view_service.create_view(
            view="invalid_view",
            definition="INVALID SQL",
            schema="public"
        )
    
    # Verifica a mensagem de erro
    assert "Erro ao criar view public.invalid_view:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_refresh_view_success(view_service, mock_repository):
    """Testa a atualização de uma view materializada com sucesso."""
    # Configura o mock para retornar sucesso
    mock_repository.refresh_view.return_value = True
    
    # Chama o método e verifica o resultado
    result = await view_service.refresh_view(
        view="stats_view",
        schema="public",
        concurrently=True
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.refresh_view.assert_called_once_with(
        view="stats_view",
        schema="public",
        concurrently=True
    )
    
    # Verifica o resultado
    assert result is True


@pytest.mark.asyncio
async def test_refresh_view_error(view_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao atualizar uma view."""
    # Configura o mock para lançar uma exceção
    mock_repository.refresh_view.side_effect = Exception("View não é materializada")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await view_service.refresh_view("non_materialized_view", "public")
    
    # Verifica a mensagem de erro
    assert "Erro ao atualizar view public.non_materialized_view:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_drop_view_success(view_service, mock_repository):
    """Testa a exclusão de uma view com sucesso."""
    # Configura o mock para retornar sucesso
    mock_repository.drop_view.return_value = True
    
    # Chama o método e verifica o resultado
    result = await view_service.drop_view(
        view="old_view",
        schema="public",
        if_exists=True,
        cascade=True
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.drop_view.assert_called_once_with(
        view="old_view",
        schema="public",
        if_exists=True,
        cascade=True
    )
    
    # Verifica o resultado
    assert result is True


@pytest.mark.asyncio
async def test_drop_view_error(view_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao excluir uma view."""
    # Configura o mock para lançar uma exceção
    mock_repository.drop_view.side_effect = Exception("View não existe")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await view_service.drop_view("non_existent_view", "public")
    
    # Verifica a mensagem de erro
    assert "Erro ao excluir view public.non_existent_view:" in str(excinfo.value) 