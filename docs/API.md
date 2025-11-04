# API Documentation - MonitorDB

## Visão Geral

A API MonitorDB oferece endpoints para gerenciamento de clientes, transações e logs de acesso em um sistema bancário/financeiro.

**Base URL:** `http://localhost:8000`  
**Documentação Interativa:** `http://localhost:8000/docs`

## Autenticação

Atualmente a API não requer autenticação (versão simplificada).

## Endpoints Principais

### 📊 Status da API

#### GET `/`
Endpoint raiz da API.

**Response:**
```json
{
  "message": "MonitorDB API - Sistema de Monitoramento Bancário",
  "version": "1.0.0",
  "status": "active"
}
```

#### GET `/health`
Health check da aplicação.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-04T10:30:00Z"
}
```

---

### 👥 Clientes

#### POST `/api/clientes`
Cria um novo cliente.

**Request Body:**
```json
{
  "nome": "João da Silva",
  "email": "joao@email.com",
  "cpf": "11144477735",
  "telefone": "11987654321",
  "endereco": "Rua Exemplo, 123",
  "data_nascimento": "1990-01-01T00:00:00Z",
  "status": "ativo"
}
```

**Campos Obrigatórios:** `nome`, `email`, `cpf`
**Campos Opcionais:** `telefone`, `endereco`, `data_nascimento`, `status`

**Validações:**
- CPF: 11 dígitos com validação de dígitos verificadores
- Email: Formato válido de email
- Telefone: 10 ou 11 dígitos
- Status: `ativo`, `inativo`, `suspenso`

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "nome": "João da Silva",
  "email": "joao@email.com",
  "cpf": "11144477735",
  "telefone": "11987654321",
  "endereco": "Rua Exemplo, 123",
  "data_nascimento": "1990-01-01T00:00:00Z",
  "status": "ativo",
  "data_criacao": "2025-11-04T10:30:00Z"
}
```

#### GET `/api/clientes`
Lista todos os clientes.

**Query Parameters:**
- `page` (int): Página (padrão: 1)
- `size` (int): Itens por página (padrão: 50)
- `status` (string): Filtrar por status

**Response (200):**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "nome": "João da Silva",
    "email": "joao@email.com",
    "cpf": "11144477735",
    "status": "ativo",
    "data_criacao": "2025-11-04T10:30:00Z"
  }
]
```

#### GET `/api/clientes/{id}`
Busca cliente específico por ID.

**Response (200):** Mesmo formato do POST
**Response (404):** Cliente não encontrado

#### PUT `/api/clientes/{id}`
Atualiza dados do cliente.

**Request Body:** Campos opcionais para atualização
**Response (200):** Cliente atualizado
**Response (404):** Cliente não encontrado

#### DELETE `/api/clientes/{id}`
Remove cliente.

**Response (200):** `{"message": "Cliente removido com sucesso"}`
**Response (404):** Cliente não encontrado

---

### 💰 Transações

#### POST `/api/transacoes`
Cria nova transação.

**Request Body:**
```json
{
  "id_cliente": "507f1f77bcf86cd799439011",
  "valor": 150.50,
  "tipo": "pix",
  "descricao": "Pagamento PIX para loja",
  "status": "pendente",
  "metadados": {
    "banco_destino": "341",
    "chave_pix": "joao@email.com"
  }
}
```

**Campos Obrigatórios:** `id_cliente`, `valor`, `tipo`
**Tipos Válidos:** `credito`, `debito`, `pix`, `transferencia`, `boleto`
**Status Válidos:** `pendente`, `aprovada`, `rejeitada`, `cancelada`

**Validações:**
- Valor: Deve ser positivo (> 0)
- Cliente: Deve existir no sistema

#### GET `/api/transacoes`
Lista todas as transações.

**Query Parameters:**
- `cliente_id` (string): Filtrar por cliente
- `tipo` (string): Filtrar por tipo
- `status` (string): Filtrar por status
- `data_inicio` (datetime): Data inicial
- `data_fim` (datetime): Data final

#### GET `/api/clientes/{id}/transacoes`
Lista transações de um cliente específico.

#### PUT `/api/transacoes/{id}`
Atualiza transação (principalmente status).

#### DELETE `/api/transacoes/{id}`
Remove transação.

---

### 📝 Logs de Acesso

#### POST `/api/logs`
Registra log de acesso.

**Request Body:**
```json
{
  "id_cliente": "507f1f77bcf86cd799439011",
  "acao": "login",
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "endpoint": "/api/clientes",
  "status_code": 200,
  "detalhes": {
    "tempo_resposta": 0.15,
    "bytes_enviados": 1024
  }
}
```

**Campos Obrigatórios:** `acao`, `ip`
**Ações Válidas:** `login`, `logout`, `create`, `read`, `update`, `delete`, `error`

#### GET `/api/logs`
Lista logs de acesso.

**Query Parameters:**
- `cliente_id` (string): Filtrar por cliente
- `acao` (string): Filtrar por ação
- `ip` (string): Filtrar por IP
- `data_inicio` (datetime): Data inicial
- `data_fim` (datetime): Data final

#### GET `/api/clientes/{id}/logs`
Lista logs de um cliente específico.

---

## Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | Sucesso |
| 201 | Criado com sucesso |
| 400 | Dados inválidos |
| 404 | Não encontrado |
| 422 | Erro de validação |
| 500 | Erro interno do servidor |

## Exemplos de Uso

### Criar Cliente e Transação

```bash
# 1. Criar cliente
curl -X POST "http://localhost:8000/api/clientes" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria Silva",
    "email": "maria@teste.com",
    "cpf": "11144477735",
    "telefone": "11987654321"
  }'

# Response: {"id": "507f1f77bcf86cd799439011", ...}

# 2. Criar transação
curl -X POST "http://localhost:8000/api/transacoes" \
  -H "Content-Type: application/json" \
  -d '{
    "id_cliente": "507f1f77bcf86cd799439011",
    "valor": 100.0,
    "tipo": "pix",
    "descricao": "Teste PIX"
  }'
```

### Consultar Dados

```bash
# Listar clientes
curl "http://localhost:8000/api/clientes"

# Buscar transações de um cliente
curl "http://localhost:8000/api/clientes/507f1f77bcf86cd799439011/transacoes"

# Filtrar transações por tipo
curl "http://localhost:8000/api/transacoes?tipo=pix"
```

## Modelos de Dados

### Cliente
- `id`: ObjectId (MongoDB)
- `nome`: String (2-100 chars)
- `email`: String (formato email)
- `cpf`: String (11 dígitos, validado)
- `telefone`: String (10-11 dígitos, opcional)
- `endereco`: String (até 200 chars, opcional)
- `data_nascimento`: DateTime (opcional)
- `status`: Enum (ativo/inativo/suspenso)
- `data_criacao`: DateTime (auto)

### Transação
- `id`: ObjectId
- `id_cliente`: ObjectId (referência)
- `valor`: Float (positivo)
- `tipo`: Enum (credito/debito/pix/transferencia/boleto)
- `status`: Enum (pendente/aprovada/rejeitada/cancelada)
- `data`: DateTime (auto)
- `descricao`: String (até 200 chars, opcional)
- `metadados`: Dict (opcional)

### Log de Acesso
- `id`: ObjectId
- `id_cliente`: ObjectId (opcional)
- `timestamp`: DateTime (auto)
- `acao`: Enum (login/logout/create/read/update/delete/error)
- `ip`: String (formato IPv4)
- `user_agent`: String (opcional)
- `endpoint`: String (opcional)
- `status_code`: Integer (100-599, opcional)
- `detalhes`: Dict (opcional)

## Documentação Interativa

Acesse `http://localhost:8000/docs` para:
- Interface Swagger UI
- Testar endpoints diretamente
- Ver schemas detalhados
- Exemplos de requisição/resposta