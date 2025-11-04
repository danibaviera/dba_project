# Endpoints para clientes

from fastapi import APIRouter, HTTPException
from app.database.mongo_client import db
from app.database.models import Cliente

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.post("/", summary="Cria um novo cliente")
async def create_cliente(cliente: Cliente):
    existing = await db.clientes.find_one({"email": cliente.email})
    if existing:
        raise HTTPException(status_code=400, detail="Cliente já existe com este e-mail")
    result = await db.clientes.insert_one(cliente.dict())
    return {"id": str(result.inserted_id), "message": "Cliente criado com sucesso"}

@router.get("/", summary="Lista todos os clientes")
async def list_clientes():
    clientes = await db.clientes.find().to_list(100)
    return clientes
