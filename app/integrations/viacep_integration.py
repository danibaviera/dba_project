"""
Integração ViaCEP - Consulta de endereços por CEP
Permite enriquecimento automático de dados de clientes com informações de endereço
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ViaCEPIntegration:
    """Cliente para integração com a API ViaCEP"""
    
    BASE_URL = "https://viacep.com.br/ws"
    TIMEOUT = 10.0
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def consultar_cep(self, cep: str) -> Optional[Dict[str, Any]]:
        """
        Consulta informações de endereço por CEP
        
        Args:
            cep: CEP no formato XXXXX-XXX ou XXXXXXXX
            
        Returns:
            Dicionário com dados do endereço ou None se não encontrado
        """
        try:
            # Limpar e validar CEP
            cep_limpo = self._limpar_cep(cep)
            if not self._validar_cep(cep_limpo):
                logger.warning(f"CEP inválido: {cep}")
                return None
            
            # Fazer requisição
            url = f"{self.BASE_URL}/{cep_limpo}/json/"
            
            if not self.session:
                self.session = httpx.AsyncClient(timeout=self.TIMEOUT)
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se encontrou o CEP
            if data.get('erro'):
                logger.info(f"CEP não encontrado: {cep_limpo}")
                return None
            
            # Padronizar retorno
            endereco = {
                'cep': data.get('cep', ''),
                'logradouro': data.get('logradouro', ''),
                'complemento': data.get('complemento', ''),
                'bairro': data.get('bairro', ''),
                'localidade': data.get('localidade', ''),  # Cidade
                'uf': data.get('uf', ''),  # Estado
                'ibge': data.get('ibge', ''),
                'gia': data.get('gia', ''),
                'ddd': data.get('ddd', ''),
                'siafi': data.get('siafi', ''),
                'consultado_em': datetime.utcnow().isoformat()
            }
            
            logger.info(f"CEP consultado com sucesso: {cep_limpo}")
            return endereco
            
        except httpx.TimeoutException:
            logger.error(f"Timeout na consulta do CEP: {cep}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP na consulta do CEP {cep}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado na consulta do CEP {cep}: {str(e)}")
            return None
    
    def _limpar_cep(self, cep: str) -> str:
        """Remove formatação do CEP, mantendo apenas números"""
        if not cep:
            return ""
        return ''.join(filter(str.isdigit, cep))
    
    def _validar_cep(self, cep: str) -> bool:
        """Valida se CEP tem formato correto (8 dígitos)"""
        return len(cep) == 8 and cep.isdigit()
    
    async def consultar_multiplos_ceps(self, ceps: list) -> Dict[str, Optional[Dict]]:
        """
        Consulta múltiplos CEPs de forma assíncrona
        
        Args:
            ceps: Lista de CEPs para consultar
            
        Returns:
            Dicionário com CEP como chave e dados do endereço como valor
        """
        resultados = {}
        
        # Criar tasks para consultas paralelas
        tasks = []
        for cep in ceps:
            task = asyncio.create_task(self.consultar_cep(cep))
            tasks.append((cep, task))
        
        # Aguardar todos os resultados
        for cep, task in tasks:
            try:
                resultado = await task
                resultados[cep] = resultado
            except Exception as e:
                logger.error(f"Erro na consulta paralela do CEP {cep}: {str(e)}")
                resultados[cep] = None
        
        return resultados


class EnderecoEnricher:
    """Classe para enriquecimento de dados de endereço"""
    
    def __init__(self):
        self.viacep = ViaCEPIntegration()
    
    async def enriquecer_cliente_endereco(self, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece dados do cliente com informações de endereço baseadas no CEP
        
        Args:
            cliente_data: Dados do cliente (deve conter 'cep')
            
        Returns:
            Dados do cliente enriquecidos com informações de endereço
        """
        if 'cep' not in cliente_data or not cliente_data['cep']:
            logger.warning("Cliente sem CEP para enriquecimento")
            return cliente_data
        
        async with self.viacep as viacep_client:
            endereco_info = await viacep_client.consultar_cep(cliente_data['cep'])
            
            if endereco_info:
                # Enriquecer dados do cliente
                cliente_enriquecido = cliente_data.copy()
                
                # Atualizar/adicionar informações de endereço
                if 'endereco' not in cliente_enriquecido:
                    cliente_enriquecido['endereco'] = {}
                
                endereco = cliente_enriquecido['endereco']
                endereco.update({
                    'logradouro': endereco_info.get('logradouro', endereco.get('logradouro', '')),
                    'bairro': endereco_info.get('bairro', endereco.get('bairro', '')),
                    'cidade': endereco_info.get('localidade', endereco.get('cidade', '')),
                    'estado': endereco_info.get('uf', endereco.get('estado', '')),
                    'cep': endereco_info.get('cep', endereco.get('cep', '')),
                    'ddd': endereco_info.get('ddd', endereco.get('ddd', '')),
                    'ibge_codigo': endereco_info.get('ibge', ''),
                    'complemento': endereco_info.get('complemento', endereco.get('complemento', ''))
                })
                
                logger.info(f"Cliente enriquecido com dados de endereço: CEP {cliente_data['cep']}")
                return cliente_enriquecido
            else:
                logger.warning(f"Não foi possível enriquecer endereço para CEP: {cliente_data['cep']}")
                return cliente_data
    
    async def validar_cep_cliente(self, cep: str) -> bool:
        """
        Valida se um CEP existe consultando a API ViaCEP
        
        Args:
            cep: CEP para validar
            
        Returns:
            True se o CEP existe, False caso contrário
        """
        async with self.viacep as viacep_client:
            endereco_info = await viacep_client.consultar_cep(cep)
            return endereco_info is not None


# Instância global para uso em toda a aplicação
endereco_enricher = EnderecoEnricher()


# Funções utilitárias para uso direto
async def consultar_cep_simples(cep: str) -> Optional[Dict[str, Any]]:
    """Função simplificada para consulta de CEP"""
    async with ViaCEPIntegration() as viacep:
        return await viacep.consultar_cep(cep)


async def validar_cep_simples(cep: str) -> bool:
    """Função simplificada para validação de CEP"""
    resultado = await consultar_cep_simples(cep)
    return resultado is not None


# Exemplo de uso
if __name__ == "__main__":
    async def exemplo():
        # Consulta simples
        endereco = await consultar_cep_simples("01310-100")
        print("Endereço encontrado:", endereco)
        
        # Enriquecimento de cliente
        cliente = {
            "nome": "João Silva",
            "cep": "01310-100",
            "endereco": {"numero": "123"}
        }
        
        cliente_enriquecido = await endereco_enricher.enriquecer_cliente_endereco(cliente)
        print("Cliente enriquecido:", cliente_enriquecido)
    
    asyncio.run(exemplo())