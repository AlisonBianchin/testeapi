from flask import Flask, request, jsonify
import logging
from database import SessionLocal, init_db
from client_manager import ClientManager
from handlers import MessageHandler, CommentHandler, StoryMentionHandler
from functools import wraps

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializa Flask
app = Flask(__name__)

# Inicializa banco de dados
init_db()
logger.info("✅ Sistema multi-tenant inicializado")


def get_db_session():
    """Retorna sessão do banco"""
    return SessionLocal()


def require_api_key(f):
    """Decorator para rotas que requerem autenticação via API Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API Key required'}), 401
        
        db = get_db_session()
        manager = ClientManager(db)
        
        client = manager.validate_api_key(api_key)
        if not client:
            db.close()
            return jsonify({'error': 'Invalid API Key'}), 401
        
        db.close()
        return f(*args, **kwargs, client=client)
    
    return decorated_function


@app.route('/')
def home():
    """Rota inicial"""
    return jsonify({
        'status': 'online',
        'service': 'Instagram Agent Multi-Tenant',
        'version': '2.0.0',
        'features': [
            'Multi-client support',
            'Custom responses per client',
            'Rate limiting',
            'Webhook management',
            'Analytics'
        ]
    })


# ========== WEBHOOKS ==========

@app.route('/webhook/<verify_token>', methods=['GET'])
def webhook_verify(verify_token):
    """
    Verificação do webhook por cliente
    Cada cliente tem seu próprio verify_token único
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    db = get_db_session()
    manager = ClientManager(db)
    
    # Busca cliente pelo verify_token da URL
    client = manager.get_client_by_verify_token(verify_token)
    
    if not client:
        logger.warning(f"Verify token inválido: {verify_token}")
        db.close()
        return 'Forbidden', 403
    
    if mode == 'subscribe' and token == verify_token:
        logger.info(f"✅ Webhook verificado para cliente {client.id} ({client.name})")
        db.close()
        return challenge, 200
    else:
        logger.warning(f"Falha na verificação do webhook para cliente {client.id}")
        db.close()
        return 'Forbidden', 403


@app.route('/webhook/<verify_token>', methods=['POST'])
def webhook_receive(verify_token):
    """
    Recebe eventos do Instagram via webhook
    Roteado automaticamente para o cliente correto
    """
    try:
        data = request.get_json()
        
        db = get_db_session()
        manager = ClientManager(db)
        
        # Identifica cliente pelo verify_token
        client = manager.get_client_by_verify_token(verify_token)
        
        if not client:
            logger.warning(f"Cliente não encontrado para verify_token: {verify_token}")
            db.close()
            return 'Forbidden', 403
        
        if not client.active:
            logger.warning(f"Cliente {client.id} está desativado")
            db.close()
            return 'CLIENT_INACTIVE', 200
        
        logger.info(f"[Cliente {client.id}] Webhook recebido")
        
        # Log webhook
        webhook = manager.log_webhook(
            event_type='instagram_event',
            payload=data,
            client_id=client.id
        )
        
        # Processa cada entrada
        if 'entry' in data:
            for entry in data['entry']:
                process_entry(entry, client, db, manager)
        
        # Marca webhook como processado
        manager.mark_webhook_processed(webhook.id)
        
        db.close()
        return 'EVENT_RECEIVED', 200
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        if 'db' in locals():
            db.close()
        return 'ERROR', 500


def process_entry(entry, client, db, manager):
    """Processa cada entrada do webhook para um cliente específico"""
    
    # Processa mensagens
    if 'messaging' in entry:
        for messaging_event in entry['messaging']:
            process_messaging_event(messaging_event, client, db, manager)
    
    # Processa comentários
    if 'changes' in entry:
        for change in entry['changes']:
            process_change_event(change, client, db, manager)


def process_messaging_event(event, client, db, manager):
    """Processa eventos de mensagem"""
    sender_id = event.get('sender', {}).get('id')
    
    # Inicializa handler com contexto do cliente
    message_handler = MessageHandler(client, db, manager)
    
    # Mensagem de texto
    if 'message' in event:
        message = event['message']
        
        # Ignora mensagens enviadas pelo próprio bot
        if 'is_echo' in message:
            return
        
        message_text = message.get('text', '')
        
        if message_text:
            logger.info(f"[Cliente {client.id}] Nova mensagem de {sender_id}: {message_text}")
            message_handler.process_message(sender_id, message_text)
    
    # Menção em story
    elif 'story_mention' in event:
        story_mention = event['story_mention']
        media_id = story_mention.get('id')
        
        story_handler = StoryMentionHandler(client, db, manager)
        story_handler.process_mention(sender_id, media_id)


def process_change_event(change, client, db, manager):
    """Processa eventos de mudança (comentários, etc)"""
    field = change.get('field')
    value = change.get('value')
    
    # Comentário
    if field == 'comments':
        comment_id = value.get('id')
        comment_text = value.get('text', '')
        username = value.get('from', {}).get('username', 'unknown')
        
        comment_handler = CommentHandler(client, db, manager)
        comment_handler.process_comment(comment_id, comment_text, username)
    
    # Menção em post
    elif field == 'mentions':
        logger.info(f"[Cliente {client.id}] Menção em post detectada")


# ========== API DE GERENCIAMENTO ==========

@app.route('/api/clients', methods=['GET'])
def list_clients():
    """Lista todos os clientes (sem autenticação - para admin)"""
    db = get_db_session()
    manager = ClientManager(db)
    
    clients = manager.list_clients(active_only=False)
    result = [client.to_dict() for client in clients]
    
    db.close()
    return jsonify(result)


@app.route('/api/clients', methods=['POST'])
def create_client():
    """
    Cria novo cliente
    POST /api/clients
    Body: {
        "name": "Nome da Empresa",
        "email": "email@empresa.com",
        "access_token": "token_instagram",
        "instagram_account_id": "123456",
        "page_id": "789012",
        "keywords": ["preço", "contato"],
        "custom_responses": {"preço": "Mensagem customizada"}
    }
    """
    try:
        data = request.get_json()
        
        db = get_db_session()
        manager = ClientManager(db)
        
        client = manager.create_client(
            name=data['name'],
            email=data['email'],
            access_token=data['access_token'],
            instagram_account_id=data['instagram_account_id'],
            page_id=data['page_id'],
            keywords=data.get('keywords', []),
            custom_responses=data.get('custom_responses', {}),
            daily_limit=data.get('daily_limit', 1000)
        )
        
        # Gera API Key para o cliente
        api_key = manager.generate_api_key(client.id, "Initial Key")
        
        db.close()
        
        return jsonify({
            'success': True,
            'client': client.to_dict(),
            'api_key': api_key.key,
            'webhook_url': f'/webhook/{client.verify_token}',
            'verify_token': client.verify_token
        }), 201
    
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {e}")
        if 'db' in locals():
            db.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Obtém detalhes de um cliente"""
    db = get_db_session()
    manager = ClientManager(db)
    
    client = manager.get_client(client_id)
    
    if not client:
        db.close()
        return jsonify({'error': 'Client not found'}), 404
    
    result = client.to_dict()
    db.close()
    
    return jsonify(result)


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """
    Atualiza dados de um cliente
    PUT /api/clients/1
    Body: {"keywords": ["nova", "palavra"]}
    """
    try:
        data = request.get_json()
        
        db = get_db_session()
        manager = ClientManager(db)
        
        client = manager.update_client(client_id, **data)
        
        if not client:
            db.close()
            return jsonify({'error': 'Client not found'}), 404
        
        result = client.to_dict()
        db.close()
        
        return jsonify({'success': True, 'client': result})
    
    except Exception as e:
        logger.error(f"Erro ao atualizar cliente: {e}")
        if 'db' in locals():
            db.close()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Desativa cliente (soft delete)"""
    db = get_db_session()
    manager = ClientManager(db)
    
    success = manager.deactivate_client(client_id)
    
    db.close()
    
    if success:
        return jsonify({'success': True, 'message': 'Client deactivated'})
    else:
        return jsonify({'error': 'Client not found'}), 404


@app.route('/api/clients/<int:client_id>/stats', methods=['GET'])
def get_client_stats(client_id):
    """Obtém estatísticas do cliente"""
    db = get_db_session()
    manager = ClientManager(db)
    
    stats = manager.get_client_stats(client_id)
    
    db.close()
    
    if not stats:
        return jsonify({'error': 'Client not found'}), 404
    
    return jsonify(stats)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check para monitoramento"""
    db = get_db_session()
    manager = ClientManager(db)
    
    total_clients = len(manager.list_clients(active_only=False))
    active_clients = len(manager.list_clients(active_only=True))
    
    db.close()
    
    return jsonify({
        'status': 'healthy',
        'total_clients': total_clients,
        'active_clients': active_clients
    })


# ========== ROTAS PROTEGIDAS (COM API KEY) ==========

@app.route('/api/send-message', methods=['POST'])
@require_api_key
def send_message(client):
    """
    Envia mensagem usando API Key do cliente
    Headers: X-API-Key: sk_...
    Body: {"recipient_id": "123", "message": "Olá!"}
    """
    try:
        data = request.get_json()
        
        db = get_db_session()
        manager = ClientManager(db)
        
        message_handler = MessageHandler(client, db, manager)
        
        recipient_id = data['recipient_id']
        message_text = data['message']
        
        result = message_handler.api.send_message(recipient_id, message_text)
        
        manager.log_message(
            client_id=client.id,
            recipient_id=recipient_id,
            message_type='dm',
            message_text=message_text,
            sent=bool(result)
        )
        
        db.close()
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        if 'db' in locals():
            db.close()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"🚀 Iniciando servidor multi-tenant na porta {port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
