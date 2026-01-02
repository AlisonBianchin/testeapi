import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class Config:
    """Configurações do agente Instagram"""
    
    # Instagram API
    ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_ACCOUNT_ID')
    PAGE_ID = os.getenv('PAGE_ID')
    
    # Webhook
    VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'meu_token_secreto')
    
    # Server
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Keywords para monitorar comentários
    KEYWORDS = os.getenv('KEYWORDS', 'preço,orçamento,informação').split(',')
    KEYWORDS = [k.strip().lower() for k in KEYWORDS]
    
    # Graph API Base URL
    GRAPH_API_URL = 'https://graph.facebook.com/v18.0'
    
    @staticmethod
    def validate():
        """Valida se as configurações essenciais estão presentes"""
        if not Config.ACCESS_TOKEN:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN não configurado no .env")
        if not Config.INSTAGRAM_ACCOUNT_ID:
            raise ValueError("INSTAGRAM_ACCOUNT_ID não configurado no .env")
        return True
