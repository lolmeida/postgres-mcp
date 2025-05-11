"""
Testes unitários para os handlers de funções do MCP.
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from postgres_mcp.models.base import FunctionInfo
from postgres_mcp.models.requests import (
    FunctionReference, 
    ListFunctionsRequest,
    DescribeFunctionRequest,
    ExecuteFunctionRequest,
    CreateFunctionRequest,
    DropFunctionRequest
)
from postgres_mcp.services.functions import FunctionService
from postgres_mcp.handlers.functions import (
    ListFunctionsHandler,
    DescribeFunctionHandler,
    ExecuteFunctionHandler,
    CreateFunctionHandler,
    DropFunctionHandler
)


@pytest.fixture
def mock_service_container():
    """Fixture que cria um mock do contêiner de serviços."""
    container = MagicMock()
    container.function_service = MagicMock(spec=FunctionService)
    # Transformar os métodos em coroutines
    container.function_service.list_functions = AsyncMock()
    container.function_service.describe_function = AsyncMock()
    container.function_service.execute_function = AsyncMock()
    container.function_service.create_function = AsyncMock()
    container.function_service.drop_function = AsyncMock()
    return container


@pytest.mark.asyncio
async def test_list_functions_handler(mock_service_container):
    """Testa o handler de listagem de funções."""
    # Configura o mock para retornar funções
    mock_service_container.function_service.list_functions.return_value = [
        "func1", "func2", "func3"
    ]
    
    # Cria o handler
    handler = ListFunctionsHandler(mock_service_container)
    
    # Cria uma requisição
    request = ListFunctionsRequest(schema="public")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.list_functions.assert_called_once_with(
        schema="public", 
        include_procedures=True,
        include_aggregates=True
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "functions" in response
    assert len(response["functions"]) == 3
    assert response["functions"] == ["func1", "func2", "func3"]


@pytest.mark.asyncio
async def test_list_functions_handler_with_filters(mock_service_container):
    """Testa o handler de listagem de funções com filtros."""
    # Configura o mock para retornar funções
    mock_service_container.function_service.list_functions.return_value = ["func1"]
    
    # Cria o handler
    handler = ListFunctionsHandler(mock_service_container)
    
    # Cria uma requisição com filtros
    request = ListFunctionsRequest(
        schema="analytics",
        include_procedures=False,
        include_aggregates=False
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.list_functions.assert_called_once_with(
        schema="analytics", 
        include_procedures=False,
        include_aggregates=False
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert len(response["functions"]) == 1
    assert response["functions"] == ["func1"]


@pytest.mark.asyncio
async def test_list_functions_handler_error(mock_service_container):
    """Testa o handler de listagem de funções quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.function_service.list_functions.side_effect = Exception("Erro de teste")
    
    # Cria o handler
    handler = ListFunctionsHandler(mock_service_container)
    
    # Cria uma requisição
    request = ListFunctionsRequest(schema="public")
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro de teste" in response["error"]


@pytest.mark.asyncio
async def test_describe_function_handler(mock_service_container):
    """Testa o handler de descrição de função."""
    # Cria um objeto de função para retorno
    function_info = FunctionInfo(
        name="test_function",
        schema="public",
        return_type="integer",
        definition="BEGIN RETURN 1; END;",
        language="plpgsql",
        argument_types=["text", "integer"],
        argument_names=["arg1", "arg2"],
        argument_defaults=[None, "5"],
        is_procedure=False,
        is_aggregate=False,
        is_window=False,
        is_security_definer=False,
        volatility="stable",
        comment="Função de teste"
    )
    
    # Configura o mock para retornar a função
    mock_service_container.function_service.describe_function.return_value = function_info
    
    # Cria o handler
    handler = DescribeFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = DescribeFunctionRequest(
        function=FunctionReference(name="test_function", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.describe_function.assert_called_once_with(
        "test_function", "public"
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "function" in response
    assert response["function"]["name"] == "test_function"
    assert response["function"]["schema"] == "public"
    assert response["function"]["return_type"] == "integer"
    assert response["function"]["language"] == "plpgsql"
    assert response["function"]["is_procedure"] is False


@pytest.mark.asyncio
async def test_describe_function_handler_error(mock_service_container):
    """Testa o handler de descrição de função quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.function_service.describe_function.side_effect = Exception("Função não encontrada")
    
    # Cria o handler
    handler = DescribeFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = DescribeFunctionRequest(
        function=FunctionReference(name="non_existent", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Função não encontrada" in response["error"]


@pytest.mark.asyncio
async def test_execute_function_handler_positional_args(mock_service_container):
    """Testa o handler de execução de função com argumentos posicionais."""
    # Configura o mock para retornar um resultado
    mock_service_container.function_service.execute_function.return_value = 42
    
    # Cria o handler
    handler = ExecuteFunctionHandler(mock_service_container)
    
    # Cria uma requisição com argumentos posicionais
    request = ExecuteFunctionRequest(
        function=FunctionReference(name="calculate_sum", schema="public"),
        args=[20, 22]
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.execute_function.assert_called_once_with(
        function="calculate_sum",
        schema="public",
        args=[20, 22],
        named_args=None
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "result" in response
    assert response["result"] == 42


@pytest.mark.asyncio
async def test_execute_function_handler_named_args(mock_service_container):
    """Testa o handler de execução de função com argumentos nomeados."""
    # Configura o mock para retornar um resultado
    mock_service_container.function_service.execute_function.return_value = "Olá, Mundo!"
    
    # Cria o handler
    handler = ExecuteFunctionHandler(mock_service_container)
    
    # Cria uma requisição com argumentos nomeados
    request = ExecuteFunctionRequest(
        function=FunctionReference(name="format_greeting", schema="utils"),
        named_args={"name": "Mundo", "language": "pt"}
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.execute_function.assert_called_once_with(
        function="format_greeting",
        schema="utils",
        args=None,
        named_args={"name": "Mundo", "language": "pt"}
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert response["result"] == "Olá, Mundo!"


@pytest.mark.asyncio
async def test_execute_function_handler_error(mock_service_container):
    """Testa o handler de execução de função quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.function_service.execute_function.side_effect = Exception("Erro de execução")
    
    # Cria o handler
    handler = ExecuteFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = ExecuteFunctionRequest(
        function=FunctionReference(name="invalid_function", schema="public"),
        args=[1, 2]
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro de execução" in response["error"]


@pytest.mark.asyncio
async def test_create_function_handler(mock_service_container):
    """Testa o handler de criação de função."""
    # Cria um objeto de função para retorno
    function_info = FunctionInfo(
        name="new_function",
        schema="public",
        return_type="text",
        definition="BEGIN RETURN 'Hello'; END;",
        language="plpgsql",
        is_procedure=False,
        volatility="immutable"
    )
    
    # Configura o mock para retornar a função criada
    mock_service_container.function_service.create_function.return_value = function_info
    
    # Cria o handler
    handler = CreateFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = CreateFunctionRequest(
        function=FunctionReference(name="new_function", schema="public"),
        definition="BEGIN RETURN 'Hello'; END;",
        return_type="text",
        language="plpgsql",
        volatility="immutable",
        replace=True
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.create_function.assert_called_once_with(
        function="new_function",
        schema="public",
        definition="BEGIN RETURN 'Hello'; END;",
        return_type="text",
        argument_definitions=None,
        language="plpgsql",
        is_procedure=False,
        replace=True,
        security_definer=False,
        volatility="immutable"
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert "function" in response
    assert response["function"]["name"] == "new_function"
    assert response["function"]["schema"] == "public"
    assert response["function"]["return_type"] == "text"
    assert response["function"]["definition"] == "BEGIN RETURN 'Hello'; END;"


@pytest.mark.asyncio
async def test_create_procedure_handler(mock_service_container):
    """Testa o handler de criação de procedimento."""
    # Cria um objeto de procedimento para retorno
    procedure_info = FunctionInfo(
        name="new_procedure",
        schema="public",
        return_type="void",
        definition="BEGIN PERFORM pg_sleep(1); END;",
        language="plpgsql",
        is_procedure=True,
        volatility="volatile"
    )
    
    # Configura o mock para retornar o procedimento criado
    mock_service_container.function_service.create_function.return_value = procedure_info
    
    # Cria o handler
    handler = CreateFunctionHandler(mock_service_container)
    
    # Cria uma requisição para um procedimento
    request = CreateFunctionRequest(
        function=FunctionReference(name="new_procedure", schema="public"),
        definition="BEGIN PERFORM pg_sleep(1); END;",
        is_procedure=True,
        language="plpgsql"
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.create_function.assert_called_once_with(
        function="new_procedure",
        schema="public",
        definition="BEGIN PERFORM pg_sleep(1); END;",
        return_type=None,
        argument_definitions=None,
        language="plpgsql",
        is_procedure=True,
        replace=False,
        security_definer=False,
        volatility="volatile"  # Valor padrão para procedimentos
    )
    
    # Verifica a resposta
    assert response["success"] is True
    assert response["function"]["name"] == "new_procedure"
    assert response["function"]["is_procedure"] is True


@pytest.mark.asyncio
async def test_create_function_handler_error(mock_service_container):
    """Testa o handler de criação de função quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.function_service.create_function.side_effect = Exception("Erro de sintaxe SQL")
    
    # Cria o handler
    handler = CreateFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = CreateFunctionRequest(
        function=FunctionReference(name="invalid_function", schema="public"),
        definition="INVALID SQL",
        return_type="integer"
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Erro de sintaxe SQL" in response["error"]


@pytest.mark.asyncio
async def test_drop_function_handler(mock_service_container):
    """Testa o handler de exclusão de função."""
    # Configura o mock para retornar sucesso
    mock_service_container.function_service.drop_function.return_value = True
    
    # Cria o handler
    handler = DropFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = DropFunctionRequest(
        function=FunctionReference(name="old_function", schema="public"),
        if_exists=True,
        cascade=True
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.drop_function.assert_called_once_with(
        function="old_function",
        schema="public",
        if_exists=True,
        cascade=True,
        arg_types=None
    )
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_drop_function_with_arg_types(mock_service_container):
    """Testa o handler de exclusão de função com tipos de argumentos."""
    # Configura o mock para retornar sucesso
    mock_service_container.function_service.drop_function.return_value = True
    
    # Cria o handler
    handler = DropFunctionHandler(mock_service_container)
    
    # Cria uma requisição com tipos de argumentos
    request = DropFunctionRequest(
        function=FunctionReference(
            name="overloaded_function", 
            schema="public", 
            arg_types=["integer", "text"]
        )
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica se o serviço foi chamado corretamente
    mock_service_container.function_service.drop_function.assert_called_once_with(
        function="overloaded_function",
        schema="public",
        if_exists=False,
        cascade=False,
        arg_types=["integer", "text"]
    )
    
    # Verifica a resposta
    assert response["success"] is True


@pytest.mark.asyncio
async def test_drop_function_handler_error(mock_service_container):
    """Testa o handler de exclusão de função quando ocorre um erro."""
    # Configura o mock para lançar uma exceção
    mock_service_container.function_service.drop_function.side_effect = Exception("Função não existe")
    
    # Cria o handler
    handler = DropFunctionHandler(mock_service_container)
    
    # Cria uma requisição
    request = DropFunctionRequest(
        function=FunctionReference(name="non_existent", schema="public")
    )
    
    # Executa o handler
    response = await handler.handle(request)
    
    # Verifica a resposta de erro
    assert response["success"] is False
    assert "error" in response
    assert "Função não existe" in response["error"] 