"""
Serviço de Autenticação e Gerenciamento de Usuários - MonitorDB
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.database.mongo_client import db
from app.security.auth import (
    PasswordUtils, JWTManager, TokenData, UserCreate, UserLogin, 
    UserInDB, Token, UserStatus, jwt_manager
)
from app.security.roles import Role, RolePermissions
from app.utils.logger import get_logger
from app.integrations import send_alert, NotificationPriority

logger = get_logger(__name__)

class AuthenticationError(Exception):
    """Exceção para erros de autenticação"""
    pass

class AuthService:
    """Serviço de autenticação e gerenciamento de usuários"""
    
    def __init__(self):
        self.users_collection = db.users
        self.sessions_collection = db.user_sessions
        self.password_utils = PasswordUtils()
        self.jwt_manager = JWTManager()
        
        # Configurações de segurança
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.session_timeout_hours = 24
    
    async def create_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria novo usuário no sistema
        
        Args:
            user_data: Dados do usuário a ser criado
            created_by: ID do usuário que está criando (para auditoria)
            
        Returns:
            Dados do usuário criado (sem senha)
            
        Raises:
            HTTPException: Se houver erro na criação
        """
        try:
            # Valida força da senha
            is_strong, errors = self.password_utils.validate_password_strength(user_data.password)
            if not is_strong:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Senha não atende aos critérios de segurança", "errors": errors}
                )
            
            # Verifica se role é válido
            try:
                role_enum = Role(user_data.role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role inválido: {user_data.role}"
                )
            
            # Cria documento do usuário
            user_doc = {
                "_id": ObjectId(),
                "email": user_data.email.lower(),
                "full_name": user_data.full_name,
                "hashed_password": self.password_utils.hash_password(user_data.password),
                "role": user_data.role,
                "status": UserStatus.ACTIVE.value,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": created_by,
                "last_login": None,
                "failed_login_attempts": 0,
                "locked_until": None,
                "permissions": [perm.value for perm in RolePermissions.get_permissions(role_enum)],
                "metadata": {
                    "password_changed_at": datetime.now(timezone.utc),
                    "must_change_password": False,
                    "email_verified": False
                }
            }
            
            # Insere no banco
            result = await self.users_collection.insert_one(user_doc)
            
            # Remove senha do retorno
            user_doc.pop("hashed_password")
            user_doc["id"] = str(result.inserted_id)
            user_doc.pop("_id")
            
            logger.info(f"Usuário criado: {user_data.email} (ID: {result.inserted_id})")
            
            # Envia notificação de novo usuário
            await send_alert(
                title="Novo Usuário Criado",
                message=f"Usuário {user_data.full_name} ({user_data.email}) foi criado com role {user_data.role}",
                priority=NotificationPriority.NORMAL
            )
            
            return user_doc
            
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Autentica usuário com email e senha
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            Dados do usuário se autenticado, None caso contrário
        """
        try:
            # Busca usuário no banco
            user_doc = await self.users_collection.find_one({"email": email.lower()})
            if not user_doc:
                logger.warning(f"Tentativa de login com email inexistente: {email}")
                return None
            
            # Verifica se conta está bloqueada
            if user_doc.get("locked_until"):
                locked_until = user_doc["locked_until"]
                if datetime.now(timezone.utc) < locked_until:
                    logger.warning(f"Tentativa de login em conta bloqueada: {email}")
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail=f"Conta bloqueada até {locked_until.strftime('%d/%m/%Y %H:%M')}"
                    )
                else:
                    # Desbloqueia conta se o tempo expirou
                    await self.users_collection.update_one(
                        {"_id": user_doc["_id"]},
                        {"$unset": {"locked_until": ""}, "$set": {"failed_login_attempts": 0}}
                    )
            
            # Verifica senha
            if not self.password_utils.verify_password(password, user_doc["hashed_password"]):
                # Incrementa tentativas falhadas
                failed_attempts = user_doc.get("failed_login_attempts", 0) + 1
                
                update_data = {
                    "failed_login_attempts": failed_attempts,
                    "updated_at": datetime.now(timezone.utc)
                }
                
                # Bloqueia conta se excedeu tentativas
                if failed_attempts >= self.max_failed_attempts:
                    lockout_until = datetime.now(timezone.utc) + timedelta(minutes=self.lockout_duration_minutes)
                    update_data["locked_until"] = lockout_until
                    
                    logger.warning(f"Conta bloqueada por excesso de tentativas: {email}")
                    
                    # Envia alerta de segurança
                    await send_alert(
                        title="🚨 Conta Bloqueada por Tentativas de Login",
                        message=f"A conta {email} foi bloqueada devido a {failed_attempts} tentativas de login falhadas",
                        priority=NotificationPriority.HIGH
                    )
                
                await self.users_collection.update_one(
                    {"_id": user_doc["_id"]},
                    {"$set": update_data}
                )
                
                logger.warning(f"Senha incorreta para usuário: {email} (tentativa {failed_attempts})")
                return None
            
            # Reset tentativas falhadas em login bem-sucedido
            await self.users_collection.update_one(
                {"_id": user_doc["_id"]},
                {
                    "$set": {
                        "last_login": datetime.now(timezone.utc),
                        "failed_login_attempts": 0,
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$unset": {"locked_until": ""}
                }
            )
            
            # Converte para modelo UserInDB
            user = UserInDB(
                id=str(user_doc["_id"]),
                email=user_doc["email"],
                full_name=user_doc["full_name"],
                hashed_password=user_doc["hashed_password"],
                role=user_doc["role"],
                status=UserStatus(user_doc["status"]),
                created_at=user_doc["created_at"],
                updated_at=user_doc["updated_at"],
                last_login=user_doc.get("last_login"),
                failed_login_attempts=user_doc.get("failed_login_attempts", 0),
                locked_until=user_doc.get("locked_until"),
                permissions=user_doc.get("permissions", [])
            )
            
            logger.info(f"Login bem-sucedido: {email}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro na autenticação: {str(e)}")
            return None
    
    async def login(self, login_data: UserLogin) -> Token:
        """
        Realiza login e retorna tokens JWT
        
        Args:
            login_data: Dados de login (email e senha)
            
        Returns:
            Token JWT com access e refresh tokens
            
        Raises:
            HTTPException: Se credenciais forem inválidas
        """
        user = await self.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Conta está {user.status.value}"
            )
        
        # Cria tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions
        }
        
        access_token = self.jwt_manager.create_access_token(token_data)
        refresh_token = self.jwt_manager.create_refresh_token({"sub": user.id})
        
        # Registra sessão
        session_id = await self.create_session(user.id, access_token)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.jwt_manager.access_token_expire_minutes * 60,
            user_id=user.id,
            role=user.role
        )
    
    async def create_session(self, user_id: str, access_token: str) -> str:
        """
        Cria sessão de usuário
        
        Args:
            user_id: ID do usuário
            access_token: Token de acesso
            
        Returns:
            ID da sessão criada
        """
        session_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "access_token_hash": secrets.token_urlsafe(32),  # Hash do token por segurança
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=self.session_timeout_hours),
            "is_active": True,
            "metadata": {
                "user_agent": None,  # Pode ser preenchido pelo endpoint
                "ip_address": None   # Pode ser preenchido pelo endpoint
            }
        }
        
        result = await self.sessions_collection.insert_one(session_doc)
        return str(result.inserted_id)
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """
        Renova token de acesso usando refresh token
        
        Args:
            refresh_token: Token de refresh
            
        Returns:
            Novo token de acesso
            
        Raises:
            HTTPException: Se refresh token for inválido
        """
        try:
            from app.security.auth import TokenType
            token_data = self.jwt_manager.verify_token(refresh_token, TokenType.REFRESH)
            
            # Busca usuário no banco para verificar se ainda está ativo
            user_doc = await self.users_collection.find_one({"_id": ObjectId(token_data.user_id)})
            if not user_doc or user_doc["status"] != UserStatus.ACTIVE.value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário inativo"
                )
            
            # Cria novo token de acesso
            new_token_data = {
                "sub": token_data.user_id,
                "email": user_doc["email"],
                "role": user_doc["role"],
                "permissions": user_doc.get("permissions", [])
            }
            
            access_token = self.jwt_manager.create_access_token(new_token_data)
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,  # Mantém o mesmo refresh token
                token_type="bearer",
                expires_in=self.jwt_manager.access_token_expire_minutes * 60,
                user_id=token_data.user_id,
                role=user_doc["role"]
            )
            
        except Exception as e:
            logger.error(f"Erro ao renovar token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresh inválido"
            )
    
    async def logout(self, user_id: str, access_token: str = None):
        """
        Realiza logout do usuário
        
        Args:
            user_id: ID do usuário
            access_token: Token de acesso (opcional)
        """
        try:
            # Desativa todas as sessões do usuário
            await self.sessions_collection.update_many(
                {"user_id": user_id},
                {"$set": {"is_active": False, "logout_at": datetime.now(timezone.utc)}}
            )
            
            logger.info(f"Logout realizado para usuário: {user_id}")
            
        except Exception as e:
            logger.error(f"Erro no logout: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca usuário por ID
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dados do usuário (sem senha) ou None
        """
        try:
            user_doc = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                user_doc["id"] = str(user_doc.pop("_id"))
                user_doc.pop("hashed_password", None)
                return user_doc
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário {user_id}: {str(e)}")
            return None
    
    async def update_user_role(self, user_id: str, new_role: str, updated_by: str) -> bool:
        """
        Atualiza role de usuário
        
        Args:
            user_id: ID do usuário
            new_role: Novo role
            updated_by: ID de quem está atualizando
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            # Valida role
            role_enum = Role(new_role)
            permissions = [perm.value for perm in RolePermissions.get_permissions(role_enum)]
            
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "role": new_role,
                        "permissions": permissions,
                        "updated_at": datetime.now(timezone.utc),
                        "updated_by": updated_by
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Role atualizado para usuário {user_id}: {new_role}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar role: {str(e)}")
            return False
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Altera senha do usuário
        
        Args:
            user_id: ID do usuário
            current_password: Senha atual
            new_password: Nova senha
            
        Returns:
            True se alterado com sucesso
        """
        try:
            # Busca usuário
            user_doc = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                return False
            
            # Verifica senha atual
            if not self.password_utils.verify_password(current_password, user_doc["hashed_password"]):
                return False
            
            # Valida nova senha
            is_strong, errors = self.password_utils.validate_password_strength(new_password)
            if not is_strong:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"message": "Nova senha não atende aos critérios", "errors": errors}
                )
            
            # Atualiza senha
            new_hash = self.password_utils.hash_password(new_password)
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "hashed_password": new_hash,
                        "updated_at": datetime.now(timezone.utc),
                        "metadata.password_changed_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Senha alterada para usuário {user_id}")
                return True
            return False
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {str(e)}")
            return False

# Instância global do serviço
auth_service = AuthService()