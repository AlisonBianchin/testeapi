# 🤖 Instagram Agent Multi-Tenant - Sistema Escalável

**Agente inteligente para Instagram que gerencia MÚLTIPLOS CLIENTES** com respostas automáticas, configurações personalizadas e isolamento completo de dados.

## 🎯 Funcionalidades

### ✨ Multi-Tenant (Múltiplos Clientes)
- 🏢 Gerenciamento de múltiplos clientes simultaneamente
- 🔐 Isolamento completo de dados entre clientes
- ⚙️ Configurações personalizadas por cliente
- 🔑 API Keys individuais para cada cliente
- 📊 Estatísticas e analytics por cliente

### 🤖 Automação Inteligente
- ✅ **Resposta automática de DMs** com personalização por cliente
- ✅ **Resposta automática de comentários** com keywords configuráveis
- ✅ **Envio de mídia** (imagens, vídeos, áudios, documentos)
- ✅ **Rate limiting** individual por cliente
- ✅ **Webhooks em tempo real** com roteamento automático

### 📈 Gestão e Analytics
- ✅ Histórico completo de mensagens
- ✅ Log de webhooks recebidos
- ✅ Contadores e limites diários
- ✅ API REST para gerenciamento
- ✅ CLI para administração

## 🏗️ Arquitetura

```
instagram-agent/
├── app.py                  # Servidor Flask multi-tenant
├── models.py               # Modelos de dados (Client, Message, Webhook)
├── database.py             # Conexão e configuração do banco
├── client_manager.py       # CRUD e lógica de negócio
├── instagram_api.py        # Interface com Instagram Graph API
├── handlers.py             # Processadores de eventos
├── manage.py               # CLI de administração
├── config.py               # Configurações (legacy - opcional)
├── requirements.txt        # Dependências Python
└── README.md              # Esta documentação
```

## 📋 Pré-requisitos

- **Python 3.8+**
- **SQLite** (padrão) ou **PostgreSQL** (produção)
- **Instagram Graph API** configurada para cada cliente

## 🚀 Instalação

### 1. Instale dependências

```bash
pip install -r requirements.txt
```

### 2. Inicialize o banco de dados

```bash
python manage.py init
```

### 3. Adicione seu primeiro cliente

```bash
python manage.py add-client
```

Siga as instruções e forneça:
- Nome da empresa
- Email
- Access Token (Instagram Graph API)
- Instagram Account ID
- Page ID (Facebook)
- Keywords para monitorar
- Limite diário de mensagens

### 4. Inicie o servidor

```bash
python app.py
```

## 📝 Gerenciamento de Clientes

### Via CLI

```bash
# Adicionar cliente
python manage.py add-client

# Listar todos os clientes
python manage.py list-clients

# Estatísticas de um cliente
python manage.py stats

# Desativar cliente
python manage.py deactivate

# Resetar banco de dados (CUIDADO!)
python manage.py reset
```

### Via API REST

#### Criar Cliente

```bash
POST /api/clients
Content-Type: application/json

{
  "name": "Minha Empresa",
  "email": "contato@empresa.com",
  "access_token": "seu_token_instagram",
  "instagram_account_id": "123456789",
  "page_id": "987654321",
  "keywords": ["preço", "orçamento", "contato"],
  "custom_responses": {
    "preço": "Nossos preços começam em R$ 100. Entre em contato para mais detalhes!"
  },
  "daily_limit": 1000
}
```

**Resposta:**
```json
{
  "success": true,
  "client": {
    "id": 1,
    "name": "Minha Empresa",
    "email": "contato@empresa.com",
    ...
  },
  "api_key": "sk_xxxxx...",
  "webhook_url": "/webhook/abc123...",
  "verify_token": "abc123..."
}
```

#### Listar Clientes

```bash
GET /api/clients
```

#### Obter Cliente

```bash
GET /api/clients/1
```

#### Atualizar Cliente

```bash
PUT /api/clients/1
Content-Type: application/json

{
  "keywords": ["preço", "contato", "horário"],
  "auto_reply_enabled": true
}
```

#### Estatísticas do Cliente

```bash
GET /api/clients/1/stats
```

**Resposta:**
```json
{
  "client_id": 1,
  "name": "Minha Empresa",
  "total_messages": 150,
  "messages_today": 25,
  "webhooks_received": 200,
  "active": true,
  "daily_limit": 1000,
  "limit_remaining": 975
}
```

#### Desativar Cliente

```bash
DELETE /api/clients/1
```

## 🔗 Webhooks

Cada cliente tem sua própria URL de webhook **única**:

```
https://seu-dominio.com/webhook/{verify_token}
```

### Configurar no Meta for Developers

1. Vá em **Webhooks** do seu app
2. Selecione **Instagram**
3. Configure:
   - **Callback URL**: `https://seu-dominio.com/webhook/{verify_token}`
   - **Verify Token**: O `verify_token` fornecido ao criar o cliente
4. Inscreva-se nos eventos:
   - ✅ `messages`
   - ✅ `messaging_postbacks`
   - ✅ `comments`
   - ✅ `mentions`

## 🔑 Autenticação

### API Keys

Cada cliente possui sua própria API Key para enviar mensagens programaticamente:

```bash
POST /api/send-message
X-API-Key: sk_xxxxx...
Content-Type: application/json

{
  "recipient_id": "123456",
  "message": "Olá! Como podemos ajudar?"
}
```

## 🎨 Personalização por Cliente

### Respostas Customizadas

Cada cliente pode ter respostas completamente personalizadas:

```json
{
  "custom_responses": {
    "preço": "💰 Nossos valores começam em R$ 50,00!",
    "horário": "🕐 Atendemos de Seg-Sex, 9h-18h",
    "contato": "📱 WhatsApp: (11) 99999-9999"
  }
}
```

### Keywords Personalizadas

```json
{
  "keywords": ["preço", "valor", "quanto custa", "orçamento"]
}
```

Comentários contendo essas palavras recebem resposta automática.

### Rate Limiting Individual

```json
{
  "daily_limit": 500
}
```

Cada cliente tem seu próprio limite diário de mensagens.

## 📊 Banco de Dados

### SQLite (Desenvolvimento)

Por padrão, usa SQLite:
```
sqlite:///instagram_agent.db
```

### PostgreSQL (Produção)

Configure a variável de ambiente:

```bash
export DATABASE_URL="postgresql://user:password@localhost/instagram_agent"
```

### Estrutura de Tabelas

- **clients** - Dados dos clientes e credenciais
- **messages** - Histórico de mensagens enviadas
- **webhooks** - Log de webhooks recebidos
- **api_keys** - Chaves de API por cliente

## 🔒 Segurança

### Boas Práticas

1. **Nunca commite credenciais** no Git
2. Use **HTTPS** em produção
3. **Rotate API keys** regularmente
4. Implemente **autenticação adicional** para rotas de gerenciamento
5. Use **rate limiting** no nível do servidor (ex: nginx)
6. Configure **firewall** adequadamente

### Variáveis de Ambiente

```bash
# Database
export DATABASE_URL="postgresql://..."

# Server
export PORT=5000
```

## 🌐 Deploy em Produção

### Opções de Hospedagem

- **Heroku** ✅ Fácil
- **AWS EC2** ✅ Controle
- **Google Cloud Run** ✅ Escalável
- **DigitalOcean** ✅ Simples
- **Azure** ✅ Enterprise

### Deploy no Heroku (Exemplo)

```bash
# Login
heroku login

# Criar app
heroku create meu-instagram-agent

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main

# Ver logs
heroku logs --tail
```

**Procfile:**
```
web: gunicorn app:app
```

### Expor Webhooks (Desenvolvimento)

Use **ngrok** ou **localtunnel**:

```bash
# ngrok
ngrok http 5000

# Use a URL HTTPS gerada nos webhooks do Meta
# Ex: https://abc123.ngrok.io/webhook/token_do_cliente
```

## 📈 Casos de Uso

### 1. Agência de Marketing

Gerencie contas Instagram de múltiplos clientes com configurações independentes.

### 2. SaaS

Ofereça automação de Instagram como serviço (Instagram-as-a-Service).

### 3. E-commerce

Automatize atendimento para várias lojas simultaneamente.

### 4. Revendedor

Revenda soluções de automação Instagram white-label.

## 🛠️ Desenvolvimento

### Adicionar Nova Funcionalidade

1. **Crie novo campo em models.py**
```python
class Client(Base):
    new_feature = Column(Boolean, default=False)
```

2. **Atualize client_manager.py**
```python
def enable_feature(self, client_id):
    return self.update_client(client_id, new_feature=True)
```

3. **Adicione rota em app.py**
```python
@app.route('/api/clients/<int:id>/feature', methods=['POST'])
def toggle_feature(id):
    # Implementação
```

## 🐛 Troubleshooting

### Erro: "Client not found"
- Verifique se o cliente está ativo
- Confirme o ID do cliente

### Webhooks não funcionam
- Verifique se a URL está acessível publicamente
- Confirme que o verify_token está correto
- Teste a verificação do webhook manualmente

### Rate limit excedido
- Verifique `messages_sent_today` do cliente
- Ajuste `daily_limit` se necessário
- Contador reseta automaticamente todo dia

### Erro de banco de dados
- Execute `python manage.py init` para criar tabelas
- Verifique permissões do arquivo SQLite

## 📚 API Reference

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Status do servidor |
| GET | `/api/health` | Health check |
| GET | `/api/clients` | Lista clientes |
| POST | `/api/clients` | Cria cliente |
| GET | `/api/clients/:id` | Detalhes do cliente |
| PUT | `/api/clients/:id` | Atualiza cliente |
| DELETE | `/api/clients/:id` | Desativa cliente |
| GET | `/api/clients/:id/stats` | Estatísticas |
| POST | `/api/send-message` | Envia mensagem (requer API Key) |
| GET | `/webhook/:token` | Verificação webhook |
| POST | `/webhook/:token` | Recebe eventos |

## 🤝 Contribuindo

Sugestões de melhorias:

- [ ] Dashboard web (React/Vue)
- [ ] Integração com IA (GPT) para respostas
- [ ] Análise de sentimento
- [ ] Multi-idioma
- [ ] Sistema de filas (Celery/RQ)
- [ ] Cache (Redis)
- [ ] Monitoring (Prometheus)
- [ ] Backup automático

## 📄 Licença

Código aberto. Use livremente!

## ⚠️ Aviso Legal

Este sistema usa a **Instagram Graph API oficial**. Certifique-se de:
- Seguir os [Termos de Serviço do Instagram](https://help.instagram.com/581066165581870)
- Respeitar a privacidade dos usuários
- Não fazer spam
- Obter aprovação necessária do Meta

---

## 📞 Fluxo de Uso

### Para Administrador do Sistema

1. **Setup Inicial**
```bash
pip install -r requirements.txt
python manage.py init
python app.py
```

2. **Adicionar Clientes**
```bash
python manage.py add-client
# OU via API
curl -X POST http://localhost:5000/api/clients -H "Content-Type: application/json" -d '{...}'
```

3. **Monitorar**
```bash
python manage.py list-clients
python manage.py stats
```

### Para Cada Cliente

1. **Recebe credenciais**:
   - API Key
   - Webhook URL
   - Verify Token

2. **Configura no Meta for Developers**:
   - Adiciona Webhook URL
   - Configura Verify Token
   - Inscreve em eventos

3. **Personaliza (opcional)**:
   - Via API: atualiza keywords, respostas customizadas
   - Via suporte: solicita ajustes

4. **Usa API para envios manuais** (opcional):
```bash
curl -X POST http://localhost:5000/api/send-message \
  -H "X-API-Key: sk_xxxxx..." \
  -H "Content-Type: application/json" \
  -d '{"recipient_id": "123", "message": "Olá!"}'
```

---

**Desenvolvido com ❤️ usando Python, Flask e Instagram Graph API**

**Happy Coding! 🚀**

## 📖 Próximos Passos

1. **Configure primeiro cliente**
2. **Teste webhooks localmente** (ngrok)
3. **Deploy em produção**
4. **Configure monitoramento**
5. **Escale conforme necessário**

Para suporte, abra uma issue ou entre em contato!
