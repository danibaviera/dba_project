""""""

MonitorDB API - Sistema Completo de Gestão com ObservabilidadeMonitorDB API - Sistema Completo de Gestão com Observabilidade

Aplicação FastAPI com monitoramento, segurança JWT e métricas PrometheusAplicação FastAPI com monitoramento, segurança JWT e métricas Prometheus

""""""



import asyncioimport logging
import loggingimport os
import timeimport time

from contextlib import asynccontextmanagerfrom contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Dependsfrom fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddlewarefrom fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponsefrom fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPBearerfrom datetime import datetime
from datetime import datetime
from typing import Optional

# Imports do sistema
from app.database.mongo_client import init_database, close_database

# Imports do sistema from app.api import routes_clients, routes_transactions, routes_logs, routes_auth

from app.database.mongo_client import init_database, close_database, get_databasefrom app.config import settings
from app.api import routes_clients, routes_transactions, routes_logs, routes_auth
from app.config import settings

# Imports de monitoramento

from app.monitoring.metrics_exporter import prometheus_metrics, start_metrics_server

# Imports de monitoramentofrom app.monitoring.performance_monitor import performance_monitor

from app.monitoring.metrics_exporter import prometheus_metrics, start_metrics_server
from app.monitoring.performance_monitor import performance_monitor

# Configurar logging

logging.basicConfig(

# Imports de segurança    level=logging.INFO,

from app.security.auth import get_current_user, require_permission    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

)

# Configurar logginglogger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)@asynccontextmanager

async def lifespan(app: FastAPI):

# Security scheme    """Gerencia o ciclo de vida da aplicação"""

security = HTTPBearer()    logger.info("🚀 Iniciando MonitorDB API...")

    

# Lifecycle events    # Startup

@asynccontextmanager    try:

async def lifespan(app: FastAPI):        # Inicializar conexão com MongoDB

    """Gerenciar ciclo de vida da aplicação"""        await init_database()

    logger.info("🚀 Iniciando MonitorDB API...")        logger.info("✅ Conexão com MongoDB estabelecida")

            

    # Startup        # Inicializar servidor de métricas Prometheus

    try:        prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8001"))

        await init_database()        start_metrics_server(prometheus_port)

        logger.info("✅ Database conectado")        logger.info(f"✅ Servidor de métricas Prometheus iniciado na porta {prometheus_port}")

                

        # Iniciar servidor de métricas Prometheus        # Inicializar motor de regras de alertas

        metrics_port = int(settings.monitoring.get('prometheus_port', 8001))        await alert_rules_engine.start()

        start_metrics_server(metrics_port)        logger.info("✅ Motor de regras de alertas inicializado")

        logger.info(f"✅ Servidor Prometheus rodando na porta {metrics_port}")        

                # Inicializar verificação automática de alertas (legacy)

        # Iniciar monitoramento de performance        asyncio.create_task(alert_check_loop())

        performance_monitor.start_monitoring()        logger.info("✅ Sistema de alertas legacy inicializado")

        logger.info("✅ Monitoramento de performance iniciado")        

            except Exception as e:

        logger.info("🎉 MonitorDB API iniciada com sucesso!")        logger.error(f"❌ Erro na inicialização: {e}")

                raise

    except Exception as e:    

        logger.error(f"❌ Erro durante inicialização: {e}")    yield

        raise    

        # Shutdown

    yield    logger.info("🛑 Finalizando MonitorDB API...")

        

    # Shutdown    # Para o motor de alertas

    logger.info("🔄 Finalizando MonitorDB API...")    await alert_rules_engine.stop()

    try:    logger.info("✅ Motor de alertas finalizado")

        performance_monitor.stop_monitoring()    

        await close_database()    # Para métricas

        logger.info("✅ Recursos liberados com sucesso")    prometheus_metrics.stop_auto_update()

    except Exception as e:    

        logger.error(f"❌ Erro durante finalização: {e}")    # Fechar conexão com MongoDB

        await close_database()

    logger.info("👋 MonitorDB API finalizada")    logger.info("✅ Shutdown concluído")



# Criar aplicação FastAPI# Configuração do FastAPI

app = FastAPI(app = FastAPI(

    title="MonitorDB API",    title="MonitorDB API",

    description="Sistema Completo de Gestão de Clientes e Transações com Observabilidade",    description="""

    version="2.0.0",    🚀 **Sistema de Monitoramento e Gestão de Clientes**

    docs_url="/docs",    

    redoc_url="/redoc",    Sistema completo com:

    lifespan=lifespan    - CRUD de clientes e transações

)    - Sistema de logs e auditoria  

    - Monitoramento em tempo real

# Middleware CORS    - Observabilidade com Prometheus + Grafana

app.add_middleware(    - Alertas automatizados

    CORSMiddleware,    

    allow_origins=settings.cors_origins,    ## 📊 Monitoramento

    allow_credentials=True,    

    allow_methods=["*"],    - **Métricas Prometheus**: [http://localhost:8001/metrics](http://localhost:8001/metrics)

    allow_headers=["*"],    - **Grafana Dashboard**: [http://localhost:3000](http://localhost:3000) (admin/admin123)

)    - **Prometheus UI**: [http://localhost:9090](http://localhost:9090)

    - **AlertManager**: [http://localhost:9093](http://localhost:9093)

# Middleware de métricas    

@app.middleware("http")    ## 🔍 Observabilidade

async def metrics_middleware(request: Request, call_next):    

    """Middleware para coletar métricas HTTP"""    - Métricas de sistema (CPU, memória, disco)

    start_time = time.time()    - Métricas de aplicação (latência, throughput, erros)

        - Métricas de banco de dados (MongoDB)

    # Processar request    - Métricas de negócio (transações, clientes)

    response = await call_next(request)    """,

        version="1.0.0",

    # Registrar métricas    docs_url="/docs",

    process_time = time.time() - start_time    redoc_url="/redoc",

    prometheus_metrics.http_requests_total.labels(    lifespan=lifespan

        method=request.method,)

        endpoint=request.url.path,

        status_code=response.status_code# Configuração CORS

    ).inc()app.add_middleware(

        CORSMiddleware,

    prometheus_metrics.http_request_duration_seconds.labels(    allow_origins=["*"],  # Em produção, especificar domínios específicos

        method=request.method,    allow_credentials=True,

        endpoint=request.url.path    allow_methods=["*"],

    ).observe(process_time)    allow_headers=["*"],

    )

    return response

# Middleware para métricas Prometheus

# Middleware de loggingapp.add_middleware(

@app.middleware("http")    PrometheusMiddleware,

async def logging_middleware(request: Request, call_next):    exclude_paths=["/metrics", "/favicon.ico"]

    """Middleware para logging de requests""")

    start_time = time.time()

    # Registrar routers

    # Processar requestapp.include_router(routes_auth.router, prefix="/api/v1", tags=["Autenticação"])

    response = await call_next(request)app.include_router(routes_clients.router, prefix="/api/v1", tags=["Clientes"])

    app.include_router(routes_transactions.router, prefix="/api/v1", tags=["Transações"])

    # Log da requisiçãoapp.include_router(routes_logs.router, prefix="/api/v1", tags=["Logs"])

    process_time = time.time() - start_timeapp.include_router(routes_monitoring.router, prefix="/api/v1", tags=["Monitoramento"])

    logger.info(app.include_router(routes_integrations.router, prefix="/api/v1", tags=["Integrações"])

        f"{request.method} {request.url.path} - "app.include_router(routes_alerts.router, tags=["Alertas e Observabilidade"])

        f"Status: {response.status_code} - "

        f"Tempo: {process_time:.3f}s"# Loop de verificação de alertas em background

    )async def alert_check_loop():

        """Loop em background para verificar alertas periodicamente"""

    return response    while True:

        try:

# Incluir routers            await alert_manager.check_all_rules()

app.include_router(routes_auth.router, prefix="/api/v1", tags=["Autenticação"])            await asyncio.sleep(60)  # Verificar a cada minuto

app.include_router(routes_clients.router, prefix="/api/v1", tags=["Clientes"])        except Exception as e:

app.include_router(routes_transactions.router, prefix="/api/v1", tags=["Transações"])            logger.error(f"Erro no loop de alertas: {e}")

app.include_router(routes_logs.router, prefix="/api/v1", tags=["Logs"])            await asyncio.sleep(30)  # Aguardar menos tempo em caso de erro



# Routes de sistema# Middleware para logs de acesso detalhados

@app.get("/", tags=["Sistema"])@app.middleware("http")

async def root():async def access_logging_middleware(request: Request, call_next):

    """Endpoint raiz da API"""    """Middleware para log detalhado de acessos"""

    return {    start_time = time.time()

        "message": "MonitorDB API v2.0.0",    

        "status": "online",    # Capturar informações da requisição

        "timestamp": datetime.utcnow().isoformat(),    client_ip = request.client.host if request.client else "unknown"

        "docs": "/docs",    user_agent = request.headers.get("user-agent", "unknown")

        "metrics": f"http://localhost:{settings.monitoring.get('prometheus_port', 8001)}/metrics"    method = request.method

    }    url = str(request.url)

    

@app.get("/health", tags=["Sistema"])    # Processar requisição

async def health_check():    try:

    """Verificação de saúde da aplicação"""        response = await call_next(request)

    try:        status_code = response.status_code

        # Verificar conexão com MongoDB        error_occurred = status_code >= 400

        db = await get_database()    except Exception as e:

        await db.command('ping')        logger.error(f"Erro durante processamento da requisição: {e}")

                status_code = 500

        # Coletar estatísticas básicas        error_occurred = True

        stats = {        raise

            "status": "healthy",    finally:

            "timestamp": datetime.utcnow().isoformat(),        # Calcular tempo de processamento

            "database": "connected",        process_time = time.time() - start_time

            "monitoring": "active",        

            "performance": performance_monitor.get_current_metrics()        # Registrar log de acesso no banco (se não for endpoint de health check)

        }        if not url.endswith("/health") and not url.endswith("/metrics"):

                    try:

        return stats                log_data = {

                            "timestamp": datetime.utcnow(),

    except Exception as e:                    "ip": client_ip,

        logger.error(f"Health check falhou: {e}")                    "user_agent": user_agent,

        raise HTTPException(status_code=503, detail="Service unavailable")                    "metodo": method,

                    "endpoint": request.url.path,

@app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoramento"])                    "status_code": status_code,

async def metrics_endpoint():                    "response_time_ms": round(process_time * 1000, 2),

    """Endpoint para métricas Prometheus (backup)"""                    "acao": f"{method} {request.url.path}",

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST                    "details": {

    return PlainTextResponse(                        "query_params": dict(request.query_params),

        generate_latest(),                        "full_url": url

        media_type=CONTENT_TYPE_LATEST                    }

    )                }

                

@app.get("/status", tags=["Sistema"])                # Inserir log de forma assíncrona (fire-and-forget)

async def system_status(current_user: dict = Depends(get_current_user)):                asyncio.create_task(insert_access_log(log_data))

    """Status detalhado do sistema (requer autenticação)"""                

    try:                # Registrar métricas no Prometheus via middleware

        db = await get_database()                # (o PrometheusMiddleware já faz isso)

                        

        # Estatísticas do banco            except Exception as e:

        clients_count = await db.clientes.count_documents({})                logger.warning(f"Erro ao registrar log de acesso: {e}")

        transactions_count = await db.transacoes.count_documents({})        

        logs_count = await db.logs_acesso.count_documents({})        # Log no console para debug

                logger.info(

        # Métricas de sistema            f"{client_ip} - {method} {request.url.path} - "

        system_metrics = performance_monitor.get_current_metrics()            f"{status_code} - {process_time*1000:.2f}ms"

                )

        return {    

            "status": "operational",    return response

            "timestamp": datetime.utcnow().isoformat(),

            "user": current_user.get("username"),async def insert_access_log(log_data: dict):

            "database": {    """Insere log de acesso no banco de dados de forma assíncrona"""

                "clients": clients_count,    try:

                "transactions": transactions_count,        await db.logs_acesso.insert_one(log_data)

                "access_logs": logs_count    except Exception as e:

            },        logger.error(f"Erro ao inserir log no banco: {e}")

            "system": system_metrics,

            "uptime": time.time() - performance_monitor.start_time if hasattr(performance_monitor, 'start_time') else 0# Handler global de exceções

        }@app.exception_handler(HTTPException)

        async def http_exception_handler(request: Request, exc: HTTPException):

    except Exception as e:    """Handler para exceções HTTP"""

        logger.error(f"Erro ao obter status: {e}")    return JSONResponse(

        raise HTTPException(status_code=500, detail="Erro interno do servidor")        status_code=exc.status_code,

        content={

# Handler de exceções            "error": exc.detail,

@app.exception_handler(404)            "status_code": exc.status_code,

async def not_found_handler(request: Request, exc: HTTPException):            "timestamp": datetime.utcnow().isoformat(),

    """Handler para 404"""            "path": request.url.path

    return JSONResponse(        }

        status_code=404,    )

        content={

            "error": "Endpoint não encontrado",@app.exception_handler(Exception)

            "message": f"O endpoint {request.url.path} não existe",async def global_exception_handler(request: Request, exc: Exception):

            "timestamp": datetime.utcnow().isoformat()    """Handler global para exceções não tratadas"""

        }    logger.error(f"Erro não tratado: {exc}", exc_info=True)

    )    

    # Registrar erro nas métricas

@app.exception_handler(500)    prometheus_metrics.record_log_entry("error", "unhandled_exception")

async def internal_server_error_handler(request: Request, exc: Exception):    

    """Handler para erros 500"""    return JSONResponse(

    logger.error(f"Erro interno: {exc}")        status_code=500,

    return JSONResponse(        content={

        status_code=500,            "error": "Internal Server Error",

        content={            "message": "Ocorreu um erro interno no servidor",

            "error": "Erro interno do servidor",            "timestamp": datetime.utcnow().isoformat(),

            "message": "Ocorreu um erro inesperado",            "path": request.url.path,

            "timestamp": datetime.utcnow().isoformat()            "request_id": f"{int(time.time())}-{hash(str(request.url))}"

        }        }

    )    )



# Inicialização# Endpoint raiz

if __name__ == "__main__":@app.get("/", tags=["Sistema"])

    import uvicornasync def root():

    uvicorn.run(    """

        "app.main:app",    Endpoint raiz - informações básicas do sistema

        host="0.0.0.0",    """

        port=8000,    try:

        reload=True,        # Contadores rápidos

        log_level="info"        clientes_count = await db.clientes.count_documents({})

    )        transacoes_count = await db.transacoes.count_documents({})
        logs_count = await db.logs_acesso.count_documents({})
        
        return {
            "status": "ok",
            "message": "MonitorDB API está funcionando!",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": {
                "clientes_registrados": clientes_count,
                "transacoes_registradas": transacoes_count,
                "logs_registrados": logs_count
            },
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/api/v1/monitoring/health",
                "clientes": "/api/v1/clientes",
                "transacoes": "/api/v1/transacoes",
                "logs": "/api/v1/logs",
                "monitoring": "/api/v1/monitoring"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao conectar com o banco de dados: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

# Endpoint de informações da API
@app.get("/info", tags=["Sistema"])
async def api_info():
    """
    Informações detalhadas da API
    """
    return {
        "name": "MonitorDB API",
        "version": "1.0.0",
        "description": "Sistema de observabilidade e gestão de dados de clientes",
        "features": [
            "CRUD completo de clientes",
            "Gestão de transações",
            "Sistema de logs de acesso",
            "Monitoramento e observabilidade",
            "Métricas de performance",
            "Alertas automáticos"
        ],
        "technologies": {
            "framework": "FastAPI",
            "database": "MongoDB",
            "language": "Python",
            "async_driver": "Motor"
        },
        "endpoints_count": len(app.routes)
    }
