"""Sécurité : hachage des mots de passe et création/validation de JWT.

Ce module centralise les opérations liées aux mots de passe (hash/verify),
ainsi que la création et la vérification de tokens JWT utilisés par les
microservices. Les commentaires ci‑dessous expliquent brièvement chaque
fonctionnalité pour faciliter la lecture.
"""

from passlib.context import CryptContext
import re
from datetime import datetime, timedelta, timezone
import os
from jose import jwt, JWTError

# Configuration du hachage : on privilégie `pbkdf2_sha256` pour supporter
# des phrases de passe longues tout en conservant `bcrypt` pour compatibilité.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

# Paramètres JWT (doivent être configurés via variables d'environnement)
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError(
        "JWT_SECRET must be set and at least 32 characters long. "
        "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
JWT_ALGO = "HS256"
# Durée par défaut du token en minutes (1 journée)
JWT_EXPIRES_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    """Calcule le hash d'un mot de passe en utilisant `passlib`.

    Renvoie la chaîne encodée complète contenant le sel et les paramètres.
    """
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    return pwd_context.verify(password, password_hash)


def validate_password_strength(password: str) -> bool:
    """Règles minimales de robustesse : longueur, majuscule, minuscule et symbole.

    Cette politique est volontairement simple ; pour un produit réel, on
    complètera par des listes de mots communs ou des mesures d'entropie.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Crée un JWT signé contenant `data` et une date d'expiration (`exp`)."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=JWT_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)
    return encoded


def decode_access_token(token: str):
    """Décode et vérifie un JWT. Retourne le payload ou `None` si invalide."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except JWTError:
        return None
