"""Database connection helper for the Auth microservice.

This module constructs a SQLAlchemy engine configured for MySQL and exposes a
`SessionLocal` factory plus `init_db` / `get_db` helpers used by FastAPI.

The connection logic includes a retry loop with exponential backoff so the
service can wait for the MySQL container when started by Docker Compose.
"""

from typing import Generator
import os
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .models import Base

# Environment-driven configuration (sane Docker Compose defaults)
DB_HOST = os.getenv("AUTH_DB_HOST", "mysql")
DB_USER = os.getenv("AUTH_DB_USER", "auth_user")
DB_PASSWORD = os.getenv("AUTH_DB_PASSWORD", "auth_password")
DB_PORT = os.getenv("AUTH_DB_PORT", "3306")
DB_NAME = os.getenv("AUTH_DB_NAME", "auth_db")

# Allow tests to run without a MySQL instance by using an in-memory SQLite
# database when `USE_SQLITE_IN_MEMORY=1` is set in the environment. This
# keeps import-time behaviour fast and testable on developer machines.
if os.getenv("USE_SQLITE_IN_MEMORY", "0") == "1":
    DATABASE_URL = "sqlite:///:memory:"
else:
    # Build a SQLAlchemy connection URL for PyMySQL driver
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def _create_engine_with_retry(url: str, max_retries: int = 10):
    """Create a SQLAlchemy engine and retry until MySQL accepts connections.

    This helper wraps engine creation and executes a trivial `SELECT 1` to
    ensure the server is reachable. It exits the process on failure after
    `max_retries` attempts to avoid running the service in a broken state.
    """
    # Special-case SQLite in-memory for fast local tests: no network retries
    if url.startswith("sqlite"):
        engine = create_engine(url, echo=False)
        return engine

    retry_count = 0
    engine = None
    while retry_count < max_retries:
        try:
            # pass a connect timeout only for networked DB drivers
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

# Provide a Session factory used by FastAPI dependencies
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create DB tables defined in SQLAlchemy models if they are missing."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
