from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import time
import sys

# Configuration avec variables d'environnement pour Docker Compose
DB_HOST = os.getenv("DB_HOST", "mysql")  # Nom du service dans docker-compose
DB_USER = os.getenv("DB_USER", "video_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "video_password")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "videos_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Retry logic for database connection
max_retries = 10
retry_count = 0
engine = None

while retry_count < max_retries:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            echo=False,
            pool_recycle=3600,
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

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
