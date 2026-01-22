"""
Tests unitaires pour le module src/auth/security.py.

Ce module teste les fonctionnalités de sécurité :
- Hachage et vérification des mots de passe (passlib)
- Validation de la robustesse des mots de passe
- Création et décodage des tokens JWT

Auteur: Équipe Moustass Video
"""

import importlib
import os
import secrets
from datetime import timedelta

import pytest


# =============================================================================
# CONFIGURATION DU MODULE DE TEST
# =============================================================================

def setup_module(module):
    """
    Configure l'environnement avant l'exécution des tests.

    Génère un JWT_SECRET aléatoire pour éviter de committer
    des credentials dans le code source.
    """
    os.environ.setdefault("JWT_SECRET", secrets.token_urlsafe(48))


def _get_security_module():
    """
    Importe dynamiquement le module security.

    Returns:
        Module security importé dynamiquement
    """
    return importlib.import_module("src.auth.security")


# =============================================================================
# TESTS : HACHAGE ET VÉRIFICATION DES MOTS DE PASSE
# =============================================================================

def test_hash_and_verify_password():
    """
    Vérifie que le hachage et la vérification fonctionnent correctement.

    Scénarios testés :
    - Le hash est une chaîne non vide
    - Le mot de passe correct est accepté
    - Un mot de passe incorrect est rejeté
    """
    from tests.conftest import TEST_PASSWORD_FIXTURE
    security = _get_security_module()
    # Utilisation de la fixture centralisée (donnée de test non sensible)
    password = TEST_PASSWORD_FIXTURE

    # Hacher le mot de passe
    hashed = security.hash_password(password)

    # Vérifications
    assert isinstance(hashed, str), "Le hash doit être une chaîne"
    assert len(hashed) > 0, "Le hash ne doit pas être vide"
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrong", hashed) is False


# =============================================================================
# TESTS : VALIDATION DE LA ROBUSTESSE DES MOTS DE PASSE
# =============================================================================

def test_validate_password_strength_valid():
    """
    Vérifie qu'un mot de passe robuste est accepté.

    Critères : >= 8 caractères, majuscule, minuscule, symbole.
    """
    security = _get_security_module()

    assert security.validate_password_strength("Aa1!aaaa") is True
    # La politique actuelle n'exige pas de chiffre
    assert security.validate_password_strength("NoNumber!") is True


def test_validate_password_strength_too_short():
    """Vérifie qu'un mot de passe trop court est rejeté (< 8 caractères)."""
    security = _get_security_module()

    assert security.validate_password_strength("short") is False


def test_validate_password_strength_missing_uppercase():
    """Vérifie qu'un mot de passe sans majuscule est rejeté."""
    security = _get_security_module()

    assert security.validate_password_strength("nouppercase1!") is False


def test_validate_password_strength_missing_lowercase():
    """Vérifie qu'un mot de passe sans minuscule est rejeté."""
    security = _get_security_module()

    assert security.validate_password_strength("NOLOWERCASE1!") is False


def test_validate_password_strength_missing_symbol():
    """Vérifie qu'un mot de passe sans symbole est rejeté."""
    security = _get_security_module()

    assert security.validate_password_strength("NoSymbol123") is False


# =============================================================================
# TESTS : CRÉATION ET DÉCODAGE DES TOKENS JWT
# =============================================================================

def test_jwt_create_and_decode():
    """
    Vérifie la création et le décodage d'un token JWT.

    Scénarios testés :
    - Le token a le format JWT standard (3 parties séparées par des points)
    - Le payload décodé contient les données originales
    """
    security = _get_security_module()
    payload = {"sub": "user@example.com"}

    # Créer le token
    token = security.create_access_token(payload, expires_delta=None)

    # Vérifications
    assert isinstance(token, str), "Le token doit être une chaîne"
    assert token.count(".") == 2, "Le token JWT doit avoir 3 parties"

    # Décoder et vérifier le contenu
    decoded = security.decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "user@example.com"


def test_jwt_create_with_custom_expiry():
    """
    Vérifie la création d'un token JWT avec une durée d'expiration personnalisée.

    Couvre la branche où expires_delta est fourni explicitement.
    """
    security = _get_security_module()
    payload = {"sub": "custom@example.com", "role": "admin"}
    custom_expiry = timedelta(minutes=5)

    # Créer le token avec expiration personnalisée
    token = security.create_access_token(payload, expires_delta=custom_expiry)

    # Décoder et vérifier
    decoded = security.decode_access_token(token)

    assert decoded is not None
    assert decoded.get("sub") == "custom@example.com"
    assert "exp" in decoded, "Le token doit contenir une date d'expiration"


def test_jwt_decode_invalid_token():
    """
    Vérifie que les tokens invalides retournent None.

    Scénarios testés :
    - Token malformé
    - Token vide
    - Token avec signature invalide
    """
    security = _get_security_module()

    # Token malformé
    assert security.decode_access_token("not.a.valid.token") is None

    # Token vide
    assert security.decode_access_token("") is None

    # Token avec signature invalide (header et payload valides, signature incorrecte)
    invalid_signature_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiJ0ZXN0In0"
        ".invalidsig"
    )
    assert security.decode_access_token(invalid_signature_token) is None
