import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base
import time
import sys

# Configuration MySQL pour le service d'authentification
# Utilise des variables d'environnement avec défauts adaptés à docker-compose
DB_HOST = os.getenv("AUTH_DB_HOST", "mysql")
DB_USER = os.getenv("AUTH_DB_USER", "auth_user")
DB_PASSWORD = os.getenv("AUTH_DB_PASSWORD", "auth_password")
DB_PORT = os.getenv("AUTH_DB_PORT", "3306")
DB_NAME = os.getenv("AUTH_DB_NAME", "auth_db")

# Construction de l'URL de connexion MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# If running tests, use an in-memory SQLite database to avoid network calls
if os.getenv("TESTING") == "1":
    engine = create_engine("sqlite:///:memory:", echo=False)
    # Create a sessionmaker bound to the in-memory engine
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False
    )
    print("⚠️ TESTING mode enabled: using in-memory SQLite database")
else:
    # Retry logic for database connection
    max_retries = 10
    retry_count = 0
    engine = None

    while retry_count < max_retries:
        try:
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,      # Vérifie la connexion avant utilisation
                echo=False,              # Pas de logs SQL
                pool_recycle=3600,       # Recycle les connexions après 1h
                connect_args={"connect_timeout": 10}
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Successfully connected to MySQL at {DB_HOST}:{DB_PORT}")
            break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ Failed to connect to MySQL after {max_retries} attempts")
                print(f"Error: {str(e)}")
                sys.exit(1)
            
            wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
            print(f"⏳ MySQL not ready. Attempt {retry_count}/{max_retries}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

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
