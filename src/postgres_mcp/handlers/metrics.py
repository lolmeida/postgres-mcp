"""
Handlers para operações de métricas
"""

from typing import Any, Dict, Optional

from postgres_mcp.handlers.base import BaseHandler
from postgres_mcp.services.metrics import MetricsService


class GetMetricsHandler(BaseHandler):
    """
    Handler para obter métricas de desempenho.
    """
    
    def __init__(self, metrics_service: MetricsService):
        """
        Inicializa o handler.
        
        Args:
            metrics_service: Serviço de métricas
        """
        self.metrics_service = metrics_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retorna métricas de desempenho do sistema.
        
        Args:
            parameters: Parâmetros da requisição
                - metric_type (str, opcional): Tipo específico de métrica a retornar
                - operation (str, opcional): Nome da operação para filtrar estatísticas
                
        Returns:
            Resposta com métricas de desempenho
        """
        metric_type = parameters.get("metric_type")
        operation = parameters.get("operation")
        
        # Atualizar métricas de sistema antes de retornar resultados
        await self.metrics_service.update_system_metrics()
        
        if metric_type == "execution_times":
            data = self.metrics_service.get_execution_time_stats(operation)
        elif metric_type == "errors":
            data = self.metrics_service.get_error_stats()
        elif metric_type == "resource_usage":
            data = self.metrics_service.get_resource_usage_stats()
        elif metric_type == "operations_per_second":
            window_seconds = parameters.get("window_seconds", 60)
            data = self.metrics_service.get_operations_per_second(window_seconds)
        else:
            # Retornar todas as métricas se nenhum tipo específico for solicitado
            data = self.metrics_service.get_all_metrics()
            
        return self.success_response(data)


class ResetMetricsHandler(BaseHandler):
    """
    Handler para resetar métricas de desempenho.
    """
    
    def __init__(self, metrics_service: MetricsService):
        """
        Inicializa o handler.
        
        Args:
            metrics_service: Serviço de métricas
        """
        self.metrics_service = metrics_service
    
    async def handle(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reseta as métricas de desempenho do sistema.
        
        Args:
            parameters: Não utiliza parâmetros
            
        Returns:
            Resposta indicando sucesso
        """
        self.metrics_service.reset_metrics()
        return self.success_response({"message": "Métricas resetadas com sucesso"}) 