"""
Monitor de Performance do Sistema
Coleta métricas detalhadas do sistema operacional e aplicação
"""

import psutil
import time
import threading
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor de performance do sistema"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.metrics_history = []
        self.max_history_size = 1000  # Manter últimas 1000 medições
        self._monitoring = False
        self._monitor_thread = None
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Coleta métricas completas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memória
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disco
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Rede
            network_io = psutil.net_io_counters()
            
            # Processos
            processes = len(psutil.pids())
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.utcnow() - boot_time
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else None
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "percent": memory.percent,
                    "swap_total_gb": swap.total / (1024**3),
                    "swap_used_gb": swap.used / (1024**3),
                    "swap_percent": swap.percent
                },
                "disk": {
                    "total_gb": disk_usage.total / (1024**3),
                    "used_gb": disk_usage.used / (1024**3),
                    "free_gb": disk_usage.free / (1024**3),
                    "percent": (disk_usage.used / disk_usage.total) * 100,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                },
                "network": {
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv
                },
                "system": {
                    "processes_count": processes,
                    "boot_time": boot_time.isoformat(),
                    "uptime_seconds": uptime.total_seconds()
                }
            }
        
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do sistema: {e}")
            return {"error": str(e)}
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """Coleta métricas do processo atual da aplicação"""
        try:
            current_process = psutil.Process()
            
            # CPU do processo
            cpu_percent = current_process.cpu_percent()
            
            # Memória do processo
            memory_info = current_process.memory_info()
            memory_percent = current_process.memory_percent()
            
            # I/O do processo
            io_counters = current_process.io_counters()
            
            # Threads
            threads_count = current_process.num_threads()
            
            # Arquivos abertos
            open_files = len(current_process.open_files())
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "process": {
                    "pid": current_process.pid,
                    "name": current_process.name(),
                    "status": current_process.status(),
                    "create_time": datetime.fromtimestamp(current_process.create_time()).isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_rss_mb": memory_info.rss / (1024**2),
                    "memory_vms_mb": memory_info.vms / (1024**2),
                    "memory_percent": memory_percent,
                    "threads_count": threads_count,
                    "open_files_count": open_files,
                    "io_read_count": io_counters.read_count,
                    "io_write_count": io_counters.write_count,
                    "io_read_bytes": io_counters.read_bytes,
                    "io_write_bytes": io_counters.write_bytes
                }
            }
        
        except Exception as e:
            logger.error(f"Erro ao coletar métricas do processo: {e}")
            return {"error": str(e)}
    
    def get_top_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna os processos que mais consomem recursos"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Ordenar por CPU
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            return processes[:limit]
        
        except Exception as e:
            logger.error(f"Erro ao obter top processos: {e}")
            return []
    
    def start_monitoring(self, interval: int = 60):
        """Inicia monitoramento contínuo"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Monitoramento de performance iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Monitoramento de performance parado")
    
    def _monitor_loop(self, interval: int):
        """Loop principal do monitoramento"""
        while self._monitoring:
            try:
                metrics = self.get_system_metrics()
                metrics.update(self.get_process_metrics())
                
                # Adicionar ao histórico
                self.metrics_history.append(metrics)
                
                # Limitar tamanho do histórico
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(interval)
    
    def get_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Retorna histórico de métricas dos últimos N minutos"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        filtered_metrics = []
        for metric in self.metrics_history:
            try:
                metric_time = datetime.fromisoformat(metric["timestamp"].replace('Z', '+00:00'))
                if metric_time >= cutoff_time:
                    filtered_metrics.append(metric)
            except:
                continue
        
        return filtered_metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retorna resumo de performance"""
        try:
            current_metrics = self.get_system_metrics()
            process_metrics = self.get_process_metrics()
            
            # Calcular médias do histórico recente (última hora)
            recent_history = self.get_metrics_history(60)
            
            avg_cpu = 0
            avg_memory = 0
            if recent_history:
                avg_cpu = sum(m.get("cpu", {}).get("percent", 0) for m in recent_history) / len(recent_history)
                avg_memory = sum(m.get("memory", {}).get("percent", 0) for m in recent_history) / len(recent_history)
            
            return {
                "summary": {
                    "monitoring_since": self.start_time.isoformat(),
                    "metrics_collected": len(self.metrics_history),
                    "current_cpu_percent": current_metrics.get("cpu", {}).get("percent", 0),
                    "current_memory_percent": current_metrics.get("memory", {}).get("percent", 0),
                    "avg_cpu_percent_1h": round(avg_cpu, 2),
                    "avg_memory_percent_1h": round(avg_memory, 2),
                    "process_memory_mb": process_metrics.get("process", {}).get("memory_rss_mb", 0),
                    "process_threads": process_metrics.get("process", {}).get("threads_count", 0)
                },
                "current": current_metrics,
                "process": process_metrics
            }
        
        except Exception as e:
            logger.error(f"Erro ao gerar resumo de performance: {e}")
            return {"error": str(e)}
    
    def check_performance_alerts(self) -> List[Dict[str, Any]]:
        """Verifica se há alertas de performance"""
        alerts = []
        
        try:
            metrics = self.get_system_metrics()
            
            # CPU alto
            cpu_percent = metrics.get("cpu", {}).get("percent", 0)
            if cpu_percent > 80:
                alerts.append({
                    "type": "high_cpu",
                    "severity": "warning" if cpu_percent < 90 else "critical",
                    "message": f"CPU usage is {cpu_percent:.1f}%",
                    "value": cpu_percent,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Memória alta
            memory_percent = metrics.get("memory", {}).get("percent", 0)
            if memory_percent > 80:
                alerts.append({
                    "type": "high_memory",
                    "severity": "warning" if memory_percent < 90 else "critical",
                    "message": f"Memory usage is {memory_percent:.1f}%",
                    "value": memory_percent,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Disco alto
            disk_percent = metrics.get("disk", {}).get("percent", 0)
            if disk_percent > 85:
                alerts.append({
                    "type": "high_disk",
                    "severity": "warning" if disk_percent < 95 else "critical",
                    "message": f"Disk usage is {disk_percent:.1f}%",
                    "value": disk_percent,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de performance: {e}")
        
        return alerts

# Instância global
performance_monitor = PerformanceMonitor()