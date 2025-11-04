"""
Serviço de Notificações Multi-Canal
Sistema completo para envio de notificações via Email, SMS, Push, Slack e WhatsApp
"""

import asyncio
import smtplib
import httpx
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import logging
from enum import Enum
from dataclasses import dataclass, asdict

from app.config import settings

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Canais de notificação disponíveis"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

class NotificationPriority(Enum):
    """Prioridades de notificação"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationTemplate:
    """Template de notificação"""
    subject: str
    content: str
    html_content: Optional[str] = None
    variables: Dict[str, Any] = None
    
    def render(self, **kwargs) -> 'NotificationTemplate':
        """Renderiza template com variáveis"""
        variables = {**(self.variables or {}), **kwargs}
        
        rendered_subject = self.subject.format(**variables)
        rendered_content = self.content.format(**variables)
        rendered_html = None
        
        if self.html_content:
            rendered_html = self.html_content.format(**variables)
        
        return NotificationTemplate(
            subject=rendered_subject,
            content=rendered_content,
            html_content=rendered_html,
            variables=variables
        )

@dataclass
class Notification:
    """Modelo de notificação"""
    id: str
    recipient: str
    channel: NotificationChannel
    template: NotificationTemplate
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    status: str = "pending"
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte notificação para dicionário"""
        return {
            "id": self.id,
            "recipient": self.recipient,
            "channel": self.channel.value,
            "subject": self.template.subject,
            "content": self.template.content,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "error_message": self.error_message
        }

class EmailNotificationService:
    """Serviço de notificação por email"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@monitordb.com')
        self.from_name = getattr(settings, 'FROM_NAME', 'MonitorDB')
    
    async def send_notification(self, notification: Notification) -> bool:
        """Envia notificação por email"""
        try:
            # Criar mensagem
            msg = MimeMultipart('alternative')
            msg['Subject'] = notification.template.subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = notification.recipient
            msg['Date'] = notification.created_at.strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Adicionar prioridade
            if notification.priority == NotificationPriority.URGENT:
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            elif notification.priority == NotificationPriority.HIGH:
                msg['X-Priority'] = '2'
                msg['X-MSMail-Priority'] = 'High'
            
            # Corpo em texto
            text_part = MimeText(notification.template.content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Corpo em HTML se disponível
            if notification.template.html_content:
                html_part = MimeText(notification.template.html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            logger.info(f"Email sent successfully to {notification.recipient}")
            return True
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            logger.error(f"Failed to send email to {notification.recipient}: {str(e)}")
            return False

class SMSNotificationService:
    """Serviço de notificação por SMS"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'SMS_API_URL', '')
        self.api_key = getattr(settings, 'SMS_API_KEY', '')
        self.sender_id = getattr(settings, 'SMS_SENDER_ID', 'MonitorDB')
    
    async def send_notification(self, notification: Notification) -> bool:
        """Envia notificação por SMS"""
        if not self.api_url or not self.api_key:
            notification.status = "failed"
            notification.error_message = "SMS API not configured"
            return False
        
        try:
            payload = {
                'to': notification.recipient,
                'from': self.sender_id,
                'message': notification.template.content[:160],  # Limite SMS
                'api_key': self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload)
                response.raise_for_status()
            
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            logger.info(f"SMS sent successfully to {notification.recipient}")
            return True
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            logger.error(f"Failed to send SMS to {notification.recipient}: {str(e)}")
            return False

class PushNotificationService:
    """Serviço de notificação push"""
    
    def __init__(self):
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', '')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
    
    async def send_notification(self, notification: Notification) -> bool:
        """Envia notificação push"""
        if not self.fcm_server_key:
            notification.status = "failed"
            notification.error_message = "FCM server key not configured"
            return False
        
        try:
            headers = {
                'Authorization': f'key={self.fcm_server_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'to': notification.recipient,  # FCM token
                'notification': {
                    'title': notification.template.subject,
                    'body': notification.template.content,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                },
                'data': notification.metadata
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.fcm_url, json=payload, headers=headers)
                response.raise_for_status()
            
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            logger.info(f"Push notification sent successfully to {notification.recipient}")
            return True
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            logger.error(f"Failed to send push notification to {notification.recipient}: {str(e)}")
            return False

class SlackNotificationService:
    """Serviço de notificação Slack"""
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
        self.bot_token = getattr(settings, 'SLACK_BOT_TOKEN', '')
    
    async def send_notification(self, notification: Notification) -> bool:
        """Envia notificação para Slack"""
        if not self.webhook_url and not self.bot_token:
            notification.status = "failed"
            notification.error_message = "Slack webhook/token not configured"
            return False
        
        try:
            # Preparar payload
            payload = {
                'channel': notification.recipient,
                'username': 'MonitorDB',
                'icon_emoji': ':bell:',
                'text': notification.template.content,
                'attachments': [
                    {
                        'color': self._get_color_for_priority(notification.priority),
                        'title': notification.template.subject,
                        'text': notification.template.content,
                        'footer': 'MonitorDB',
                        'ts': int(notification.created_at.timestamp())
                    }
                ]
            }
            
            # Enviar via webhook ou API
            if self.webhook_url:
                async with httpx.AsyncClient() as client:
                    response = await client.post(self.webhook_url, json=payload)
                    response.raise_for_status()
            else:
                # Usar Bot API (implementação simplificada)
                headers = {'Authorization': f'Bearer {self.bot_token}'}
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://slack.com/api/chat.postMessage',
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
            
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            logger.info(f"Slack notification sent successfully to {notification.recipient}")
            return True
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            logger.error(f"Failed to send Slack notification to {notification.recipient}: {str(e)}")
            return False
    
    def _get_color_for_priority(self, priority: NotificationPriority) -> str:
        """Retorna cor baseada na prioridade"""
        colors = {
            NotificationPriority.LOW: "#36a64f",
            NotificationPriority.NORMAL: "#2196F3",
            NotificationPriority.HIGH: "#ff9800",
            NotificationPriority.URGENT: "#f44336"
        }
        return colors.get(priority, "#2196F3")

class WhatsAppNotificationService:
    """Serviço de notificação WhatsApp Business API"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'WHATSAPP_API_URL', '')
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    
    async def send_notification(self, notification: Notification) -> bool:
        """Envia notificação via WhatsApp"""
        if not all([self.api_url, self.access_token, self.phone_number_id]):
            notification.status = "failed"
            notification.error_message = "WhatsApp API not configured"
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': notification.recipient,
                'text': {
                    'body': f"*{notification.template.subject}*\n\n{notification.template.content}"
                }
            }
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
            
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            logger.info(f"WhatsApp message sent successfully to {notification.recipient}")
            return True
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            logger.error(f"Failed to send WhatsApp message to {notification.recipient}: {str(e)}")
            return False

class NotificationService:
    """Serviço central de notificações"""
    
    def __init__(self):
        self.services = {
            NotificationChannel.EMAIL: EmailNotificationService(),
            NotificationChannel.SMS: SMSNotificationService(),
            NotificationChannel.PUSH: PushNotificationService(),
            NotificationChannel.SLACK: SlackNotificationService(),
            NotificationChannel.WHATSAPP: WhatsAppNotificationService()
        }
        self.notification_history = []
        self.max_history = 1000
        
        # Templates predefinidos
        self.templates = {
            'welcome': NotificationTemplate(
                subject="Bem-vindo ao MonitorDB!",
                content="Olá {nome}, sua conta foi criada com sucesso em {data}.",
                html_content="<h2>Bem-vindo ao MonitorDB!</h2><p>Olá <strong>{nome}</strong>, sua conta foi criada com sucesso em <em>{data}</em>.</p>"
            ),
            'transaction_alert': NotificationTemplate(
                subject="Transação Realizada - R$ {valor}",
                content="Uma transação de R$ {valor} foi realizada na sua conta em {data}.\nTipo: {tipo}\nStatus: {status}",
                html_content="<h3>Transação Realizada</h3><p>Uma transação de <strong>R$ {valor}</strong> foi realizada na sua conta em {data}.</p><p><strong>Tipo:</strong> {tipo}<br><strong>Status:</strong> {status}</p>"
            ),
            'system_alert': NotificationTemplate(
                subject="Alerta do Sistema: {tipo}",
                content="Alerta: {mensagem}\nData: {data}\nSeveridade: {severidade}",
                html_content="<div style='padding: 20px; border-left: 4px solid #f44336;'><h3>🚨 Alerta do Sistema</h3><p><strong>Tipo:</strong> {tipo}</p><p><strong>Mensagem:</strong> {mensagem}</p><p><strong>Severidade:</strong> {severidade}</p></div>"
            )
        }
    
    async def send_notification(
        self,
        channel: NotificationChannel,
        recipient: str,
        template: Union[str, NotificationTemplate],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> Notification:
        """
        Envia notificação
        
        Args:
            channel: Canal de notificação
            recipient: Destinatário
            template: Template (nome ou objeto)
            priority: Prioridade
            **kwargs: Variáveis do template
            
        Returns:
            Objeto Notification com status do envio
        """
        # Resolver template
        if isinstance(template, str):
            if template not in self.templates:
                raise ValueError(f"Template '{template}' não encontrado")
            template_obj = self.templates[template].render(**kwargs)
        else:
            template_obj = template.render(**kwargs)
        
        # Criar notificação
        notification_id = f"notif_{int(datetime.utcnow().timestamp() * 1000)}"
        notification = Notification(
            id=notification_id,
            recipient=recipient,
            channel=channel,
            template=template_obj,
            priority=priority,
            metadata=kwargs
        )
        
        # Enviar através do serviço apropriado
        service = self.services.get(channel)
        if service:
            await service.send_notification(notification)
        else:
            notification.status = "failed"
            notification.error_message = f"Channel {channel.value} not supported"
        
        # Adicionar ao histórico
        self._add_to_history(notification)
        
        return notification
    
    async def send_multi_channel_notification(
        self,
        channels: List[NotificationChannel],
        recipient: str,
        template: Union[str, NotificationTemplate],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs
    ) -> List[Notification]:
        """Envia notificação através de múltiplos canais"""
        notifications = []
        
        for channel in channels:
            try:
                notification = await self.send_notification(
                    channel, recipient, template, priority, **kwargs
                )
                notifications.append(notification)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.value}: {str(e)}")
        
        return notifications
    
    def _add_to_history(self, notification: Notification):
        """Adiciona notificação ao histórico"""
        self.notification_history.append(notification)
        if len(self.notification_history) > self.max_history:
            self.notification_history.pop(0)
    
    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """Retorna histórico de notificações"""
        return [notif.to_dict() for notif in self.notification_history[-limit:]]
    
    def get_template(self, name: str) -> Optional[NotificationTemplate]:
        """Retorna template por nome"""
        return self.templates.get(name)
    
    def add_template(self, name: str, template: NotificationTemplate):
        """Adiciona novo template"""
        self.templates[name] = template

# Instância global
notification_service = NotificationService()

# Funções utilitárias
async def send_welcome_email(email: str, nome: str):
    """Envia email de boas-vindas"""
    return await notification_service.send_notification(
        channel=NotificationChannel.EMAIL,
        recipient=email,
        template='welcome',
        nome=nome,
        data=datetime.now().strftime('%d/%m/%Y')
    )

async def send_transaction_alert(email: str, valor: float, tipo: str, status: str):
    """Envia alerta de transação"""
    return await notification_service.send_notification(
        channel=NotificationChannel.EMAIL,
        recipient=email,
        template='transaction_alert',
        priority=NotificationPriority.HIGH,
        valor=f"{valor:.2f}",
        tipo=tipo,
        status=status,
        data=datetime.now().strftime('%d/%m/%Y %H:%M')
    )

async def send_system_alert_multi_channel(message: str, severity: str = "HIGH"):
    """Envia alerta de sistema em múltiplos canais"""
    channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]
    
    return await notification_service.send_multi_channel_notification(
        channels=channels,
        recipient="admin@monitordb.com",  # ou canal Slack
        template='system_alert',
        priority=NotificationPriority.URGENT if severity == "CRITICAL" else NotificationPriority.HIGH,
        tipo="Sistema",
        mensagem=message,
        severidade=severity,
        data=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    )

# Exemplo de uso
if __name__ == "__main__":
    async def exemplo():
        # Email de boas-vindas
        await send_welcome_email("user@example.com", "João Silva")
        
        # Alerta de transação
        await send_transaction_alert("user@example.com", 150.00, "PIX", "Aprovada")
        
        # Alerta de sistema multi-canal
        await send_system_alert_multi_channel("Sistema reiniciado", "INFO")
    
    asyncio.run(exemplo())