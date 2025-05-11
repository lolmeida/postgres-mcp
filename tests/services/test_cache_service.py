"""
Testes unitários para o serviço de cache.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from postgres_mcp.core.exceptions import ServiceError
from postgres_mcp.services.cache import CacheService


@pytest.fixture
def cache_service():
    """Fixture que cria uma instância do serviço de cache."""
    return CacheService(max_size=100, ttl=300)


def test_cache_service_init():
    """Testa a inicialização do serviço de cache com diferentes parâmetros."""
    # Cache com valores padrão
    cache = CacheService()
    assert cache.max_size == 1000
    assert cache.ttl == 3600  # 1 hora
    
    # Cache com valores personalizados
    cache = CacheService(max_size=500, ttl=60)
    assert cache.max_size == 500
    assert cache.ttl == 60
    
    # Cache com TTL desativado
    cache = CacheService(ttl=None)
    assert cache.ttl is None


def test_set_get_cache(cache_service):
    """Testa as operações básicas de definir e obter do cache."""
    # Define um valor no cache
    cache_service.set("test_key", "test_value")
    
    # Obtém o valor do cache
    result = cache_service.get("test_key")
    
    # Verifica o resultado
    assert result == "test_value"
    
    # Tenta obter uma chave inexistente
    result = cache_service.get("non_existent_key")
    assert result is None
    
    # Tenta obter uma chave inexistente com valor padrão
    result = cache_service.get("non_existent_key", default="default_value")
    assert result == "default_value"


def test_set_with_namespace(cache_service):
    """Testa a definição de valores no cache com namespace."""
    # Define valores com diferentes namespaces
    cache_service.set("key1", "value1", namespace="ns1")
    cache_service.set("key1", "value2", namespace="ns2")
    
    # Verifica que são armazenados separadamente
    assert cache_service.get("key1", namespace="ns1") == "value1"
    assert cache_service.get("key1", namespace="ns2") == "value2"


def test_cache_expiration():
    """Testa a expiração de itens no cache."""
    # Cria cache com TTL curto
    cache = CacheService(ttl=0.1)  # 100ms
    
    # Define um valor no cache
    cache.set("test_key", "test_value")
    
    # Verifica que está disponível imediatamente
    assert cache.get("test_key") == "test_value"
    
    # Espera a expiração
    time.sleep(0.2)  # 200ms
    
    # Verifica que o valor expirou
    assert cache.get("test_key") is None


def test_cache_item_ttl(cache_service):
    """Testa a definição de TTL específico para um item."""
    # Define um valor com TTL curto
    cache_service.set("short_lived", "value", ttl=0.1)
    
    # Define um valor com TTL padrão
    cache_service.set("long_lived", "value")
    
    # Verifica que ambos estão disponíveis imediatamente
    assert cache_service.get("short_lived") == "value"
    assert cache_service.get("long_lived") == "value"
    
    # Espera a expiração do primeiro item
    time.sleep(0.2)
    
    # Verifica que o primeiro expirou, mas o segundo continua disponível
    assert cache_service.get("short_lived") is None
    assert cache_service.get("long_lived") == "value"


def test_delete_from_cache(cache_service):
    """Testa a remoção de itens do cache."""
    # Define alguns valores no cache
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    cache_service.set("key3", "value3", namespace="custom")
    
    # Verifica que estão disponíveis
    assert cache_service.get("key1") == "value1"
    assert cache_service.get("key2") == "value2"
    assert cache_service.get("key3", namespace="custom") == "value3"
    
    # Remove um item
    result = cache_service.delete("key1")
    assert result is True
    assert cache_service.get("key1") is None
    
    # Tenta remover um item inexistente
    result = cache_service.delete("non_existent_key")
    assert result is False
    
    # Remove um item de um namespace específico
    result = cache_service.delete("key3", namespace="custom")
    assert result is True
    assert cache_service.get("key3", namespace="custom") is None
    
    # Verifica que outros itens permanecem intactos
    assert cache_service.get("key2") == "value2"


def test_clear_cache(cache_service):
    """Testa a limpeza do cache."""
    # Define alguns valores no cache
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    cache_service.set("key3", "value3", namespace="ns1")
    cache_service.set("key4", "value4", namespace="ns1")
    cache_service.set("key5", "value5", namespace="ns2")
    
    # Limpa um namespace específico
    cache_service.clear(namespace="ns1")
    
    # Verifica que apenas os itens do namespace foram limpos
    assert cache_service.get("key1") == "value1"
    assert cache_service.get("key2") == "value2"
    assert cache_service.get("key3", namespace="ns1") is None
    assert cache_service.get("key4", namespace="ns1") is None
    assert cache_service.get("key5", namespace="ns2") == "value5"
    
    # Limpa todo o cache
    cache_service.clear()
    
    # Verifica que todos os itens foram limpos
    assert cache_service.get("key1") is None
    assert cache_service.get("key2") is None
    assert cache_service.get("key5", namespace="ns2") is None


def test_cache_stats(cache_service):
    """Testa a coleta de estatísticas do cache."""
    # Define alguns valores e faz algumas consultas
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    
    # Hits
    cache_service.get("key1")
    cache_service.get("key1")
    cache_service.get("key2")
    
    # Misses
    cache_service.get("key3")
    cache_service.get("key4")
    
    # Obtém estatísticas
    stats = cache_service.get_stats()
    
    # Verifica estatísticas
    assert stats["hits"] == 3
    assert stats["misses"] == 2
    assert stats["size"] == 2
    assert stats["max_size"] == 100
    assert 0.5 <= stats["hit_ratio"] <= 0.6  # 3/(3+2) = 0.6
    
    # Limpa o cache e verifica que as estatísticas são reiniciadas
    cache_service.clear()
    cache_service.reset_stats()
    
    stats = cache_service.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["size"] == 0


def test_cache_size_limit():
    """Testa o limite de tamanho do cache."""
    # Cria um cache com tamanho pequeno
    cache = CacheService(max_size=3)
    
    # Define itens no cache até o limite
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # Verifica que todos os itens estão no cache
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    
    # Adiciona um novo item, que deve causar a remoção do item menos recentemente usado
    cache.set("key4", "value4")
    
    # Verifica que o item mais antigo foi removido (LRU)
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_cache_with_complex_objects(cache_service):
    """Testa o cache com objetos complexos."""
    # Define um dicionário como valor
    dict_value = {"name": "test", "values": [1, 2, 3]}
    cache_service.set("dict_key", dict_value)
    
    # Verifica que o objeto foi armazenado corretamente
    result = cache_service.get("dict_key")
    assert result == dict_value
    assert result["name"] == "test"
    assert result["values"] == [1, 2, 3]
    
    # Define uma lista como valor
    list_value = [{"id": 1}, {"id": 2}]
    cache_service.set("list_key", list_value)
    
    # Verifica que a lista foi armazenada corretamente
    result = cache_service.get("list_key")
    assert result == list_value
    assert len(result) == 2
    assert result[0]["id"] == 1


def test_cache_contains(cache_service):
    """Testa o método contains do cache."""
    # Define valores no cache
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2", namespace="custom")
    
    # Verifica existência de chaves
    assert "key1" in cache_service
    assert "key2" not in cache_service  # Sem especificar namespace
    assert cache_service.contains("key2", namespace="custom")
    assert not cache_service.contains("key3")


def test_multi_get_set(cache_service):
    """Testa as operações de get e set múltiplos."""
    # Define vários valores de uma vez
    data = {"key1": "value1", "key2": "value2", "key3": "value3"}
    cache_service.multi_set(data)
    
    # Obtém vários valores de uma vez
    keys = ["key1", "key2", "key4"]  # Inclui uma chave inexistente
    results = cache_service.multi_get(keys)
    
    # Verifica os resultados
    assert results == {"key1": "value1", "key2": "value2", "key4": None}
    
    # Com valor padrão
    results = cache_service.multi_get(keys, default="not_found")
    assert results == {"key1": "value1", "key2": "value2", "key4": "not_found"} 