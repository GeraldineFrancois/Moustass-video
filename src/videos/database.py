"""Database utilities for the Video microservice.

This module constructs a SQLAlchemy engine configured for MySQL and exposes a
`SessionLocal` factory and a `Base` declarative class for model definitions.
The connection logic includes a retry loop so the service waits for MySQL in
Docker Compose environments.
"""

from typing import Generator
import os
import time
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Environment-driven configuration with sensible defaults for Docker Compose
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_USER = os.getenv("DB_USER", "video_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "video_password")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "videos_db")

# Allow tests to use an in-memory SQLite DB when requested to avoid
# depending on a running MySQL instance during unit tests.
if os.getenv("USE_SQLITE_IN_MEMORY", "0") == "1":
    DATABASE_URL = "sqlite:///:memory:"
else:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def _create_engine_with_retry(url: str, max_retries: int = 10):
    # If using SQLite for tests, create engine directly without network retries
    if url.startswith("sqlite"):
        engine = create_engine(url, echo=False)
        return engine

    retry_count = 0
    engine = None
    while retry_count < max_retries:
        try:
            connect_args = {"connect_timeout": 10}
            engine = create_engine(
                url,
                pool_pre_ping=True,
                echo=False,
                pool_recycle=3600,
                connect_args=connect_args,
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Successfully connected to MySQL at {DB_HOST}:{DB_PORT}")
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
