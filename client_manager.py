import secrets
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Client, Message, Webhook, ApiKey
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClientManager:
    """Gerenciador de clientes do sistema multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_client(
        self,
        name: str,
        email: str,
        access_token: str,
        instagram_account_id: str,
        page_id: str,
        keywords: List[str] = None,
        custom_responses: Dict = None,
        daily_limit: int = 1000
    ) -> Client:
        """
        Cria um novo cliente no sistema
        
        Args:
            name: Nome do cliente/empresa
            email: Email de contato
            access_token: Token da Graph API
            instagram_account_id: ID da conta Instagram
            page_id: ID da página do Facebook
            keywords: Lista de palavras-chave para monitorar
            custom_responses: Dicionário com respostas personalizadas
            daily_limit: Limite diário de mensagens
        
        Returns:
            Client object criado
        """
        try:
            # Verifica se email já existe
            existing = self.db.query(Client).filter(Client.email == email).first()
            if existing:
                raise ValueError(f"Cliente com email {email} já existe!")
            
            # Gera verify_token único para webhooks
            verify_token = secrets.token_urlsafe(32)
            
            # Cria cliente
            client = Client(
                name=name,
                email=email,
                access_token=access_token,
                instagram_account_id=instagram_account_id,
                page_id=page_id,
                verify_token=verify_token,
                keywords=keywords or [],
                custom_responses=custom_responses or {},
                daily_message_limit=daily_limit
            )
            
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            
            logger.info(f"✅ Cliente criado: {name} (ID: {client.id})")
            return client
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro ao criar cliente: {e}")
            raise
    
    def get_client(self, client_id: int) -> Optional[Client]:
        """Busca cliente por ID"""
        return self.db.query(Client).filter(Client.id == client_id).first()
    
    def get_client_by_email(self, email: str) -> Optional[Client]:
        """Busca cliente por email"""
        return self.db.query(Client).filter(Client.email == email).first()
    
    def get_client_by_instagram_id(self, instagram_account_id: str) -> Optional[Client]:
        """Busca cliente por Instagram Account ID"""
        return self.db.query(Client).filter(
            Client.instagram_account_id == instagram_account_id
        ).first()
    
    def get_client_by_verify_token(self, verify_token: str) -> Optional[Client]:
        """Busca cliente por verify token (usado em webhooks)"""
        return self.db.query(Client).filter(
            Client.verify_token == verify_token
        ).first()
    
    def list_clients(self, active_only: bool = True) -> List[Client]:
        """Lista todos os clientes"""
        query = self.db.query(Client)
        if active_only:
            query = query.filter(Client.active == True)
        return query.all()
    
    def update_client(self, client_id: int, **kwargs) -> Optional[Client]:
        """
        Atualiza dados do cliente
        
        Args:
            client_id: ID do cliente
            **kwargs: Campos a serem atualizados
        """
        try:
            client = self.get_client(client_id)
            if not client:
                logger.warning(f"Cliente {client_id} não encontrado")
                return None
            
            for key, value in kwargs.items():
                if hasattr(client, key):
                    setattr(client, key, value)
            
            client.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(client)
            
            logger.info(f"✅ Cliente {client_id} atualizado")
            return client
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro ao atualizar cliente: {e}")
            raise
    
    def deactivate_client(self, client_id: int) -> bool:
        """Desativa cliente (soft delete)"""
        return self.update_client(client_id, active=False) is not None
    
    def activate_client(self, client_id: int) -> bool:
        """Ativa cliente"""
        return self.update_client(client_id, active=True) is not None
    
    def delete_client(self, client_id: int) -> bool:
        """Remove cliente permanentemente (CUIDADO!)"""
        try:
            client = self.get_client(client_id)
            if not client:
                return False
            
            # Remove API keys associadas
            self.db.query(ApiKey).filter(ApiKey.client_id == client_id).delete()
            
            # Remove mensagens associadas
            self.db.query(Message).filter(Message.client_id == client_id).delete()
            
            # Remove webhooks associados
            self.db.query(Webhook).filter(Webhook.client_id == client_id).delete()
            
            # Remove cliente
            self.db.delete(client)
            self.db.commit()
            
            logger.info(f"✅ Cliente {client_id} removido permanentemente")
            return True
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro ao deletar cliente: {e}")
            return False
    
    def check_rate_limit(self, client_id: int) -> bool:
        """
        Verifica se cliente ainda pode enviar mensagens hoje
        
        Returns:
            True se ainda pode enviar, False se excedeu limite
        """
        client = self.get_client(client_id)
        if not client:
            return False
        
        # Reset contador se for novo dia
        today = datetime.utcnow().date()
        last_reset = client.last_reset_date.date() if client.last_reset_date else None
        
        if last_reset != today:
            client.messages_sent_today = 0
            client.last_reset_date = datetime.utcnow()
            self.db.commit()
        
        # Verifica limite
        return client.messages_sent_today < client.daily_message_limit
    
    def increment_message_count(self, client_id: int):
        """Incrementa contador de mensagens enviadas"""
        client = self.get_client(client_id)
        if client:
            client.messages_sent_today += 1
            self.db.commit()
    
    def log_message(
        self,
        client_id: int,
        recipient_id: str,
        message_type: str,
        message_text: str = None,
        media_url: str = None,
        sent: bool = True,
        error: str = None
    ) -> Message:
        """Registra mensagem enviada no histórico"""
        try:
            message = Message(
                client_id=client_id,
                recipient_id=recipient_id,
                message_type=message_type,
                message_text=message_text,
                media_url=media_url,
                sent=sent,
                error=error
            )
            
            self.db.add(message)
            self.db.commit()
            
            if sent:
                self.increment_message_count(client_id)
            
            return message
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro ao registrar mensagem: {e}")
            raise
    
    def log_webhook(
        self,
        event_type: str,
        payload: dict,
        client_id: int = None
    ) -> Webhook:
        """Registra webhook recebido"""
        try:
            webhook = Webhook(
                client_id=client_id,
                event_type=event_type,
                payload=payload
            )
            
            self.db.add(webhook)
            self.db.commit()
            
            return webhook
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro ao registrar webhook: {e}")
            raise
    
    def mark_webhook_processed(self, webhook_id: int, error: str = None):
        """Marca webhook como processado"""
        webhook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if webhook:
            webhook.processed = True
            webhook.processed_at = datetime.utcnow()
            if error:
                webhook.error = error
            self.db.commit()
    
    def generate_api_key(self, client_id: int, name: str = "Default") -> ApiKey:
        """Gera API key para autenticação do cliente"""
        try:
            key = f"sk_{secrets.token_urlsafe(48)}"
            
            api_key = ApiKey(
                client_id=client_id,
                key=key,
                name=name
            )
            
            self.db.add(api_key)
            self.db.commit()
            self.db.refresh(api_key)
            
            logger.info(f"✅ API Key gerada para cliente {client_id}")
            return api_key
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erro ao gerar API key: {e}")
            raise
    
    def validate_api_key(self, key: str) -> Optional[Client]:
        """Valida API key e retorna cliente associado"""
        api_key = self.db.query(ApiKey).filter(
            ApiKey.key == key,
            ApiKey.active == True
        ).first()
        
        if not api_key:
            return None
        
        # Atualiza último uso
        api_key.last_used_at = datetime.utcnow()
        self.db.commit()
        
        return self.get_client(api_key.client_id)
    
    def get_client_stats(self, client_id: int) -> Dict:
        """Retorna estatísticas do cliente"""
        client = self.get_client(client_id)
        if not client:
            return {}
        
        total_messages = self.db.query(Message).filter(
            Message.client_id == client_id
        ).count()
        
        messages_today = self.db.query(Message).filter(
            Message.client_id == client_id,
            Message.created_at >= datetime.utcnow().date()
        ).count()
        
        webhooks_received = self.db.query(Webhook).filter(
            Webhook.client_id == client_id
        ).count()
        
        return {
            'client_id': client_id,
            'name': client.name,
            'total_messages': total_messages,
            'messages_today': messages_today,
            'webhooks_received': webhooks_received,
            'active': client.active,
            'daily_limit': client.daily_message_limit,
            'limit_remaining': client.daily_message_limit - client.messages_sent_today
        }
