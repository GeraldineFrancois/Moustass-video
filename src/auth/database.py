import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Configuration MySQL pour le service d'authentification
# Utilise des variables d'environnement avec défauts adaptés à docker-compose
DB_HOST = os.getenv("AUTH_DB_HOST", "mysql")
DB_USER = os.getenv("AUTH_DB_USER", "auth_user")
DB_PASSWORD = os.getenv("AUTH_DB_PASSWORD", "auth_password")
DB_PORT = os.getenv("AUTH_DB_PORT", "3306")
DB_NAME = os.getenv("AUTH_DB_NAME", "auth_db")

# Construction de l'URL de connexion MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création du moteur SQLAlchemy avec pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Vérifie la connexion avant utilisation
    echo=False,              # Pas de logs SQL
    pool_recycle=3600        # Recycle les connexions après 1h
)

# Session maker pour les dépendances FastAPI
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def init_db():
    """Crée toutes les tables si elles n'existent pas."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dépendance FastAPI pour obtenir une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
