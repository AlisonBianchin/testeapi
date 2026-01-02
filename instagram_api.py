import requests
import logging
from models import Client
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramAPI:
    """Classe para interagir com a Instagram Graph API - Multi-tenant"""
    
    def __init__(self, client: Client):
        """
        Inicializa API com credenciais do cliente
        
        Args:
            client: Objeto Client do banco de dados
        """
        self.client = client
        self.base_url = 'https://graph.facebook.com/v18.0'
        self.access_token = client.access_token
        self.account_id = client.instagram_account_id
    
    def _make_request(self, method, endpoint, **kwargs):
        """Faz requisição para a API"""
        url = f"{self.base_url}/{endpoint}"
        
        # Adiciona access_token aos parâmetros
        params = kwargs.get('params', {})
        params['access_token'] = self.access_token
        kwargs['params'] = params
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[Cliente {self.client.id}] Erro na requisição: {e}")
            return None
    
    def send_message(self, recipient_id, message_text):
        """Envia mensagem de texto via DM"""
        endpoint = f"{self.account_id}/messages"
        
        data = {
            'recipient': {'id': recipient_id},
            'message': {'text': message_text}
        }
        
        result = self._make_request('POST', endpoint, json=data)
        if result:
            logger.info(f"[Cliente {self.client.id}] Mensagem enviada para {recipient_id}")
        return result
    
    def send_media(self, recipient_id, media_url, media_type='image'):
        """
        Envia mídia via DM
        
        Args:
            recipient_id: ID do destinatário
            media_url: URL pública da mídia
            media_type: 'image', 'video', 'audio'
        """
        endpoint = f"{self.account_id}/messages"
        
        attachment = {
            'type': media_type,
            'payload': {'url': media_url}
        }
        
        data = {
            'recipient': {'id': recipient_id},
            'message': {'attachment': attachment}
        }
        
        result = self._make_request('POST', endpoint, json=data)
        if result:
            logger.info(f"[Cliente {self.client.id}] Mídia ({media_type}) enviada para {recipient_id}")
        return result
    
    def send_file(self, recipient_id, file_url):
        """Envia documento/arquivo via DM"""
        return self.send_media(recipient_id, file_url, media_type='file')
    
    def send_audio(self, recipient_id, audio_url):
        """Envia áudio via DM"""
        return self.send_media(recipient_id, audio_url, media_type='audio')
    
    def reply_to_comment(self, comment_id, message_text):
        """Responde a um comentário"""
        endpoint = f"{comment_id}/replies"
        
        data = {
            'message': message_text
        }
        
        result = self._make_request('POST', endpoint, params=data)
        if result:
            logger.info(f"[Cliente {self.client.id}] Resposta enviada ao comentário {comment_id}")
        return result
    
    def get_comment_details(self, comment_id):
        """Obtém detalhes de um comentário"""
        endpoint = f"{comment_id}"
        params = {
            'fields': 'text,username,timestamp,media'
        }
        
        return self._make_request('GET', endpoint, params=params)
    
    def get_conversation(self, conversation_id):
        """Obtém detalhes de uma conversa"""
        endpoint = f"{conversation_id}"
        params = {
            'fields': 'messages{message,from,created_time}'
        }
        
        return self._make_request('GET', endpoint, params=params)
    
    def mark_as_read(self, message_id):
        """Marca mensagem como lida"""
        endpoint = f"{self.account_id}/messages"
        
        data = {
            'recipient': {'id': message_id}
        }
        
        return self._make_request('POST', endpoint, json=data)
