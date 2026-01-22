"""
Tests pour le module Auth Service - Sécurité.

Ce module teste les fonctionnalités de sécurité de l'authentification :
- Hachage et vérification des mots de passe
- Validation de la robustesse des mots de passe
- Création et vérification des tokens JWT

Les données de test sont centralisées dans conftest.py pour éviter
les alertes de sécurité Snyk liées aux secrets hardcodés.

Auteur : Équipe Moustass Video
"""

import pytest

from src.auth import security
from tests.conftest import TEST_PASSWORD_FIXTURE


# =============================================================================
# TESTS : HACHAGE DES MOTS DE PASSE
# =============================================================================

class TestPasswordHashing:
    """Tests pour le hachage des mots de passe avec passlib."""

    @pytest.mark.unit
    def test_hash_password_creates_valid_hash(self):
        """Vérifie que le hachage crée un hash valide."""
        # Utilise la fixture centralisée
        hashed = security.hash_password(TEST_PASSWORD_FIXTURE)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        # Le hash ne doit pas être le mot de passe en clair
        assert hashed != TEST_PASSWORD_FIXTURE

    @pytest.mark.unit
    def test_verify_password_with_correct_password(self):
        """Vérifie qu'un mot de passe correct est accepté."""
        hashed = security.hash_password(TEST_PASSWORD_FIXTURE)

        assert security.verify_password(TEST_PASSWORD_FIXTURE, hashed) is True

    @pytest.mark.unit
    def test_verify_password_with_incorrect_password(self):
        """Vérifie qu'un mot de passe incorrect est rejeté."""
        hashed = security.hash_password(TEST_PASSWORD_FIXTURE)

        assert security.verify_password("wrong_password", hashed) is False

    @pytest.mark.unit
    def test_hash_same_password_twice_creates_different_hashes(self):
        """
        Vérifie que le même mot de passe produit des hash différents.

        C'est grâce au salt aléatoire ajouté par passlib.
        """
        hash1 = security.hash_password(TEST_PASSWORD_FIXTURE)
        hash2 = security.hash_password(TEST_PASSWORD_FIXTURE)

        # Les deux hash doivent être différents (salt différent)
        assert hash1 != hash2


# =============================================================================
# TESTS : VALIDATION DE LA ROBUSTESSE DES MOTS DE PASSE
# =============================================================================

class TestPasswordValidation:
    """Tests pour la validation de la robustesse des mots de passe."""

    @pytest.mark.unit
    @pytest.mark.parametrize("password", [
        "Pass123!@#",
        "MySecureP@ssw0rd",
        "Abc123!@#Xyz",
    ])
    def test_validate_strong_passwords(self, password):
        """Vérifie que les mots de passe robustes sont acceptés."""
        assert security.validate_password_strength(password) is True

    @pytest.mark.unit
    @pytest.mark.parametrize("password", [
        "short",             # Trop court (< 8 caractères)
        "nouppercase123!",   # Pas de majuscule
        "NOLOWERCASE123!",   # Pas de minuscule
        "NoSpecialChar123",  # Pas de caractère spécial
        "",                  # Vide
    ])
    def test_validate_weak_passwords(self, password):
        """Vérifie que les mots de passe faibles sont rejetés."""
        assert security.validate_password_strength(password) is False


# =============================================================================
# TESTS : TOKENS JWT
# =============================================================================

class TestJWTTokens:
    """Tests pour la création et vérification des tokens JWT."""

    @pytest.mark.unit
    def test_create_access_token(self):
        """Vérifie la création d'un token JWT."""
        payload = {"sub": "test@example.com", "role": "USER", "user_id": 1}
        token = security.create_access_token(payload)

        assert token is not None
        assert isinstance(token, str)
        # Format JWT : header.payload.signature
        assert len(token.split(".")) == 3

    @pytest.mark.unit
    def test_verify_valid_token(self):
        """Vérifie le décodage d'un token valide."""
        payload = {"sub": "test@example.com", "role": "USER", "user_id": 1}
        token = security.create_access_token(payload)

        decoded = security.decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "USER"
        assert decoded["user_id"] == 1

    @pytest.mark.unit
    def test_verify_invalid_token(self):
        """Vérifie qu'un token invalide retourne None."""
        invalid_token = "invalid.token.here"

        decoded = security.decode_access_token(invalid_token)

        assert decoded is None

    @pytest.mark.unit
    def test_decode_access_token(self):
        """Vérifie le décodage d'un token avec rôle ADMIN."""
        payload = {"sub": "admin@example.com", "role": "ADMIN"}
        token = security.create_access_token(payload)

        decoded = security.decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "admin@example.com"
        assert decoded["role"] == "ADMIN"


# =============================================================================
# TESTS : CONSTANTES DE SÉCURITÉ
# =============================================================================

class TestConstants:
    """Tests pour vérifier que les constantes de sécurité sont définies."""

    @pytest.mark.unit
    def test_constants_exist(self):
        """Vérifie que les constantes requises existent."""
        from src.auth.auth_api import (
            BEARER_PREFIX,
            ERROR_INVALID_TOKEN,
            ERROR_MISSING_BEARER,
            HEADER_AUTHORIZATION,
            ROLE_ADMIN,
            ROLE_USER,
        )

        assert HEADER_AUTHORIZATION == "authorization"
        assert BEARER_PREFIX == "bearer "
        assert ERROR_MISSING_BEARER == "Missing bearer token"
        assert ERROR_INVALID_TOKEN == "Invalid token"
        assert ROLE_ADMIN == "ADMIN"
        assert ROLE_USER == "USER"
