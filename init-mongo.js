// Script de inicialização MongoDB para MonitorDB
// Cria usuários e configurações necessárias

// Conectar ao banco monitordb
db = db.getSiblingDB('monitordb');

// Criar usuário de aplicação
db.createUser({
  user: 'monitordb_user',
  pwd: 'monitordb_pass',
  roles: [
    {
      role: 'readWrite',
      db: 'monitordb'
    }
  ]
});

// Criar coleções principais com validação
db.createCollection('clientes', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['nome', 'cpf', 'email'],
      properties: {
        nome: {
          bsonType: 'string',
          description: 'Nome do cliente é obrigatório'
        },
        cpf: {
          bsonType: 'string',
          pattern: '^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$',
          description: 'CPF deve ter formato válido'
        },
        email: {
          bsonType: 'string',
          description: 'Email é obrigatório'
        },
        telefone: {
          bsonType: 'string'
        },
        endereco: {
          bsonType: 'object',
          properties: {
            logradouro: { bsonType: 'string' },
            numero: { bsonType: 'string' },
            bairro: { bsonType: 'string' },
            cidade: { bsonType: 'string' },
            estado: { bsonType: 'string' },
            cep: { bsonType: 'string' }
          }
        },
        status: {
          bsonType: 'string',
          enum: ['ativo', 'inativo', 'suspenso']
        },
        data_cadastro: {
          bsonType: 'date'
        }
      }
    }
  }
});

db.createCollection('transacoes', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['cliente_id', 'tipo', 'valor', 'data'],
      properties: {
        cliente_id: {
          bsonType: 'objectId',
          description: 'ID do cliente é obrigatório'
        },
        tipo: {
          bsonType: 'string',
          enum: ['deposito', 'saque', 'transferencia', 'pix'],
          description: 'Tipo de transação deve ser válido'
        },
        valor: {
          bsonType: 'number',
          minimum: 0.01,
          description: 'Valor deve ser positivo'
        },
        descricao: {
          bsonType: 'string'
        },
        data: {
          bsonType: 'date'
        },
        status: {
          bsonType: 'string',
          enum: ['pendente', 'processada', 'cancelada', 'estornada']
        }
      }
    }
  }
});

db.createCollection('logs_acesso', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['timestamp', 'method', 'path', 'status_code'],
      properties: {
        timestamp: {
          bsonType: 'date'
        },
        method: {
          bsonType: 'string'
        },
        path: {
          bsonType: 'string'
        },
        status_code: {
          bsonType: 'int'
        },
        response_time: {
          bsonType: 'number'
        },
        user_agent: {
          bsonType: 'string'
        },
        ip_address: {
          bsonType: 'string'
        }
      }
    }
  }
});

// Criar usuários de teste
db.users.insertMany([
  {
    username: 'admin',
    password_hash: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5w6d8.RChm', // admin123
    role: 'admin',
    active: true,
    created_at: new Date()
  },
  {
    username: 'manager',
    password_hash: '$2b$12$8.T7GqkPmov/AI3pEO5mqOyV8XPLgqGFRmqUyH4KcxSLNqE7E/.Q2', // manager123
    role: 'manager',
    active: true,
    created_at: new Date()
  },
  {
    username: 'operator',
    password_hash: '$2b$12$9YHYtWLNjzh8G9vE8RmJeO5X4SZ6gZVYjKpQrL8BsNm3Qp.JvX7Ke', // operator123
    role: 'operator',
    active: true,
    created_at: new Date()
  }
]);

// Criar índices para performance
db.clientes.createIndex({ 'cpf': 1 }, { unique: true });
db.clientes.createIndex({ 'email': 1 });
db.clientes.createIndex({ 'status': 1 });
db.clientes.createIndex({ 'data_cadastro': 1 });

db.transacoes.createIndex({ 'cliente_id': 1 });
db.transacoes.createIndex({ 'tipo': 1 });
db.transacoes.createIndex({ 'data': 1 });
db.transacoes.createIndex({ 'status': 1 });
db.transacoes.createIndex({ 'cliente_id': 1, 'data': -1 });

db.logs_acesso.createIndex({ 'timestamp': 1 });
db.logs_acesso.createIndex({ 'method': 1, 'path': 1 });
db.logs_acesso.createIndex({ 'status_code': 1 });

db.users.createIndex({ 'username': 1 }, { unique: true });

// Inserir dados de exemplo
db.clientes.insertMany([
  {
    nome: 'João Silva Santos',
    cpf: '123.456.789-00',
    email: 'joao.silva@email.com',
    telefone: '(11) 99999-9999',
    endereco: {
      logradouro: 'Rua das Flores, 123',
      bairro: 'Centro',
      cidade: 'São Paulo',
      estado: 'SP',
      cep: '01234-567'
    },
    status: 'ativo',
    data_cadastro: new Date()
  },
  {
    nome: 'Maria Oliveira Costa',
    cpf: '987.654.321-00',
    email: 'maria.oliveira@email.com',
    telefone: '(11) 88888-8888',
    endereco: {
      logradouro: 'Av. Principal, 456',
      bairro: 'Jardim das Rosas',
      cidade: 'São Paulo',
      estado: 'SP',
      cep: '04567-890'
    },
    status: 'ativo',
    data_cadastro: new Date()
  },
  {
    nome: 'Carlos Roberto Ferreira',
    cpf: '456.789.123-00',
    email: 'carlos.ferreira@email.com',
    telefone: '(11) 77777-7777',
    endereco: {
      logradouro: 'Rua da Paz, 789',
      bairro: 'Vila Nova',
      cidade: 'São Paulo',
      estado: 'SP',
      cep: '02345-678'
    },
    status: 'ativo',
    data_cadastro: new Date()
  }
]);

// Buscar IDs dos clientes para criar transações
const clientes = db.clientes.find({}).toArray();

if (clientes.length > 0) {
  db.transacoes.insertMany([
    {
      cliente_id: clientes[0]._id,
      tipo: 'deposito',
      valor: 1000.00,
      descricao: 'Depósito inicial',
      data: new Date(),
      status: 'processada'
    },
    {
      cliente_id: clientes[0]._id,
      tipo: 'saque',
      valor: 200.00,
      descricao: 'Saque em ATM',
      data: new Date(),
      status: 'processada'
    },
    {
      cliente_id: clientes[1]._id,
      tipo: 'deposito',
      valor: 1500.00,
      descricao: 'Depósito salário',
      data: new Date(),
      status: 'processada'
    },
    {
      cliente_id: clientes[1]._id,
      tipo: 'pix',
      valor: 300.00,
      descricao: 'Transferência PIX',
      data: new Date(),
      status: 'processada'
    },
    {
      cliente_id: clientes[2]._id,
      tipo: 'deposito',
      valor: 800.00,
      descricao: 'Depósito inicial',
      data: new Date(),
      status: 'processada'
    }
  ]);
}

print('✅ MonitorDB inicializado com sucesso!');
print('📊 Usuários criados: admin, manager, operator');
print('👥 ' + db.clientes.count() + ' clientes de exemplo inseridos');
print('💰 ' + db.transacoes.count() + ' transações de exemplo inseridas');
print('🔍 Índices criados para otimização de consultas');
print('🛡️  Validações de schema configuradas');