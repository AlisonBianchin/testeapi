import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - pode ser SQLite (dev) ou PostgreSQL (prod)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///instagram_agent.db')

# Cria engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # True para debug SQL
    pool_pre_ping=True,  # Verifica conexão antes de usar
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session para thread-safety
db_session = scoped_session(SessionLocal)


def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")
        return False


def get_db():
    """
    Dependency para obter sessão do banco
    Usar em rotas FastAPI ou contexto
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def drop_all():
    """CUIDADO: Remove todas as tabelas"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("⚠️ Todas as tabelas foram removidas!")


def reset_db():
    """CUIDADO: Reseta o banco de dados"""
    drop_all()
    init_db()
    logger.info("🔄 Banco de dados resetado!")
