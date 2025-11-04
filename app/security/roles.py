"""
Sistema de Roles e Permissões RBAC para MonitorDB
Implementa controle de acesso baseado em roles hierárquicos
"""

from typing import List, Dict, Set
from enum import Enum

class Role(Enum):
    """Enum de roles disponíveis"""
    ADMIN = "admin"
    MANAGER = "manager" 
    ANALYST = "analyst"
    OPERATOR = "operator"
    READONLY = "readonly"
    GUEST = "guest"

class Permission(Enum):
    """Enum de permissões disponíveis"""
    # Permissões de Clientes
    CLIENTE_CREATE = "cliente:create"
    CLIENTE_READ = "cliente:read"
    CLIENTE_UPDATE = "cliente:update"
    CLIENTE_DELETE = "cliente:delete"
    CLIENTE_LIST = "cliente:list"
    CLIENTE_EXPORT = "cliente:export"
    
    # Permissões de Transações
    TRANSACAO_CREATE = "transacao:create"
    TRANSACAO_READ = "transacao:read"
    TRANSACAO_UPDATE = "transacao:update"
    TRANSACAO_DELETE = "transacao:delete"
    TRANSACAO_LIST = "transacao:list"
    TRANSACAO_APPROVE = "transacao:approve"
    TRANSACAO_EXPORT = "transacao:export"
    
    # Permissões de Logs
    LOG_CREATE = "log:create"
    LOG_READ = "log:read"
    LOG_DELETE = "log:delete"
    LOG_LIST = "log:list"
    LOG_EXPORT = "log:export"
    
    # Permissões de Monitoramento
    MONITORING_READ = "monitoring:read"
    MONITORING_METRICS = "monitoring:metrics"
    MONITORING_ALERTS = "monitoring:alerts"
    MONITORING_CONFIG = "monitoring:config"
    
    # Permissões de Integração
    INTEGRATION_VIACEP = "integration:viacep"
    INTEGRATION_BANKING = "integration:banking"
    INTEGRATION_NOTIFICATIONS = "integration:notifications"
    
    # Permissões de Administração
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_DATABASE = "admin:database"
    ADMIN_BACKUP = "admin:backup"
    
    # Permissões de Auditoria
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"

# Hierarquia de roles (nível mais alto = mais permissões)
ROLE_HIERARCHY: Dict[str, int] = {
    "admin": 100,      # Acesso total
    "manager": 80,     # Gestão operacional
    "analyst": 60,     # Análise e relatórios
    "operator": 40,    # CRUD básico
    "readonly": 20,    # Somente leitura
    "guest": 10        # Acesso limitado
}

# Mapeamento de permissões por role
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        # Todas as permissões (acesso total)
        Permission.CLIENTE_CREATE.value,
        Permission.CLIENTE_READ.value,
        Permission.CLIENTE_UPDATE.value,
        Permission.CLIENTE_DELETE.value,
        Permission.CLIENTE_LIST.value,
        Permission.CLIENTE_EXPORT.value,
        
        Permission.TRANSACAO_CREATE.value,
        Permission.TRANSACAO_READ.value,
        Permission.TRANSACAO_UPDATE.value,
        Permission.TRANSACAO_DELETE.value,
        Permission.TRANSACAO_LIST.value,
        Permission.TRANSACAO_APPROVE.value,
        Permission.TRANSACAO_EXPORT.value,
        
        Permission.LOG_CREATE.value,
        Permission.LOG_READ.value,
        Permission.LOG_DELETE.value,
        Permission.LOG_LIST.value,
        Permission.LOG_EXPORT.value,
        
        Permission.MONITORING_READ.value,
        Permission.MONITORING_METRICS.value,
        Permission.MONITORING_ALERTS.value,
        Permission.MONITORING_CONFIG.value,
        
        Permission.INTEGRATION_VIACEP.value,
        Permission.INTEGRATION_BANKING.value,
        Permission.INTEGRATION_NOTIFICATIONS.value,
        
        Permission.ADMIN_USERS.value,
        Permission.ADMIN_ROLES.value,
        Permission.ADMIN_SYSTEM.value,
        Permission.ADMIN_DATABASE.value,
        Permission.ADMIN_BACKUP.value,
        
        Permission.AUDIT_READ.value,
        Permission.AUDIT_EXPORT.value,
    },
    
    "manager": {
        # Gestão operacional completa (sem admin de sistema)
        Permission.CLIENTE_CREATE.value,
        Permission.CLIENTE_READ.value,
        Permission.CLIENTE_UPDATE.value,
        Permission.CLIENTE_DELETE.value,
        Permission.CLIENTE_LIST.value,
        Permission.CLIENTE_EXPORT.value,
        
        Permission.TRANSACAO_CREATE.value,
        Permission.TRANSACAO_READ.value,
        Permission.TRANSACAO_UPDATE.value,
        Permission.TRANSACAO_LIST.value,
        Permission.TRANSACAO_APPROVE.value,
        Permission.TRANSACAO_EXPORT.value,
        
        Permission.LOG_READ.value,
        Permission.LOG_LIST.value,
        Permission.LOG_EXPORT.value,
        
        Permission.MONITORING_READ.value,
        Permission.MONITORING_METRICS.value,
        Permission.MONITORING_ALERTS.value,
        
        Permission.INTEGRATION_VIACEP.value,
        Permission.INTEGRATION_BANKING.value,
        Permission.INTEGRATION_NOTIFICATIONS.value,
        
        Permission.AUDIT_READ.value,
        Permission.AUDIT_EXPORT.value,
    },
    
    "analyst": {
        # Análise e relatórios (sem alterações)
        Permission.CLIENTE_READ.value,
        Permission.CLIENTE_LIST.value,
        Permission.CLIENTE_EXPORT.value,
        
        Permission.TRANSACAO_READ.value,
        Permission.TRANSACAO_LIST.value,
        Permission.TRANSACAO_EXPORT.value,
        
        Permission.LOG_READ.value,
        Permission.LOG_LIST.value,
        Permission.LOG_EXPORT.value,
        
        Permission.MONITORING_READ.value,
        Permission.MONITORING_METRICS.value,
        
        Permission.INTEGRATION_VIACEP.value,
        
        Permission.AUDIT_READ.value,
        Permission.AUDIT_EXPORT.value,
    },
    
    "operator": {
        # CRUD básico
        Permission.CLIENTE_CREATE.value,
        Permission.CLIENTE_READ.value,
        Permission.CLIENTE_UPDATE.value,
        Permission.CLIENTE_LIST.value,
        
        Permission.TRANSACAO_CREATE.value,
        Permission.TRANSACAO_READ.value,
        Permission.TRANSACAO_UPDATE.value,
        Permission.TRANSACAO_LIST.value,
        
        Permission.LOG_CREATE.value,
        Permission.LOG_READ.value,
        Permission.LOG_LIST.value,
        
        Permission.INTEGRATION_VIACEP.value,
    },
    
    "readonly": {
        # Somente leitura
        Permission.CLIENTE_READ.value,
        Permission.CLIENTE_LIST.value,
        
        Permission.TRANSACAO_READ.value,
        Permission.TRANSACAO_LIST.value,
        
        Permission.LOG_READ.value,
        Permission.LOG_LIST.value,
        
        Permission.MONITORING_READ.value,
    },
    
    "guest": {
        # Acesso muito limitado
        Permission.CLIENTE_READ.value,
        Permission.TRANSACAO_READ.value,
    }
}

def get_role_permissions(role: str) -> List[str]:
    """Retorna lista de permissões para um role"""
    return list(ROLE_PERMISSIONS.get(role.lower(), set()))

def has_permission(user_role: str, required_permission: str) -> bool:
    """Verifica se o role tem uma permissão específica"""
    user_permissions = ROLE_PERMISSIONS.get(user_role.lower(), set())
    return required_permission in user_permissions

def has_role_level(user_role: str, required_role: str) -> bool:
    """Verifica se o usuário tem nível de role suficiente"""
    user_level = ROLE_HIERARCHY.get(user_role.lower(), 0)
    required_level = ROLE_HIERARCHY.get(required_role.lower(), 999)
    return user_level >= required_level

def get_available_roles() -> List[Dict[str, any]]:
    """Retorna lista de roles disponíveis com descrições"""
    return [
        {
            "role": "admin",
            "name": "Administrador",
            "description": "Acesso total ao sistema",
            "level": ROLE_HIERARCHY["admin"],
            "permissions_count": len(ROLE_PERMISSIONS["admin"])
        },
        {
            "role": "manager",
            "name": "Gerente",
            "description": "Gestão operacional completa",
            "level": ROLE_HIERARCHY["manager"],
            "permissions_count": len(ROLE_PERMISSIONS["manager"])
        },
        {
            "role": "analyst",
            "name": "Analista",
            "description": "Análise e relatórios",
            "level": ROLE_HIERARCHY["analyst"],
            "permissions_count": len(ROLE_PERMISSIONS["analyst"])
        },
        {
            "role": "operator",
            "name": "Operador",
            "description": "CRUD básico",
            "level": ROLE_HIERARCHY["operator"],
            "permissions_count": len(ROLE_PERMISSIONS["operator"])
        },
        {
            "role": "readonly",
            "name": "Somente Leitura",
            "description": "Acesso de leitura",
            "level": ROLE_HIERARCHY["readonly"],
            "permissions_count": len(ROLE_PERMISSIONS["readonly"])
        },
        {
            "role": "guest",
            "name": "Convidado",
            "description": "Acesso limitado",
            "level": ROLE_HIERARCHY["guest"],
            "permissions_count": len(ROLE_PERMISSIONS["guest"])
        }
    ]

def validate_role(role: str) -> bool:
    """Valida se o role existe"""
    return role.lower() in ROLE_HIERARCHY

def get_role_hierarchy() -> Dict[str, int]:
    """Retorna hierarquia completa de roles"""
    return ROLE_HIERARCHY.copy()

def get_permissions_by_module() -> Dict[str, List[str]]:
    """Agrupa permissões por módulo"""
    modules = {}
    
    for permission in Permission:
        module, action = permission.value.split(':')
        if module not in modules:
            modules[module] = []
        modules[module].append(permission.value)
    
    return modules