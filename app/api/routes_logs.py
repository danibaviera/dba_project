# Endpoints para logs de acesso

from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.database.mongo_client import db
from app.database.models import (
    LogAcessoCreate, LogAcessoResponse
)

router = APIRouter(prefix="/logs", tags=["Logs de Acesso"])


@router.post("/", response_model=dict, status_code=201)
async def create_log(log: LogAcessoCreate):
    """
    Criar um novo log de acesso
    """
    try:
        # Se foi fornecido um id_cliente, verificar se existe
        if log.id_cliente:
            if not ObjectId.is_valid(log.id_cliente):
                raise HTTPException(status_code=400, detail="ID do cliente inválido")
            cliente_exists = await db.clientes.find_one({"_id": ObjectId(log.id_cliente)})
            if not cliente_exists:
                raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        log_dict = log.dict()
        if log.id_cliente:
            log_dict["id_cliente"] = ObjectId(log.id_cliente)
        log_dict["timestamp"] = datetime.utcnow()
        
        result = await db.logs_acesso.insert_one(log_dict)
        return {
            "id": str(result.inserted_id),
            "message": "Log criado com sucesso!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/", response_model=List[LogAcessoResponse])
async def list_logs(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(10, ge=1, le=100, description="Limite de registros por página"),
    id_cliente: Optional[str] = Query(None, description="Filtrar por cliente"),
    acao: Optional[str] = Query(None, pattern="^(login|logout|create|read|update|delete|error)$", description="Filtrar por ação"),
    status_code: Optional[int] = Query(None, ge=100, le=599, description="Filtrar por código de status"),
    ip: Optional[str] = Query(None, description="Filtrar por endereço IP"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim"),
    endpoint: Optional[str] = Query(None, description="Filtrar por endpoint")
):
    """
    Listar logs de acesso com paginação e filtros
    """
    try:
        # Construir filtros
        filters = {}
        
        if id_cliente:
            if not ObjectId.is_valid(id_cliente):
                raise HTTPException(status_code=400, detail="ID do cliente inválido")
            filters["id_cliente"] = ObjectId(id_cliente)
        
        if acao:
            filters["acao"] = acao
        
        if status_code:
            filters["status_code"] = status_code
        
        if ip:
            filters["ip"] = ip
        
        if endpoint:
            filters["endpoint"] = {"$regex": endpoint, "$options": "i"}
        
        # Filtros de data
        if data_inicio or data_fim:
            date_filter = {}
            if data_inicio:
                date_filter["$gte"] = data_inicio
            if data_fim:
                date_filter["$lt"] = data_fim + timedelta(days=1)
            filters["timestamp"] = date_filter
        
        cursor = db.logs_acesso.find(filters).sort("timestamp", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        # Converter ObjectIds para string
        for log in logs:
            log["_id"] = str(log["_id"])
            if log.get("id_cliente"):
                log["id_cliente"] = str(log["id_cliente"])
            
        return logs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar logs: {str(e)}")


@router.get("/{log_id}", response_model=LogAcessoResponse)
async def get_log(log_id: str):
    """
    Buscar log por ID
    """
    try:
        if not ObjectId.is_valid(log_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        log = await db.logs_acesso.find_one({"_id": ObjectId(log_id)})
        if not log:
            raise HTTPException(status_code=404, detail="Log não encontrado")
        
        log["_id"] = str(log["_id"])
        if log.get("id_cliente"):
            log["id_cliente"] = str(log["id_cliente"])
        return log
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar log: {str(e)}")


@router.get("/cliente/{cliente_id}/logs", response_model=List[LogAcessoResponse])
async def get_logs_cliente(
    cliente_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Buscar todos os logs de um cliente específico
    """
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="ID do cliente inválido")
        
        # Verificar se cliente existe
        cliente_exists = await db.clientes.find_one({"_id": ObjectId(cliente_id)})
        if not cliente_exists:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        cursor = db.logs_acesso.find({"id_cliente": ObjectId(cliente_id)}).sort("timestamp", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        # Converter ObjectIds para string
        for log in logs:
            log["_id"] = str(log["_id"])
            log["id_cliente"] = str(log["id_cliente"])
            
        return logs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar logs do cliente: {str(e)}")


@router.get("/stats/resumo", response_model=dict)
async def get_logs_stats():
    """
    Obter estatísticas dos logs de acesso
    """
    try:
        # Contagem total
        total = await db.logs_acesso.count_documents({})
        
        # Contagem por ação
        pipeline_acoes = [
            {
                "$group": {
                    "_id": "$acao",
                    "quantidade": {"$sum": 1}
                }
            }
        ]
        
        acoes_result = await db.logs_acesso.aggregate(pipeline_acoes).to_list(length=None)
        acoes_stats = {item["_id"]: item["quantidade"] for item in acoes_result}
        
        # Contagem por status code
        pipeline_status = [
            {
                "$group": {
                    "_id": "$status_code",
                    "quantidade": {"$sum": 1}
                }
            }
        ]
        
        status_result = await db.logs_acesso.aggregate(pipeline_status).to_list(length=None)
        status_stats = {item["_id"]: item["quantidade"] for item in status_result if item["_id"]}
        
        # Top IPs
        pipeline_ips = [
            {
                "$group": {
                    "_id": "$ip",
                    "quantidade": {"$sum": 1}
                }
            },
            {"$sort": {"quantidade": -1}},
            {"$limit": 10}
        ]
        
        ips_result = await db.logs_acesso.aggregate(pipeline_ips).to_list(length=None)
        top_ips = [{"ip": item["_id"], "acessos": item["quantidade"]} for item in ips_result]
        
        # Logs das últimas 24 horas
        yesterday = datetime.utcnow() - timedelta(hours=24)
        logs_24h = await db.logs_acesso.count_documents({"timestamp": {"$gte": yesterday}})
        
        return {
            "total": total,
            "logs_24h": logs_24h,
            "por_acao": acoes_stats,
            "por_status_code": status_stats,
            "top_ips": top_ips
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/stats/atividade", response_model=dict)
async def get_atividade_logs(
    horas: int = Query(24, ge=1, le=168, description="Número de horas para análise (máximo 168 = 1 semana)")
):
    """
    Obter atividade dos logs por período
    """
    try:
        data_inicio = datetime.utcnow() - timedelta(hours=horas)
        
        # Atividade por hora
        pipeline_horas = [
            {
                "$match": {
                    "timestamp": {"$gte": data_inicio}
                }
            },
            {
                "$group": {
                    "_id": {
                        "ano": {"$year": "$timestamp"},
                        "mes": {"$month": "$timestamp"},
                        "dia": {"$dayOfMonth": "$timestamp"},
                        "hora": {"$hour": "$timestamp"}
                    },
                    "quantidade": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        atividade_result = await db.logs_acesso.aggregate(pipeline_horas).to_list(length=None)
        atividade_por_hora = []
        
        for item in atividade_result:
            timestamp_hora = datetime(
                item["_id"]["ano"],
                item["_id"]["mes"],
                item["_id"]["dia"],
                item["_id"]["hora"]
            )
            atividade_por_hora.append({
                "timestamp": timestamp_hora.isoformat(),
                "quantidade": item["quantidade"]
            })
        
        return {
            "periodo_horas": horas,
            "data_inicio": data_inicio.isoformat(),
            "atividade_por_hora": atividade_por_hora
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter atividade: {str(e)}")


@router.delete("/cleanup", response_model=dict)
async def cleanup_old_logs(
    dias: int = Query(30, ge=1, le=365, description="Remover logs mais antigos que X dias")
):
    """
    Remover logs antigos (limpeza de dados)
    """
    try:
        data_corte = datetime.utcnow() - timedelta(days=dias)
        
        result = await db.logs_acesso.delete_many({"timestamp": {"$lt": data_corte}})
        
        return {
            "message": f"Limpeza realizada com sucesso!",
            "logs_removidos": result.deleted_count,
            "data_corte": data_corte.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao realizar limpeza: {str(e)}")


# Middleware para log automático
async def log_request_middleware(request: Request, call_next):
    """
    Middleware para criar logs automáticos das requisições
    """
    start_time = datetime.utcnow()
    
    # Obter IP do cliente
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    try:
        response = await call_next(request)
        
        # Criar log de sucesso
        log_data = {
            "acao": "read" if request.method == "GET" else request.method.lower(),
            "ip": client_ip,
            "user_agent": user_agent,
            "endpoint": str(request.url.path),
            "status_code": response.status_code,
            "detalhes": {
                "method": request.method,
                "query_params": dict(request.query_params),
                "response_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
        }
        
        # Inserir log (fire and forget)
        try:
            await db.logs_acesso.insert_one(log_data)
        except:
            pass  # Não falhar por causa do log
        
        return response
        
    except Exception as e:
        # Criar log de erro
        log_data = {
            "acao": "error",
            "ip": client_ip,
            "user_agent": user_agent,
            "endpoint": str(request.url.path),
            "status_code": 500,
            "detalhes": {
                "method": request.method,
                "error": str(e),
                "response_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
        }
        
        # Inserir log (fire and forget)
        try:
            await db.logs_acesso.insert_one(log_data)
        except:
            pass  # Não falhar por causa do log
        
        raise
