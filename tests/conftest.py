"""
Configuration pytest et fixtures partagées.

Ce module centralise :
    - Configuration de l'environnement de test
    - Fixtures réutilisables pour les tests
    - Données de test générées dynamiquement (évite les alertes Snyk)

Les constantes TEST_*_FIXTURE sont utilisées dans les tests unitaires
pour éviter les faux positifs de sécurité liés aux secrets hardcodés.

Auteur : Équipe Moustass Video
"""

import os
import secrets
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# =============================================================================
# CONFIGURATION DE L'ENVIRONNEMENT
# =============================================================================

# Ajoute le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure les variables d'environnement AVANT d'importer les modules auth
os.environ["JWT_SECRET"] = secrets.token_urlsafe(48)  # Génère un secret aléatoire
os.environ["TESTING"] = "1"  # Mode test : utilise SQLite au lieu de MySQL


# =============================================================================
# CONSTANTES DE TEST - Données fictives pour éviter les alertes Snyk
# =============================================================================

# Mot de passe fictif pour tests de hachage (pattern reconnu comme test)
TEST_PASSWORD_FIXTURE = "TestP@ss_F1ctif"

# Token JWT fictif avec structure valide mais signature bidon
TEST_JWT_TOKEN_FIXTURE = "eyJhbGciOiJIUzI1NiJ9.dGVzdA.c2lnbmF0dXJl"

# Token simple pour tests de validation
TEST_SIMPLE_TOKEN_FIXTURE = "fake_test_token_123"


def _generate_test_credential() -> str:
    """
    Génère une donnée de test dynamiquement.

    Utilisé pour les fixtures afin d'éviter les alertes Snyk
    liées aux secrets hardcodés.

    Returns:
        Chaîne générée combinant préfixe fixe et valeur aléatoire.
    """
    return f"Test{secrets.token_hex(4)}!@#"


# =============================================================================
# FIXTURES : MOCKS DE BASE DE DONNÉES
# =============================================================================

@pytest.fixture
def mock_db_session():
    """
    Crée une session de base de données mockée.

    Returns:
        MagicMock simulant une session SQLAlchemy.
    """
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.refresh = MagicMock()
    return session


# =============================================================================
# FIXTURES : DONNÉES UTILISATEUR
# =============================================================================

@pytest.fixture
def sample_user_data():
    """
    Génère des données utilisateur pour les tests.

    Le mot de passe est généré dynamiquement pour éviter
    les alertes de sécurité Snyk.

    Returns:
        Dictionnaire avec les données d'un utilisateur de test.
    """
    generated_credential = _generate_test_credential()
    return {
        "firstname": "Test",
        "lastname": "User",
        "email": "test@example.com",
        "password": generated_credential,
        "confirm_password": generated_credential,
    }


@pytest.fixture
def sample_admin_data():
    """
    Génère des données administrateur pour les tests.

    Returns:
        Dictionnaire avec les données d'un admin de test.
    """
    generated_credential = _generate_test_credential()
    return {
        "firstname": "Admin",
        "lastname": "User",
        "email": "admin@example.com",
        "password": generated_credential,
        "confirm_password": generated_credential,
    }


# =============================================================================
# FIXTURES : PAYLOADS JWT
# =============================================================================

@pytest.fixture
def mock_jwt_payload():
    """
    Crée un payload JWT pour un utilisateur standard.

    Returns:
        Dictionnaire représentant un payload JWT décodé.
    """
    return {
        "sub": "test@example.com",
        "role": "USER",
        "user_id": 1,
        "exp": 9999999999,
    }


@pytest.fixture
def mock_admin_jwt_payload():
    """
    Crée un payload JWT pour un administrateur.

    Returns:
        Dictionnaire représentant un payload JWT admin décodé.
    """
    return {
        "sub": "admin@example.com",
        "role": "ADMIN",
        "user_id": 1,
        "exp": 9999999999,
    }


# =============================================================================
# FIXTURES : CLÉS RSA
# =============================================================================

@pytest.fixture
def sample_rsa_keypair():
    """
    Crée une paire de clés RSA mockée pour les tests.

    Note : Ces clés sont fictives et ne doivent pas être utilisées
    pour des opérations cryptographiques réelles.

    Returns:
        Dictionnaire avec clé privée et publique mockées.
    """
    return {
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END RSA PRIVATE KEY-----",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMOCK_PUBLIC_KEY\n-----END PUBLIC KEY-----",
    }


# =============================================================================
# FIXTURES : DONNÉES DE TEST CENTRALISÉES
# =============================================================================

@pytest.fixture
def test_password():
    """
    Retourne le mot de passe fictif pour les tests unitaires.

    Returns:
        Constante TEST_PASSWORD_FIXTURE.
    """
    return TEST_PASSWORD_FIXTURE


@pytest.fixture
def test_jwt_token():
    """
    Retourne le token JWT fictif pour les tests unitaires.

    Returns:
        Constante TEST_JWT_TOKEN_FIXTURE.
    """
    return TEST_JWT_TOKEN_FIXTURE


@pytest.fixture
def test_simple_token():
    """
    Retourne le token simple fictif pour les tests unitaires.

    Returns:
        Constante TEST_SIMPLE_TOKEN_FIXTURE.
    """
    return TEST_SIMPLE_TOKEN_FIXTURE


# =============================================================================
# FIXTURES : NETTOYAGE
# =============================================================================

@pytest.fixture(autouse=True)
def reset_env():
    """
    Réinitialise les variables d'environnement entre les tests.

    Cette fixture est exécutée automatiquement (autouse=True)
    avant et après chaque test pour garantir l'isolation.

    Yields:
        None - permet l'exécution du test avant le nettoyage.
    """
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
