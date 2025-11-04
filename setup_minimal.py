"""
Setup Minimalista do MonitorDB Project
Script simplificado para configurar apenas o essencial
"""

import os
import sys
import subprocess
import asyncio
import shutil
from pathlib import Path

class MonitorDBMinimalSetup:
    """Setup minimalista - apenas o essencial para API funcionar"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        
        # Dependências mínimas necessárias
        self.essential_packages = [
            "fastapi[all]",
            "motor",
            "pymongo", 
            "pydantic[email]",
            "python-multipart"
        ]
    
    def print_header(self, message):
        print(f"\n{'='*50}")
        print(f"🚀 {message}")
        print(f"{'='*50}")
    
    def run_command(self, command, description=""):
        print(f"🔧 {description}")
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print("✅ Sucesso")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro: {e}")
            return False
    
    def check_essentials(self):
        """Verifica apenas o essencial"""
        print("\n📋 Verificando pré-requisitos essenciais...")
        
        # Python
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ necessário")
            return False
        print("✅ Python OK")
        
        # pip
        if not self.run_command("pip --version", "Verificando pip"):
            return False
        
        return True
    
    def create_venv(self):
        """Cria ambiente virtual"""
        print("\n📦 Configurando ambiente virtual...")
        
        if self.venv_path.exists():
            print("⚠️ Removendo ambiente existente...")
            shutil.rmtree(self.venv_path)
        
        return self.run_command(f"python -m venv {self.venv_path}", "Criando venv")
    
    def install_minimal_deps(self):
        """Instala apenas dependências essenciais"""
        print("\n📥 Instalando dependências mínimas...")
        
        if os.name == 'nt':
            pip_path = self.venv_path / "Scripts" / "pip"
        else:
            pip_path = self.venv_path / "bin" / "pip"
        
        # Atualizar pip
        if not self.run_command(f"{pip_path} install --upgrade pip", "Atualizando pip"):
            return False
        
        # Instalar pacotes essenciais
        for package in self.essential_packages:
            if not self.run_command(f"{pip_path} install {package}", f"Instalando {package}"):
                print(f"⚠️ Falha ao instalar {package}")
        
        return True
    
    def create_minimal_env(self):
        """Cria arquivo .env mínimo"""
        print("\n⚙️ Criando configuração mínima...")
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_content = """# Configurações Mínimas MonitorDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=monitor_db_minimal
ENVIRONMENT=development
DEBUG=true
"""
            env_file.write_text(env_content)
            print("✅ Arquivo .env criado")
        else:
            print("⚠️ Arquivo .env já existe")
        
        return True
    
    def create_startup_script(self):
        """Cria script de inicialização simples"""
        print("\n📝 Criando script de inicialização...")
        
        if os.name == 'nt':
            script_path = self.project_root / "start_minimal.bat"
            script_content = f"""@echo off
echo Iniciando MonitorDB API Minimal...
cd /d "{self.project_root}"
call "{self.venv_path}\\Scripts\\activate.bat"
uvicorn app.main:app --reload --port 8000
pause
"""
        else:
            script_path = self.project_root / "start_minimal.sh"
            script_content = f"""#!/bin/bash
echo "Iniciando MonitorDB API Minimal..."
cd "{self.project_root}"
source "{self.venv_path}/bin/activate"
uvicorn app.main:app --reload --port 8000
"""
            
        script_path.write_text(script_content)
        if not os.name == 'nt':
            script_path.chmod(0o755)
            
        print("✅ Script de inicialização criado")
        return True
    
    def test_minimal_imports(self):
        """Testa se imports básicos funcionam"""
        print("\n🧪 Testando imports básicos...")
        
        try:
            sys.path.append(str(self.project_root))
            
            # Teste imports mínimos
            from app.config import settings
            print("✅ Config OK")
            
            from app.database import models
            print("✅ Models OK")
            
            print("✅ Todos os imports básicos funcionando")
            return True
            
        except Exception as e:
            print(f"❌ Erro nos imports: {e}")
            return False
    
    def print_instructions(self):
        """Instruções finais simplificadas"""
        print(f"\n🎉 SETUP MÍNIMO CONCLUÍDO!")
        print("=" * 40)
        
        print("\n📋 ESTRUTURA MÍNIMA CRIADA:")
        print("✅ Ambiente virtual configurado")
        print("✅ Dependências essenciais instaladas")
        print("✅ Arquivo .env básico criado")
        print("✅ Script de inicialização pronto")
        
        print(f"\n🚀 COMO USAR:")
        print("1. Configure MongoDB:")
        print("   - Instale MongoDB local ou use Docker")
        print("   - Ajuste MONGO_URI no arquivo .env se necessário")
        
        print("\n2. Iniciar API:")
        if os.name == 'nt':
            print("   - Execute: start_minimal.bat")
        else:
            print("   - Execute: ./start_minimal.sh")
        
        print("\n3. Testar:")
        print("   - API: http://localhost:8000")
        print("   - Docs: http://localhost:8000/docs")
        
        print(f"\n⚠️ PASTAS REMOVÍVEIS:")
        removable = [
            "monitoring/", 
            "app/monitoring/", 
            "app/security/", 
            "app/integrations/",
            "tests/", 
            "docs/"
        ]
        for folder in removable:
            if Path(folder).exists():
                print(f"   - {folder} (opcional)")
    
    async def run_minimal_setup(self):
        """Executa setup mínimo"""
        self.print_header("SETUP MÍNIMO MONITORDB")
        
        try:
            if not self.check_essentials():
                return False
            
            if not self.create_venv():
                return False
            
            if not self.install_minimal_deps():
                return False
            
            if not self.create_minimal_env():
                return False
            
            if not self.create_startup_script():
                return False
            
            if not self.test_minimal_imports():
                return False
            
            self.print_instructions()
            return True
            
        except Exception as e:
            print(f"❌ Erro no setup: {e}")
            return False

async def main():
    """Função principal simplificada"""
    setup = MonitorDBMinimalSetup()
    
    print("🎯 MonitorDB - Setup Mínimo (Apenas o Essencial)")
    print("Este setup instala apenas o necessário para uma API básica funcionar")
    
    success = await setup.run_minimal_setup()
    
    if success:
        print("\n✅ Setup mínimo concluído com sucesso!")
        
        print(f"\n🗑️ PARA LIMPAR PROJETO (opcional):")
        print("Você pode remover estas pastas se não precisar:")
        print("- monitoring/ (Prometheus, Grafana)")
        print("- app/security/ (JWT, autenticação)")  
        print("- app/integrations/ (ViaCEP, PIX)")
        print("- app/monitoring/ (métricas avançadas)")
        print("- tests/ (testes - mas recomendado manter)")
        
        return 0
    else:
        print("\n❌ Setup falhou")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())