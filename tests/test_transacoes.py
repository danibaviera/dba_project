"""
Testes CRUD para Transações
"""
from fastapi import status
from tests.configtest import client, CLIENTE_TEST_DATA, TRANSACAO_TEST_DATA

class TestTransacoesCRUD:
    """Testes das operações CRUD de transações"""
    
    def setup_method(self):
        """Criar cliente de teste para as transações"""
        response = client.post("/api/clientes", json=CLIENTE_TEST_DATA)
        self.cliente_id = response.json()["id"]
        
    def teardown_method(self):
        """Limpar dados após cada teste"""
        # Deletar transações do cliente
        client.delete(f"/api/clientes/{self.cliente_id}")
        
    def test_create_transacao_success(self):
        """Teste: Criar transação válida"""
        transacao_data = TRANSACAO_TEST_DATA.copy()
        transacao_data["id_cliente"] = self.cliente_id
        
        response = client.post("/api/transacoes", json=transacao_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["valor"] == TRANSACAO_TEST_DATA["valor"]
        assert data["tipo"] == TRANSACAO_TEST_DATA["tipo"]
        assert data["id_cliente"] == self.cliente_id
        assert "id" in data
        
    def test_create_transacao_invalid_cliente(self):
        """Teste: Criar transação com cliente inexistente"""
        transacao_data = TRANSACAO_TEST_DATA.copy()
        transacao_data["id_cliente"] = "507f1f77bcf86cd799439011"  # ID inexistente
        
        response = client.post("/api/transacoes", json=transacao_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_create_transacao_invalid_valor(self):
        """Teste: Criar transação com valor inválido"""
        transacao_data = TRANSACAO_TEST_DATA.copy()
        transacao_data["id_cliente"] = self.cliente_id
        transacao_data["valor"] = -100  # Valor negativo
        
        response = client.post("/api/transacoes", json=transacao_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_create_transacao_invalid_tipo(self):
        """Teste: Criar transação com tipo inválido"""
        transacao_data = TRANSACAO_TEST_DATA.copy()
        transacao_data["id_cliente"] = self.cliente_id
        transacao_data["tipo"] = "tipo_invalido"
        
        response = client.post("/api/transacoes", json=transacao_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_get_transacoes_by_cliente(self):
        """Teste: Buscar transações por cliente"""
        # Criar algumas transações
        for i in range(3):
            transacao_data = TRANSACAO_TEST_DATA.copy()
            transacao_data["id_cliente"] = self.cliente_id
            transacao_data["valor"] = 100 + i
            client.post("/api/transacoes", json=transacao_data)
        
        # Buscar transações do cliente
        response = client.get(f"/api/clientes/{self.cliente_id}/transacoes")
        
        assert response.status_code == status.HTTP_200_OK
        transacoes = response.json()
        assert len(transacoes) == 3
        
    def test_update_transacao_status(self):
        """Teste: Atualizar status da transação"""
        # Criar transação
        transacao_data = TRANSACAO_TEST_DATA.copy()
        transacao_data["id_cliente"] = self.cliente_id
        create_response = client.post("/api/transacoes", json=transacao_data)
        transacao_id = create_response.json()["id"]
        
        # Atualizar status
        update_data = {"status": "aprovada"}
        response = client.put(f"/api/transacoes/{transacao_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        updated_data = response.json()
        assert updated_data["status"] == "aprovada"
        
    def test_delete_transacao(self):
        """Teste: Deletar transação"""
        # Criar transação
        transacao_data = TRANSACAO_TEST_DATA.copy()
        transacao_data["id_cliente"] = self.cliente_id
        create_response = client.post("/api/transacoes", json=transacao_data)
        transacao_id = create_response.json()["id"]
        
        # Deletar transação
        response = client.delete(f"/api/transacoes/{transacao_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar se foi deletada
        get_response = client.get(f"/api/transacoes/{transacao_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_transacao_tipos_validos(self):
        """Teste: Todos os tipos válidos de transação"""
        tipos_validos = ["credito", "debito", "pix", "transferencia", "boleto"]
        
        for tipo in tipos_validos:
            transacao_data = TRANSACAO_TEST_DATA.copy()
            transacao_data["id_cliente"] = self.cliente_id
            transacao_data["tipo"] = tipo
            transacao_data["valor"] = 50.0
            
            response = client.post("/api/transacoes", json=transacao_data)
            assert response.status_code == status.HTTP_201_CREATED
            
            # Limpar transação criada
            transacao_id = response.json()["id"]
            client.delete(f"/api/transacoes/{transacao_id}")
            
    def test_transacao_status_validos(self):
        """Teste: Todos os status válidos de transação"""
        status_validos = ["pendente", "aprovada", "rejeitada", "cancelada"]
        
        for status_transacao in status_validos:
            transacao_data = TRANSACAO_TEST_DATA.copy()
            transacao_data["id_cliente"] = self.cliente_id
            transacao_data["status"] = status_transacao
            
            response = client.post("/api/transacoes", json=transacao_data)
            assert response.status_code == status.HTTP_201_CREATED
            
            # Limpar transação criada
            transacao_id = response.json()["id"]
            client.delete(f"/api/transacoes/{transacao_id}")