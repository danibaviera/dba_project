"""
Testes CRUD para Clientes
"""
import pytest
from fastapi import status
from tests.configtest import client, CLIENTE_TEST_DATA

class TestClientesCRUD:
    """Testes das operações CRUD de clientes"""
    
    def test_create_cliente_success(self):
        """Teste: Criar cliente com dados válidos"""
        response = client.post("/api/clientes", json=CLIENTE_TEST_DATA)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["nome"] == CLIENTE_TEST_DATA["nome"]
        assert data["email"] == CLIENTE_TEST_DATA["email"]
        assert data["cpf"] == CLIENTE_TEST_DATA["cpf"]
        assert "id" in data
        
    def test_create_cliente_invalid_cpf(self):
        """Teste: Criar cliente com CPF inválido"""
        invalid_data = CLIENTE_TEST_DATA.copy()
        invalid_data["cpf"] = "12345678901"  # CPF inválido
        
        response = client.post("/api/clientes", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_create_cliente_invalid_email(self):
        """Teste: Criar cliente com email inválido"""
        invalid_data = CLIENTE_TEST_DATA.copy()
        invalid_data["email"] = "email-invalido"
        
        response = client.post("/api/clientes", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_get_clientes_empty(self):
        """Teste: Listar clientes quando não há nenhum"""
        response = client.get("/api/clientes")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        
    def test_get_cliente_not_found(self):
        """Teste: Buscar cliente que não existe"""
        fake_id = "507f1f77bcf86cd799439011"  # ObjectId válido mas inexistente
        response = client.get(f"/api/clientes/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_full_crud_cliente(self):
        """Teste: Fluxo completo CRUD de cliente"""
        # 1. CREATE - Criar cliente
        create_response = client.post("/api/clientes", json=CLIENTE_TEST_DATA)
        assert create_response.status_code == status.HTTP_201_CREATED
        cliente_data = create_response.json()
        cliente_id = cliente_data["id"]
        
        # 2. READ - Buscar cliente específico
        get_response = client.get(f"/api/clientes/{cliente_id}")
        assert get_response.status_code == status.HTTP_200_OK
        get_data = get_response.json()
        assert get_data["id"] == cliente_id
        assert get_data["nome"] == CLIENTE_TEST_DATA["nome"]
        
        # 3. UPDATE - Atualizar cliente
        update_data = {"nome": "João Silva Atualizado"}
        update_response = client.put(f"/api/clientes/{cliente_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        updated_data = update_response.json()
        assert updated_data["nome"] == "João Silva Atualizado"
        
        # 4. LIST - Verificar se aparece na listagem
        list_response = client.get("/api/clientes")
        assert list_response.status_code == status.HTTP_200_OK
        clientes_list = list_response.json()
        assert len(clientes_list) >= 1
        assert any(c["id"] == cliente_id for c in clientes_list)
        
        # 5. DELETE - Deletar cliente
        delete_response = client.delete(f"/api/clientes/{cliente_id}")
        assert delete_response.status_code == status.HTTP_200_OK
        
        # 6. VERIFY DELETE - Verificar se foi deletado
        verify_response = client.get(f"/api/clientes/{cliente_id}")
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
        
    def test_update_cliente_partial(self):
        """Teste: Atualização parcial de cliente"""
        # Criar cliente primeiro
        create_response = client.post("/api/clientes", json=CLIENTE_TEST_DATA)
        cliente_id = create_response.json()["id"]
        
        # Atualizar apenas telefone
        update_data = {"telefone": "11999999999"}
        response = client.put(f"/api/clientes/{cliente_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        updated_data = response.json()
        assert updated_data["telefone"] == "11999999999"
        assert updated_data["nome"] == CLIENTE_TEST_DATA["nome"]  # Outros campos mantidos
        
        # Limpar
        client.delete(f"/api/clientes/{cliente_id}")
        
    def test_create_cliente_missing_required_fields(self):
        """Teste: Criar cliente sem campos obrigatórios"""
        incomplete_data = {"nome": "Teste"}  # Faltam email e CPF
        
        response = client.post("/api/clientes", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_cliente_status_validation(self):
        """Teste: Validação do campo status"""
        invalid_data = CLIENTE_TEST_DATA.copy()
        invalid_data["status"] = "status_invalido"
        
        response = client.post("/api/clientes", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY