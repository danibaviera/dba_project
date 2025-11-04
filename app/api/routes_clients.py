# Endpoints para clientes

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from app.database.mongo_client import db
from app.database.models import (
    ClienteCreate, ClienteUpdate, ClienteResponse
)

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=dict, status_code=201)
async def create_cliente(cliente: ClienteCreate):
    """
    Criar um novo cliente
    """
    try:
        # Verificar se CPF já existe
        existing_client = await db.clientes.find_one({"cpf": cliente.cpf})
        if existing_client:
            raise HTTPException(status_code=400, detail="Cliente com este CPF já existe")
        
        # Verificar se email já existe
        existing_email = await db.clientes.find_one({"email": cliente.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Cliente com este email já existe")
        
        cliente_dict = cliente.dict()
        cliente_dict["data_criacao"] = datetime.utcnow()
        
        result = await db.clientes.insert_one(cliente_dict)
        return {
            "id": str(result.inserted_id), 
            "message": "Cliente criado com sucesso!"
        }
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Cliente já existe")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/", response_model=List[ClienteResponse])
async def list_clientes(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(10, ge=1, le=100, description="Limite de registros por página"),
    status: Optional[str] = Query(None, pattern="^(ativo|inativo|suspenso)$", description="Filtrar por status"),
    nome: Optional[str] = Query(None, description="Buscar por nome (parcial)")
):
    """
    Listar clientes com paginação e filtros
    """
    try:
        # Construir filtros
        filters = {}
        if status:
            filters["status"] = status
        if nome:
            filters["nome"] = {"$regex": nome, "$options": "i"}
        
        cursor = db.clientes.find(filters).skip(skip).limit(limit)
        clientes = await cursor.to_list(length=limit)
        
        # Converter ObjectId para string
        for cliente in clientes:
            cliente["_id"] = str(cliente["_id"])
            
        return clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar clientes: {str(e)}")


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(cliente_id: str):
    """
    Buscar cliente por ID
    """
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        cliente = await db.clientes.find_one({"_id": ObjectId(cliente_id)})
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        cliente["_id"] = str(cliente["_id"])
        return cliente
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar cliente: {str(e)}")


@router.put("/{cliente_id}", response_model=dict)
async def update_cliente(cliente_id: str, cliente_update: ClienteUpdate):
    """
    Atualizar cliente por ID
    """
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        # Verificar se cliente existe
        existing_cliente = await db.clientes.find_one({"_id": ObjectId(cliente_id)})
        if not existing_cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Preparar dados para atualização (apenas campos não nulos)
        update_data = {k: v for k, v in cliente_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
        
        # Verificar se email já existe (se está sendo atualizado)
        if "email" in update_data:
            existing_email = await db.clientes.find_one({
                "email": update_data["email"],
                "_id": {"$ne": ObjectId(cliente_id)}
            })
            if existing_email:
                raise HTTPException(status_code=400, detail="Email já está em uso por outro cliente")
        
        result = await db.clientes.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Nenhuma modificação realizada")
        
        return {"message": "Cliente atualizado com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cliente: {str(e)}")


@router.delete("/{cliente_id}", response_model=dict)
async def delete_cliente(cliente_id: str):
    """
    Excluir cliente por ID (soft delete - marca como inativo)
    """
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="ID inválido")
        
        # Verificar se cliente existe
        existing_cliente = await db.clientes.find_one({"_id": ObjectId(cliente_id)})
        if not existing_cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Soft delete - marcar como inativo
        result = await db.clientes.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": {"status": "inativo"}}
        )
        
        return {"message": "Cliente desativado com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao desativar cliente: {str(e)}")


@router.get("/cpf/{cpf}", response_model=ClienteResponse)
async def get_cliente_by_cpf(cpf: str):
    """
    Buscar cliente por CPF
    """
    try:
        if not cpf.isdigit() or len(cpf) != 11:
            raise HTTPException(status_code=400, detail="CPF deve conter exatamente 11 dígitos")
        
        cliente = await db.clientes.find_one({"cpf": cpf})
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        cliente["_id"] = str(cliente["_id"])
        return cliente
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar cliente: {str(e)}")


@router.get("/stats/count", response_model=dict)
async def get_clientes_stats():
    """
    Obter estatísticas dos clientes
    """
    try:
        total = await db.clientes.count_documents({})
        ativos = await db.clientes.count_documents({"status": "ativo"})
        inativos = await db.clientes.count_documents({"status": "inativo"})
        suspensos = await db.clientes.count_documents({"status": "suspenso"})
        
        return {
            "total": total,
            "ativos": ativos,
            "inativos": inativos,
            "suspensos": suspensos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")
