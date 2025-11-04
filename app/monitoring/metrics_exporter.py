"""
Exportador de Métricas Prometheus
Coleta e expõe métricas do sistema e aplicação
"""

import time
import psutil
import threading
from typing import Dict, Any
from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    start_http_server, CollectorRegistry, 
    generate_latest, CONTENT_TYPE_LATEST
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PrometheusMetrics:
    """Classe principal para coleta de métricas"""
    
    def __init__(self):
        # Registry customizado
        self.registry = CollectorRegistry()
        
        # Métricas HTTP
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total de requisições HTTP',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'Duração das requisições HTTP',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Métricas da aplicação
        self.active_connections = Gauge(
            'mongodb_connections_active',
            'Conexões ativas com MongoDB',
            registry=self.registry
        )
        
        self.database_operations = Counter(
            'database_operations_total',
            'Total de operações no banco',
            ['operation', 'collection'],
            registry=self.registry
        )
        
        # Métricas do sistema
        self.system_cpu_percent = Gauge(
            'system_cpu_percent',
            'Percentual de uso da CPU',
            registry=self.registry
        )
        
        self.system_memory_percent = Gauge(
            'system_memory_percent',
            'Percentual de uso da memória',
            registry=self.registry
        )
        
        self.system_disk_percent = Gauge(
            'system_disk_percent',
            'Percentual de uso do disco',
            ['device'],
            registry=self.registry
        )
        
        # Métricas de negócio
        self.clientes_total = Gauge(
            'clientes_total',
            'Total de clientes cadastrados',
            registry=self.registry
        )
        
        self.transacoes_total = Counter(
            'transacoes_total',
            'Total de transações processadas',
            ['tipo', 'status'],
            registry=self.registry
        )
        
        self.transacoes_valor_total = Gauge(
            'transacoes_valor_total',
            'Valor total das transações',
            ['tipo'],
            registry=self.registry
        )
        
        # Informações da aplicação
        self.app_info = Info(
            'monitordb_app_info',
            'Informações da aplicação MonitorDB',
            registry=self.registry
        )
        
        # Configurar informações básicas
        self.app_info.info({
            'version': '2.0.0',
            'name': 'MonitorDB API',
            'environment': 'development'
        })
        
        # Thread para coleta automática
        self._collecting = False
        self._collect_thread = None
        
    def start_auto_collection(self, interval: int = 30):
        """Inicia coleta automática de métricas do sistema"""
        if self._collecting:
            return
            
        self._collecting = True
        self._collect_thread = threading.Thread(
            target=self._auto_collect_system_metrics,
            args=(interval,),
            daemon=True
        )
        self._collect_thread.start()
        logger.info(f"Coleta automática de métricas iniciada (intervalo: {interval}s)")
    
    def stop_auto_collection(self):
        """Para a coleta automática"""
        self._collecting = False
        if self._collect_thread:
            self._collect_thread.join(timeout=5)
        logger.info("Coleta automática de métricas parada")
    
    def _auto_collect_system_metrics(self, interval: int):
        """Thread para coleta automática de métricas do sistema"""
        while self._collecting:
            try:
                self.update_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Erro na coleta automática de métricas: {e}")
                time.sleep(interval)
    
    def update_system_metrics(self):
        """Atualiza métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_percent.set(cpu_percent)
            
            # Memória
            memory = psutil.virtual_memory()
            self.system_memory_percent.set(memory.percent)
            
            # Disco
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            self.system_disk_percent.labels(device='/').set(disk_percent)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas do sistema: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Registra métrica de requisição HTTP"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_database_operation(self, operation: str, collection: str):
        """Registra operação no banco de dados"""
        self.database_operations.labels(
            operation=operation,
            collection=collection
        ).inc()
    
    def update_business_metrics(self, clientes_count: int, transacoes_stats: Dict[str, Any]):
        """Atualiza métricas de negócio"""
        self.clientes_total.set(clientes_count)
        
        # Transações por tipo e status
        for tipo, stats in transacoes_stats.items():
            if isinstance(stats, dict):
                for status, count in stats.items():
                    self.transacoes_total.labels(tipo=tipo, status=status)._value._value = count
    
    def record_log_entry(self, level: str, category: str):
        """Registra entrada de log (para análise)"""
        # Pode ser usado para métricas de logs
        pass
    
    def get_metrics(self) -> str:
        """Retorna métricas no formato Prometheus"""
        return generate_latest(self.registry)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas em formato JSON"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_total_gb": memory.total / (1024**3),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_total_gb": disk.total / (1024**3)
                },
                "application": {
                    "uptime_seconds": time.time() - self._start_time if hasattr(self, '_start_time') else 0,
                    "active_connections": 1  # Placeholder
                }
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de métricas: {e}")
            return {"error": str(e)}

# Instância global
prometheus_metrics = PrometheusMetrics()

def start_metrics_server(port: int = 8001):
    """Inicia servidor HTTP para métricas Prometheus"""
    try:
        start_http_server(port, registry=prometheus_metrics.registry)
        prometheus_metrics._start_time = time.time()
        prometheus_metrics.start_auto_collection()
        logger.info(f"Servidor de métricas Prometheus iniciado na porta {port}")
        return True
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor de métricas: {e}")
        return False

def stop_metrics_server():
    """Para o servidor de métricas"""
    prometheus_metrics.stop_auto_collection()
    logger.info("Servidor de métricas parado")