from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Construction de l'URL de base de données depuis les variables d'environnement
DB_USER = os.environ.get('VIDEO_DB_USER', 'root')
DB_PASSWORD = os.environ.get('VIDEO_DB_PASSWORD', '')
DB_HOST = os.environ.get('VIDEO_DB_HOST', 'localhost')
DB_PORT = os.environ.get('VIDEO_DB_PORT', '3306')
DB_NAME = os.environ.get('VIDEO_DB_NAME', 'videos_db')

if not DB_PASSWORD:
    raise ValueError("VIDEO_DB_PASSWORD environment variable must be set")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
