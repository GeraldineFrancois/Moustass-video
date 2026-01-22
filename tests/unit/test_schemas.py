"""
Tests unitaires pour le module src/auth/schemas.py.

Ce module teste la validation Pydantic des schémas de données :
- UserCreate : création d'un nouvel utilisateur
- UserOut : données utilisateur en sortie
- LoginRequest : requête de connexion
- TokenResponse : réponse d'authentification JWT

Auteur: Équipe Moustass Video
"""

import pytest
from pydantic import ValidationError


# =============================================================================
# TESTS : SCHÉMA UserCreate
# =============================================================================

def test_user_create_valid():
    """
    Vérifie la création d'un utilisateur avec des données valides.
    """
    from src.auth.schemas import UserCreate

    user = UserCreate(
        firstname="Jean",
        lastname="Dupont",
        email="jean.dupont@example.com",
        password="SecurePass123!",
        confirm_password="SecurePass123!",
    )

    assert user.firstname == "Jean"
    assert user.lastname == "Dupont"
    assert user.email == "jean.dupont@example.com"


def test_user_create_invalid_email():
    """
    Vérifie qu'un email invalide est rejeté par Pydantic.
    """
    from src.auth.schemas import UserCreate

    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            firstname="Jean",
            lastname="Dupont",
            email="pas-un-email-valide",
            password="SecurePass123!",
            confirm_password="SecurePass123!",
        )

    # Vérifier que l'erreur concerne l'email
    error_str = str(exc_info.value).lower()
    assert "email" in error_str or "value" in error_str


def test_user_create_password_too_short():
    """
    Vérifie qu'un mot de passe trop court (< 8 caractères) est rejeté.
    """
    from src.auth.schemas import UserCreate

    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            firstname="Jean",
            lastname="Dupont",
            email="jean@example.com",
            password="court",  # Moins de 8 caractères
            confirm_password="court",
        )

    error_str = str(exc_info.value).lower()
    assert "password" in error_str or "min_length" in error_str or "short" in error_str


# =============================================================================
# TESTS : SCHÉMA UserOut
# =============================================================================

def test_user_out_complete():
    """
    Vérifie la création de UserOut avec toutes les données.
    """
    from src.auth.schemas import UserOut

    data = {
        "id": 1,
        "firstname": "Marie",
        "lastname": "Martin",
        "email": "marie@example.com",
        "role": "ADMIN",
        "public_key": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    }

    user_out = UserOut(**data)

    assert user_out.id == 1
    assert user_out.role == "ADMIN"
    assert user_out.public_key is not None


def test_user_out_without_public_key():
    """
    Vérifie que UserOut accepte une public_key nulle (optionnelle).
    """
    from src.auth.schemas import UserOut

    data = {
        "id": 2,
        "firstname": "Pierre",
        "lastname": "Durand",
        "email": "pierre@example.com",
        "role": "USER",
        "public_key": None,
    }

    user_out = UserOut(**data)

    assert user_out.public_key is None


# =============================================================================
# TESTS : SCHÉMA LoginRequest
# =============================================================================

def test_login_request_valid():
    """
    Vérifie une requête de login avec des données valides.
    """
    from src.auth.schemas import LoginRequest

    login = LoginRequest(email="user@example.com", password="mypassword")

    assert login.email == "user@example.com"
    assert login.password == "mypassword"


def test_login_request_invalid_email():
    """
    Vérifie qu'un email invalide dans LoginRequest est rejeté.
    """
    from src.auth.schemas import LoginRequest

    with pytest.raises(ValidationError):
        LoginRequest(email="email-invalide", password="mypassword")


# =============================================================================
# TESTS : SCHÉMA TokenResponse
# =============================================================================

def test_token_response_default_type():
    """
    Vérifie que TokenResponse a 'bearer' comme type par défaut.
    """
    from src.auth.schemas import TokenResponse
    from tests.conftest import TEST_JWT_TOKEN_FIXTURE

    # Utilisation de la fixture centralisée (donnée de test non sensible)
    token = TokenResponse(access_token=TEST_JWT_TOKEN_FIXTURE)

    assert token.access_token.startswith("eyJ")
    assert token.token_type == "bearer"


def test_token_response_custom_type():
    """
    Vérifie que TokenResponse accepte un type personnalisé.
    """
    from src.auth.schemas import TokenResponse
    from tests.conftest import TEST_SIMPLE_TOKEN_FIXTURE

    # Utilisation de la fixture centralisée (donnée de test non sensible)
    token = TokenResponse(access_token=TEST_SIMPLE_TOKEN_FIXTURE, token_type="custom_type")

    assert token.token_type == "custom_type"
