"""
Script para criar e configurar as coleções MongoDB do projeto.
Cria as coleções: clientes, transacoes, logs_acesso com índices e validações.

- Conecta com o MongoDB
- Cria as coleções necessárias (clientes, transacoes, logs_acesso)
- Cria índices apropriados
- Define validações de schema
- Insere dados de exemplo se necessário

"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid
from datetime import datetime
import sys
import os

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config import settings


async def create_collections_and_indexes():
    """
    Cria as coleções MongoDB e seus respectivos índices.
    """
    try:
        # Conexão com MongoDB
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        
        print(f"🔗 Conectado ao MongoDB: {settings.MONGO_DB}")
        
        # ====================== COLEÇÃO CLIENTES ======================
        try:
            # Verificar se a coleção já existe
            existing_collections = await db.list_collection_names()
            
            # Schema de validação para clientes
            cliente_validator = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["nome", "email", "cpf", "status", "data_criacao"],
                    "properties": {
                        "nome": {
                            "bsonType": "string",
                            "minLength": 2,
                            "maxLength": 100,
                            "description": "Nome completo do cliente"
                        },
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                            "description": "Email válido do cliente"
                        },
                        "cpf": {
                            "bsonType": "string",
                            "pattern": "^[0-9]{11}$",
                            "description": "CPF com 11 dígitos"
                        },
                        "endereco": {
                            "bsonType": ["string", "null"],
                            "maxLength": 200,
                            "description": "Endereço completo do cliente"
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["ativo", "inativo", "suspenso"],
                            "description": "Status do cliente"
                        },
                        "data_criacao": {
                            "bsonType": "date",
                            "description": "Data de criação do registro"
                        },
                        "telefone": {
                            "bsonType": ["string", "null"],
                            "pattern": "^[0-9]{10,11}$",
                            "description": "Telefone com 10 ou 11 dígitos"
                        },
                        "data_nascimento": {
                            "bsonType": ["date", "null"],
                            "description": "Data de nascimento do cliente"
                        }
                    }
                }
            }
            
            # Criar coleção clientes com validação
            if "clientes" not in existing_collections:
                await db.create_collection("clientes", validator=cliente_validator)
                print("✅ Coleção 'clientes' criada com validação de schema")
            else:
                print("ℹ️  Coleção 'clientes' já existe")
            
        except CollectionInvalid:
            print("ℹ️  Coleção 'clientes' já existia")
        
        # Índices para clientes
        clientes_collection = db.clientes
        
        # Índice único para email e CPF
        await clientes_collection.create_index("email", unique=True)
        await clientes_collection.create_index("cpf", unique=True)
        
        # Índices para consultas frequentes
        await clientes_collection.create_index("status")
        await clientes_collection.create_index("data_criacao")
        await clientes_collection.create_index([("nome", 1), ("status", 1)])
        
        print("📊 Índices criados para coleção 'clientes'")
        
        
        # ====================== COLEÇÃO TRANSAÇÕES ======================
        try:
            # Schema de validação para transações
            transacao_validator = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["id_cliente", "valor", "tipo", "status", "data"],
                    "properties": {
                        "id_cliente": {
                            "bsonType": "objectId",
                            "description": "Referência ao cliente"
                        },
                        "valor": {
                            "bsonType": ["double", "int"],
                            "minimum": 0,
                            "description": "Valor da transação (positivo)"
                        },
                        "tipo": {
                            "bsonType": "string",
                            "enum": ["credito", "debito", "pix", "transferencia", "boleto"],
                            "description": "Tipo da transação"
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["pendente", "aprovada", "rejeitada", "cancelada"],
                            "description": "Status da transação"
                        },
                        "data": {
                            "bsonType": "date",
                            "description": "Data da transação"
                        },
                        "descricao": {
                            "bsonType": ["string", "null"],
                            "maxLength": 200,
                            "description": "Descrição da transação"
                        },
                        "metadados": {
                            "bsonType": ["object", "null"],
                            "description": "Informações adicionais da transação"
                        }
                    }
                }
            }
            
            # Criar coleção transações
            if "transacoes" not in existing_collections:
                await db.create_collection("transacoes", validator=transacao_validator)
                print("✅ Coleção 'transacoes' criada com validação de schema")
            else:
                print("ℹ️  Coleção 'transacoes' já existe")
            
        except CollectionInvalid:
            print("ℹ️  Coleção 'transacoes' já existe")
        
        # Índices para transações
        transacoes_collection = db.transacoes
        
        await transacoes_collection.create_index("id_cliente")
        await transacoes_collection.create_index("data")
        await transacoes_collection.create_index("status")
        await transacoes_collection.create_index("tipo")
        await transacoes_collection.create_index([("id_cliente", 1), ("data", -1)])
        await transacoes_collection.create_index([("status", 1), ("data", -1)])
        
        print("📊 Índices criados para coleção 'transacoes'")
        
        
        # ====================== COLEÇÃO LOGS DE ACESSO ======================
        try:
            # Schema de validação para logs
            log_validator = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["timestamp", "acao", "ip"],
                    "properties": {
                        "id_cliente": {
                            "bsonType": ["objectId", "null"],
                            "description": "Referência ao cliente (opcional)"
                        },
                        "timestamp": {
                            "bsonType": "date",
                            "description": "Momento do acesso"
                        },
                        "acao": {
                            "bsonType": "string",
                            "enum": ["login", "logout", "create", "read", "update", "delete", "error"],
                            "description": "Tipo de ação realizada"
                        },
                        "ip": {
                            "bsonType": "string",
                            "pattern": "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$",
                            "description": "Endereço IP do usuário"
                        },
                        "user_agent": {
                            "bsonType": ["string", "null"],
                            "maxLength": 500,
                            "description": "User agent do navegador"
                        },
                        "endpoint": {
                            "bsonType": ["string", "null"],
                            "maxLength": 200,
                            "description": "Endpoint acessado"
                        },
                        "status_code": {
                            "bsonType": ["int", "null"],
                            "minimum": 100,
                            "maximum": 599,
                            "description": "Código de status HTTP"
                        },
                        "detalhes": {
                            "bsonType": ["object", "null"],
                            "description": "Informações adicionais do log"
                        }
                    }
                }
            }
            
            # Criar coleção logs
            if "logs_acesso" not in existing_collections:
                await db.create_collection("logs_acesso", validator=log_validator)
                print("✅ Coleção 'logs_acesso' criada com validação de schema")
            else:
                print("ℹ️  Coleção 'logs_acesso' já existe")
            
        except CollectionInvalid:
            print("ℹ️  Coleção 'logs_acesso' já existe")
        
        # Índices para logs
        logs_collection = db.logs_acesso
        
        await logs_collection.create_index("timestamp")
        await logs_collection.create_index("id_cliente")
        await logs_collection.create_index("acao")
        await logs_collection.create_index("ip")
        await logs_collection.create_index([("timestamp", -1), ("acao", 1)])
        
        # TTL index para logs (remover logs antigos após 90 dias)
        await logs_collection.create_index("timestamp", expireAfterSeconds=7776000)  # 90 dias
        
        print("📊 Índices criados para coleção 'logs_acesso' (com TTL de 90 dias)")
        
        
        # ====================== INFORMAÇÕES FINAIS ======================
        print("\n📋 Resumo das coleções criadas:")
        collections = await db.list_collection_names()
        for collection in collections:
            count = await db[collection].count_documents({})
            print(f"   • {collection}: {count} documentos")
        
        print(f"\n🎉 Estrutura do banco '{settings.MONGO_DB}' criada com sucesso!")
        print("📚 Coleções disponíveis: clientes, transacoes, logs_acesso")
        print("🔐 Validações de schema ativas")
        print("⚡ Índices otimizados criados")
        
        # Fechar conexão
        client.close()
        
    except Exception as e:
        print(f"❌ Erro ao criar coleções: {e}")
        raise


async def insert_sample_data():
    """
    Insere dados de exemplo nas coleções (opcional).
    """
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB]
        
        print("\n🔄 Inserindo dados de exemplo...")
        
        # Dados de exemplo para clientes
        sample_clients = [
            {
                "nome": "João Silva",
                "email": "joao.silva@email.com",
                "cpf": "12345678901",
                "endereco": "Rua das Flores, 123 - São Paulo, SP",
                "telefone": "11987654321",
                "status": "ativo",
                "data_criacao": datetime.utcnow()
            },
            {
                "nome": "Maria Santos",
                "email": "maria.santos@email.com", 
                "cpf": "98765432109",
                "endereco": "Av. Paulista, 456 - São Paulo, SP",
                "telefone": "11123456789",
                "status": "ativo",
                "data_criacao": datetime.utcnow()
            },
            {
                "nome": "Pedro Oliveira",
                "email": "pedro.oliveira@email.com",
                "cpf": "11122233344",
                "endereco": "Rua do Comércio, 789 - Rio de Janeiro, RJ",
                "telefone": "21987654321",
                "status": "inativo",
                "data_criacao": datetime.utcnow()
            }
        ]
        
        # Verificar se já existem clientes
        client_count = await db.clientes.count_documents({})
        if client_count == 0:
            result = await db.clientes.insert_many(sample_clients)
            print(f"✅ {len(result.inserted_ids)} clientes de exemplo inseridos")
            
            # Inserir algumas transações de exemplo
            client_ids = result.inserted_ids
            sample_transactions = [
                {
                    "id_cliente": client_ids[0],
                    "valor": 150.50,
                    "tipo": "pix",
                    "status": "aprovada",
                    "data": datetime.utcnow(),
                    "descricao": "Transferência PIX"
                },
                {
                    "id_cliente": client_ids[1],
                    "valor": 300.00,
                    "tipo": "credito",
                    "status": "pendente",
                    "data": datetime.utcnow(),
                    "descricao": "Pagamento cartão de crédito"
                },
                {
                    "id_cliente": client_ids[0],
                    "valor": 75.25,
                    "tipo": "debito",
                    "status": "aprovada",
                    "data": datetime.utcnow(),
                    "descricao": "Compra no débito"
                }
            ]
            
            await db.transacoes.insert_many(sample_transactions)
            print(f"✅ {len(sample_transactions)} transações de exemplo inseridas")
            
            # Inserir alguns logs de exemplo
            sample_logs = [
                {
                    "id_cliente": client_ids[0],
                    "timestamp": datetime.utcnow(),
                    "acao": "login",
                    "ip": "192.168.1.100",
                    "endpoint": "/api/auth/login",
                    "status_code": 200
                },
                {
                    "timestamp": datetime.utcnow(),
                    "acao": "read",
                    "ip": "192.168.1.100",
                    "endpoint": "/api/clientes",
                    "status_code": 200
                }
            ]
            
            await db.logs_acesso.insert_many(sample_logs)
            print(f"✅ {len(sample_logs)} logs de exemplo inseridos")
            
        else:
            print("ℹ️  Dados já existem no banco, pulando inserção de exemplos")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados de exemplo: {e}")


async def main():
    """
    Função principal para criar a estrutura do banco.
    """
    print("🚀 Iniciando criação da estrutura MongoDB...")
    print("=" * 50)
    
    # Criar coleções e índices
    await create_collections_and_indexes()
    
    # Perguntar se quer inserir dados de exemplo
    print("\n" + "=" * 50)
    response = input("💡 Deseja inserir dados de exemplo? (s/n): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        await insert_sample_data()
        print("\n🎯 Estrutura criada e dados de exemplo inseridos!")
    else:
        print("\n🎯 Estrutura criada sem dados de exemplo!")
    
    print("\n✨ Processo concluído com sucesso!")


if __name__ == "__main__":
    # Executar o script
    asyncio.run(main())