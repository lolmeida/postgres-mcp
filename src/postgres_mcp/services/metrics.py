"""
Serviço para monitoramento de métricas de desempenho
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast
import threading
import statistics
import random
import asyncio

from postgres_mcp.repository.base import BaseRepository
from postgres_mcp.services.base import BaseService

T = TypeVar('T')
FuncType = Callable[..., Any]


class MetricsService(BaseService):
    """
    Serviço para coletar, armazenar e analisar métricas de desempenho do sistema.
    
    Permite monitorar tempos de execução, taxas de erro, uso de recursos,
    e outras métricas importantes para avaliar o desempenho do MCP.
    """
    
    def __init__(
        self, 
        repository: BaseRepository, 
        logger: logging.Logger,
        sampling_rate: float = 1.0,  # Taxa de amostragem (1.0 = 100%)
        history_size: int = 1000     # Tamanho do histórico para cada métrica
    ):
        """
        Inicializa o serviço de métricas.
        
        Args:
            repository: Repositório para acesso a dados
            logger: Logger configurado
            sampling_rate: Taxa de amostragem para reduzir overhead (0.0 a 1.0)
            history_size: Número máximo de amostras para cada métrica
        """
        super().__init__(repository, logger)
        self.logger.info(
            "Inicializando serviço de métricas: sampling_rate=%.2f, history_size=%d", 
            sampling_rate, history_size
        )
        
        self.sampling_rate = max(0.0, min(1.0, sampling_rate))  # Garantir entre 0.0 e 1.0
        self.history_size = history_size
        
        # Métricas de tempo de execução por operação
        self.execution_times: Dict[str, List[float]] = {}
        
        # Contadores de operações
        self.operation_counts: Dict[str, int] = {}
        
        # Contadores de erros
        self.error_counts: Dict[str, int] = {}
        
        # Métricas de utilização de recursos
        self.resource_usage: Dict[str, List[float]] = {
            "memory_usage": [],
            "cpu_usage": [],
            "db_connections": []
        }
        
        # Timestamp da inicialização do serviço
        self.start_time = time.time()
        
        # Lock para acesso thread-safe às métricas
        self.metrics_lock = threading.RLock()
    
    def track_execution_time(self, operation_name: str) -> Callable[[FuncType], FuncType]:
        """
        Decorador para rastrear o tempo de execução de uma função.
        
        Args:
            operation_name: Nome da operação para identificar a métrica
            
        Returns:
            Decorador que mede o tempo de execução
        """
        def decorator(func: FuncType) -> FuncType:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Aplicar amostragem
                if self.sampling_rate < 1.0 and random.random() > self.sampling_rate:
                    return await func(*args, **kwargs)
                
                # Medir tempo de execução
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    self.record_success(operation_name, time.time() - start_time)
                    return result
                except Exception as e:
                    self.record_error(operation_name, str(e))
                    raise
                    
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Aplicar amostragem
                if self.sampling_rate < 1.0 and random.random() > self.sampling_rate:
                    return func(*args, **kwargs)
                
                # Medir tempo de execução
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.record_success(operation_name, time.time() - start_time)
                    return result
                except Exception as e:
                    self.record_error(operation_name, str(e))
                    raise
            
            # Retornar o wrapper apropriado baseado no tipo da função
            if asyncio.iscoroutinefunction(func):
                return cast(FuncType, async_wrapper)
            else:
                return cast(FuncType, sync_wrapper)
            
        return decorator
    
    def record_success(self, operation_name: str, execution_time: float) -> None:
        """
        Registra uma operação bem-sucedida com seu tempo de execução.
        
        Args:
            operation_name: Nome da operação
            execution_time: Tempo de execução em segundos
        """
        with self.metrics_lock:
            # Inicializar lista se não existir
            if operation_name not in self.execution_times:
                self.execution_times[operation_name] = []
                
            # Adicionar tempo de execução, limitando o histórico
            times = self.execution_times[operation_name]
            times.append(execution_time)
            if len(times) > self.history_size:
                times.pop(0)  # Remover o mais antigo
                
            # Incrementar contador de operações
            self.operation_counts[operation_name] = self.operation_counts.get(operation_name, 0) + 1
    
    def record_error(self, operation_name: str, error_type: str) -> None:
        """
        Registra um erro durante uma operação.
        
        Args:
            operation_name: Nome da operação
            error_type: Tipo ou mensagem de erro
        """
        with self.metrics_lock:
            error_key = f"{operation_name}:{error_type}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def update_resource_usage(self, resource_type: str, value: float) -> None:
        """
        Atualiza métricas de uso de recursos.
        
        Args:
            resource_type: Tipo de recurso (memory_usage, cpu_usage, db_connections)
            value: Valor numérico da métrica
        """
        with self.metrics_lock:
            if resource_type in self.resource_usage:
                values = self.resource_usage[resource_type]
                values.append(value)
                if len(values) > self.history_size:
                    values.pop(0)
    
    def get_execution_time_stats(self, operation_name: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Retorna estatísticas de tempo de execução.
        
        Args:
            operation_name: Se especificado, retorna apenas para esta operação
            
        Returns:
            Dicionário com estatísticas para cada operação
        """
        with self.metrics_lock:
            results = {}
            
            operations = [operation_name] if operation_name else list(self.execution_times.keys())
            
            for op in operations:
                if op not in self.execution_times or not self.execution_times[op]:
                    continue
                    
                times = self.execution_times[op]
                
                results[op] = {
                    "min": min(times),
                    "max": max(times),
                    "avg": sum(times) / len(times),
                    "median": statistics.median(times) if len(times) > 0 else 0,
                    "p95": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                    "count": len(times),
                    "total_count": self.operation_counts.get(op, 0)
                }
                
            return results
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas de erros.
        
        Returns:
            Dicionário com contagem de erros por tipo
        """
        with self.metrics_lock:
            return dict(self.error_counts)
    
    def get_resource_usage_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Retorna estatísticas de uso de recursos.
        
        Returns:
            Dicionário com estatísticas para cada tipo de recurso
        """
        with self.metrics_lock:
            results = {}
            
            for resource_type, values in self.resource_usage.items():
                if not values:
                    continue
                    
                results[resource_type] = {
                    "current": values[-1],
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values)
                }
                
            return results
    
    def get_uptime(self) -> float:
        """
        Retorna o tempo de atividade do serviço em segundos.
        
        Returns:
            Tempo em segundos desde o início do serviço
        """
        return time.time() - self.start_time
    
    def get_operations_per_second(self, window_seconds: int = 60) -> Dict[str, float]:
        """
        Calcula operações por segundo em uma janela recente.
        
        Args:
            window_seconds: Janela de tempo em segundos
            
        Returns:
            Dicionário com taxa de operações por segundo para cada operação
        """
        # Esta implementação é simplificada e pode ser aprimorada com uma 
        # abordagem mais precisa baseada em timestamps para cada operação
        
        with self.metrics_lock:
            results = {}
            for op, times in self.execution_times.items():
                # Filtra para obter apenas tempos recentes (dentro da janela)
                recent_count = len([t for t in times if t <= window_seconds])
                if recent_count > 0:
                    results[op] = recent_count / window_seconds
                    
            return results
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Retorna todas as métricas coletadas.
        
        Returns:
            Dicionário com todas as métricas
        """
        return {
            "execution_times": self.get_execution_time_stats(),
            "errors": self.get_error_stats(),
            "resource_usage": self.get_resource_usage_stats(),
            "uptime_seconds": self.get_uptime(),
            "operations_per_second": self.get_operations_per_second(),
            "total_operations": sum(self.operation_counts.values()),
            "total_errors": sum(self.error_counts.values()),
            "error_rate": sum(self.error_counts.values()) / max(1, sum(self.operation_counts.values()))
        }
    
    def reset_metrics(self) -> None:
        """
        Resetar todas as métricas coletadas.
        """
        with self.metrics_lock:
            self.execution_times = {}
            self.operation_counts = {}
            self.error_counts = {}
            self.resource_usage = {
                "memory_usage": [],
                "cpu_usage": [],
                "db_connections": []
            }
            self.start_time = time.time()
            self.logger.info("Métricas resetadas")
    
    # Métodos auxiliares para coleta de métricas de recursos
    
    async def update_system_metrics(self) -> None:
        """
        Atualiza métricas de sistema (CPU, memória).
        Esta função pode ser chamada periodicamente.
        """
        try:
            import psutil
            
            # Coletar uso de CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.update_resource_usage("cpu_usage", cpu_percent)
            
            # Coletar uso de memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.update_resource_usage("memory_usage", memory_percent)
            
            # Coletar conexões de banco (aproximação via pool)
            pool_stats = await self.repository.get_pool_stats()
            if pool_stats and "used_connections" in pool_stats:
                self.update_resource_usage("db_connections", pool_stats["used_connections"])
                
        except ImportError:
            self.logger.warning("Pacote psutil não instalado. Algumas métricas de sistema não serão coletadas.")
        except Exception as e:
            self.logger.warning("Erro ao coletar métricas de sistema: %s", str(e)) 