"""
Database configuration for Security Service
Stores security audit logs, key metadata (not the keys themselves)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool
import os
import time
import sys

# Configuration MySQL
MYSQL_USER = os.getenv("MYSQL_USER", "security_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "security_password")
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = "security_db"

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Retry logic for database connection
max_retries = 10
retry_count = 0
engine = None

while retry_count < max_retries:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={
                "connect_timeout": 10,
            }
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Successfully connected to MySQL at {MYSQL_HOST}:{MYSQL_PORT}")
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

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
