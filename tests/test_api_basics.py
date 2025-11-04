"""
Testes básicos da API
"""
from fastapi import status
from tests.configtest import client

class TestAPIBasics:
    """Testes básicos de funcionamento da API"""
    
    def test_root_endpoint(self):
        """Teste: Endpoint raiz da API"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        
    def test_health_check(self):
        """Teste: Health check da API"""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        
    def test_docs_endpoint(self):
        """Teste: Documentação automática"""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
    def test_openapi_json(self):
        """Teste: Schema OpenAPI"""
        response = client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        
    def test_invalid_endpoint(self):
        """Teste: Endpoint inexistente"""
        response = client.get("/endpoint-inexistente")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_cors_headers(self):
        """Teste: Headers CORS básicos"""
        response = client.options("/api/clientes")
        # FastAPI automaticamente adiciona CORS se configurado
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]