# Guia de Testes - MonitorDB

## Visão Geral

O MonitorDB possui uma suite de testes automatizados para garantir a qualidade e funcionamento correto da API.

## Estrutura de Testes

```
tests/
├── __init__.py           # Inicialização do módulo de testes
├── conftest.py           # Configurações e fixtures compartilhadas
├── test_api_basics.py    # Testes básicos da API
├── test_clientes.py      # Testes CRUD de clientes
├── test_transacoes.py    # Testes CRUD de transações
└── test_logs.py          # Testes CRUD de logs de acesso
```

## Pré-requisitos para Testes

### 1. Instalar Dependências de Teste
```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Instalar pytest e dependências
pip install pytest pytest-asyncio httpx
```

### 2. Configurar MongoDB para Testes
Os testes usam um banco separado: `monitor_db_test`

**Opção A: MongoDB Local**
```bash
# MongoDB deve estar rodando na porta padrão 27017
mongosh
# Deve conectar sem erros
```

**Opção B: MongoDB Docker (Recomendado para testes)**
```bash
docker run -d \
  --name mongodb-test \
  -p 27017:27017 \
  mongo:latest
```

### 3. Configurar Variáveis de Ambiente
Criar `.env.test` (opcional):
```bash
MONGO_URI=mongodb://localhost:27017
MONGO_DB=monitor_db_test
ENVIRONMENT=test
DEBUG=true
```

## Executando Testes

### Executar Todos os Testes
```bash
# Método básico
python -m pytest

# Com saída detalhada
python -m pytest -v

# Com relatório de cobertura
python -m pytest --cov=app

# Parar no primeiro erro
python -m pytest -x
```

### Executar Testes Específicos

**Por arquivo:**
```bash
# Testes de clientes apenas
python -m pytest tests/test_clientes.py -v

# Testes de transações apenas
python -m pytest tests/test_transacoes.py -v

# Testes básicos da API
python -m pytest tests/test_api_basics.py -v
```

**Por classe ou função:**
```bash
# Classe específica
python -m pytest tests/test_clientes.py::TestClientesCRUD -v

# Função específica
python -m pytest tests/test_clientes.py::TestClientesCRUD::test_create_cliente_success -v
```

**Por padrão:**
```bash
# Testes que contém "create" no nome
python -m pytest -k "create" -v

# Testes que contém "crud"
python -m pytest -k "crud" -v
```

## Tipos de Testes

### 1. Testes Básicos da API (`test_api_basics.py`)
- ✅ Endpoint raiz (`/`)
- ✅ Health check (`/health`)
- ✅ Documentação (`/docs`)
- ✅ Schema OpenAPI
- ✅ Endpoints inválidos
- ✅ Headers CORS

**Exemplo:**
```bash
python -m pytest tests/test_api_basics.py -v
```

### 2. Testes CRUD de Clientes (`test_clientes.py`)
- ✅ Criar cliente válido
- ✅ Validação de CPF (algoritmo completo)
- ✅ Validação de email
- ✅ Buscar cliente por ID
- ✅ Listar clientes
- ✅ Atualizar cliente
- ✅ Deletar cliente
- ✅ Fluxo completo CRUD

**Casos de teste:**
```python
# CPFs testados
CPF_VALIDO = "11144477735"    # ✅ Válido
CPF_INVALIDO = "12345678901"  # ❌ Dígitos inválidos
CPF_SEQUENCIA = "11111111111" # ❌ Sequência inválida
```

### 3. Testes CRUD de Transações (`test_transacoes.py`)
- ✅ Criar transação válida
- ✅ Validação de valor (deve ser positivo)
- ✅ Validação de tipo (credito, debito, pix, etc.)
- ✅ Validação de cliente (deve existir)
- ✅ Buscar transações por cliente
- ✅ Atualizar status da transação
- ✅ Deletar transação

**Tipos de transação testados:**
- `credito`, `debito`, `pix`, `transferencia`, `boleto`

### 4. Testes CRUD de Logs (`test_logs.py`)
- ✅ Criar log válido
- ✅ Log sem cliente (acesso público)
- ✅ Validação de IP
- ✅ Validação de ação
- ✅ Validação de status code
- ✅ Buscar logs por cliente

**Ações testadas:**
- `login`, `logout`, `create`, `read`, `update`, `delete`, `error`

## Fixtures e Configurações

### Fixtures Principais (`conftest.py`)

**`test_client`**: Cliente FastAPI para requisições
```python
def test_client():
    return TestClient(app)
```

**`test_db`**: Conexão de teste com MongoDB
```python
async def test_db():
    # Limpa dados antes do teste
    # Executa teste
    # Limpa dados após o teste
```

### Dados de Teste Padrão
```python
CLIENTE_TEST_DATA = {
    "nome": "João da Silva",
    "email": "joao.silva@teste.com",
    "cpf": "11144477735",  # CPF válido
    "telefone": "11987654321",
    "endereco": "Rua Teste, 123"
}

TRANSACAO_TEST_DATA = {
    "valor": 100.50,
    "tipo": "pix",
    "descricao": "Teste de transação PIX"
}
```

## Relatórios de Testes

### Relatório Básico
```bash
python -m pytest tests/ -v
# =================== test session starts ===================
# tests/test_api_basics.py::TestAPIBasics::test_root_endpoint PASSED
# tests/test_clientes.py::TestClientesCRUD::test_create_cliente_success PASSED
# =================== 15 passed in 2.34s ===================
```

### Relatório de Cobertura
```bash
# Instalar coverage
pip install pytest-cov

# Executar com cobertura
python -m pytest --cov=app --cov-report=html

# Abrir relatório HTML
# Windows: start htmlcov/index.html
# Linux/macOS: open htmlcov/index.html
```

### Relatório XML (para CI/CD)
```bash
python -m pytest --junitxml=tests-results.xml
```

## Cenários de Teste Avançados

### Testes de Performance
```bash
# Instalar pytest-benchmark
pip install pytest-benchmark

# Executar testes de performance
python -m pytest --benchmark-only
```

### Testes Paralelos
```bash
# Instalar pytest-xdist
pip install pytest-xdist

# Executar em paralelo
python -m pytest -n 4  # 4 processos
```

### Testes com Dados Aleatórios
```bash
# Instalar hypothesis
pip install hypothesis

# Executar testes com dados gerados
python -m pytest tests/test_property_based.py
```

## Debugging de Testes

### Executar com Debug
```bash
# Parar no primeiro erro e entrar no debugger
python -m pytest --pdb

# Mostrar prints durante os testes
python -m pytest -s

# Modo verbose com detalhes
python -m pytest -vvv
```

### Debug de Teste Específico
```python
# Adicionar breakpoint no teste
def test_exemplo():
    import pdb; pdb.set_trace()
    # código do teste
```

## Integração Contínua (CI)

### GitHub Actions (`.github/workflows/tests.yml`)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mongodb:
        image: mongo:latest
        ports:
          - 27017:27017
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov
      - name: Run tests
        run: python -m pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Boas Práticas

### 1. Estrutura de Teste
```python
def test_nome_descritivo():
    # Arrange (preparar)
    data = {"campo": "valor"}
    
    # Act (executar)
    response = client.post("/api/endpoint", json=data)
    
    # Assert (verificar)
    assert response.status_code == 201
    assert response.json()["campo"] == "valor"
```

### 2. Limpeza de Dados
```python
def setup_method(self):
    """Executado antes de cada teste"""
    # Criar dados de teste
    
def teardown_method(self):
    """Executado após cada teste"""
    # Limpar dados de teste
```

### 3. Testes Independentes
- Cada teste deve funcionar sozinho
- Não depender da ordem de execução
- Limpar dados entre testes

### 4. Nomes Descritivos
```python
# ✅ Bom
def test_create_cliente_with_valid_cpf_should_return_201():

# ❌ Ruim  
def test_client_creation():
```

## Solução de Problemas

### MongoDB não conecta
```bash
# Verificar se MongoDB está rodando
mongosh mongodb://localhost:27017

# Verificar variáveis de ambiente
echo $MONGO_URI
```

### Testes falham por dados antigos
```bash
# Limpar banco de teste manualmente
mongosh monitor_db_test --eval "db.dropDatabase()"
```

### ImportError nos testes
```bash
# Verificar se o projeto está no PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/caminho/para/projeto"

# Ou executar do diretório raiz
cd /caminho/para/dba_project
python -m pytest
```

## Comandos Úteis

```bash
# Executar apenas testes que falharam na última execução
python -m pytest --lf

# Executar testes em modo "fail fast"
python -m pytest -x

# Mostrar os 10 testes mais lentos
python -m pytest --durations=10

# Executar testes e gerar relatório HTML
python -m pytest --html=report.html --self-contained-html
```

## Próximos Passos

1. ✅ **Executar testes básicos** - Verificar se tudo funciona
2. 🔧 **Configurar CI/CD** - Automatizar testes
3. 📊 **Monitorar cobertura** - Manter cobertura alta
4. 🚀 **Testes de integração** - Testar fluxos completos