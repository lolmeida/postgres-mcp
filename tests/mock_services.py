"""
Mock para serviços do MCP.
"""

from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, AsyncMock


class CacheService:
    """Serviço de cache mockado."""
    
    def __init__(self):
        """Inicializa o serviço de cache mockado."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "size": 0,
            "max_size": 1000,
            "hit_ratio": 0.0
        }
        self._cache = {}
    
    def get(self, key: str, namespace: Optional[str] = None) -> Any:
        """Obtém um valor do cache."""
        ns_cache = self._cache.get(namespace or "default", {})
        if key in ns_cache:
            self._stats["hits"] += 1
            return ns_cache[key]
        self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: Optional[str] = None) -> None:
        """Define um valor no cache."""
        ns = namespace or "default"
        if ns not in self._cache:
            self._cache[ns] = {}
        self._cache[ns][key] = value
        self._stats["size"] = sum(len(ns_cache) for ns_cache in self._cache.values())
    
    def remove(self, key: str, namespace: Optional[str] = None) -> bool:
        """Remove um valor do cache."""
        ns = namespace or "default"
        if ns in self._cache and key in self._cache[ns]:
            del self._cache[ns][key]
            self._stats["size"] = sum(len(ns_cache) for ns_cache in self._cache.values())
            return True
        return False
    
    def clear(self, namespace: Optional[str] = None) -> None:
        """Limpa o cache."""
        if namespace is None:
            self._cache = {}
            self._stats["size"] = 0
        elif namespace in self._cache:
            del self._cache[namespace]
            self._stats["size"] = sum(len(ns_cache) for ns_cache in self._cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        total = self._stats["hits"] + self._stats["misses"]
        if total > 0:
            self._stats["hit_ratio"] = self._stats["hits"] / total
        return self._stats.copy()


class TransactionService:
    """Serviço de transação mockado."""
    
    def __init__(self):
        """Inicializa o serviço de transação mockado."""
        self._transactions = {}
    
    async def begin_transaction(self) -> str:
        """Inicia uma nova transação."""
        tx_id = f"tx_{len(self._transactions) + 1}"
        self._transactions[tx_id] = {
            "id": tx_id,
            "status": "active",
            "started_at": "2023-01-01T12:00:00Z",
            "query_count": 0
        }
        return tx_id
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Faz commit de uma transação."""
        if transaction_id not in self._transactions:
            raise Exception(f"Transação não encontrada: {transaction_id}")
        
        if self._transactions[transaction_id]["status"] != "active":
            raise Exception(f"Transação não está ativa: {transaction_id}")
        
        self._transactions[transaction_id]["status"] = "committed"
        return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Faz rollback de uma transação."""
        if transaction_id not in self._transactions:
            raise Exception(f"Transação não encontrada: {transaction_id}")
        
        if self._transactions[transaction_id]["status"] != "active":
            raise Exception(f"Transação não está ativa: {transaction_id}")
        
        self._transactions[transaction_id]["status"] = "rolledback"
        return True
    
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Obtém o status de uma transação."""
        if transaction_id not in self._transactions:
            raise Exception(f"Transação não encontrada: {transaction_id}")
        
        return self._transactions[transaction_id].copy() 