# Configurações do MongoDB e variáveis de ambiente

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List

class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str
    MONGO_DB: str
    
    # Autenticação e Segurança
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Configurações de segurança de senha
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30
    
    # Configurações SMTP para notificações por email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    ALERT_EMAIL: Optional[str] = None
    
    # Notificações Slack
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Notificações Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Notificações WhatsApp Business API
    WHATSAPP_API_URL: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_DEFAULT_RECIPIENT: Optional[str] = None
    
    # Webhook genérico
    DEFAULT_WEBHOOK_URL: Optional[str] = None
    
    # Redis (para cache e filas)
    REDIS_URL: Optional[str] = None
    
    # Configurações de ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Configurações de API
    API_TITLE: str = "MonitorDB API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Sistema de monitoramento e gestão de dados de clientes"
    
    # Limites de rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # segundos
    
    # Timeouts para integrações externas
    HTTP_TIMEOUT: float = 30.0
    VIACEP_TIMEOUT: float = 10.0
    BANK_API_TIMEOUT: float = 15.0
    
    # Configurações de Autenticação JWT
    JWT_SECRET_KEY: str = Field(default="your-super-secret-jwt-key-change-in-production", description="Chave secreta JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Algoritmo JWT")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Expiração do token de acesso em minutos")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Expiração do token de refresh em dias")
    JWT_ISSUER: str = Field(default="MonitorDB", description="Emissor do token JWT")
    
    # Configurações de Email para Notificações
    SMTP_SERVER: str = Field(default="smtp.gmail.com", description="Servidor SMTP")
    SMTP_PORT: int = Field(default=587, description="Porta SMTP")
    SMTP_USERNAME: str = Field(default="", description="Usuário SMTP")
    SMTP_PASSWORD: str = Field(default="", description="Senha SMTP")
    SMTP_USE_TLS: bool = Field(default=True, description="Usar TLS no SMTP")
    EMAIL_FROM: str = Field(default="admin@monitordb.com", description="Email remetente")
    
    # Configurações de Segurança
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Tamanho mínimo da senha")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Senha deve ter maiúscula")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="Senha deve ter minúscula")
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True, description="Senha deve ter números")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, description="Senha deve ter caracteres especiais")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, description="Máximo de tentativas de login")
    LOCKOUT_DURATION_MINUTES: int = Field(default=15, description="Duração do bloqueio em minutos")
    
    # Configurações de Alertas e Notificações
    ALERT_FROM_EMAIL: str = Field(default="alerts@monitordb.com", description="Email para alertas")
    ALERT_EMAIL_RECIPIENTS: List[str] = Field(default_factory=list, description="Destinatários padrão dos alertas")
    ALERT_CRITICAL_RECIPIENTS: List[str] = Field(default_factory=list, description="Destinatários para alertas críticos")
    
    # Configurações do Slack
    SLACK_WEBHOOK_URL: str = Field(default="", description="URL do webhook Slack")
    SLACK_CHANNEL: str = Field(default="#alerts", description="Canal Slack para alertas")
    SLACK_USERNAME: str = Field(default="MonitorDB Alerts", description="Nome do bot Slack")
    
    # Configurações de Webhooks
    ALERT_WEBHOOK_URLS: List[str] = Field(default_factory=list, description="URLs de webhooks para alertas")
    
    # Configurações do Prometheus
    PROMETHEUS_METRICS_PORT: int = Field(default=8001, description="Porta para métricas Prometheus")
    PROMETHEUS_METRICS_PATH: str = Field(default="/metrics", description="Caminho para métricas Prometheus")
    
    # Configurações do Grafana
    GRAFANA_URL: str = Field(default="http://localhost:3000", description="URL do Grafana")
    GRAFANA_API_KEY: str = Field(default="", description="API Key do Grafana")
    
    # Configurações de Observabilidade
    ENABLE_METRICS_EXPORT: bool = Field(default=True, description="Habilitar exportação de métricas")
    ENABLE_ALERTING: bool = Field(default=True, description="Habilitar sistema de alertas")
    METRICS_RETENTION_DAYS: int = Field(default=30, description="Retenção de métricas em dias")

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

settings = Settings()
