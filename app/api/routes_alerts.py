"""
Routes para API de Alertas e Observabilidade
Endpoints para gerenciar alertas, regras e visualizar métricas
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from app.monitoring.alert_manager import alert_manager, Alert, AlertSeverity, AlertStatus
from app.monitoring.alert_rules import alert_rules_engine, AlertRule, AlertRuleType, ComparisonOperator
from app.monitoring.performance_monitor import performance_monitor
from app.security.auth import get_current_user, require_permissions
from app.security.roles import Permission
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/alerts", tags=["Alertas e Observabilidade"])

# Modelos Pydantic para API

class AlertResponse(BaseModel):
    """Modelo de resposta para alertas"""
    id: str
    name: str
    description: str
    severity: str
    status: str
    metric_name: str
    metric_value: float
    threshold: float
    labels: Dict[str, str]
    annotations: Dict[str, str]
    starts_at: datetime
    ends_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
class AlertRuleResponse(BaseModel):
    """Modelo de resposta para regras de alerta"""
    id: str
    name: str
    description: str
    metric_name: str
    rule_type: str
    operator: str
    threshold: float
    severity: str
    duration_minutes: int
    evaluation_interval: int
    labels: Dict[str, str]
    annotations: Dict[str, str]
    enabled: bool

class CreateAlertRuleRequest(BaseModel):
    """Modelo para criar regra de alerta"""
    name: str = Field(..., description="Nome da regra")
    description: str = Field(..., description="Descrição da regra")
    metric_name: str = Field(..., description="Nome da métrica")
    rule_type: str = Field(..., description="Tipo da regra (threshold, rate, absence, anomaly)")
    operator: str = Field(..., description="Operador de comparação (>, >=, <, <=, ==, !=)")
    threshold: float = Field(..., description="Valor limite")
    severity: str = Field(..., description="Severidade (critical, high, medium, low, info)")
    duration_minutes: int = Field(5, description="Duração mínima em minutos")
    evaluation_interval: int = Field(60, description="Intervalo de avaliação em segundos")
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = Field(True, description="Regra habilitada")

class UpdateAlertRuleRequest(BaseModel):
    """Modelo para atualizar regra de alerta"""
    name: Optional[str] = None
    description: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    duration_minutes: Optional[int] = None
    evaluation_interval: Optional[int] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None

class AlertActionRequest(BaseModel):
    """Modelo para ações em alertas"""
    user_id: str = Field(..., description="ID do usuário")
    comment: Optional[str] = Field(None, description="Comentário opcional")

class MetricsResponse(BaseModel):
    """Modelo de resposta para métricas"""
    timestamp: datetime
    metrics: Dict[str, Any]

class AlertStatistics(BaseModel):
    """Estatísticas de alertas"""
    total_alerts: int
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    alerts_last_24h: int
    alerts_last_7d: int
    most_frequent_alerts: List[Dict[str, Any]]

# Endpoints de Alertas

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    severity: Optional[str] = Query(None, description="Filtrar por severidade"),
    limit: int = Query(100, le=1000, description="Limite de resultados"),
    current_user = Depends(require_permissions([Permission.MONITORING_VIEW]))
):
    """Lista alertas com filtros opcionais"""
    try:
        # Obtém alertas ativos
        active_alerts = alert_manager.get_active_alerts()
        
        # Obtém histórico recente
        historical_alerts = alert_manager.get_alert_history(limit)
        
        # Combina e remove duplicatas
        all_alerts = []
        alert_ids = set()
        
        for alert in active_alerts + historical_alerts:
            if alert.id not in alert_ids:
                alert_ids.add(alert.id)
                all_alerts.append(alert)
        
        # Aplica filtros
        filtered_alerts = all_alerts
        
        if status:
            try:
                status_enum = AlertStatus(status.lower())
                filtered_alerts = [a for a in filtered_alerts if a.status == status_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status inválido: {status}"
                )
        
        if severity:
            try:
                severity_enum = AlertSeverity(severity.lower())
                filtered_alerts = [a for a in filtered_alerts if a.severity == severity_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Severidade inválida: {severity}"
                )
        
        # Ordena por data (mais recentes primeiro)
        filtered_alerts.sort(key=lambda x: x.starts_at, reverse=True)
        
        # Aplica limite
        filtered_alerts = filtered_alerts[:limit]
        
        # Converte para modelo de resposta
        return [
            AlertResponse(
                id=alert.id,
                name=alert.name,
                description=alert.description,
                severity=alert.severity.value,
                status=alert.status.value,
                metric_name=alert.metric_name,
                metric_value=alert.metric_value,
                threshold=alert.threshold,
                labels=alert.labels,
                annotations=alert.annotations,
                starts_at=alert.starts_at,
                ends_at=alert.ends_at,
                resolved_at=alert.resolved_at,
                acknowledged_at=alert.acknowledged_at
            )
            for alert in filtered_alerts
        ]
        
    except Exception as e:
        logger.error(f"Erro ao listar alertas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/active", response_model=List[AlertResponse])
async def list_active_alerts(
    current_user = Depends(require_permissions([Permission.MONITORING_VIEW]))
):
    """Lista apenas alertas ativos"""
    try:
        active_alerts = alert_manager.get_active_alerts()
        
        return [
            AlertResponse(
                id=alert.id,
                name=alert.name,
                description=alert.description,
                severity=alert.severity.value,
                status=alert.status.value,
                metric_name=alert.metric_name,
                metric_value=alert.metric_value,
                threshold=alert.threshold,
                labels=alert.labels,
                annotations=alert.annotations,
                starts_at=alert.starts_at,
                ends_at=alert.ends_at,
                resolved_at=alert.resolved_at,
                acknowledged_at=alert.acknowledged_at
            )
            for alert in active_alerts
        ]
        
    except Exception as e:
        logger.error(f"Erro ao listar alertas ativos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    action: AlertActionRequest,
    current_user = Depends(require_permissions([Permission.MONITORING_MANAGE]))
):
    """Reconhece um alerta"""
    try:
        success = alert_manager.acknowledge_alert(alert_id, action.user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerta não encontrado"
            )
        
        return {"message": "Alerta reconhecido com sucesso", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reconhecer alerta {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/{alert_id}/silence")
async def silence_alert(
    alert_id: str,
    action: AlertActionRequest,
    duration_minutes: int = Query(60, description="Duração do silêncio em minutos"),
    current_user = Depends(require_permissions([Permission.MONITORING_MANAGE]))
):
    """Silencia um alerta temporariamente"""
    try:
        success = alert_manager.silence_alert(alert_id, duration_minutes)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alerta não encontrado"
            )
        
        return {
            "message": f"Alerta silenciado por {duration_minutes} minutos",
            "alert_id": alert_id,
            "duration_minutes": duration_minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao silenciar alerta {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/statistics", response_model=AlertStatistics)
async def get_alert_statistics(
    current_user = Depends(require_permissions([Permission.MONITORING_VIEW]))
):
    """Obtém estatísticas de alertas"""
    try:
        active_alerts = alert_manager.get_active_alerts()
        historical_alerts = alert_manager.get_alert_history(1000)
        
        # Contadores por severidade (alertas ativos)
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for alert in active_alerts:
            if alert.severity.value in severity_counts:
                severity_counts[alert.severity.value] += 1
        
        # Alertas nas últimas 24h e 7 dias
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        alerts_24h = len([a for a in historical_alerts if a.starts_at >= last_24h])
        alerts_7d = len([a for a in historical_alerts if a.starts_at >= last_7d])
        
        # Alertas mais frequentes
        alert_counts = {}
        for alert in historical_alerts:
            rule_id = alert.labels.get('rule_id', alert.name)
            alert_counts[rule_id] = alert_counts.get(rule_id, 0) + 1
        
        most_frequent = [
            {"rule": k, "count": v}
            for k, v in sorted(alert_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return AlertStatistics(
            total_alerts=len(historical_alerts),
            active_alerts=len(active_alerts),
            critical_alerts=severity_counts["critical"],
            high_alerts=severity_counts["high"],
            medium_alerts=severity_counts["medium"],
            low_alerts=severity_counts["low"],
            alerts_last_24h=alerts_24h,
            alerts_last_7d=alerts_7d,
            most_frequent_alerts=most_frequent
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de alertas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

# Endpoints de Regras de Alerta

@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    current_user = Depends(require_permissions([Permission.MONITORING_VIEW]))
):
    """Lista todas as regras de alerta"""
    try:
        rules = alert_rules_engine.list_rules()
        
        return [
            AlertRuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                metric_name=rule.metric_name,
                rule_type=rule.rule_type.value,
                operator=rule.operator.value,
                threshold=rule.threshold,
                severity=rule.severity.value,
                duration_minutes=rule.duration_minutes,
                evaluation_interval=rule.evaluation_interval,
                labels=rule.labels,
                annotations=rule.annotations,
                enabled=rule.enabled
            )
            for rule in rules
        ]
        
    except Exception as e:
        logger.error(f"Erro ao listar regras de alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_data: CreateAlertRuleRequest,
    current_user = Depends(require_permissions([Permission.MONITORING_ADMIN]))
):
    """Cria uma nova regra de alerta"""
    try:
        # Valida enums
        try:
            rule_type = AlertRuleType(rule_data.rule_type)
            operator = ComparisonOperator(rule_data.operator)
            severity = AlertSeverity(rule_data.severity)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor inválido: {str(e)}"
            )
        
        # Cria regra
        rule = AlertRule(
            id=f"custom_{int(datetime.now().timestamp())}",
            name=rule_data.name,
            description=rule_data.description,
            metric_name=rule_data.metric_name,
            rule_type=rule_type,
            operator=operator,
            threshold=rule_data.threshold,
            severity=severity,
            duration_minutes=rule_data.duration_minutes,
            evaluation_interval=rule_data.evaluation_interval,
            labels=rule_data.labels,
            annotations=rule_data.annotations,
            enabled=rule_data.enabled
        )
        
        # Adiciona ao motor
        alert_rules_engine.add_rule(rule)
        
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            metric_name=rule.metric_name,
            rule_type=rule.rule_type.value,
            operator=rule.operator.value,
            threshold=rule.threshold,
            severity=rule.severity.value,
            duration_minutes=rule.duration_minutes,
            evaluation_interval=rule.evaluation_interval,
            labels=rule.labels,
            annotations=rule.annotations,
            enabled=rule.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar regra de alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    rule_data: UpdateAlertRuleRequest,
    current_user = Depends(require_permissions([Permission.MONITORING_ADMIN]))
):
    """Atualiza uma regra de alerta"""
    try:
        rule = alert_rules_engine.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regra não encontrada"
            )
        
        # Atualiza campos se fornecidos
        if rule_data.name is not None:
            rule.name = rule_data.name
        if rule_data.description is not None:
            rule.description = rule_data.description
        if rule_data.threshold is not None:
            rule.threshold = rule_data.threshold
        if rule_data.severity is not None:
            try:
                rule.severity = AlertSeverity(rule_data.severity)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Severidade inválida: {rule_data.severity}"
                )
        if rule_data.duration_minutes is not None:
            rule.duration_minutes = rule_data.duration_minutes
        if rule_data.evaluation_interval is not None:
            rule.evaluation_interval = rule_data.evaluation_interval
        if rule_data.labels is not None:
            rule.labels = rule_data.labels
        if rule_data.annotations is not None:
            rule.annotations = rule_data.annotations
        if rule_data.enabled is not None:
            rule.enabled = rule_data.enabled
        
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            metric_name=rule.metric_name,
            rule_type=rule.rule_type.value,
            operator=rule.operator.value,
            threshold=rule.threshold,
            severity=rule.severity.value,
            duration_minutes=rule.duration_minutes,
            evaluation_interval=rule.evaluation_interval,
            labels=rule.labels,
            annotations=rule.annotations,
            enabled=rule.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar regra {rule_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user = Depends(require_permissions([Permission.MONITORING_ADMIN]))
):
    """Remove uma regra de alerta"""
    try:
        success = alert_rules_engine.remove_rule(rule_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regra não encontrada"
            )
        
        return {"message": "Regra removida com sucesso", "rule_id": rule_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover regra {rule_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

# Endpoints de Métricas

@router.get("/metrics", response_model=MetricsResponse)
async def get_current_metrics(
    current_user = Depends(require_permissions([Permission.MONITORING_VIEW]))
):
    """Obtém métricas atuais do sistema"""
    try:
        metrics = performance_monitor.get_current_metrics()
        
        return MetricsResponse(
            timestamp=datetime.now(),
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/health")
async def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        # Verifica se os sistemas estão funcionando
        is_alert_engine_running = alert_rules_engine.is_running
        active_alerts_count = len(alert_manager.get_active_alerts())
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "alert_engine": "running" if is_alert_engine_running else "stopped",
                "alert_manager": "running",
                "metrics_collector": "running"
            },
            "active_alerts": active_alerts_count
        }
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }