"""
Integração Bancária e PIX - Simulação de operações financeiras
Sistema para processar transações PIX, TED, DOC e validações bancárias
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import random
import re

logger = logging.getLogger(__name__)

class TipoTransacao(Enum):
    """Tipos de transação suportados"""
    PIX = "pix"
    TED = "ted"
    DOC = "doc"
    DEPOSITO = "deposito"
    SAQUE = "saque"
    TRANSFERENCIA = "transferencia"

class StatusTransacao(Enum):
    """Status possíveis de uma transação"""
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"
    CANCELADA = "cancelada"
    ESTORNADA = "estornada"

class TipoChavePix(Enum):
    """Tipos de chave PIX"""
    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    TELEFONE = "telefone"
    CHAVE_ALEATORIA = "chave_aleatoria"

class BankingTransaction:
    """Modelo de transação bancária"""
    
    def __init__(
        self,
        tipo: TipoTransacao,
        valor: float,
        origem_conta: str,
        destino_conta: Optional[str] = None,
        chave_pix: Optional[str] = None,
        descricao: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.id = str(uuid.uuid4())
        self.tipo = tipo
        self.valor = valor
        self.origem_conta = origem_conta
        self.destino_conta = destino_conta
        self.chave_pix = chave_pix
        self.descricao = descricao or f"Transação {tipo.value}"
        self.metadata = metadata or {}
        
        self.status = StatusTransacao.PENDENTE
        self.created_at = datetime.utcnow()
        self.processed_at = None
        self.error_message = None
        self.fee = 0.0
        self.banco_central_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte transação para dicionário"""
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "valor": self.valor,
            "origem_conta": self.origem_conta,
            "destino_conta": self.destino_conta,
            "chave_pix": self.chave_pix,
            "descricao": self.descricao,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "error_message": self.error_message,
            "fee": self.fee,
            "banco_central_id": self.banco_central_id
        }

class PixValidator:
    """Validador de chaves PIX"""
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Valida CPF"""
        cpf = re.sub(r'\D', '', cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Cálculo dos dígitos verificadores
        for i in range(9, 11):
            valor = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
            digito = ((valor * 10) % 11) % 10
            if digito != int(cpf[i]):
                return False
        return True
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """Valida CNPJ"""
        cnpj = re.sub(r'\D', '', cnpj)
        if len(cnpj) != 14:
            return False
        
        # Cálculo simplificado para simulação
        return True
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Valida email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validar_telefone(telefone: str) -> bool:
        """Valida telefone"""
        telefone = re.sub(r'\D', '', telefone)
        return len(telefone) in [10, 11] and telefone.isdigit()
    
    @staticmethod
    def validar_chave_aleatoria(chave: str) -> bool:
        """Valida chave aleatória UUID"""
        try:
            uuid.UUID(chave)
            return True
        except ValueError:
            return False
    
    @classmethod
    def validar_chave_pix(cls, chave: str, tipo: Optional[TipoChavePix] = None) -> bool:
        """
        Valida chave PIX determinando o tipo automaticamente ou validando tipo específico
        
        Args:
            chave: Chave PIX a ser validada
            tipo: Tipo específico para validar (opcional)
            
        Returns:
            True se válida, False caso contrário
        """
        if not chave:
            return False
        
        # Se tipo específico for fornecido
        if tipo:
            if tipo == TipoChavePix.CPF:
                return cls.validar_cpf(chave)
            elif tipo == TipoChavePix.CNPJ:
                return cls.validar_cnpj(chave)
            elif tipo == TipoChavePix.EMAIL:
                return cls.validar_email(chave)
            elif tipo == TipoChavePix.TELEFONE:
                return cls.validar_telefone(chave)
            elif tipo == TipoChavePix.CHAVE_ALEATORIA:
                return cls.validar_chave_aleatoria(chave)
        
        # Determinar tipo automaticamente
        if cls.validar_cpf(chave):
            return True
        elif cls.validar_cnpj(chave):
            return True
        elif cls.validar_email(chave):
            return True
        elif cls.validar_telefone(chave):
            return True
        elif cls.validar_chave_aleatoria(chave):
            return True
        
        return False
    
    @classmethod
    def detectar_tipo_chave(cls, chave: str) -> Optional[TipoChavePix]:
        """Detecta o tipo de chave PIX"""
        if cls.validar_cpf(chave):
            return TipoChavePix.CPF
        elif cls.validar_cnpj(chave):
            return TipoChavePix.CNPJ
        elif cls.validar_email(chave):
            return TipoChavePix.EMAIL
        elif cls.validar_telefone(chave):
            return TipoChavePix.TELEFONE
        elif cls.validar_chave_aleatoria(chave):
            return TipoChavePix.CHAVE_ALEATORIA
        return None

class BankingSimulator:
    """Simulador de operações bancárias"""
    
    def __init__(self):
        self.transacoes_processadas = {}
        self.contas_bloqueadas = set()
        self.limite_diario = 5000.00  # Limite PIX por dia
        self.limite_noturno = 1000.00  # Limite PIX noturno (20h-6h)
    
    async def processar_transacao(self, transacao: BankingTransaction) -> BankingTransaction:
        """
        Processa uma transação bancária
        
        Args:
            transacao: Transação a ser processada
            
        Returns:
            Transação processada com status atualizado
        """
        logger.info(f"Processando transação {transacao.id} - {transacao.tipo.value}")
        
        try:
            # Simular tempo de processamento
            await asyncio.sleep(random.uniform(1, 3))
            
            # Validações gerais
            if not await self._validar_transacao(transacao):
                transacao.status = StatusTransacao.REJEITADA
                transacao.processed_at = datetime.utcnow()
                return transacao
            
            # Processamento específico por tipo
            if transacao.tipo == TipoTransacao.PIX:
                await self._processar_pix(transacao)
            elif transacao.tipo in [TipoTransacao.TED, TipoTransacao.DOC]:
                await self._processar_transferencia_tradicional(transacao)
            else:
                await self._processar_operacao_simples(transacao)
            
            # Simular chance de falha (5%)
            if random.random() < 0.05:
                transacao.status = StatusTransacao.REJEITADA
                transacao.error_message = "Falha na comunicação com o sistema bancário"
            else:
                transacao.status = StatusTransacao.APROVADA
                transacao.banco_central_id = f"BC{random.randint(10000000, 99999999)}"
            
            transacao.processed_at = datetime.utcnow()
            self.transacoes_processadas[transacao.id] = transacao
            
            logger.info(f"Transação {transacao.id} processada: {transacao.status.value}")
            return transacao
            
        except Exception as e:
            logger.error(f"Erro ao processar transação {transacao.id}: {str(e)}")
            transacao.status = StatusTransacao.REJEITADA
            transacao.error_message = f"Erro interno: {str(e)}"
            transacao.processed_at = datetime.utcnow()
            return transacao
    
    async def _validar_transacao(self, transacao: BankingTransaction) -> bool:
        """Validações gerais da transação"""
        # Validar valor
        if transacao.valor <= 0:
            transacao.error_message = "Valor deve ser positivo"
            return False
        
        if transacao.valor > 50000:  # Limite máximo
            transacao.error_message = "Valor excede limite máximo permitido"
            return False
        
        # Validar conta origem
        if transacao.origem_conta in self.contas_bloqueadas:
            transacao.error_message = "Conta de origem bloqueada"
            return False
        
        # Validar chave PIX se for PIX
        if transacao.tipo == TipoTransacao.PIX:
            if not transacao.chave_pix:
                transacao.error_message = "Chave PIX é obrigatória"
                return False
            
            if not PixValidator.validar_chave_pix(transacao.chave_pix):
                transacao.error_message = "Chave PIX inválida"
                return False
        
        # Validar conta destino para transferências tradicionais
        if transacao.tipo in [TipoTransacao.TED, TipoTransacao.DOC, TipoTransacao.TRANSFERENCIA]:
            if not transacao.destino_conta:
                transacao.error_message = "Conta de destino é obrigatória"
                return False
        
        return True
    
    async def _processar_pix(self, transacao: BankingTransaction):
        """Processamento específico para PIX"""
        # Verificar limites PIX
        agora = datetime.now().time()
        limite = self.limite_noturno if agora.hour >= 20 or agora.hour <= 6 else self.limite_diario
        
        if transacao.valor > limite:
            transacao.error_message = f"Valor excede limite PIX de R$ {limite:.2f}"
            return False
        
        # PIX é instantâneo, sem taxa
        transacao.fee = 0.0
        transacao.metadata['tipo_chave'] = PixValidator.detectar_tipo_chave(transacao.chave_pix).value
        transacao.metadata['processamento'] = 'instantaneo'
        
        return True
    
    async def _processar_transferencia_tradicional(self, transacao: BankingTransaction):
        """Processamento para TED/DOC"""
        # Calcular taxas
        if transacao.tipo == TipoTransacao.TED:
            transacao.fee = 15.00  # Taxa TED
            transacao.metadata['processamento'] = 'mesmo_dia'
        else:  # DOC
            transacao.fee = 10.00  # Taxa DOC
            transacao.metadata['processamento'] = 'proximo_dia_util'
        
        transacao.metadata['taxa_aplicada'] = transacao.fee
        return True
    
    async def _processar_operacao_simples(self, transacao: BankingTransaction):
        """Processamento para depósito/saque"""
        # Operações simples sem taxa
        transacao.fee = 0.0
        transacao.metadata['processamento'] = 'imediato'
        return True
    
    def obter_transacao(self, transacao_id: str) -> Optional[BankingTransaction]:
        """Obtém transação por ID"""
        return self.transacoes_processadas.get(transacao_id)
    
    def listar_transacoes(self, conta: Optional[str] = None, limit: int = 50) -> List[BankingTransaction]:
        """Lista transações, opcionalmente filtradas por conta"""
        transacoes = list(self.transacoes_processadas.values())
        
        if conta:
            transacoes = [
                t for t in transacoes 
                if t.origem_conta == conta or t.destino_conta == conta
            ]
        
        # Ordenar por data mais recente
        transacoes.sort(key=lambda t: t.created_at, reverse=True)
        return transacoes[:limit]

class PixIntegration:
    """Integração específica para PIX"""
    
    def __init__(self):
        self.banking_simulator = BankingSimulator()
        self.chaves_cadastradas = {}  # Simular DICT do Banco Central
    
    async def criar_chave_pix(self, conta: str, chave: str, tipo: TipoChavePix) -> bool:
        """
        Simula cadastro de chave PIX
        
        Args:
            conta: Conta bancária
            chave: Chave PIX
            tipo: Tipo da chave
            
        Returns:
            True se cadastrada com sucesso
        """
        if not PixValidator.validar_chave_pix(chave, tipo):
            logger.warning(f"Chave PIX inválida: {chave}")
            return False
        
        if chave in self.chaves_cadastradas:
            logger.warning(f"Chave PIX já cadastrada: {chave}")
            return False
        
        self.chaves_cadastradas[chave] = {
            'conta': conta,
            'tipo': tipo.value,
            'cadastrada_em': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Chave PIX cadastrada: {chave} -> {conta}")
        return True
    
    async def consultar_chave_pix(self, chave: str) -> Optional[Dict]:
        """Consulta informações de uma chave PIX"""
        return self.chaves_cadastradas.get(chave)
    
    async def processar_pix(
        self,
        origem_conta: str,
        chave_destino: str,
        valor: float,
        descricao: Optional[str] = None
    ) -> BankingTransaction:
        """
        Processa transação PIX
        
        Args:
            origem_conta: Conta de origem
            chave_destino: Chave PIX de destino
            valor: Valor da transação
            descricao: Descrição opcional
            
        Returns:
            Transação PIX processada
        """
        transacao = BankingTransaction(
            tipo=TipoTransacao.PIX,
            valor=valor,
            origem_conta=origem_conta,
            chave_pix=chave_destino,
            descricao=descricao
        )
        
        # Consultar chave de destino
        destino_info = await self.consultar_chave_pix(chave_destino)
        if destino_info:
            transacao.destino_conta = destino_info['conta']
            transacao.metadata['destino_encontrado'] = True
        else:
            transacao.metadata['destino_encontrado'] = False
            transacao.error_message = "Chave PIX não encontrada"
        
        return await self.banking_simulator.processar_transacao(transacao)

# Instâncias globais
banking_simulator = BankingSimulator()
pix_integration = PixIntegration()

# Funções utilitárias
async def processar_pix_simples(origem: str, chave_pix: str, valor: float) -> Dict:
    """Função simplificada para processar PIX"""
    transacao = await pix_integration.processar_pix(origem, chave_pix, valor)
    return transacao.to_dict()

async def validar_chave_pix_simples(chave: str) -> Dict:
    """Função simplificada para validar chave PIX"""
    is_valid = PixValidator.validar_chave_pix(chave)
    tipo = PixValidator.detectar_tipo_chave(chave) if is_valid else None
    
    return {
        'chave': chave,
        'valida': is_valid,
        'tipo': tipo.value if tipo else None
    }

# Exemplo de uso
if __name__ == "__main__":
    async def exemplo():
        # Cadastrar chave PIX
        await pix_integration.criar_chave_pix(
            conta="12345-6",
            chave="user@example.com",
            tipo=TipoChavePix.EMAIL
        )
        
        # Processar PIX
        resultado = await pix_integration.processar_pix(
            origem_conta="98765-4",
            chave_destino="user@example.com",
            valor=100.00,
            descricao="Pagamento de teste"
        )
        
        print("Resultado PIX:", resultado.to_dict())
        
        # Validar chave
        validacao = await validar_chave_pix_simples("11122233344")
        print("Validação chave:", validacao)
    
    asyncio.run(exemplo())