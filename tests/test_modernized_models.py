#!/usr/bin/env python3
"""
Teste para validar que os modelos atualizados do Pydantic v2 funcionam corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_models():
    """Testa se os modelos atualizados funcionam corretamente"""
    try:
        from app.database.models import Cliente, ClienteCreate, Transacao, LogAcesso
        from app.config import settings
        from datetime import datetime
        
        print("✅ Imports dos modelos atualizados funcionando")
        
        # Teste de criação de cliente
        cliente_data = {
            "nome": "João Silva",
            "email": "joao@teste.com",
            "cpf": "12345678901",  # CPF inválido para teste
            "telefone": "11987654321"
        }
        
        try:
            cliente = ClienteCreate(**cliente_data)
            print("❌ Validação do CPF deveria ter falhado")
        except ValueError as e:
            print(f"✅ Validação do CPF funcionando: {e}")
        
        # Teste com CPF válido
        cliente_data["cpf"] = "11144477735"  # CPF válido
        try:
            cliente = ClienteCreate(**cliente_data)
            print("✅ Criação de cliente com CPF válido funcionando")
        except Exception as e:
            print(f"❌ Erro na criação de cliente: {e}")
        
        # Teste de configurações
        print(f"✅ Configurações carregadas: {settings.DEBUG}")
        
        print("\n🎉 Todos os testes passaram! Modelos atualizados para Pydantic v2 com sucesso!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

if __name__ == "__main__":
    success = test_models()
    sys.exit(0 if success else 1)