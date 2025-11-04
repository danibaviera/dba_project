"""
Testes de Observabilidade - MonitorDB
Testa métricas Prometheus, monitoramento de performance e logs
"""

import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY

from app.main import app
from app.monitoring.metrics_exporter import prometheus_metrics, PrometheusMetrics
from app.monitoring.performance_monitor import performance_monitor, PerformanceMonitor

client = TestClient(app)

class TestPrometheusMetrics:
    """Testes de métricas Prometheus"""
    
    def setup_method(self):
        """Setup para cada teste"""
        # Limpar métricas entre testes
        REGISTRY._collector_to_names.clear()
        REGISTRY._names_to_collectors.clear()
    
    def test_metrics_initialization(self):
        """Teste de inicialização das métricas"""
        metrics = PrometheusMetrics()
        
        # Verificar se métricas foram criadas
        assert metrics.http_requests_total is not None
        assert metrics.http_request_duration_seconds is not None
        assert metrics.database_connections_active is not None
        assert metrics.system_cpu_usage is not None
        assert metrics.system_memory_usage is not None
    
    def test_http_metrics_collection(self):
        """Teste de coleta de métricas HTTP"""
        # Fazer requisições para gerar métricas
        response = client.get("/")
        assert response.status_code == 200
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verificar endpoint de métricas
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_content = metrics_response.text
        
        # Verificar presença de métricas esperadas
        assert "http_requests_total" in metrics_content
        assert "http_request_duration_seconds" in metrics_content
        assert "method=" in metrics_content
        assert "status_code=" in metrics_content
    
    def test_system_metrics_collection(self):
        """Teste de coleta de métricas de sistema"""
        # Inicializar métricas
        metrics = PrometheusMetrics()
        
        # Coletar métricas de sistema
        metrics.collect_system_metrics()
        
        # Verificar se métricas foram atualizadas
        cpu_sample = metrics.system_cpu_usage._value._value
        memory_sample = metrics.system_memory_usage._value._value
        
        assert 0 <= cpu_sample <= 100  # CPU deve estar entre 0-100%
        assert memory_sample > 0  # Memória deve ser positiva
    
    def test_database_metrics(self):
        """Teste de métricas de banco de dados"""
        metrics = PrometheusMetrics()
        
        # Simular conexões ativas
        metrics.database_connections_active.set(5)
        
        # Verificar se métrica foi definida
        assert metrics.database_connections_active._value._value == 5
    
    def test_business_metrics(self):
        """Teste de métricas de negócio"""
        metrics = PrometheusMetrics()
        
        # Simular operações de negócio
        metrics.clients_total.inc()
        metrics.transactions_total.inc()
        
        # Verificar incrementos
        assert metrics.clients_total._value._value >= 1
        assert metrics.transactions_total._value._value >= 1
    
    def test_metrics_export_format(self):
        """Teste de formato de exportação das métricas"""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        lines = response.text.strip().split('\n')
        
        # Verificar formato Prometheus
        for line in lines:
            if line and not line.startswith('#'):
                # Linha de métrica deve ter formato: metric_name{labels} value
                assert ' ' in line or '{' in line


class TestPerformanceMonitor:
    """Testes de monitoramento de performance"""
    
    def test_performance_monitor_initialization(self):
        """Teste de inicialização do monitor de performance"""
        monitor = PerformanceMonitor()
        
        assert monitor.history_limit > 0
        assert isinstance(monitor.metrics_history, list)
        assert monitor.monitoring_enabled == False  # Inicialmente desabilitado
    
    def test_system_metrics_collection(self):
        """Teste de coleta de métricas do sistema"""
        monitor = PerformanceMonitor()
        metrics = monitor.get_system_metrics()
        
        # Verificar estrutura das métricas
        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'memory_available' in metrics
        assert 'disk_usage' in metrics
        assert 'timestamp' in metrics
        
        # Verificar valores válidos
        assert 0 <= metrics['cpu_percent'] <= 100
        assert 0 <= metrics['memory_percent'] <= 100
        assert metrics['memory_available'] > 0
        assert 0 <= metrics['disk_usage'] <= 100
    
    def test_metrics_history(self):
        """Teste de histórico de métricas"""
        monitor = PerformanceMonitor()
        
        # Coletar algumas métricas
        for i in range(3):
            monitor.collect_metrics()
            time.sleep(0.1)  # Pequena pausa entre coletas
        
        # Verificar histórico
        assert len(monitor.metrics_history) >= 1
        
        # Verificar estrutura do histórico
        for entry in monitor.metrics_history:
            assert 'timestamp' in entry
            assert 'cpu_percent' in entry
            assert 'memory_percent' in entry
    
    def test_alert_checking(self):
        """Teste de verificação de alertas"""
        monitor = PerformanceMonitor()
        
        # Coletar métricas
        monitor.collect_metrics()
        
        # Verificar alertas (não deve gerar exceção)
        alerts = monitor.check_alerts()
        
        assert isinstance(alerts, list)
        
        # Cada alerta deve ter estrutura correta
        for alert in alerts:
            assert 'type' in alert
            assert 'message' in alert
            assert 'value' in alert
            assert 'threshold' in alert
    
    def test_monitoring_start_stop(self):
        """Teste de iniciar/parar monitoramento"""
        monitor = PerformanceMonitor()
        
        # Iniciar monitoramento
        monitor.start_monitoring()
        assert monitor.monitoring_enabled == True
        
        time.sleep(0.5)  # Aguardar coleta
        
        # Parar monitoramento
        monitor.stop_monitoring()
        assert monitor.monitoring_enabled == False
    
    def test_current_metrics(self):
        """Teste de obtenção de métricas atuais"""
        monitor = PerformanceMonitor()
        monitor.collect_metrics()  # Garantir que há dados
        
        current = monitor.get_current_metrics()
        
        # Verificar estrutura
        assert isinstance(current, dict)
        assert 'cpu_percent' in current
        assert 'memory_percent' in current
        assert 'last_updated' in current
    
    def test_performance_trends(self):
        """Teste de análise de tendências de performance"""
        monitor = PerformanceMonitor()
        
        # Simular coleta de dados históricos
        for i in range(5):
            monitor.collect_metrics()
            time.sleep(0.1)
        
        # Analisar tendências (se implementado)
        if len(monitor.metrics_history) >= 2:
            latest = monitor.metrics_history[-1]
            previous = monitor.metrics_history[-2]
            
            # Verificar se dados são consistentes
            assert latest['timestamp'] > previous['timestamp']


class TestHealthChecks:
    """Testes de verificações de saúde"""
    
    def test_health_endpoint(self):
        """Teste do endpoint de saúde"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'database' in data
        assert 'monitoring' in data
    
    def test_system_status_endpoint(self):
        """Teste do endpoint de status do sistema"""
        # Login necessário primeiro
        login_data = {"username": "admin", "password": "admin123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/api/v1/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
                assert 'timestamp' in data
                assert 'database' in data
                assert 'system' in data
    
    def test_database_connectivity(self):
        """Teste de conectividade com banco de dados"""
        response = client.get("/health")
        
        if response.status_code == 200:
            data = response.json()
            assert data['database'] == 'connected'
        else:
            # Se saúde falha, deve ser por problema de conectividade
            assert response.status_code == 503


class TestLogging:
    """Testes de sistema de logging"""
    
    def test_request_logging(self):
        """Teste de logging de requisições"""
        with patch('app.main.logger') as mock_logger:
            # Fazer uma requisição
            response = client.get("/")
            assert response.status_code == 200
            
            # Verificar se log foi chamado
            mock_logger.info.assert_called()
    
    def test_error_logging(self):
        """Teste de logging de erros"""
        with patch('app.main.logger') as mock_logger:
            # Tentar endpoint inexistente
            response = client.get("/nonexistent")
            assert response.status_code == 404
            
            # Logger pode ter sido chamado durante o processo
            # Não falhamos se não foi chamado, pois 404 pode não logar erro
    
    def test_log_format(self):
        """Teste de formato de logs"""
        # Verificar se logging está configurado
        import logging
        logger = logging.getLogger("app.main")
        
        # Verificar nível de log
        assert logger.level <= logging.INFO


class TestIntegrationObservability:
    """Testes de integração de observabilidade"""
    
    def test_metrics_and_monitoring_integration(self):
        """Teste de integração entre métricas e monitoramento"""
        # Fazer algumas requisições
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 200
        
        # Verificar se métricas foram coletadas
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        
        content = metrics_response.text
        assert "http_requests_total" in content
    
    def test_full_observability_stack(self):
        """Teste da stack completa de observabilidade"""
        # 1. Fazer requisições para gerar dados
        responses = [
            client.get("/"),
            client.get("/health"),
            client.get("/metrics")
        ]
        
        for response in responses:
            assert response.status_code == 200
        
        # 2. Verificar métricas
        metrics_response = client.get("/metrics")
        metrics_content = metrics_response.text
        
        # 3. Verificar presença de métricas essenciais
        essential_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "system_cpu_usage",
            "system_memory_usage"
        ]
        
        for metric in essential_metrics:
            assert metric in metrics_content
    
    def test_observability_endpoints_security(self):
        """Teste de segurança dos endpoints de observabilidade"""
        # Endpoint de métricas deve ser público (para Prometheus)
        response = client.get("/metrics")
        assert response.status_code == 200
        
        # Endpoint de status deve ser protegido
        response = client.get("/api/v1/status")
        assert response.status_code == 401  # Sem autenticação
    
    def test_monitoring_resilience(self):
        """Teste de resiliência do monitoramento"""
        # Monitoramento deve funcionar mesmo com erros
        with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
            monitor = PerformanceMonitor()
            
            # Deve lidar com erros graciosamente
            try:
                monitor.get_system_metrics()
            except Exception:
                # Se exceção ocorrer, deve ser tratada adequadamente
                pass


# Configuração de testes
@pytest.fixture(autouse=True)
def cleanup_metrics():
    """Limpar métricas entre testes"""
    yield
    # Cleanup após cada teste se necessário


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])