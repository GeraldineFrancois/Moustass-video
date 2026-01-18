import os
import importlib
import secrets
import pytest


def setup_module(module):
    # Ensure JWT_SECRET is set before importing module.
    # Use a runtime-generated secret to avoid committing credentials.
    os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))


def test_hash_and_verify_password():
    sec = importlib.import_module("src.auth.security")
    password = "StrongP@ssw0rd"
    hashed = sec.hash_password(password)
    assert isinstance(hashed, str) and len(hashed) > 0
    assert sec.verify_password(password, hashed) is True
    assert sec.verify_password("wrong", hashed) is False


def test_validate_password_strength():
    sec = importlib.import_module("src.auth.security")
    assert sec.validate_password_strength("Aa1!aaaa") is True
    assert sec.validate_password_strength("short") is False
    # current policy does not require a digit, so this should be accepted
    assert sec.validate_password_strength("NoNumber!") is True


def test_jwt_create_and_decode():
    sec = importlib.import_module("src.auth.security")
    payload = {"sub": "user@example.com"}
    token = sec.create_access_token(payload, expires_delta=None)
    assert isinstance(token, str) and token.count(".") == 2
    decoded = sec.decode_access_token(token)
    assert decoded is not None and decoded.get("sub") == "user@example.com"
