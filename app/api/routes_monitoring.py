# Endpoints de observabilidade

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import psutil
import asyncio
from app.database.mongo_client import db, client

router = APIRouter(prefix="/monitoring", tags=["Monitoramento"])


@router.get("/health", response_model=dict)
async def health_check():
    """
    Verificação de saúde do sistema
    """
    try:
        # Testar conexão com MongoDB
        start_time = datetime.utcnow()
        await db.admin.command('ping')
        db_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "connected",
                "response_time_ms": round(db_response_time, 2)
            },
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "status": "disconnected",
                "error": str(e)
            },
            "version": "1.0.0"
        }


@router.get("/system/metrics", response_model=dict)
async def get_system_metrics():
    """
    Obter métricas do sistema
    """
    try:
        # Métricas de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Métricas de memória
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Métricas de disco
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Métricas de rede
        network_io = psutil.net_io_counters()
        
        # Informações do processo Python
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency_mhz": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent": swap.percent
            },
            "disk": {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "percent": round((disk_usage.used / disk_usage.total) * 100, 2)
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")


@router.get("/database/stats", response_model=dict)
async def get_database_stats():
    """
    Obter estatísticas do banco de dados MongoDB
    """
    try:
        # Stats do banco de dados
        db_stats = await db.command("dbStats")
        
        # Stats das coleções
        collections_stats = {}
        collection_names = ["clientes", "transacoes", "logs_acesso"]
        
        for collection_name in collection_names:
            try:
                collection = db[collection_name]
                
                # Contagem de documentos
                doc_count = await collection.count_documents({})
                
                # Stats da coleção
                if doc_count > 0:
                    coll_stats = await db.command("collStats", collection_name)
                    collections_stats[collection_name] = {
                        "documents": doc_count,
                        "size_mb": round(coll_stats.get("size", 0) / (1024**2), 2),
                        "storage_size_mb": round(coll_stats.get("storageSize", 0) / (1024**2), 2),
                        "indexes": coll_stats.get("nindexes", 0),
                        "avg_obj_size": coll_stats.get("avgObjSize", 0)
                    }
                else:
                    collections_stats[collection_name] = {
                        "documents": 0,
                        "size_mb": 0,
                        "storage_size_mb": 0,
                        "indexes": 0,
                        "avg_obj_size": 0
                    }
            except Exception as coll_error:
                collections_stats[collection_name] = {
                    "error": str(coll_error)
                }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "name": db_stats.get("db"),
                "collections": db_stats.get("collections", 0),
                "objects": db_stats.get("objects", 0),
                "data_size_mb": round(db_stats.get("dataSize", 0) / (1024**2), 2),
                "storage_size_mb": round(db_stats.get("storageSize", 0) / (1024**2), 2),
                "indexes": db_stats.get("indexes", 0),
                "index_size_mb": round(db_stats.get("indexSize", 0) / (1024**2), 2)
            },
            "collections": collections_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter stats do banco: {str(e)}")


@router.get("/performance/summary", response_model=dict)
async def get_performance_summary():
    """
    Resumo de performance do sistema
    """
    try:
        # Métricas básicas do sistema
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Teste de latência do banco de dados
        start_time = datetime.utcnow()
        await db.admin.command('ping')
        db_latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Contagem rápida de documentos
        clientes_count = await db.clientes.count_documents({})
        transacoes_count = await db.transacoes.count_documents({})
        logs_count = await db.logs_acesso.count_documents({})
        
        # Análise das últimas 24h
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        transacoes_24h = await db.transacoes.count_documents({
            "data": {"$gte": yesterday}
        })
        
        logs_24h = await db.logs_acesso.count_documents({
            "timestamp": {"$gte": yesterday}
        })
        
        # Status geral
        status = "healthy"
        issues = []
        
        if cpu_percent > 80:
            status = "warning"
            issues.append("CPU usage high")
        
        if memory.percent > 85:
            status = "warning"
            issues.append("Memory usage high")
        
        if db_latency > 1000:  # > 1 segundo
            status = "warning"
            issues.append("Database latency high")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "issues": issues,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "database_latency_ms": round(db_latency, 2)
            },
            "database": {
                "total_documents": clientes_count + transacoes_count + logs_count,
                "clientes": clientes_count,
                "transacoes": transacoes_count,
                "logs": logs_count
            },
            "activity_24h": {
                "new_transactions": transacoes_24h,
                "log_entries": logs_24h
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo: {str(e)}")


@router.get("/alerts/check", response_model=dict)
async def check_alerts():
    """
    Verificar condições de alerta
    """
    try:
        alerts = []
        
        # Verificar recursos do sistema
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        if cpu_percent > 90:
            alerts.append({
                "level": "critical",
                "type": "system",
                "message": f"CPU usage very high: {cpu_percent:.1f}%"
            })
        elif cpu_percent > 80:
            alerts.append({
                "level": "warning",
                "type": "system",
                "message": f"CPU usage high: {cpu_percent:.1f}%"
            })
        
        if memory.percent > 90:
            alerts.append({
                "level": "critical",
                "type": "system",
                "message": f"Memory usage very high: {memory.percent:.1f}%"
            })
        elif memory.percent > 85:
            alerts.append({
                "level": "warning",
                "type": "system",
                "message": f"Memory usage high: {memory.percent:.1f}%"
            })
        
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > 90:
            alerts.append({
                "level": "critical",
                "type": "storage",
                "message": f"Disk usage very high: {disk_percent:.1f}%"
            })
        elif disk_percent > 80:
            alerts.append({
                "level": "warning",
                "type": "storage",
                "message": f"Disk usage high: {disk_percent:.1f}%"
            })
        
        # Verificar transações com erro
        failed_transactions = await db.transacoes.count_documents({
            "status": {"$in": ["rejeitada", "cancelada"]},
            "data": {"$gte": datetime.utcnow() - timedelta(hours=1)}
        })
        
        if failed_transactions > 10:
            alerts.append({
                "level": "warning",
                "type": "business",
                "message": f"High number of failed transactions in last hour: {failed_transactions}"
            })
        
        # Verificar logs de erro
        error_logs = await db.logs_acesso.count_documents({
            "acao": "error",
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
        })
        
        if error_logs > 5:
            alerts.append({
                "level": "warning",
                "type": "application",
                "message": f"High number of error logs in last hour: {error_logs}"
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_count": len(alerts),
            "status": "critical" if any(a["level"] == "critical" for a in alerts) else "warning" if alerts else "ok",
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar alertas: {str(e)}")


@router.post("/maintenance/optimize", response_model=dict)
async def optimize_database():
    """
    Executar otimizações de manutenção do banco
    """
    try:
        results = []
        
        # Reindexar coleções principais
        collections = ["clientes", "transacoes", "logs_acesso"]
        
        for collection_name in collections:
            try:
                await db[collection_name].reindex()
                results.append({
                    "collection": collection_name,
                    "operation": "reindex",
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "collection": collection_name,
                    "operation": "reindex",
                    "status": "error",
                    "error": str(e)
                })
        
        # Compact se suportado (pode não estar disponível em todas as versões)
        try:
            await db.command("compact", "logs_acesso")
            results.append({
                "operation": "compact_logs",
                "status": "success"
            })
        except Exception as e:
            results.append({
                "operation": "compact_logs",
                "status": "skipped",
                "reason": "Not supported or failed"
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Database optimization completed",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na otimização: {str(e)}")


@router.get("/uptime", response_model=dict)
async def get_uptime():
    """
    Obter tempo de atividade do sistema
    """
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.utcnow() - boot_time
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "boot_time": boot_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_formatted": str(uptime).split('.')[0],  # Remove microseconds
            "system_load": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter uptime: {str(e)}")