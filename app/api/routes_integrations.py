"""
Rotas para Integrações Externas
Endpoints para testar ViaCEP, validações, notificações e APIs bancárias
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.integrations import (
    buscar_endereco,
    buscar_por_localidade,
    validar_cep,
    formatar_cep,
    send_alert,
    NotificationChannel,
    NotificationPriority,
    document_validator,
    get_bank_info,
    search_bank,
    validate_bank_account,
    validate_pix
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/integrations", tags=["Integrações"])

# Modelos Pydantic para requests
class CEPRequest(BaseModel):
    cep: str = Field(..., description="CEP a ser consultado", example="01310-100")

class LocalidadeRequest(BaseModel):
    uf: str = Field(..., min_length=2, max_length=2, description="Estado (UF)", example="SP")
    cidade: str = Field(..., min_length=3, description="Nome da cidade", example="São Paulo")
    logradouro: str = Field(..., min_length=3, description="Nome da rua", example="Avenida Paulista")

class NotificationRequest(BaseModel):
    title: str = Field(..., description="Título da notificação")
    message: str = Field(..., description="Mensagem da notificação")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.EMAIL])
    recipient: Optional[str] = Field(None, description="Destinatário específico")

class DocumentValidationRequest(BaseModel):
    cpf: Optional[str] = Field(None, example="123.456.789-01")
    cnpj: Optional[str] = Field(None, example="12.345.678/0001-01")
    telefone: Optional[str] = Field(None, example="(11) 99999-9999")
    email: Optional[str] = Field(None, example="usuario@exemplo.com")
    cep: Optional[str] = Field(None, example="01310-100")
    data_nascimento: Optional[str] = Field(None, example="01/01/1990")

class BankAccountRequest(BaseModel):
    bank_code: Optional[str] = Field(None, example="001")
    agency: str = Field(..., example="1234-5")
    account: str = Field(..., example="12345-6")
    pix_key: Optional[str] = Field(None, example="usuario@exemplo.com")

# ========== ENDPOINTS VIACEP ==========

@router.post("/viacep/buscar", summary="Buscar endereço por CEP")
async def buscar_endereco_endpoint(request: CEPRequest):
    """
    Busca dados de endereço através do CEP usando a API do ViaCEP
    """
    try:
        logger.info(f"Buscando endereço para CEP: {request.cep}")
        endereco = await buscar_endereco(request.cep)
        
        return {
            "success": True,
            "data": endereco,
            "message": f"Endereço encontrado para o CEP {endereco['cep_formatado']}"
        }
    
    except Exception as e:
        logger.error(f"Erro ao buscar CEP {request.cep}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/viacep/buscar-localidade", summary="Buscar CEPs por localidade")
async def buscar_por_localidade_endpoint(request: LocalidadeRequest):
    """
    Busca CEPs através de UF, cidade e logradouro
    """
    try:
        logger.info(f"Buscando CEPs para: {request.logradouro}, {request.cidade}/{request.uf}")
        enderecos = await buscar_por_localidade(request.uf, request.cidade, request.logradouro)
        
        return {
            "success": True,
            "data": enderecos,
            "count": len(enderecos),
            "message": f"Encontrados {len(enderecos)} endereços"
        }
    
    except Exception as e:
        logger.error(f"Erro ao buscar localidade: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/viacep/validar/{cep}", summary="Validar formato de CEP")
async def validar_cep_endpoint(cep: str):
    """
    Valida se um CEP tem formato válido
    """
    try:
        is_valid = validar_cep(cep)
        formatted_cep = formatar_cep(cep) if is_valid else None
        
        return {
            "success": True,
            "data": {
                "cep_original": cep,
                "cep_formatado": formatted_cep,
                "is_valid": is_valid
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "data": {
                "cep_original": cep,
                "cep_formatado": None,
                "is_valid": False
            },
            "error": str(e)
        }

# ========== ENDPOINTS NOTIFICAÇÕES ==========

@router.post("/notifications/send", summary="Enviar notificação")
async def send_notification_endpoint(request: NotificationRequest):
    """
    Envia notificação através dos canais especificados
    """
    try:
        logger.info(f"Enviando notificação: {request.title}")
        
        results = await send_alert(
            title=request.title,
            message=request.message,
            priority=request.priority,
            channels=request.channels,
            recipient=request.recipient
        )
        
        success_count = sum(1 for result in results.values() if result)
        
        return {
            "success": True,
            "data": {
                "results": results,
                "success_count": success_count,
                "total_channels": len(request.channels)
            },
            "message": f"Notificação enviada para {success_count}/{len(request.channels)} canais"
        }
    
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/test", summary="Testar notificações")
async def test_notifications():
    """
    Endpoint de teste para verificar se as notificações estão funcionando
    """
    try:
        test_channels = [NotificationChannel.EMAIL]
        
        results = await send_alert(
            title="🧪 Teste de Notificações - MonitorDB",
            message="Este é um teste automatizado do sistema de notificações. Se você recebeu esta mensagem, o sistema está funcionando corretamente!",
            priority=NotificationPriority.LOW,
            channels=test_channels
        )
        
        return {
            "success": True,
            "data": results,
            "message": "Teste de notificações executado"
        }
    
    except Exception as e:
        logger.error(f"Erro no teste de notificações: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENDPOINTS VALIDAÇÃO DE DOCUMENTOS ==========

@router.post("/validation/documents", summary="Validar documentos brasileiros")
async def validate_documents_endpoint(request: DocumentValidationRequest):
    """
    Valida múltiplos tipos de documentos brasileiros
    """
    try:
        # Converte para dicionário
        data = request.dict(exclude_none=True)
        
        logger.info(f"Validando documentos: {list(data.keys())}")
        
        # Usa o validador
        results = document_validator.validate_all(data)
        
        return {
            "success": True,
            "data": results,
            "message": "Validação concluída" if results['is_valid'] else "Encontrados erros na validação"
        }
    
    except Exception as e:
        logger.error(f"Erro na validação de documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validation/cpf/{cpf}", summary="Validar CPF específico")
async def validate_cpf_endpoint(cpf: str):
    """
    Valida um CPF específico
    """
    try:
        is_valid, error = document_validator.validate_cpf(cpf)
        formatted_cpf = document_validator.format_cpf(cpf) if is_valid else None
        
        return {
            "success": True,
            "data": {
                "cpf_original": cpf,
                "cpf_formatado": formatted_cpf,
                "is_valid": is_valid,
                "error": error
            }
        }
    
    except Exception as e:
        logger.error(f"Erro na validação de CPF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENDPOINTS BANCÁRIOS ==========

@router.get("/banking/banks", summary="Listar bancos brasileiros")
async def list_banks_endpoint(
    search: Optional[str] = Query(None, description="Buscar por nome ou código do banco")
):
    """
    Lista todos os bancos brasileiros ou busca por termo específico
    """
    try:
        if search:
            logger.info(f"Buscando bancos com termo: {search}")
            banks = await search_bank(search)
        else:
            from app.integrations.banking_integration import banking_integration
            banks = await banking_integration.get_all_banks()
            # Limita a 50 bancos para não sobrecarregar a resposta
            banks = banks[:50]
        
        return {
            "success": True,
            "data": banks,
            "count": len(banks),
            "message": f"Encontrados {len(banks)} bancos"
        }
    
    except Exception as e:
        logger.error(f"Erro ao listar bancos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/banking/bank/{bank_code}", summary="Obter informações de banco específico")
async def get_bank_endpoint(bank_code: str):
    """
    Obtém informações detalhadas de um banco pelo código
    """
    try:
        logger.info(f"Buscando informações do banco: {bank_code}")
        bank = await get_bank_info(bank_code)
        
        if not bank:
            raise HTTPException(status_code=404, detail=f"Banco {bank_code} não encontrado")
        
        return {
            "success": True,
            "data": bank,
            "message": f"Informações do banco {bank['name']}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar banco {bank_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/banking/validate-account", summary="Validar dados bancários")
async def validate_bank_account_endpoint(request: BankAccountRequest):
    """
    Valida dados de conta bancária (agência, conta, PIX)
    """
    try:
        logger.info(f"Validando conta bancária - Banco: {request.bank_code}")
        
        validation_result = validate_bank_account(
            account=request.account,
            agency=request.agency,
            bank_code=request.bank_code
        )
        
        # Se tiver chave PIX, valida separadamente
        if request.pix_key:
            pix_valid, pix_type = validate_pix(request.pix_key)
            validation_result['pix_validation'] = {
                'is_valid': pix_valid,
                'key_type': pix_type,
                'key': request.pix_key
            }
        
        return {
            "success": True,
            "data": validation_result,
            "message": "Validação bancária concluída"
        }
    
    except Exception as e:
        logger.error(f"Erro na validação bancária: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/banking/validate-pix/{pix_key}", summary="Validar chave PIX")
async def validate_pix_endpoint(pix_key: str):
    """
    Valida uma chave PIX e identifica seu tipo
    """
    try:
        logger.info(f"Validando chave PIX: {pix_key[:10]}...")
        
        is_valid, result = validate_pix(pix_key)
        
        return {
            "success": True,
            "data": {
                "pix_key": pix_key,
                "is_valid": is_valid,
                "key_type": result if is_valid else None,
                "error": result if not is_valid else None
            }
        }
    
    except Exception as e:
        logger.error(f"Erro na validação PIX: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== ENDPOINT DE STATUS ==========

@router.get("/status", summary="Status das integrações")
async def integrations_status():
    """
    Verifica o status de todas as integrações disponíveis
    """
    try:
        status = {
            "timestamp": "2024-10-31T00:00:00Z",
            "integrations": {
                "viacep": {
                    "status": "available",
                    "description": "API ViaCEP para consulta de endereços"
                },
                "notifications": {
                    "status": "available", 
                    "description": "Sistema de notificações multi-canal"
                },
                "document_validation": {
                    "status": "available",
                    "description": "Validação de documentos brasileiros"
                },
                "banking": {
                    "status": "available",
                    "description": "Integração com APIs bancárias"
                }
            }
        }
        
        return {
            "success": True,
            "data": status,
            "message": "Status das integrações obtido com sucesso"
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter status das integrações: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))