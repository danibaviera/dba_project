"""
Sistema de Alertas e Notificações Multi-Canal
Suporta envio de alertas via email, Slack, Telegram e webhook genérico
"""

import smtplib
import httpx
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Níveis de severidade de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Canais disponíveis para envio de alertas"""
    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    
class Alert:
    """Modelo de um alerta"""
    
    def __init__(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.MEDIUM,
        source: str = "MonitorDB",
        metadata: Optional[Dict] = None
    ):
        self.id = f"alert_{int(datetime.utcnow().timestamp() * 1000)}"
        self.title = title
        self.message = message
        self.level = level
        self.source = source
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.sent_channels = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte alerta para dicionário"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "sent_channels": self.sent_channels
        }

class EmailNotifier:
    """Notificador via email usando SMTP"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'monitordb@localhost')
    
    async def send_alert(self, alert: Alert, recipients: List[str]) -> bool:
        """
        Envia alerta por email
        
        Args:
            alert: Alerta a ser enviado
            recipients: Lista de emails destinatários
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            # Criar mensagem
            msg = MimeMultipart('alternative')
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
            msg['From'] = self.from_email
            msg['To'] = ", ".join(recipients)
            
            # Corpo do email em texto
            text_body = f"""
MonitorDB Alert

Título: {alert.title}
Nível: {alert.level.value.upper()}
Origem: {alert.source}
Data: {alert.created_at.strftime('%d/%m/%Y %H:%M:%S')}

Mensagem:
{alert.message}

Metadados:
{json.dumps(alert.metadata, indent=2)}

---
MonitorDB System
            """.strip()
            
            # Corpo do email em HTML
            html_body = f"""
            <html>
              <head></head>
              <body>
                <h2>🚨 MonitorDB Alert</h2>
                <table style="border-collapse: collapse; width: 100%;">
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Título</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert.title}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Nível</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert.level.value.upper()}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Origem</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert.source}</td>
                  </tr>
                  <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;"><strong>Data</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alert.created_at.strftime('%d/%m/%Y %H:%M:%S')}</td>
                  </tr>
                </table>
                
                <h3>Mensagem:</h3>
                <p>{alert.message.replace(chr(10), '<br>')}</p>
                
                <h3>Metadados:</h3>
                <pre style="background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd;">
{json.dumps(alert.metadata, indent=2)}
                </pre>
                
                <hr>
                <p><em>MonitorDB System</em></p>
              </body>
            </html>
            """
            
            # Anexar partes da mensagem
            msg.attach(MimeText(text_body, 'plain', 'utf-8'))
            msg.attach(MimeText(html_body, 'html', 'utf-8'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Alert {alert.id} sent via email to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert {alert.id}: {str(e)}")
            return False

class SlackNotifier:
    """Notificador via Slack usando webhook"""
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', '')
    
    async def send_alert(self, alert: Alert, channel: Optional[str] = None) -> bool:
        """
        Envia alerta para Slack
        
        Args:
            alert: Alerta a ser enviado
            channel: Canal do Slack (opcional)
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            # Mapear nível para cor
            color_map = {
                AlertLevel.LOW: "#36a64f",      # Verde
                AlertLevel.MEDIUM: "#ffb74d",   # Laranja
                AlertLevel.HIGH: "#ff9800",     # Laranja escuro
                AlertLevel.CRITICAL: "#f44336"  # Vermelho
            }
            
            # Criar payload do Slack
            payload = {
                "channel": channel or "#alerts",
                "username": "MonitorDB",
                "icon_emoji": ":rotating_light:",
                "attachments": [
                    {
                        "color": color_map.get(alert.level, "#36a64f"),
                        "title": f"{alert.level.value.upper()} Alert: {alert.title}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Source",
                                "value": alert.source,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.created_at.strftime('%d/%m/%Y %H:%M:%S'),
                                "short": True
                            }
                        ],
                        "footer": "MonitorDB System",
                        "ts": int(alert.created_at.timestamp())
                    }
                ]
            }
            
            # Adicionar metadados se existirem
            if alert.metadata:
                payload["attachments"][0]["fields"].append({
                    "title": "Metadata",
                    "value": f"```{json.dumps(alert.metadata, indent=2)}```",
                    "short": False
                })
            
            # Enviar para Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
            
            logger.info(f"Alert {alert.id} sent to Slack")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert {alert.id}: {str(e)}")
            return False

class TelegramNotifier:
    """Notificador via Telegram Bot API"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_alert(self, alert: Alert, chat_id: str) -> bool:
        """
        Envia alerta via Telegram
        
        Args:
            alert: Alerta a ser enviado
            chat_id: ID do chat ou canal do Telegram
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return False
        
        try:
            # Mapear nível para emoji
            emoji_map = {
                AlertLevel.LOW: "🟢",
                AlertLevel.MEDIUM: "🟡",
                AlertLevel.HIGH: "🟠",
                AlertLevel.CRITICAL: "🔴"
            }
            
            # Criar mensagem
            emoji = emoji_map.get(alert.level, "🟡")
            message = f"""
{emoji} *MonitorDB Alert*

*{alert.level.value.upper()}*: {alert.title}

*Message:* {alert.message}

*Source:* {alert.source}
*Time:* {alert.created_at.strftime('%d/%m/%Y %H:%M:%S')}

*Metadata:*
```json
{json.dumps(alert.metadata, indent=2)}
```
            """.strip()
            
            # Enviar mensagem
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            
            logger.info(f"Alert {alert.id} sent to Telegram chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert {alert.id}: {str(e)}")
            return False

class WebhookNotifier:
    """Notificador via webhook genérico"""
    
    async def send_alert(self, alert: Alert, webhook_url: str, headers: Optional[Dict] = None) -> bool:
        """
        Envia alerta via webhook
        
        Args:
            alert: Alerta a ser enviado
            webhook_url: URL do webhook
            headers: Headers HTTP opcionais
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            payload = alert.to_dict()
            
            default_headers = {"Content-Type": "application/json"}
            if headers:
                default_headers.update(headers)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=default_headers,
                    timeout=30.0
                )
                response.raise_for_status()
            
            logger.info(f"Alert {alert.id} sent via webhook to {webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert {alert.id} to {webhook_url}: {str(e)}")
            return False

class AlertService:
    """Serviço central de alertas e notificações"""
    
    def __init__(self):
        self.email_notifier = EmailNotifier()
        self.slack_notifier = SlackNotifier()
        self.telegram_notifier = TelegramNotifier()
        self.webhook_notifier = WebhookNotifier()
        self.alert_history = []
        self.max_history = 1000
    
    async def send_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.MEDIUM,
        channels: List[AlertChannel] = None,
        recipients: Dict[str, Any] = None
    ) -> Alert:
        """
        Envia alerta através dos canais especificados
        
        Args:
            title: Título do alerta
            message: Mensagem do alerta
            level: Nível de severidade
            channels: Lista de canais para envio
            recipients: Configurações de destinatários por canal
            
        Returns:
            Objeto Alert criado
        """
        # Criar alerta
        alert = Alert(title=title, message=message, level=level)
        
        # Configurações padrão
        channels = channels or [AlertChannel.EMAIL]
        recipients = recipients or {}
        
        # Enviar através dos canais
        for channel in channels:
            success = False
            
            try:
                if channel == AlertChannel.EMAIL:
                    email_recipients = recipients.get('email', ['admin@localhost'])
                    success = await self.email_notifier.send_alert(alert, email_recipients)
                
                elif channel == AlertChannel.SLACK:
                    slack_channel = recipients.get('slack_channel', '#alerts')
                    success = await self.slack_notifier.send_alert(alert, slack_channel)
                
                elif channel == AlertChannel.TELEGRAM:
                    telegram_chat = recipients.get('telegram_chat_id', '')
                    if telegram_chat:
                        success = await self.telegram_notifier.send_alert(alert, telegram_chat)
                
                elif channel == AlertChannel.WEBHOOK:
                    webhook_config = recipients.get('webhook', {})
                    if 'url' in webhook_config:
                        success = await self.webhook_notifier.send_alert(
                            alert,
                            webhook_config['url'],
                            webhook_config.get('headers')
                        )
                
                if success:
                    alert.sent_channels.append(channel.value)
                    
            except Exception as e:
                logger.error(f"Error sending alert via {channel.value}: {str(e)}")
        
        # Adicionar ao histórico
        self._add_to_history(alert)
        
        return alert
    
    def _add_to_history(self, alert: Alert):
        """Adiciona alerta ao histórico mantendo limite máximo"""
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Retorna histórico de alertas"""
        return [alert.to_dict() for alert in self.alert_history[-limit:]]
    
    async def send_system_alert(self, message: str, level: AlertLevel = AlertLevel.HIGH):
        """Envia alerta de sistema com configurações padrão"""
        return await self.send_alert(
            title="System Alert",
            message=message,
            level=level,
            channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
            recipients={
                'email': ['admin@monitordb.com'],
                'slack_channel': '#system-alerts'
            }
        )
    
    async def send_performance_alert(self, metric: str, value: float, threshold: float):
        """Envia alerta específico de performance"""
        return await self.send_alert(
            title=f"Performance Alert: {metric}",
            message=f"Metric {metric} reached {value:.2f}, exceeding threshold of {threshold:.2f}",
            level=AlertLevel.WARNING if value < threshold * 1.2 else AlertLevel.HIGH,
            channels=[AlertChannel.EMAIL],
            recipients={'email': ['monitoring@monitordb.com']}
        )


# Instância global do serviço de alertas
alert_service = AlertService()


# Funções utilitárias
async def send_critical_alert(title: str, message: str):
    """Função simplificada para alertas críticos"""
    return await alert_service.send_alert(
        title=title,
        message=message,
        level=AlertLevel.CRITICAL,
        channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.TELEGRAM]
    )

async def send_info_alert(title: str, message: str):
    """Função simplificada para alertas informativos"""
    return await alert_service.send_alert(
        title=title,
        message=message,
        level=AlertLevel.LOW,
        channels=[AlertChannel.EMAIL]
    )


# Exemplo de uso
if __name__ == "__main__":
    async def exemplo():
        # Alerta simples
        await alert_service.send_system_alert(
            "Sistema reiniciado com sucesso",
            AlertLevel.LOW
        )
        
        # Alerta de performance
        await alert_service.send_performance_alert(
            "CPU Usage",
            85.5,
            80.0
        )
        
        # Alerta crítico
        await send_critical_alert(
            "Database Connection Lost",
            "Unable to connect to MongoDB. System may be down."
        )
    
    asyncio.run(exemplo())