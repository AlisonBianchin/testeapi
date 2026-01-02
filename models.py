from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Client(Base):
    """Modelo de Cliente - cada cliente representa uma conta Instagram"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # Nome do cliente/empresa
    email = Column(String(255), unique=True, nullable=False)  # Email de contato
    
    # Credenciais Instagram Graph API
    access_token = Column(Text, nullable=False)  # Long-lived token
    instagram_account_id = Column(String(255), nullable=False)
    page_id = Column(String(255), nullable=False)
    
    # Webhook
    verify_token = Column(String(255), nullable=False)  # Token único por cliente
    
    # Configurações personalizadas
    keywords = Column(JSON, default=list)  # Lista de keywords para monitorar
    auto_reply_enabled = Column(Boolean, default=True)  # Auto-resposta ativada
    
    # Mensagens personalizadas (JSON)
    custom_responses = Column(JSON, default=dict)  # Respostas customizadas
    
    # Status e controle
    active = Column(Boolean, default=True)  # Cliente ativo/inativo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Rate limiting
    daily_message_limit = Column(Integer, default=1000)  # Limite diário de mensagens
    messages_sent_today = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', email='{self.email}')>"
    
    def to_dict(self):
        """Converte para dicionário (para API)"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'instagram_account_id': self.instagram_account_id,
            'keywords': self.keywords,
            'auto_reply_enabled': self.auto_reply_enabled,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'daily_message_limit': self.daily_message_limit,
            'messages_sent_today': self.messages_sent_today
        }


class Message(Base):
    """Histórico de mensagens enviadas"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, nullable=False)  # FK para Client
    
    # Dados da mensagem
    recipient_id = Column(String(255), nullable=False)  # ID do destinatário
    message_type = Column(String(50), nullable=False)  # 'dm', 'comment', 'story_mention'
    message_text = Column(Text)
    media_url = Column(String(500))
    
    # Status
    sent = Column(Boolean, default=False)
    error = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Message(id={self.id}, client_id={self.client_id}, type='{self.message_type}')>"


class Webhook(Base):
    """Log de webhooks recebidos"""
    __tablename__ = 'webhooks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer)  # FK para Client (pode ser null se não identificado)
    
    # Dados do webhook
    event_type = Column(String(50), nullable=False)  # 'message', 'comment', etc
    payload = Column(JSON, nullable=False)  # Payload completo do webhook
    
    # Status de processamento
    processed = Column(Boolean, default=False)
    error = Column(Text)
    
    # Timestamp
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, type='{self.event_type}', processed={self.processed})>"


class ApiKey(Base):
    """Chaves de API para autenticação de clientes"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, nullable=False)  # FK para Client
    
    key = Column(String(255), unique=True, nullable=False)  # API Key
    name = Column(String(255))  # Nome/descrição da chave
    
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, client_id={self.client_id}, name='{self.name}')>"
