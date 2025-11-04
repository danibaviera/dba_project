"""
Configuração base para testes
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.config import settings

# Cliente de teste FastAPI
client = TestClient(app)

# Configurações de teste
TEST_DATABASE = "monitor_db_test"
TEST_MONGO_URI = "mongodb://localhost:27017"

@pytest.fixture
def test_client():
    """Cliente de teste para FastAPI"""
    return client

@pytest.fixture
async def test_db():
    """Conexão de teste com MongoDB"""
    client = AsyncIOMotorClient(TEST_MONGO_URI)
    db = client[TEST_DATABASE]
    
    # Limpar dados de teste antes de cada teste
    await db.clientes.delete_many({})
    await db.transacoes.delete_many({})
    await db.logs_acesso.delete_many({})
    
    yield db
    
    # Limpar após o teste
    await db.clientes.delete_many({})
    await db.transacoes.delete_many({})
    await db.logs_acesso.delete_many({})
    client.close()

# Dados de teste reutilizáveis
CLIENTE_TEST_DATA = {
    "nome": "João da Silva",
    "email": "joao.silva@teste.com",
    "cpf": "11144477735",  # CPF válido
    "telefone": "11987654321",
    "endereco": "Rua Teste, 123"
}

TRANSACAO_TEST_DATA = {
    "valor": 100.50,
    "tipo": "pix",
    "descricao": "Teste de transação PIX"
}

LOG_ACESSO_TEST_DATA = {
    "acao": "create",
    "ip": "192.168.1.1",
    "user_agent": "TestAgent/1.0",
    "endpoint": "/api/clientes",
    "status_code": 201
}