"""Tests for Auth Service - API Endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from src.auth.auth_api import health


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.unit
    def test_health_check(self):
        """Test health endpoint returns healthy status."""
        resp = health()
        assert resp["status"] == "healthy"
        assert resp["service"] == "auth-service"


class TestAuthConstants:
    """Test that auth constants are used correctly."""

    @pytest.mark.unit
    def test_constants_imported(self):
        """Test that constants are properly imported in auth_api."""
        from src.auth.auth_api import (
            HEADER_AUTHORIZATION,
            BEARER_PREFIX,
            TOKEN_TYPE_BEARER,
            ROLE_ADMIN,
            ROLE_USER,
            ERROR_MISSING_BEARER,
            ERROR_INVALID_TOKEN,
            ERROR_INVALID_CREDENTIALS,
            ERROR_USER_NOT_FOUND,
            ERROR_PASSWORDS_MISMATCH,
            ERROR_PASSWORD_STRENGTH,
            ERROR_EMAIL_REGISTERED,
            ERROR_ADMIN_REQUIRED
        )

        # Verify string values
        assert HEADER_AUTHORIZATION == 'authorization'
        assert BEARER_PREFIX == 'bearer '
        assert TOKEN_TYPE_BEARER == 'bearer'
        assert ROLE_ADMIN == 'ADMIN'
        assert ROLE_USER == 'USER'


class TestFormRequestHelper:
    """Test form request helper function."""

    @pytest.mark.unit
    def test_is_form_request_true(self):
        """Test form request detection for form-encoded content."""
        from src.auth.auth_api import _is_form_request

        mock_request = MagicMock()
        mock_request.headers.get.return_value = 'application/x-www-form-urlencoded'

        assert _is_form_request(mock_request) is True

    @pytest.mark.unit
    def test_is_form_request_false(self):
        """Test form request detection for JSON content."""
        from src.auth.auth_api import _is_form_request

        mock_request = MagicMock()
        mock_request.headers.get.return_value = 'application/json'

        assert _is_form_request(mock_request) is False
