# Modelos Pydantic e schemas de dados
# Define os modelos Pydantic para validação de dados na aplicação Python

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional, Any, Dict, List
from bson import ObjectId
import re


class PyObjectId(ObjectId):
    """Classe personalizada para ObjectId do MongoDB"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema


class Cliente(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    cpf: str = Field(..., pattern="^[0-9]{11}$")
    endereco: Optional[str] = Field(None, max_length=200)
    telefone: Optional[str] = Field(None, pattern="^[0-9]{10,11}$")
    data_nascimento: Optional[datetime] = None
    status: str = Field(default="ativo", pattern="^(ativo|inativo|suspenso)$")
    data_criacao: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v):
        """Validação completa do CPF com dígito verificador"""
        if not re.match(r'^\d{11}$', v):
            raise ValueError('CPF deve conter 11 dígitos')
        
        # Algoritmo de validação do CPF
        def calculate_digit(cpf_digits, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Verificar sequências inválidas
        if v in ['00000000000', '11111111111', '22222222222', '33333333333',
                 '44444444444', '55555555555', '66666666666', '77777777777',
                 '88888888888', '99999999999']:
            raise ValueError('CPF inválido')
        
        # Calcular dígitos verificadores
        first_digit = calculate_digit(v[:9], range(10, 1, -1))
        second_digit = calculate_digit(v[:9] + first_digit, range(11, 1, -1))
        
        if v[9:] != first_digit + second_digit:
            raise ValueError('CPF inválido')
        
        return v

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class ClienteCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    cpf: str = Field(..., pattern="^[0-9]{11}$")
    endereco: Optional[str] = Field(None, max_length=200)
    telefone: Optional[str] = Field(None, pattern="^[0-9]{10,11}$")
    data_nascimento: Optional[datetime] = None
    status: str = Field(default="ativo", pattern="^(ativo|inativo|suspenso)$")
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v):
        """Validação completa do CPF com dígito verificador"""
        if not re.match(r'^\d{11}$', v):
            raise ValueError('CPF deve conter 11 dígitos')
        
        # Algoritmo de validação do CPF
        def calculate_digit(cpf_digits, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Verificar sequências inválidas
        if v in ['00000000000', '11111111111', '22222222222', '33333333333',
                 '44444444444', '55555555555', '66666666666', '77777777777',
                 '88888888888', '99999999999']:
            raise ValueError('CPF inválido')
        
        # Calcular dígitos verificadores
        first_digit = calculate_digit(v[:9], range(10, 1, -1))
        second_digit = calculate_digit(v[:9] + first_digit, range(11, 1, -1))
        
        if v[9:] != first_digit + second_digit:
            raise ValueError('CPF inválido')
        
        return v


class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    endereco: Optional[str] = Field(None, max_length=200)
    telefone: Optional[str] = Field(None, pattern="^[0-9]{10,11}$")
    data_nascimento: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(ativo|inativo|suspenso)$")


class Transacao(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    id_cliente: PyObjectId
    valor: float = Field(..., gt=0)
    tipo: str = Field(..., pattern="^(credito|debito|pix|transferencia|boleto)$")
    status: str = Field(..., pattern="^(pendente|aprovada|rejeitada|cancelada)$")
    data: datetime = Field(default_factory=datetime.utcnow)
    descricao: Optional[str] = Field(None, max_length=200)
    metadados: Optional[Dict[str, Any]] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class TransacaoCreate(BaseModel):
    id_cliente: str  # String representation of ObjectId
    valor: float = Field(..., gt=0)
    tipo: str = Field(..., pattern="^(credito|debito|pix|transferencia|boleto)$")
    descricao: Optional[str] = Field(None, max_length=200)
    metadados: Optional[Dict[str, Any]] = None
    status: str = Field(default="pendente", pattern="^(pendente|aprovada|rejeitada|cancelada)$")


class TransacaoUpdate(BaseModel):
    valor: Optional[float] = Field(None, gt=0)
    tipo: Optional[str] = Field(None, pattern="^(credito|debito|pix|transferencia|boleto)$")
    status: Optional[str] = Field(None, pattern="^(pendente|aprovada|rejeitada|cancelada)$")
    descricao: Optional[str] = Field(None, max_length=200)
    metadados: Optional[Dict[str, Any]] = None


class LogAcesso(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    id_cliente: Optional[PyObjectId] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    acao: str = Field(..., pattern="^(login|logout|create|read|update|delete|error)$")
    ip: str = Field(..., pattern="^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$")
    user_agent: Optional[str] = Field(None, max_length=500)
    endpoint: Optional[str] = Field(None, max_length=200)
    status_code: Optional[int] = Field(None, ge=100, le=599)
    detalhes: Optional[Dict[str, Any]] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class LogAcessoCreate(BaseModel):
    id_cliente: Optional[str] = None  # String representation of ObjectId
    acao: str = Field(..., pattern="^(login|logout|create|read|update|delete|error)$")
    ip: str = Field(..., pattern="^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$")
    user_agent: Optional[str] = Field(None, max_length=500)
    endpoint: Optional[str] = Field(None, max_length=200)
    status_code: Optional[int] = Field(None, ge=100, le=599)
    detalhes: Optional[Dict[str, Any]] = None


# Modelos para respostas da API
class ClienteResponse(BaseModel):
    id: str = Field(..., alias="_id")
    nome: str
    email: str
    cpf: str
    endereco: Optional[str] = None
    telefone: Optional[str] = None
    data_nascimento: Optional[datetime] = None
    status: str
    data_criacao: datetime
    
    model_config = {"populate_by_name": True}


class TransacaoResponse(BaseModel):
    id: str = Field(..., alias="_id")
    id_cliente: str
    valor: float
    tipo: str
    status: str
    data: datetime
    descricao: Optional[str] = None
    metadados: Optional[Dict[str, Any]] = None
    
    model_config = {"populate_by_name": True}


class LogAcessoResponse(BaseModel):
    id: str = Field(..., alias="_id")
    id_cliente: Optional[str] = None
    timestamp: datetime
    acao: str
    ip: str
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    detalhes: Optional[Dict[str, Any]] = None
    
    model_config = {"populate_by_name": True}


# Modelos para paginação
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    
# Modelos para estatísticas
class ClienteStats(BaseModel):
    total_clientes: int
    clientes_ativos: int
    clientes_inativos: int
    clientes_suspensos: int
    novos_hoje: int
    novos_mes: int


class TransacaoStats(BaseModel):
    total_transacoes: int
    valor_total: float
    transacoes_aprovadas: int
    transacoes_pendentes: int
    transacoes_rejeitadas: int
    transacoes_hoje: int
    valor_hoje: float
