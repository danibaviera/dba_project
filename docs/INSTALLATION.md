# Guia de Instalação - MonitorDB

## Pré-requisitos

### Requisitos Mínimos
- **Python 3.8+** (recomendado: Python 3.10+)
- **MongoDB** (local ou Docker)
- **Git** (para clonar o repositório)

### Verificar Pré-requisitos

```bash
# Verificar Python
python --version
# Deve mostrar: Python 3.8.x ou superior

# Verificar pip
pip --version

# Verificar Git
git --version
```

## Opção 1: Instalação Automática (Recomendada)

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd dba_project
```

### 2. Executar Setup Automático
```bash
# Windows
python setup_minimal.py

# Linux/macOS
python3 setup_minimal.py
```

O script automático irá:
- ✅ Verificar pré-requisitos
- ✅ Criar ambiente virtual
- ✅ Instalar dependências
- ✅ Configurar arquivo .env
- ✅ Criar scripts de inicialização

### 3. Iniciar a API
```bash
# Windows
start_minimal.bat

# Linux/macOS
./start_minimal.sh
```

## Opção 2: Instalação Manual

### 1. Criar Ambiente Virtual
```bash
# Criar ambiente
python -m venv venv

# Ativar ambiente
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 2. Instalar Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependências Essenciais:**
```
fastapi[all]==0.121.0
motor==3.7.1
pymongo==4.10.1
pydantic[email]==2.12.3
python-multipart==0.0.20
```

### 3. Configurar Ambiente

Criar arquivo `.env`:
```bash
# Copiar template
cp .env.example .env

# Ou criar manualmente:
MONGO_URI=mongodb://localhost:27017
MONGO_DB=monitor_db
ENVIRONMENT=development
DEBUG=true
```

### 4. Configurar MongoDB

#### Opção A: MongoDB Local
1. **Instalar MongoDB:**
   - Windows: [MongoDB Community Server](https://www.mongodb.com/try/download/community)
   - Linux: `sudo apt-get install mongodb`
   - macOS: `brew install mongodb-community`

2. **Iniciar MongoDB:**
   ```bash
   # Windows (como serviço)
   net start MongoDB

   # Linux/macOS
   sudo systemctl start mongod
   # ou
   mongod --dbpath /data/db
   ```

3. **Verificar conexão:**
   ```bash
   mongosh
   # Deve conectar sem erros
   ```

#### Opção B: MongoDB com Docker
```bash
# Iniciar MongoDB em container
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=<your-password> \
  mongo:latest

# Ajustar .env
MONGO_URI=mongodb://admin:<your-password>@localhost:27017
```

#### Opção C: MongoDB Atlas (Cloud)
1. Criar conta no [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Criar cluster gratuito
3. Obter string de conexão
4. Configurar no .env:
   ```
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/<database-name>
   ```

## Opção 3: Docker Compose - Stack Completa (Recomendada para Produção)

### ✅ Validação Aprovada - Stack Otimizada

A configuração Docker foi **totalmente validada** e inclui apenas serviços essenciais:

**🔧 Configuração Final:**
- **4 Serviços Essenciais:** MongoDB, API, Prometheus, Grafana
- **🔗 Dependências Corretas:** Ordem de inicialização otimizada
- **📋 Portas Configuradas:** Sem conflitos
- **🎯 Stack Pronta:** Zero configuração manual

### Pré-requisitos Docker
```bash
# Verificar Docker
docker --version
docker-compose --version

# Deve mostrar versões instaladas
```

### 1. Validar Configuração
```bash
# Validar sintaxe (deve passar sem erros)
docker-compose config

# Resultado esperado: configuração válida com warning menor sobre versão
```

### 2. Iniciar Stack Completa
```bash
# Construir e iniciar todos os serviços
docker-compose up --build -d

# Ver logs em tempo real
docker-compose logs -f

# Ver status dos containers
docker-compose ps
```

### 3. Acessar Serviços

**📋 Portas de Acesso:**
- **🚀 API MonitorDB:** http://localhost:8000
  - Documentação: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health
- **📊 Prometheus:** http://localhost:9090
  - Métricas da API disponíveis automaticamente
- **📈 Grafana:** http://localhost:3000
  - Login: admin / admin123
  - Dashboards pré-configurados
- **🗄️ MongoDB:** localhost:27017
  - Usuário: admin / admin123
  - Banco: monitordb (criado automaticamente)

### 4. Configuração Automática

A stack inclui **inicialização automática**:

**🔐 Segurança:**
- Usuários de aplicação criados automaticamente
- Permissões de acesso configuradas
- JWT tokens configurados

**📋 Estrutura do Banco:**
- Coleções com validação de schema
- Índices para performance otimizada
- Dados de exemplo para testes

**🚀 Dados Iniciais:**
- 3 usuários de teste (admin, manager, operator)
- Clientes de demonstração
- Transações de exemplo

### 5. Comandos Úteis

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (reset completo)
docker-compose down -v

# Ver logs de um serviço específico
docker-compose logs api
docker-compose logs mongodb

# Reiniciar um serviço
docker-compose restart api

# Atualizar configuração (após mudanças no código)
docker-compose up --build -d
```

### 6. Verificação de Saúde

**🏥 Health Checks Automáticos:**
- MongoDB: Ping database
- API: HTTP health endpoint
- Prometheus: Targets discovery
- Grafana: Dashboard availability

**🔍 Monitoramento:**
- Métricas coletadas automaticamente
- Alertas configurados
- Dashboards prontos para uso

### 5. Inicializar Banco de Dados (Manual - se não usar Docker)
```bash
# Ativar ambiente virtual primeiro
python app/database/create_table_clients.py
```

### 6. Iniciar a API
```bash
# Desenvolvimento (com reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Verificação da Instalação

### 1. Testar API
```bash
# Health check
curl http://localhost:8000/health

# Documentação
# Abrir: http://localhost:8000/docs
```

### 2. Testar MongoDB
```bash
# Conectar ao MongoDB
mongosh mongodb://localhost:27017/monitor_db

# Listar collections
show collections
```

### 3. Executar Testes
```bash
# Instalar pytest (se não instalado)
pip install pytest pytest-asyncio

# Executar testes
python -m pytest tests/ -v
```

## Solução de Problemas

### Erro: Python não encontrado
```bash
# Windows: Instalar do site oficial
https://python.org/downloads

# Ubuntu/Debian
sudo apt-get install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### Erro: MongoDB não conecta
```bash
# Verificar se está rodando
# Windows:
net start MongoDB

# Linux:
sudo systemctl status mongod

# Verificar porta
netstat -an | grep 27017
```

### Erro: Dependências não instalam
```bash
# Atualizar pip
pip install --upgrade pip

# Instalar uma por vez
pip install fastapi
pip install motor
pip install pymongo
pip install pydantic[email]
```

### Erro: Permissão negada (Linux/macOS)
```bash
# Dar permissão aos scripts
chmod +x start_minimal.sh

# Usar sudo se necessário
sudo ./start_minimal.sh
```

### Erro: Porta 8000 em uso
```bash
# Verificar processo usando a porta
# Windows:
netstat -ano | findstr :8000

# Linux/macOS:
lsof -i :8000

# Usar porta diferente
uvicorn app.main:app --port 8001
```

## Configurações Avançadas

### Variáveis de Ambiente (.env)
```bash
# Configurações básicas
MONGO_URI=mongodb://localhost:27017
MONGO_DB=monitor_db
ENVIRONMENT=development
DEBUG=true

# Configurações de produção
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Configurações de API
API_PORT=8000
API_HOST=0.0.0.0
CORS_ORIGINS=["http://localhost:3000"]

# Configurações do MongoDB
MONGO_MAX_CONNECTIONS=100
MONGO_MIN_CONNECTIONS=10
```

### Scripts Personalizados

**start_dev.sh** (desenvolvimento):
```bash
#!/bin/bash
source venv/bin/activate
export DEBUG=true
uvicorn app.main:app --reload --port 8000
```

**start_prod.sh** (produção):
```bash
#!/bin/bash
source venv/bin/activate
export ENVIRONMENT=production
uvicorn app.main:app --workers 4 --port 8000
```

## Próximos Passos

1. ✅ **API funcionando** - Acesse http://localhost:8000/docs
2. 📚 **Ler documentação** - Veja `docs/API.md`
3. 🧪 **Executar testes** - Veja `docs/TESTING.md`
4. 🚀 **Deploy** - Configure para produção

## Suporte

- 📖 **Documentação:** `docs/`
- 🐛 **Issues:** Criar issue no repositório
- 📧 **Contato:** [email do desenvolvedor]