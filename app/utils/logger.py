# Configuração de logs

import logging
import os
from typing import Optional

# Configuração básica do logging
def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Configura o sistema de logging
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Arquivo de log (opcional)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Formato personalizado
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar handlers
    handlers = [logging.StreamHandler()]
    
    if log_file:
        # Criar diretório de logs se não existir
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger com o nome especificado
    
    Args:
        name: Nome do logger (geralmente __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

# Configuração padrão
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/monitor.log"
)

# Logger padrão para compatibilidade
logger = get_logger(__name__)
