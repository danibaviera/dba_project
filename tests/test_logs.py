"""
Testes CRUD para Logs de Acesso
"""
from fastapi import status
from tests.configtest import client, CLIENTE_TEST_DATA, LOG_ACESSO_TEST_DATA

class TestLogsAcessoCRUD:
    """Testes das operações CRUD de logs de acesso"""
    
    def setup_method(self):
        """Criar cliente de teste para os logs"""
        response = client.post("/api/clientes", json=CLIENTE_TEST_DATA)
        self.cliente_id = response.json()["id"]
        
    def teardown_method(self):
        """Limpar dados após cada teste"""
        client.delete(f"/api/clientes/{self.cliente_id}")
        
    def test_create_log_acesso_success(self):
        """Teste: Criar log de acesso válido"""
        log_data = LOG_ACESSO_TEST_DATA.copy()
        log_data["id_cliente"] = self.cliente_id
        
        response = client.post("/api/logs", json=log_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["acao"] == LOG_ACESSO_TEST_DATA["acao"]
        assert data["ip"] == LOG_ACESSO_TEST_DATA["ip"]
        assert data["id_cliente"] == self.cliente_id
        assert "id" in data
        
    def test_create_log_acesso_without_cliente(self):
        """Teste: Criar log de acesso sem cliente (acesso público)"""
        log_data = LOG_ACESSO_TEST_DATA.copy()
        # Não definir id_cliente (opcional)
        
        response = client.post("/api/logs", json=log_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["acao"] == LOG_ACESSO_TEST_DATA["acao"]
        assert data["id_cliente"] is None
        
    def test_create_log_invalid_ip(self):
        """Teste: Criar log com IP inválido"""
        log_data = LOG_ACESSO_TEST_DATA.copy()
        log_data["ip"] = "ip_invalido"
        
        response = client.post("/api/logs", json=log_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_create_log_invalid_acao(self):
        """Teste: Criar log com ação inválida"""
        log_data = LOG_ACESSO_TEST_DATA.copy()
        log_data["acao"] = "acao_invalida"
        
        response = client.post("/api/logs", json=log_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_get_logs_by_cliente(self):
        """Teste: Buscar logs por cliente"""
        # Criar alguns logs
        for i in range(3):
            log_data = LOG_ACESSO_TEST_DATA.copy()
            log_data["id_cliente"] = self.cliente_id
            log_data["acao"] = ["create", "read", "update"][i]
            client.post("/api/logs", json=log_data)
        
        # Buscar logs do cliente
        response = client.get(f"/api/clientes/{self.cliente_id}/logs")
        
        assert response.status_code == status.HTTP_200_OK
        logs = response.json()
        assert len(logs) >= 3
        
    def test_get_logs_all(self):
        """Teste: Buscar todos os logs"""
        # Criar alguns logs
        for i in range(2):
            log_data = LOG_ACESSO_TEST_DATA.copy()
            if i == 0:
                log_data["id_cliente"] = self.cliente_id
            # Segundo log sem cliente
            client.post("/api/logs", json=log_data)
        
        response = client.get("/api/logs")
        
        assert response.status_code == status.HTTP_200_OK
        logs = response.json()
        assert len(logs) >= 2
        
    def test_log_acoes_validas(self):
        """Teste: Todas as ações válidas de log"""
        acoes_validas = ["login", "logout", "create", "read", "update", "delete", "error"]
        
        for acao in acoes_validas:
            log_data = LOG_ACESSO_TEST_DATA.copy()
            log_data["acao"] = acao
            
            response = client.post("/api/logs", json=log_data)
            assert response.status_code == status.HTTP_201_CREATED
            
    def test_log_status_codes_validos(self):
        """Teste: Status codes válidos"""
        status_codes = [200, 201, 400, 401, 404, 500]
        
        for status_code in status_codes:
            log_data = LOG_ACESSO_TEST_DATA.copy()
            log_data["status_code"] = status_code
            
            response = client.post("/api/logs", json=log_data)
            assert response.status_code == status.HTTP_201_CREATED
            
    def test_log_status_code_invalid(self):
        """Teste: Status code inválido"""
        log_data = LOG_ACESSO_TEST_DATA.copy()
        log_data["status_code"] = 99  # Menor que 100
        
        response = client.post("/api/logs", json=log_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        log_data["status_code"] = 600  # Maior que 599
        response = client.post("/api/logs", json=log_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY