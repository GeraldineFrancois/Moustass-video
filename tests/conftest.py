"""Pytest configuration and shared fixtures."""
import pytest
import os
import sys
from unittest.mock import MagicMock, Mock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set JWT_SECRET for tests BEFORE importing any auth modules
os.environ["JWT_SECRET"] = "test-jwt-secret-key-for-testing-purposes-only-32chars-minimum-length-required"
# Indicate testing mode so modules use local SQLite instead of MySQL
os.environ["TESTING"] = "1"


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "firstname": "Test",
        "lastname": "User",
        "email": "test@example.com",
        "password": "SecurePass123!@#",
        "confirm_password": "SecurePass123!@#"
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin data for testing."""
    return {
        "firstname": "Admin",
        "lastname": "User",
        "email": "admin@example.com",
        "password": "AdminPass123!@#",
        "confirm_password": "AdminPass123!@#"
    }


@pytest.fixture
def mock_jwt_payload():
    """Mock JWT payload."""
    return {
        "sub": "test@example.com",
        "role": "USER",
        "user_id": 1,
        "exp": 9999999999
    }


@pytest.fixture
def mock_admin_jwt_payload():
    """Mock admin JWT payload."""
    return {
        "sub": "admin@example.com",
        "role": "ADMIN",
        "user_id": 1,
        "exp": 9999999999
    }


@pytest.fixture
def sample_rsa_keypair():
    """Sample RSA keypair (mock)."""
    return {
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END RSA PRIVATE KEY-----",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMOCK_PUBLIC_KEY\n-----END PUBLIC KEY-----"
    }


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables between tests."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
