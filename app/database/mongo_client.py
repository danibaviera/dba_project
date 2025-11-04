# Conexão com MongoDB (Motor)

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger(__name__)

class MongoClient:
    """Cliente MongoDB com funcionalidades avançadas"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._is_connected = False
    
    async def connect(self):
        """Estabelece conexão com MongoDB"""
        try:
            # Configurações avançadas de conexão
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                maxPoolSize=50,  # Máximo de conexões no pool
                minPoolSize=10,  # Mínimo de conexões no pool
                maxIdleTimeMS=30000,  # Tempo limite para conexões inativas
                serverSelectionTimeoutMS=5000,  # Timeout para seleção do servidor
                socketTimeoutMS=20000,  # Timeout do socket
                retryWrites=True,  # Retry automático para escritas
                retryReads=True,   # Retry automático para leituras
            )
            
            self.db = self.client[settings.MONGO_DB]
            
            # Testar conexão
            await self.client.admin.command('ping')
            self._is_connected = True
            
            logger.info(f"✅ Conectado ao MongoDB: {settings.MONGO_DB}")
            
        except ConnectionFailure as e:
            logger.error(f"❌ Falha na conexão com MongoDB: {e}")
            raise
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ Timeout na conexão com MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado na conexão: {e}")
            raise
    
    async def disconnect(self):
        """Fecha conexão com MongoDB"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("🔌 Conexão com MongoDB fechada")
    
    async def is_healthy(self) -> bool:
        """Verifica se a conexão está saudável"""
        try:
            if not self._is_connected or not self.client:
                return False
            
            # Ping no servidor
            await self.client.admin.command('ping')
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Verificação de saúde falhou: {e}")
            return False
    
    async def get_database_stats(self) -> dict:
        """Obtém estatísticas do banco de dados"""
        try:
            stats = await self.db.command("dbStats")
            
            # Estatísticas das coleções
            collections_stats = {}
            collection_names = await self.db.list_collection_names()
            
            for collection_name in collection_names:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                collections_stats[collection_name] = count
            
            return {
                "database_stats": {
                    "size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                    "storage_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                    "indexes": stats.get("indexes", 0),
                    "collections": stats.get("collections", 0)
                },
                "collections": collections_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}


# Instância global do cliente MongoDB
mongo_client = MongoClient()

# Aliases para compatibilidade
client = None  # Será definido após connect()
db = None      # Será definido após connect()

async def init_database():
    """Inicializa a conexão com o banco de dados"""
    global client, db
    
    await mongo_client.connect()
    client = mongo_client.client
    db = mongo_client.db

async def close_database():
    """Fecha a conexão com o banco de dados"""
    await mongo_client.disconnect()
