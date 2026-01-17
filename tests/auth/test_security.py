"""Tests for Auth Service - Security Module."""
import pytest
from unittest.mock import patch, MagicMock
from src.auth import security


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    @pytest.mark.unit
    def test_hash_password_creates_valid_hash(self):
        """Test that password hashing creates a valid bcrypt hash."""
        password = "SecurePassword123!@#"
        hashed = security.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be hashed
    
    @pytest.mark.unit
    def test_verify_password_with_correct_password(self):
        """Test password verification with correct password."""
        password = "SecurePassword123!@#"
        hashed = security.hash_password(password)
        
        assert security.verify_password(password, hashed) is True
    
    @pytest.mark.unit
    def test_verify_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "SecurePassword123!@#"
        wrong_password = "WrongPassword456"
        hashed = security.hash_password(password)
        
        assert security.verify_password(wrong_password, hashed) is False
    
    @pytest.mark.unit
    def test_hash_same_password_twice_creates_different_hashes(self):
        """Test that hashing the same password twice creates different hashes (salt)."""
        password = "SecurePassword123!@#"
        hash1 = security.hash_password(password)
        hash2 = security.hash_password(password)
        
        assert hash1 != hash2  # Different salts


class TestPasswordValidation:
    """Test password strength validation."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("password", [
        "Pass123!@#",          # Valid
        "MySecureP@ssw0rd",    # Valid
        "Abc123!@#Xyz",        # Valid
    ])
    def test_validate_strong_passwords(self, password):
        """Test that strong passwords pass validation."""
        assert security.validate_password_strength(password) is True
    
    @pytest.mark.unit
    @pytest.mark.parametrize("password", [
        "short",               # Too short
        "nouppercase123!",     # No uppercase
        "NOLOWERCASE123!",     # No lowercase
        # "NoDigits!!!" is acceptable per current policy (digits not required)
        "NoSpecialChar123",    # No special char
        "",                    # Empty
    ])
    def test_validate_weak_passwords(self, password):
        """Test that weak passwords fail validation."""
        assert security.validate_password_strength(password) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    @pytest.mark.unit
    def test_create_access_token(self):
        """Test JWT token creation."""
        payload = {"sub": "test@example.com", "role": "USER", "user_id": 1}
        token = security.create_access_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT format: header.payload.signature
    
    @pytest.mark.unit
    def test_verify_valid_token(self):
        """Test verification of a valid token."""
        payload = {"sub": "test@example.com", "role": "USER", "user_id": 1}
        token = security.create_access_token(payload)
        
        # The security module exposes `decode_access_token` for verification
        decoded = security.decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "USER"
        assert decoded["user_id"] == 1
    
    @pytest.mark.unit
    def test_verify_invalid_token(self):
        """Test verification of an invalid token."""
        invalid_token = "invalid.token.here"
        
        decoded = security.decode_access_token(invalid_token)
        
        assert decoded is None
    
    @pytest.mark.unit
    def test_decode_access_token(self):
        """Test decoding access token."""
        payload = {"sub": "test@example.com", "role": "ADMIN"}
        token = security.create_access_token(payload)
        
        decoded = security.decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "ADMIN"


class TestConstants:
    """Test that security constants are properly defined."""
    
    @pytest.mark.unit
    def test_constants_exist(self):
        """Test that required constants are defined."""
        # These should be imported from auth_api if they exist
        from src.auth.auth_api import (
            HEADER_AUTHORIZATION,
            BEARER_PREFIX,
            ERROR_MISSING_BEARER,
            ERROR_INVALID_TOKEN,
            ROLE_ADMIN,
            ROLE_USER
        )
        
        assert HEADER_AUTHORIZATION == 'authorization'
        assert BEARER_PREFIX == 'bearer '
        assert ERROR_MISSING_BEARER == 'Missing bearer token'
        assert ERROR_INVALID_TOKEN == 'Invalid token'
        assert ROLE_ADMIN == 'ADMIN'
        assert ROLE_USER == 'USER'
