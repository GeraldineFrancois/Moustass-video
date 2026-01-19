"""Database configuration for the Security service.

This module configures a SQLAlchemy engine for the security DB and exposes
`SessionLocal` and `Base` for models. A retry loop allows the containerized
service to wait for MySQL to become available.
"""

from typing import Generator
import os
import time
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuration from environment with Docker-friendly defaults
MYSQL_USER = os.getenv("MYSQL_USER", "security_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "security_password")
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = "security_db"

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"


def _create_engine_with_retry(url: str, max_retries: int = 10):
    retry_count = 0
    engine = None
    while retry_count < max_retries:
        try:
            engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
                connect_args={"connect_timeout": 10},
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Successfully connected to MySQL at {MYSQL_HOST}:{MYSQL_PORT}")
            return engine
        except Exception as exc:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ Failed to connect to MySQL after {max_retries} attempts")
                print(f"Error: {str(exc)}")
                sys.exit(1)
            wait_time = min(2 ** retry_count, 30)
            print(f"⏳ MySQL not ready. Attempt {retry_count}/{max_retries}. Retrying in {wait_time}s...")
            time.sleep(wait_time)


engine = _create_engine_with_retry(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Yield a DB session for use as a FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
