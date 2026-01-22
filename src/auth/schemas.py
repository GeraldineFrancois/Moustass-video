"""
Schémas Pydantic - Validation des données d'entrée/sortie de l'API.

Ce module définit les modèles de données utilisés pour valider
les requêtes et formater les réponses de l'API d'authentification.

Pydantic garantit :
    - Validation automatique des types
    - Messages d'erreur clairs en cas de données invalides
    - Sérialisation/désérialisation JSON automatique

Auteur : Équipe Moustass Video
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, constr


# =============================================================================
# SCHÉMAS UTILISATEUR
# =============================================================================

class UserCreate(BaseModel):
    """
    Schéma pour la création d'un nouvel utilisateur.

    Utilisé lors de l'inscription pour valider les données envoyées
    par le formulaire d'enregistrement.

    Attributes:
        firstname: Prénom de l'utilisateur.
        lastname: Nom de famille de l'utilisateur.
        email: Adresse email (format validé par EmailStr).
        password: Mot de passe (minimum 8 caractères).
        confirm_password: Confirmation du mot de passe.

    Exemple:
        >>> data = UserCreate(
        ...     firstname="Jean",
        ...     lastname="Dupont",
        ...     email="jean@example.com",
        ...     password="SecureP@ss1",
        ...     confirm_password="SecureP@ss1"
        ... )
    """

    firstname: str
    lastname: str
    email: EmailStr
    password: constr(min_length=8)  # Minimum 8 caractères
    confirm_password: str


class UserOut(BaseModel):
    """
    Schéma pour retourner les informations d'un utilisateur.

    Utilisé dans les réponses API pour éviter d'exposer
    des données sensibles comme le mot de passe hashé.

    Attributes:
        id: Identifiant unique de l'utilisateur.
        firstname: Prénom.
        lastname: Nom de famille.
        email: Adresse email.
        role: Rôle de l'utilisateur ("USER" ou "ADMIN").
        public_key: Clé publique RSA (optionnelle, pour le chiffrement).

    Exemple:
        >>> user = UserOut(
        ...     id=1,
        ...     firstname="Jean",
        ...     lastname="Dupont",
        ...     email="jean@example.com",
        ...     role="USER",
        ...     public_key=None
        ... )
    """

    id: int
    firstname: str
    lastname: str
    email: EmailStr
    role: str
    public_key: Optional[str]

    # Pydantic v2 : permet de lire depuis les attributs ORM (SQLAlchemy)
    model_config = {"from_attributes": True}


# =============================================================================
# SCHÉMAS D'AUTHENTIFICATION
# =============================================================================

class LoginRequest(BaseModel):
    """
    Schéma pour une requête de connexion.

    Attributes:
        email: Adresse email de l'utilisateur.
        password: Mot de passe en clair (sera vérifié contre le hash).

    Exemple:
        >>> login = LoginRequest(
        ...     email="jean@example.com",
        ...     password="SecureP@ss1"
        ... )
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Schéma pour la réponse contenant le token JWT.

    Retourné après une connexion réussie. Le token doit être
    inclus dans les requêtes suivantes via le header Authorization.

    Attributes:
        access_token: Token JWT signé.
        token_type: Type de token (toujours "bearer").

    Exemple:
        >>> response = TokenResponse(access_token="eyJ...")
        >>> print(f"Authorization: {response.token_type} {response.access_token}")
    """

    access_token: str
    token_type: str = "bearer"
