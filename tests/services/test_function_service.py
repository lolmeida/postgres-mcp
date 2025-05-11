"""
Testes unitários para o serviço de funções.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from postgres_mcp.core.exceptions import ServiceError
from postgres_mcp.models.base import FunctionInfo
from postgres_mcp.services.functions import FunctionService


@pytest.fixture
def mock_repository():
    """Fixture que cria um mock do repositório PostgreSQL."""
    mock = MagicMock()
    # Transformar os métodos em coroutines
    mock.get_functions = AsyncMock()
    mock.describe_function = AsyncMock()
    mock.execute_function = AsyncMock()
    mock.create_function = AsyncMock()
    mock.drop_function = AsyncMock()
    return mock


@pytest.fixture
def function_service(mock_repository):
    """Fixture que cria uma instância do serviço de funções com o repositório mockado."""
    return FunctionService(repository=mock_repository)


@pytest.mark.asyncio
async def test_list_functions_success(function_service, mock_repository):
    """Testa a listagem de funções com sucesso."""
    # Configura o mock para retornar uma lista de funções
    mock_repository.get_functions.return_value = ["func1", "func2", "func3"]
    
    # Chama o método e verifica o resultado
    result = await function_service.list_functions("public")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.get_functions.assert_called_once_with(
        schema="public", 
        include_procedures=True,
        include_aggregates=True
    )
    
    # Verifica o resultado
    assert result == ["func1", "func2", "func3"]
    assert len(result) == 3


@pytest.mark.asyncio
async def test_list_functions_with_filters(function_service, mock_repository):
    """Testa a listagem de funções com filtros."""
    # Configura o mock para retornar uma lista de funções
    mock_repository.get_functions.return_value = ["func1"]
    
    # Chama o método com filtros e verifica o resultado
    result = await function_service.list_functions(
        schema="analytics",
        include_procedures=False,
        include_aggregates=False
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.get_functions.assert_called_once_with(
        schema="analytics", 
        include_procedures=False,
        include_aggregates=False
    )
    
    # Verifica o resultado
    assert result == ["func1"]
    assert len(result) == 1


@pytest.mark.asyncio
async def test_list_functions_error(function_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao listar funções."""
    # Configura o mock para lançar uma exceção
    mock_repository.get_functions.side_effect = Exception("Erro de teste")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await function_service.list_functions("public")
    
    # Verifica a mensagem de erro
    assert "Erro ao listar funções: Erro de teste" in str(excinfo.value)


@pytest.mark.asyncio
async def test_describe_function_success(function_service, mock_repository):
    """Testa a descrição de uma função com sucesso."""
    # Configura o mock para retornar dados da função
    mock_function_data = {
        "name": "test_function",
        "schema": "public",
        "return_type": "integer",
        "definition": "BEGIN RETURN 1; END;",
        "language": "plpgsql",
        "argument_types": ["text", "integer"],
        "argument_names": ["arg1", "arg2"],
        "argument_defaults": [None, "5"],
        "is_procedure": False,
        "is_aggregate": False,
        "is_window": False,
        "is_security_definer": False,
        "volatility": "stable",
        "comment": "Função de teste"
    }
    mock_repository.describe_function.return_value = mock_function_data
    
    # Chama o método e verifica o resultado
    result = await function_service.describe_function("test_function", "public")
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.describe_function.assert_called_once_with("test_function", "public")
    
    # Verifica o resultado
    assert isinstance(result, FunctionInfo)
    assert result.name == "test_function"
    assert result.schema == "public"
    assert result.return_type == "integer"
    assert result.definition == "BEGIN RETURN 1; END;"
    assert result.language == "plpgsql"
    assert result.argument_types == ["text", "integer"]
    assert result.argument_names == ["arg1", "arg2"]
    assert result.argument_defaults == [None, "5"]
    assert result.is_procedure is False
    assert result.is_aggregate is False
    assert result.is_window is False
    assert result.is_security_definer is False
    assert result.volatility == "stable"
    assert result.comment == "Função de teste"


@pytest.mark.asyncio
async def test_describe_function_error(function_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao descrever uma função."""
    # Configura o mock para lançar uma exceção
    mock_repository.describe_function.side_effect = Exception("Função não encontrada")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await function_service.describe_function("non_existent_function", "public")
    
    # Verifica a mensagem de erro
    assert "Erro ao descrever função public.non_existent_function:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_execute_function_success(function_service, mock_repository):
    """Testa a execução de uma função com sucesso."""
    # Configura o mock para retornar um resultado
    mock_repository.execute_function.return_value = 42
    
    # Chama o método com argumentos posicionais
    result = await function_service.execute_function(
        function="calculate_sum",
        schema="public",
        args=[20, 22]
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.execute_function.assert_called_once_with(
        function="calculate_sum",
        schema="public",
        args=[20, 22],
        named_args=None
    )
    
    # Verifica o resultado
    assert result == 42


@pytest.mark.asyncio
async def test_execute_function_with_named_args(function_service, mock_repository):
    """Testa a execução de uma função com argumentos nomeados."""
    # Configura o mock para retornar um resultado
    mock_repository.execute_function.return_value = "Olá, Mundo!"
    
    # Chama o método com argumentos nomeados
    result = await function_service.execute_function(
        function="format_greeting",
        schema="utils",
        named_args={"name": "Mundo", "language": "pt"}
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.execute_function.assert_called_once_with(
        function="format_greeting",
        schema="utils",
        args=None,
        named_args={"name": "Mundo", "language": "pt"}
    )
    
    # Verifica o resultado
    assert result == "Olá, Mundo!"


@pytest.mark.asyncio
async def test_execute_function_error(function_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao executar uma função."""
    # Configura o mock para lançar uma exceção
    mock_repository.execute_function.side_effect = Exception("Erro ao executar função")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await function_service.execute_function("calculate_sum", "public", [1, 2])
    
    # Verifica a mensagem de erro
    assert "Erro ao executar função public.calculate_sum:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_function_success(function_service, mock_repository):
    """Testa a criação de uma função com sucesso."""
    # Configura o mock para retornar dados da função criada
    mock_function_data = {
        "name": "new_function",
        "schema": "public",
        "return_type": "text",
        "definition": "BEGIN RETURN 'Hello'; END;",
        "language": "plpgsql",
        "is_procedure": False,
        "volatility": "immutable"
    }
    mock_repository.create_function.return_value = mock_function_data
    
    # Chama o método e verifica o resultado
    result = await function_service.create_function(
        function="new_function",
        definition="BEGIN RETURN 'Hello'; END;",
        return_type="text",
        schema="public",
        language="plpgsql",
        volatility="immutable"
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.create_function.assert_called_once_with(
        function="new_function",
        definition="BEGIN RETURN 'Hello'; END;",
        return_type="text",
        schema="public",
        argument_definitions=None,
        language="plpgsql",
        is_procedure=False,
        replace=False,
        security_definer=False,
        volatility="immutable"
    )
    
    # Verifica o resultado
    assert isinstance(result, FunctionInfo)
    assert result.name == "new_function"
    assert result.schema == "public"
    assert result.return_type == "text"
    assert result.definition == "BEGIN RETURN 'Hello'; END;"
    assert result.language == "plpgsql"
    assert result.is_procedure is False
    assert result.volatility == "immutable"


@pytest.mark.asyncio
async def test_create_procedure_success(function_service, mock_repository):
    """Testa a criação de um procedimento com sucesso."""
    # Configura o mock para retornar dados do procedimento criado
    mock_procedure_data = {
        "name": "new_procedure",
        "schema": "public",
        "return_type": "void",
        "definition": "BEGIN PERFORM pg_sleep(1); END;",
        "language": "plpgsql",
        "is_procedure": True,
        "volatility": "volatile"
    }
    mock_repository.create_function.return_value = mock_procedure_data
    
    # Chama o método e verifica o resultado
    result = await function_service.create_function(
        function="new_procedure",
        definition="BEGIN PERFORM pg_sleep(1); END;",
        return_type="void",
        schema="public",
        language="plpgsql",
        is_procedure=True
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.create_function.assert_called_once_with(
        function="new_procedure",
        definition="BEGIN PERFORM pg_sleep(1); END;",
        return_type="void",
        schema="public",
        argument_definitions=None,
        language="plpgsql",
        is_procedure=True,
        replace=False,
        security_definer=False,
        volatility="volatile"
    )
    
    # Verifica o resultado
    assert isinstance(result, FunctionInfo)
    assert result.name == "new_procedure"
    assert result.is_procedure is True


@pytest.mark.asyncio
async def test_create_function_error(function_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao criar uma função."""
    # Configura o mock para lançar uma exceção
    mock_repository.create_function.side_effect = Exception("Erro de sintaxe")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await function_service.create_function(
            function="invalid_function",
            definition="INVALID SQL",
            return_type="integer",
            schema="public"
        )
    
    # Verifica a mensagem de erro
    assert "Erro ao criar função public.invalid_function:" in str(excinfo.value)


@pytest.mark.asyncio
async def test_drop_function_success(function_service, mock_repository):
    """Testa a exclusão de uma função com sucesso."""
    # Configura o mock para retornar sucesso
    mock_repository.drop_function.return_value = True
    
    # Chama o método e verifica o resultado
    result = await function_service.drop_function(
        function="old_function",
        schema="public",
        if_exists=True,
        cascade=True
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.drop_function.assert_called_once_with(
        function="old_function",
        schema="public",
        if_exists=True,
        cascade=True,
        arg_types=None
    )
    
    # Verifica o resultado
    assert result is True


@pytest.mark.asyncio
async def test_drop_function_with_arg_types(function_service, mock_repository):
    """Testa a exclusão de uma função específica com tipos de argumentos."""
    # Configura o mock para retornar sucesso
    mock_repository.drop_function.return_value = True
    
    # Chama o método e verifica o resultado
    result = await function_service.drop_function(
        function="overloaded_function",
        schema="public",
        arg_types=["integer", "text"]
    )
    
    # Verifica se o método do repositório foi chamado corretamente
    mock_repository.drop_function.assert_called_once_with(
        function="overloaded_function",
        schema="public",
        if_exists=False,
        cascade=False,
        arg_types=["integer", "text"]
    )
    
    # Verifica o resultado
    assert result is True


@pytest.mark.asyncio
async def test_drop_function_error(function_service, mock_repository):
    """Testa o comportamento quando ocorre um erro ao excluir uma função."""
    # Configura o mock para lançar uma exceção
    mock_repository.drop_function.side_effect = Exception("Função não existe")
    
    # Verifica se a exceção ServiceError é lançada
    with pytest.raises(ServiceError) as excinfo:
        await function_service.drop_function("non_existent_function", "public")
    
    # Verifica a mensagem de erro
    assert "Erro ao excluir função public.non_existent_function:" in str(excinfo.value) 