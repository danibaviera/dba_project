# Endpoints para transações

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from app.database.mongo_client import db
from app.database.models import (
    TransacaoCreate, TransacaoUpdate, TransacaoResponse
)

router = APIRouter(prefix="/transacoes", tags=["Transações"])


@router.post("/", response_model=dict, status_code=201)
async def create_transacao(transacao: TransacaoCreate):
    """
    Criar uma nova transação
    """
    try:
        # Verificar se o cliente existe
        if not ObjectId.is_valid(transacao.id_cliente):
            raise HTTPException(status_code=400, detail="ID do cliente inválido")
        cliente_exists = await db.clientes.find_one({"_id": ObjectId(transacao.id_cliente)})
        if not cliente_exists:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Verificar se o cliente está ativo
        if cliente_exists.get("status") != "ativo":
            raise HTTPException(status_code=400, detail="Cliente não está ativo")
        
        transacao_dict = transacao.dict()
        transacao_dict["id_cliente"] = ObjectId(transacao.id_cliente)
        transacao_dict["data"] = datetime.utcnow()
        
        result = await db.transacoes.insert_one(transacao_dict)
        return {
            "id": str(result.inserted_id),
            "message": "Transação criada com sucesso!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/", response_model=List[TransacaoResponse])
async def list_transacoes(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(10, ge=1, le=100, description="Limite de registros por página"),
    id_cliente: Optional[str] = Query(None, description="Filtrar por cliente"),
    status: Optional[str] = Query(None, pattern="^(pendente|aprovada|rejeitada|cancelada)$", description="Filtrar por status"),
    tipo: Optional[str] = Query(None, pattern="^(credito|debito|pix|transferencia|boleto)$", description="Filtrar por tipo"),
    data_inicio: Optional[datetime] = Query(None, description="Data de início (formato: YYYY-MM-DD)"),
    data_fim: Optional[datetime] = Query(None, description="Data de fim (formato: YYYY-MM-DD)")
):
    """
    Listar transações com paginação e filtros
    """
    try:
        # Construir filtros
        filters = {}
        
        if id_cliente:
            if not ObjectId.is_valid(id_cliente):
                raise HTTPException(status_code=400, detail="ID do cliente inválido")
            filters["id_cliente"] = ObjectId(id_cliente)
        
        if status:
            filters["status"] = status
        
        if tipo:
            filters["tipo"] = tipo
        
        # Filtros de data
        if data_inicio or data_fim:
            date_filter = {}
            if data_inicio:
                date_filter["$gte"] = data_inicio
            if data_fim:
                # Adicionar 1 dia para incluir todo o dia final
                date_filter["$lt"] = data_fim + timedelta(days=1)
            filters["data"] = date_filter
        
        cursor = db.transacoes.find(filters).sort("data", -1).skip(skip).limit(limit)
        transacoes = await cursor.to_list(length=limit)
        
        # Converter ObjectIds para string
        for transacao in transacoes:
            transacao["_id"] = str(transacao["_id"])
            transacao["id_cliente"] = str(transacao["id_cliente"])
            
        return transacoes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transações: {str(e)}")


@router.get("/{transacao_id}", response_model=TransacaoResponse)
async def get_transacao(transacao_id: str):
    """
    Buscar transação por ID
    """
    try:
        if not ObjectId.is_valid(transacao_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        transacao = await db.transacoes.find_one({"_id": ObjectId(transacao_id)})
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        transacao["_id"] = str(transacao["_id"])
        transacao["id_cliente"] = str(transacao["id_cliente"])
        return transacao
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transação: {str(e)}")


@router.put("/{transacao_id}", response_model=dict)
async def update_transacao(transacao_id: str, transacao_update: TransacaoUpdate):
    """
    Atualizar transação por ID
    """
    try:
        if not ObjectId.is_valid(transacao_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        # Verificar se transação existe
        existing_transacao = await db.transacoes.find_one({"_id": ObjectId(transacao_id)})
        if not existing_transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        # Preparar dados para atualização
        update_data = {k: v for k, v in transacao_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
        
        result = await db.transacoes.update_one(
            {"_id": ObjectId(transacao_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Nenhuma modificação realizada")
        
        return {"message": "Transação atualizada com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar transação: {str(e)}")


@router.delete("/{transacao_id}", response_model=dict)
async def cancel_transacao(transacao_id: str):
    """
    Cancelar transação por ID
    """
    try:
        if not ObjectId.is_valid(transacao_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        # Verificar se transação existe
        existing_transacao = await db.transacoes.find_one({"_id": ObjectId(transacao_id)})
        if not existing_transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        # Verificar se pode ser cancelada
        if existing_transacao.get("status") in ["aprovada", "cancelada"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Transação já foi {existing_transacao.get('status')} e não pode ser cancelada"
            )
        
        # Cancelar transação
        result = await db.transacoes.update_one(
            {"_id": ObjectId(transacao_id)},
            {"$set": {"status": "cancelada"}}
        )
        
        return {"message": "Transação cancelada com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar transação: {str(e)}")


@router.get("/cliente/{cliente_id}/transacoes", response_model=List[TransacaoResponse])
async def get_transacoes_cliente(
    cliente_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Buscar todas as transações de um cliente específico
    """
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="ID do cliente inválido")
        
        # Verificar se cliente existe
        cliente_exists = await db.clientes.find_one({"_id": ObjectId(cliente_id)})
        if not cliente_exists:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        cursor = db.transacoes.find({"id_cliente": ObjectId(cliente_id)}).sort("data", -1).skip(skip).limit(limit)
        transacoes = await cursor.to_list(length=limit)
        
        # Converter ObjectIds para string
        for transacao in transacoes:
            transacao["_id"] = str(transacao["_id"])
            transacao["id_cliente"] = str(transacao["id_cliente"])
            
        return transacoes
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar transações do cliente: {str(e)}")


@router.get("/stats/resumo", response_model=dict)
async def get_transacoes_stats():
    """
    Obter estatísticas das transações
    """
    try:
        # Contagem por status
        total = await db.transacoes.count_documents({})
        pendentes = await db.transacoes.count_documents({"status": "pendente"})
        aprovadas = await db.transacoes.count_documents({"status": "aprovada"})
        rejeitadas = await db.transacoes.count_documents({"status": "rejeitada"})
        canceladas = await db.transacoes.count_documents({"status": "cancelada"})
        
        # Valores totais por status
        pipeline_valores = [
            {
                "$group": {
                    "_id": "$status",
                    "valor_total": {"$sum": "$valor"},
                    "quantidade": {"$sum": 1}
                }
            }
        ]
        
        valores_result = await db.transacoes.aggregate(pipeline_valores).to_list(length=None)
        valores_por_status = {item["_id"]: item["valor_total"] for item in valores_result}
        
        return {
            "contagem": {
                "total": total,
                "pendentes": pendentes,
                "aprovadas": aprovadas,
                "rejeitadas": rejeitadas,
                "canceladas": canceladas
            },
            "valores_totais": valores_por_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.post("/{transacao_id}/aprovar", response_model=dict)
async def aprovar_transacao(transacao_id: str):
    """
    Aprovar uma transação pendente
    """
    try:
        if not ObjectId.is_valid(transacao_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        # Verificar se transação existe e está pendente
        transacao = await db.transacoes.find_one({"_id": ObjectId(transacao_id)})
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        if transacao.get("status") != "pendente":
            raise HTTPException(
                status_code=400, 
                detail=f"Transação deve estar pendente para ser aprovada. Status atual: {transacao.get('status')}"
            )
        
        # Aprovar transação
        await db.transacoes.update_one(
            {"_id": ObjectId(transacao_id)},
            {"$set": {"status": "aprovada"}}
        )
        
        return {"message": "Transação aprovada com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao aprovar transação: {str(e)}")


@router.post("/{transacao_id}/rejeitar", response_model=dict)
async def rejeitar_transacao(transacao_id: str):
    """
    Rejeitar uma transação pendente
    """
    try:
        if not ObjectId.is_valid(transacao_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        # Verificar se transação existe e está pendente
        transacao = await db.transacoes.find_one({"_id": ObjectId(transacao_id)})
        if not transacao:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        if transacao.get("status") != "pendente":
            raise HTTPException(
                status_code=400, 
                detail=f"Transação deve estar pendente para ser rejeitada. Status atual: {transacao.get('status')}"
            )
        
        # Rejeitar transação
        await db.transacoes.update_one(
            {"_id": ObjectId(transacao_id)},
            {"$set": {"status": "rejeitada"}}
        )
        
        return {"message": "Transação rejeitada com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao rejeitar transação: {str(e)}")
