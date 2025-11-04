"""
Rotas de Autenticação e Autorização - MonitorDB
Endpoints para login, cadastro, gerenciamento de usuários e permissões
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from app.security.auth import (
    UserCreate, UserLogin, Token, TokenData, 
    get_current_user, get_current_active_user
)
from app.security.roles import (
    Role, Permission, require_permission, require_role_or_higher,
    get_user_permissions, validate_role_transition
)
from app.services.auth_service import auth_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Modelos para requests/responses
class UserResponse(BaseModel):
    """Modelo de resposta de usuário (sem dados sensíveis)"""
    id: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: str
    last_login: Optional[str] = None
    permissions: List[str] = []

class ChangePasswordRequest(BaseModel):
    """Modelo para alteração de senha"""
    current_password: str
    new_password: str

class UpdateRoleRequest(BaseModel):
    """Modelo para atualização de role"""
    user_id: str
    new_role: str

class PermissionsResponse(BaseModel):
    """Modelo de resposta de permissões"""
    role: str
    permissions: List[str]

# ========== ENDPOINTS DE AUTENTICAÇÃO ==========

@router.post("/register", response_model=UserResponse, summary="Cadastrar novo usuário")
async def register_user(
    user_data: UserCreate,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Cadastra novo usuário no sistema
    
    Requer permissão: USER_CREATE
    """
    # Verifica permissão
    if Permission.USER_CREATE.value not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para criar usuários"
        )
    
    # Valida se pode criar usuário com o role especificado
    if not validate_role_transition("guest", user_data.role, current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Não é possível criar usuário com role '{user_data.role}'"
        )
    
    try:
        user = await auth_service.create_user(user_data, current_user.user_id)
        logger.info(f"Usuário criado por {current_user.email}: {user_data.email}")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no cadastro de usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/login", response_model=Token, summary="Fazer login")
async def login(login_data: UserLogin, request: Request):
    """
    Realiza login no sistema com email e senha
    
    Retorna tokens JWT (access e refresh)
    """
    try:
        # Captura informações da requisição para auditoria
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(f"Tentativa de login: {login_data.email} de {client_ip}")
        
        token = await auth_service.login(login_data)
        
        logger.info(f"Login bem-sucedido: {login_data.email}")
        
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/refresh", response_model=Token, summary="Renovar token")
async def refresh_token(refresh_token: str):
    """
    Renova token de acesso usando refresh token
    """
    try:
        token = await auth_service.refresh_token(refresh_token)
        return token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao renovar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/logout", summary="Fazer logout")
async def logout(current_user: TokenData = Depends(get_current_active_user)):
    """
    Realiza logout e invalida sessões do usuário
    """
    try:
        await auth_service.logout(current_user.user_id)
        
        return {
            "success": True,
            "message": "Logout realizado com sucesso"
        }
        
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

# ========== ENDPOINTS DE USUÁRIO ==========

@router.get("/me", response_model=UserResponse, summary="Obter dados do usuário atual")
async def get_current_user_info(current_user: TokenData = Depends(get_current_active_user)):
    """
    Retorna informações do usuário atualmente autenticado
    """
    try:
        user_data = await auth_service.get_user_by_id(current_user.user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter dados do usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/me/permissions", response_model=PermissionsResponse, summary="Obter permissões do usuário")
async def get_my_permissions(current_user: TokenData = Depends(get_current_active_user)):
    """
    Retorna permissões do usuário atual
    """
    permissions = get_user_permissions(current_user.role)
    
    return PermissionsResponse(
        role=current_user.role,
        permissions=permissions
    )

@router.post("/change-password", summary="Alterar senha")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Altera senha do usuário atual
    """
    try:
        success = await auth_service.change_password(
            current_user.user_id,
            password_data.current_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta"
            )
        
        logger.info(f"Senha alterada para usuário {current_user.user_id}")
        
        return {
            "success": True,
            "message": "Senha alterada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao alterar senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

# ========== ENDPOINTS DE ADMINISTRAÇÃO ==========

@router.get("/users", response_model=List[UserResponse], summary="Listar usuários")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Lista usuários do sistema
    
    Requer permissão: USER_LIST
    """
    if Permission.USER_LIST.value not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para listar usuários"
        )
    
    try:
        from app.database.mongo_client import db
        
        cursor = db.users.find(
            {},
            {"hashed_password": 0}  # Exclui senha
        ).skip(skip).limit(limit)
        
        users = []
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            user_doc["created_at"] = user_doc["created_at"].isoformat()
            if user_doc.get("last_login"):
                user_doc["last_login"] = user_doc["last_login"].isoformat()
            users.append(UserResponse(**user_doc))
        
        return users
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/users/{user_id}", response_model=UserResponse, summary="Obter usuário por ID")
async def get_user_by_id(
    user_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Obtém informações de usuário específico
    
    Requer permissão: USER_READ  
    """
    if Permission.USER_READ.value not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para visualizar usuários"
        )
    
    try:
        user_data = await auth_service.get_user_by_id(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        user_data["created_at"] = user_data["created_at"].isoformat()
        if user_data.get("last_login"):
            user_data["last_login"] = user_data["last_login"].isoformat()
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/users/role", summary="Atualizar role de usuário")
async def update_user_role(
    role_data: UpdateRoleRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Atualiza role de um usuário
    
    Requer permissão: USER_MANAGE_ROLES
    """
    if Permission.USER_MANAGE_ROLES.value not in current_user.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para gerenciar roles"
        )
    
    try:
        # Obtém dados do usuário alvo
        target_user = await auth_service.get_user_by_id(role_data.user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Valida se pode alterar o role
        if not validate_role_transition(target_user["role"], role_data.new_role, current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não é possível alterar para este role"
            )
        
        success = await auth_service.update_user_role(
            role_data.user_id,
            role_data.new_role,
            current_user.user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao atualizar role"
            )
        
        logger.info(f"Role atualizado por {current_user.email}: {target_user['email']} -> {role_data.new_role}")
        
        return {
            "success": True,
            "message": f"Role atualizado para {role_data.new_role}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

# ========== ENDPOINTS DE INFORMAÇÕES ==========

@router.get("/roles", summary="Listar roles disponíveis")
async def list_roles(current_user: TokenData = Depends(get_current_active_user)):
    """
    Lista todos os roles disponíveis no sistema
    """
    roles_info = []
    
    for role in Role:
        permissions = get_user_permissions(role.value)
        roles_info.append({
            "role": role.value,
            "description": f"Role {role.value}",
            "permissions_count": len(permissions),
            "permissions": permissions
        })
    
    return {
        "success": True,
        "data": roles_info
    }

@router.get("/permissions", summary="Listar permissões disponíveis")
async def list_permissions(current_user: TokenData = Depends(get_current_active_user)):
    """
    Lista todas as permissões disponíveis no sistema
    """
    permissions_info = []
    
    for permission in Permission:
        permissions_info.append({
            "permission": permission.value,
            "description": f"Permissão {permission.value}"
        })
    
    return {
        "success": True,
        "data": permissions_info
    }

@router.get("/validate-token", summary="Validar token atual")
async def validate_token(current_user: TokenData = Depends(get_current_active_user)):
    """
    Valida se o token atual ainda é válido
    """
    return {
        "success": True,
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role
    }