import logging
from instagram_api import InstagramAPI
from models import Client
from client_manager import ClientManager
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageHandler:
    """Gerencia respostas automáticas para mensagens - Multi-tenant"""
    
    def __init__(self, client: Client, db: Session, client_manager: ClientManager):
        self.client = client
        self.db = db
        self.client_manager = client_manager
        self.api = InstagramAPI(client)
    
    def process_message(self, sender_id: str, message_text: str):
        """
        Processa mensagem recebida e envia resposta personalizada
        
        Args:
            sender_id: ID de quem enviou a mensagem
            message_text: Texto da mensagem
        """
        logger.info(f"[Cliente {self.client.id}] Processando mensagem de {sender_id}: {message_text}")
        
        # Verifica rate limit
        if not self.client_manager.check_rate_limit(self.client.id):
            logger.warning(f"[Cliente {self.client.id}] Limite diário de mensagens excedido!")
            return
        
        # Verifica se auto-reply está habilitado
        if not self.client.auto_reply_enabled:
            logger.info(f"[Cliente {self.client.id}] Auto-reply desabilitado")
            return
        
        # Converte para minúsculo para análise
        text_lower = message_text.lower()
        
        # Usa respostas personalizadas do cliente se disponíveis
        custom_responses = self.client.custom_responses or {}
        
        response = None
        
        # Verifica respostas customizadas primeiro
        for keyword, custom_response in custom_responses.items():
            if keyword.lower() in text_lower:
                response = custom_response
                break
        
        # Se não houver resposta customizada, usa lógica padrão
        if not response:
            response = self._get_default_response(text_lower)
        
        # Envia resposta
        try:
            result = self.api.send_message(sender_id, response)
            
            # Registra mensagem no banco
            self.client_manager.log_message(
                client_id=self.client.id,
                recipient_id=sender_id,
                message_type='dm',
                message_text=response,
                sent=bool(result)
            )
        except Exception as e:
            logger.error(f"[Cliente {self.client.id}] Erro ao enviar mensagem: {e}")
            self.client_manager.log_message(
                client_id=self.client.id,
                recipient_id=sender_id,
                message_type='dm',
                message_text=response,
                sent=False,
                error=str(e)
            )
    
    def _get_default_response(self, text_lower: str) -> str:
        """Retorna resposta padrão baseada em palavras-chave"""
        
        if any(word in text_lower for word in ['oi', 'olá', 'ola', 'hey', 'boa']):
            return "Olá! 👋 Como posso ajudar você hoje?"
        
        elif any(word in text_lower for word in ['preço', 'preco', 'valor', 'quanto custa']):
            return "📋 Para informações sobre preços, nossa equipe te enviará todos os detalhes em breve!"
        
        elif any(word in text_lower for word in ['horário', 'horario', 'atendimento']):
            return "🕐 Nosso horário de atendimento:\nSeg-Sex: 9h às 18h\nSáb: 9h às 13h"
        
        elif any(word in text_lower for word in ['catálogo', 'catalogo', 'produtos']):
            return "📸 Vou te enviar nosso catálogo completo!"
        
        elif any(word in text_lower for word in ['contato', 'telefone', 'whatsapp']):
            return "📞 Entre em contato conosco pelos nossos canais oficiais!"
        
        else:
            return "Obrigado pela sua mensagem! 🙂 Em breve retornaremos."
    
    def send_media(self, sender_id: str, media_url: str, media_type: str = 'image'):
        """Envia mídia para destinatário"""
        try:
            result = self.api.send_media(sender_id, media_url, media_type)
            
            self.client_manager.log_message(
                client_id=self.client.id,
                recipient_id=sender_id,
                message_type='dm',
                media_url=media_url,
                sent=bool(result)
            )
            return result
        except Exception as e:
            logger.error(f"[Cliente {self.client.id}] Erro ao enviar mídia: {e}")
            return None


class CommentHandler:
    """Gerencia respostas automáticas para comentários - Multi-tenant"""
    
    def __init__(self, client: Client, db: Session, client_manager: ClientManager):
        self.client = client
        self.db = db
        self.client_manager = client_manager
        self.api = InstagramAPI(client)
    
    def process_comment(self, comment_id: str, comment_text: str, username: str):
        """
        Processa comentário e responde se contiver palavras-chave do cliente
        
        Args:
            comment_id: ID do comentário
            comment_text: Texto do comentário
            username: Usuário que comentou
        """
        logger.info(f"[Cliente {self.client.id}] Processando comentário de @{username}: {comment_text}")
        
        # Verifica rate limit
        if not self.client_manager.check_rate_limit(self.client.id):
            logger.warning(f"[Cliente {self.client.id}] Limite diário de mensagens excedido!")
            return
        
        # Verifica se auto-reply está habilitado
        if not self.client.auto_reply_enabled:
            return
        
        text_lower = comment_text.lower()
        
        # Usa keywords do cliente
        client_keywords = self.client.keywords or []
        should_reply = any(keyword.lower() in text_lower for keyword in client_keywords)
        
        if should_reply:
            response = self._generate_comment_response(text_lower, username)
            
            try:
                result = self.api.reply_to_comment(comment_id, response)
                
                self.client_manager.log_message(
                    client_id=self.client.id,
                    recipient_id=username,
                    message_type='comment',
                    message_text=response,
                    sent=bool(result)
                )
                
                logger.info(f"[Cliente {self.client.id}] Resposta enviada ao comentário {comment_id}")
            except Exception as e:
                logger.error(f"[Cliente {self.client.id}] Erro ao responder comentário: {e}")
        else:
            logger.info(f"[Cliente {self.client.id}] Comentário não contém keywords configuradas")
    
    def _generate_comment_response(self, text_lower: str, username: str) -> str:
        """Gera resposta personalizada para comentário"""
        
        if any(word in text_lower for word in ['preço', 'preco', 'valor']):
            return f"@{username} Oi! Enviamos os preços por DM! 📩"
        
        elif any(word in text_lower for word in ['orçamento', 'orcamento']):
            return f"@{username} Olá! Vamos te enviar um orçamento personalizado por DM! 💼"
        
        elif any(word in text_lower for word in ['informação', 'informacao', 'info']):
            return f"@{username} Oi! Te enviamos todas as informações por DM! ✉️"
        
        elif any(word in text_lower for word in ['contato', 'whatsapp']):
            return f"@{username} Te respondemos por DM! 📱"
        
        else:
            return f"@{username} Olá! Vamos te responder por DM! 😊"


class StoryMentionHandler:
    """Gerencia menções em stories - Multi-tenant"""
    
    def __init__(self, client: Client, db: Session, client_manager: ClientManager):
        self.client = client
        self.db = db
        self.client_manager = client_manager
        self.api = InstagramAPI(client)
    
    def process_mention(self, sender_id: str, media_id: str):
        """Processa menção em story"""
        logger.info(f"[Cliente {self.client.id}] Menção em story de {sender_id}")
        
        if not self.client.auto_reply_enabled:
            return
        
        response = "Obrigado por compartilhar! 🙏✨"
        
        try:
            result = self.api.send_message(sender_id, response)
            
            self.client_manager.log_message(
                client_id=self.client.id,
                recipient_id=sender_id,
                message_type='story_mention',
                message_text=response,
                sent=bool(result)
            )
        except Exception as e:
            logger.error(f"[Cliente {self.client.id}] Erro ao responder menção: {e}")
