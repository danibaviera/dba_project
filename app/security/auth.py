"""
Sistema de Autenticação JWT para MonitorDB
Implementa autenticação robusta com tokens de acesso e refresh
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
import logging

logger = logging.getLogger(__name__)

# Configurações JWT
JWT_SECRET_KEY = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

class TokenData(BaseModel):
    """Dados do token JWT"""
    user_id: str
    username: str
    email: str
    role: str
    permissions: list
    exp: int
    jti: str  # JWT ID único

class UserInDB(BaseModel):
    """Modelo do usuário no banco"""
    id: str
    username: str
    email: str
    hashed_password: str
    role: str
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserCreate(BaseModel):
    """Modelo para criar usuário"""
    username: str
    email: str
    password: str
    role: str = "readonly"

class UserLogin(BaseModel):
    """Modelo para login"""
    username: str
    password: str

class TokenResponse(BaseModel):
    """Resposta do token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

def hash_password(password: str) -> str:
    """Gera hash seguro da senha"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica senha contra hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_password_strength(password: str) -> bool:
    """Valida força da senha"""
    if len(password) < 8:
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True

def generate_jwt_token(user_data: Dict[str, Any], token_type: str = "access") -> str:
    """Gera token JWT"""
    now = datetime.utcnow()
    
    if token_type == "access":
        expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # refresh
        expire = now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "permissions": user_data.get("permissions", []),
        "token_type": token_type,
        "exp": expire,
        "iat": now,
        "jti": secrets.token_urlsafe(32)  # JWT ID único
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[TokenData]:
    """Verifica e decodifica token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verificar expiração
        if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
            return None
        
        return TokenData(
            user_id=payload["user_id"],
            username=payload["username"],
            email=payload["email"],
            role=payload["role"],
            permissions=payload.get("permissions", []),
            exp=payload["exp"],
            jti=payload["jti"]
        )
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token JWT inválido: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao verificar token: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Dependency para obter usuário atual do token"""
    token = credentials.credentials
    
    token_data = verify_jwt_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

async def require_permission(permission: str):
    """Dependency para verificar permissão específica"""
    def permission_checker(current_user: TokenData = Depends(get_current_user)):
        if permission not in current_user.permissions and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão requerida: {permission}"
            )
        return current_user
    return permission_checker

async def require_role(required_role: str):
    """Dependency para verificar role mínimo"""
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        from .roles import ROLE_HIERARCHY
        
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role mínimo requerido: {required_role}"
            )
        return current_user
    return role_checker

def is_account_locked(user: UserInDB) -> bool:
    """Verifica se conta está bloqueada"""
    if user.locked_until and datetime.utcnow() < user.locked_until:
        return True
    return False

def should_lock_account(user: UserInDB) -> bool:
    """Verifica se deve bloquear conta por tentativas"""
    return user.failed_attempts >= 5

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Autentica usuário (simulado - implementar com banco)"""
    # TODO: Implementar busca real no banco de dados
    # Por enquanto, usuário admin padrão
    if username == "admin" and password == "admin123":
        return UserInDB(
            id="1",
            username="admin",
            email="admin@monitordb.com",
            hashed_password=hash_password("admin123"),
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
    return None

class AuthService:
    """Serviço de autenticação"""
    
    @staticmethod
    async def login(login_data: UserLogin) -> TokenResponse:
        """Realiza login e retorna tokens"""
        user = await authenticate_user(login_data.username, login_data.password)
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta desativada"
            )
        
        if is_account_locked(user):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Conta temporariamente bloqueada"
            )
        
        # Obter permissões do usuário
        from .roles import get_role_permissions
        permissions = get_role_permissions(user.role)
        
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "permissions": permissions
        }
        
        # Gerar tokens
        access_token = generate_jwt_token(user_data, "access")
        refresh_token = generate_jwt_token(user_data, "refresh")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        )
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> TokenResponse:
        """Renova token de acesso"""
        token_data = verify_jwt_token(refresh_token)
        
        if not token_data or token_data.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )
        
        # Gerar novo access token
        user_data = {
            "id": token_data.user_id,
            "username": token_data.username,
            "email": token_data.email,
            "role": token_data.role,
            "permissions": token_data.permissions
        }
        
        new_access_token = generate_jwt_token(user_data, "access")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Manter o mesmo refresh token
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": token_data.user_id,
                "username": token_data.username,
                "email": token_data.email,
                "role": token_data.role
            }
        )