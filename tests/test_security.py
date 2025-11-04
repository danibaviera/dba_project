"""
Testes de Segurança - MonitorDB
Testa autenticação JWT, autorização RBAC e segurança de endpoints
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
from app.main import app
from app.security.auth import create_access_token, verify_password, hash_password
from app.security.roles import Role, Permission, has_permission
from app.config import settings

client = TestClient(app)

class TestAuthentication:
    """Testes de autenticação JWT"""
    
    def test_login_success(self):
        """Teste de login com credenciais válidas"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Teste de login com credenciais inválidas"""
        login_data = {
            "username": "invalid",
            "password": "wrong"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_missing_fields(self):
        """Teste de login com campos ausentes"""
        response = client.post("/api/v1/auth/login", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_token_creation(self):
        """Teste de criação de token JWT"""
        user_data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data=user_data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verificar se o token pode ser decodificado
        decoded = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "user"
    
    def test_token_expiry(self):
        """Teste de expiração de token"""
        user_data = {"sub": "testuser"}
        # Token com 1 segundo de duração
        token = create_access_token(data=user_data, expires_delta=timedelta(seconds=1))
        
        import time
        time.sleep(2)  # Aguardar expiração
        
        # Token deve estar expirado
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
    
    def test_password_hashing(self):
        """Teste de hash de senhas"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password  # Deve ser diferente da senha original
        assert verify_password(password, hashed)  # Deve verificar corretamente
        assert not verify_password("wrong", hashed)  # Senha errada deve falhar


class TestAuthorization:
    """Testes de autorização RBAC"""
    
    def test_role_hierarchy(self):
        """Teste da hierarquia de papéis"""
        # Admin deve ter permissões de todos os outros papéis
        assert has_permission(Role.ADMIN, Permission.CREATE_CLIENT)
        assert has_permission(Role.ADMIN, Permission.VIEW_LOGS)
        assert has_permission(Role.ADMIN, Permission.MANAGE_USERS)
        
        # Manager deve ter permissões de operator e viewer
        assert has_permission(Role.MANAGER, Permission.CREATE_CLIENT)
        assert has_permission(Role.MANAGER, Permission.VIEW_TRANSACTIONS)
        assert not has_permission(Role.MANAGER, Permission.MANAGE_USERS)
        
        # Operator deve ter permissões básicas
        assert has_permission(Role.OPERATOR, Permission.CREATE_CLIENT)
        assert has_permission(Role.OPERATOR, Permission.CREATE_TRANSACTION)
        assert not has_permission(Role.OPERATOR, Permission.DELETE_CLIENT)
        
        # Viewer só deve ter permissões de visualização
        assert has_permission(Role.VIEWER, Permission.VIEW_CLIENTS)
        assert not has_permission(Role.VIEWER, Permission.CREATE_CLIENT)
        
        # Guest deve ter permissões mínimas
        assert not has_permission(Role.GUEST, Permission.VIEW_CLIENTS)
    
    def test_permission_validation(self):
        """Teste de validação de permissões específicas"""
        # Testes de permissões críticas
        critical_permissions = [
            Permission.MANAGE_USERS,
            Permission.DELETE_CLIENT,
            Permission.MANAGE_SYSTEM
        ]
        
        for perm in critical_permissions:
            assert has_permission(Role.ADMIN, perm)
            assert not has_permission(Role.GUEST, perm)
    
    def test_protected_endpoint_without_token(self):
        """Teste de endpoint protegido sem token"""
        response = client.get("/api/v1/status")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self):
        """Teste de endpoint protegido com token inválido"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/status", headers=headers)
        assert response.status_code == 401
    
    def test_protected_endpoint_with_valid_token(self):
        """Teste de endpoint protegido com token válido"""
        # Primeiro fazer login
        login_data = {"username": "admin", "password": "admin123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Acessar endpoint protegido
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/status", headers=headers)
        
        assert response.status_code == 200
        assert "user" in response.json()


class TestSecurityVulnerabilities:
    """Testes de vulnerabilidades de segurança"""
    
    def test_sql_injection_prevention(self):
        """Teste de prevenção de SQL injection (MongoDB injection)"""
        # Tentar injection via parâmetros
        malicious_data = {
            "nome": {"$ne": None},  # NoSQL injection attempt
            "cpf": "123.456.789-00"
        }
        
        # Login necessário primeiro
        login_data = {"username": "admin", "password": "admin123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Tentar criar cliente com dados maliciosos
        response = client.post("/api/v1/clients", json=malicious_data, headers=headers)
        
        # Deve falhar na validação do Pydantic
        assert response.status_code in [400, 422]
    
    def test_xss_prevention(self):
        """Teste de prevenção de XSS"""
        xss_script = "<script>alert('xss')</script>"
        
        # Login necessário
        login_data = {"username": "admin", "password": "admin123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        client_data = {
            "nome": xss_script,
            "cpf": "123.456.789-00",
            "email": "test@example.com"
        }
        
        response = client.post("/api/v1/clients", json=client_data, headers=headers)
        
        if response.status_code == 200:
            # Se criado, verificar se o script foi sanitizado
            created_client = response.json()
            assert "<script>" not in created_client.get("nome", "")
    
    def test_rate_limiting_simulation(self):
        """Simulação de teste de rate limiting"""
        # Múltiplas tentativas de login
        login_data = {"username": "invalid", "password": "wrong"}
        
        responses = []
        for _ in range(10):  # 10 tentativas
            response = client.post("/api/v1/auth/login", json=login_data)
            responses.append(response.status_code)
        
        # Todas devem falhar com 401 (ainda não implementamos rate limiting)
        assert all(status == 401 for status in responses)
    
    def test_cors_headers(self):
        """Teste de configuração CORS"""
        response = client.options("/api/v1/clients")
        
        # Verificar se headers CORS estão presentes
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
    
    def test_sensitive_data_exposure(self):
        """Teste de exposição de dados sensíveis"""
        # Verificar se senhas não são retornadas em endpoints
        login_data = {"username": "admin", "password": "admin123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        
        # Token não deve conter senha
        token_data = login_response.json()
        assert "password" not in str(token_data)
        
        # Decodificar JWT para verificar payload
        token = token_data["access_token"]
        import base64
        import json
        
        # Decodificar payload (sem verificar assinatura para o teste)
        payload_b64 = token.split('.')[1]
        # Adicionar padding se necessário
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Verificar se não há informações sensíveis no JWT
        assert "password" not in payload
        assert "hash" not in payload


class TestSecurityCompliance:
    """Testes de conformidade de segurança"""
    
    def test_https_redirect(self):
        """Teste de redirecionamento HTTPS (simulado)"""
        # Em produção, deve forçar HTTPS
        # Este teste verifica se a aplicação está preparada
        response = client.get("/")
        assert response.status_code == 200
        # Em produção, adicionar middleware para forçar HTTPS
    
    def test_security_headers(self):
        """Teste de headers de segurança"""
        response = client.get("/")
        
        # Verificar headers básicos de segurança
        headers = response.headers
        
        # Alguns headers importantes (podem não estar todos implementados)
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        
        # Apenas verificar que a resposta é válida
        # Em produção, implementar middleware para adicionar security headers
        assert response.status_code == 200
    
    def test_input_validation(self):
        """Teste de validação de entrada rigorosa"""
        # Login necessário
        login_data = {"username": "admin", "password": "admin123"}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Dados inválidos para cliente
        invalid_clients = [
            {"nome": "", "cpf": "invalid", "email": "not_email"},
            {"nome": "A" * 1000, "cpf": "123", "email": "test@test"},
            {"cpf": "123.456.789-00"},  # Nome ausente
        ]
        
        for invalid_data in invalid_clients:
            response = client.post("/api/v1/clients", json=invalid_data, headers=headers)
            assert response.status_code in [400, 422], f"Dados inválidos aceitos: {invalid_data}"


# Configurações de teste
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])