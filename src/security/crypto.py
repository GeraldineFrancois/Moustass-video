"""
Module de cryptographie - Opérations RSA et AES.

Ce module centralise toutes les fonctions cryptographiques utilisées
par les microservices de la plateforme Moustass Video.

Fonctionnalités :
    - Génération de paires de clés RSA (3072 bits)
    - Signature et vérification RSA-PSS
    - Chiffrement et déchiffrement AES-GCM
    - Chiffrement RSA-OAEP (pour envelopper les clés AES)

Auteur : Équipe Moustass Video
"""

import base64
import os
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# =============================================================================
# GÉNÉRATION DE CLÉS RSA
# =============================================================================

def generate_rsa_keypair(key_size: int = 3072) -> Tuple[str, str]:
    """
    Génère une paire de clés RSA (publique et privée).

    La taille par défaut est 3072 bits, recommandée pour une sécurité
    élevée jusqu'en 2030 selon le NIST.

    Args:
        key_size: Taille de la clé en bits (3072 recommandé).

    Returns:
        Tuple contenant (clé_privée_PEM, clé_publique_PEM).

    Exemple:
        >>> private_pem, public_pem = generate_rsa_keypair()
        >>> print(private_pem[:30])
        '-----BEGIN PRIVATE KEY-----'
    """
    # Génère la clé privée avec l'exposant public standard (65537)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )

    # Exporte la clé privée au format PEM (PKCS#8)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # Extrait et exporte la clé publique au format PEM
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


# =============================================================================
# SIGNATURE NUMÉRIQUE RSA-PSS
# =============================================================================

def sign_data(data: bytes, private_key_pem: str) -> str:
    """
    Signe des données avec une clé privée RSA en utilisant PSS.

    PSS (Probabilistic Signature Scheme) est plus robuste que PKCS#1 v1.5
    car il utilise un salt aléatoire, rendant les signatures non déterministes.

    Args:
        data: Données binaires à signer (souvent un hash de fichier).
        private_key_pem: Clé privée au format PEM.

    Returns:
        Signature encodée en Base64.

    Raises:
        ValueError: Si la signature échoue (clé invalide, etc.).

    Exemple:
        >>> sig = sign_data(b"hello", private_pem)
        >>> print(len(sig))  # Signature Base64
        512
    """
    try:
        # Charge la clé privée depuis le format PEM
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )

        # Signe avec RSA-PSS et SHA-256
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),  # Mask Generation Function
                salt_length=padding.PSS.MAX_LENGTH  # Salt maximum pour plus de sécurité
            ),
            hashes.SHA256()
        )

        # Retourne la signature encodée en Base64
        return base64.b64encode(signature).decode("utf-8")

    except Exception as e:
        raise ValueError(f"Échec de la signature : {e}")


def verify_signature(data: bytes, signature_b64: str, public_key_pem: str) -> bool:
    """
    Vérifie une signature RSA-PSS avec la clé publique.

    Args:
        data: Données originales qui ont été signées.
        signature_b64: Signature encodée en Base64.
        public_key_pem: Clé publique au format PEM.

    Returns:
        True si la signature est valide, False sinon.

    Exemple:
        >>> is_valid = verify_signature(b"hello", signature, public_pem)
        >>> print(is_valid)
        True
    """
    try:
        # Charge la clé publique
        public_key = serialization.load_pem_public_key(public_key_pem.encode())

        # Décode la signature depuis Base64
        signature = base64.b64decode(signature_b64)

        # Vérifie avec les mêmes paramètres PSS
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return True

    except Exception:
        # Signature invalide ou autre erreur
        return False


# =============================================================================
# CHIFFREMENT SYMÉTRIQUE AES-GCM
# =============================================================================

def generate_aes_key(key_size: int = 256) -> str:
    """
    Génère une clé AES aléatoire.

    AES-256 offre une sécurité de 256 bits, suffisante pour les
    applications les plus exigeantes.

    Args:
        key_size: Taille de la clé en bits (128, 192 ou 256).

    Returns:
        Clé encodée en Base64.

    Exemple:
        >>> key = generate_aes_key()
        >>> print(len(key))  # Base64 de 32 bytes = 44 caractères
        44
    """
    # Génère des bytes aléatoires cryptographiquement sûrs
    key_bytes = os.urandom(key_size // 8)

    return base64.b64encode(key_bytes).decode("utf-8")


def encrypt_aes_gcm(
    data: bytes,
    key_b64: str,
    iv: Optional[bytes] = None
) -> Tuple[bytes, bytes]:
    """
    Chiffre des données avec AES-GCM (Galois/Counter Mode).

    GCM fournit à la fois confidentialité et intégrité des données
    (chiffrement authentifié). Le IV ne doit JAMAIS être réutilisé
    avec la même clé.

    Args:
        data: Données en clair à chiffrer.
        key_b64: Clé AES encodée en Base64.
        iv: Vecteur d'initialisation (12 bytes). Si None, génère un IV aléatoire.

    Returns:
        Tuple contenant (données_chiffrées, iv).

    Note:
        Les données chiffrées incluent le tag d'authentification (16 bytes).

    Exemple:
        >>> ciphertext, iv = encrypt_aes_gcm(b"secret", aes_key)
        >>> print(len(iv))
        12
    """
    # Décode la clé depuis Base64
    key = base64.b64decode(key_b64)

    # Génère un IV aléatoire si non fourni (12 bytes = standard GCM)
    if iv is None:
        iv = os.urandom(12)

    # Chiffre avec AES-GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)  # None = pas de données associées

    return ciphertext, iv


def decrypt_aes_gcm(ciphertext: bytes, key_b64: str, iv: bytes) -> bytes:
    """
    Déchiffre des données chiffrées avec AES-GCM.

    Vérifie automatiquement l'intégrité des données via le tag
    d'authentification inclus dans le ciphertext.

    Args:
        ciphertext: Données chiffrées (incluant le tag de 16 bytes).
        key_b64: Clé AES encodée en Base64.
        iv: Vecteur d'initialisation utilisé lors du chiffrement.

    Returns:
        Données en clair.

    Raises:
        ValueError: Si le déchiffrement échoue (clé incorrecte, données corrompues).

    Exemple:
        >>> plaintext = decrypt_aes_gcm(ciphertext, aes_key, iv)
        >>> print(plaintext)
        b'secret'
    """
    try:
        # Décode la clé depuis Base64
        key = base64.b64decode(key_b64)

        # Déchiffre et vérifie l'intégrité
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)

        return plaintext

    except Exception as e:
        raise ValueError(f"Échec du déchiffrement : {e}")


# =============================================================================
# CHIFFREMENT ASYMÉTRIQUE RSA-OAEP (ENVELOPPEMENT DE CLÉS)
# =============================================================================

def encrypt_rsa_oaep(data: bytes, public_key_pem: str) -> str:
    """
    Chiffre des données avec RSA-OAEP.

    Typiquement utilisé pour envelopper (chiffrer) une clé AES avant
    de la transmettre. La taille des données est limitée par la taille
    de la clé RSA (~380 bytes max pour RSA-3072).

    Args:
        data: Données à chiffrer (max ~380 bytes pour RSA-3072).
        public_key_pem: Clé publique au format PEM.

    Returns:
        Données chiffrées encodées en Base64.

    Raises:
        ValueError: Si le chiffrement échoue.

    Exemple:
        >>> wrapped_key = encrypt_rsa_oaep(aes_key_bytes, public_pem)
    """
    try:
        # Charge la clé publique
        public_key = serialization.load_pem_public_key(public_key_pem.encode())

        # Chiffre avec RSA-OAEP et SHA-256
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return base64.b64encode(ciphertext).decode("utf-8")

    except Exception as e:
        raise ValueError(f"Échec du chiffrement RSA : {e}")


def decrypt_rsa_oaep(ciphertext_b64: str, private_key_pem: str) -> bytes:
    """
    Déchiffre des données avec RSA-OAEP.

    Utilisé pour récupérer une clé AES enveloppée.

    Args:
        ciphertext_b64: Données chiffrées encodées en Base64.
        private_key_pem: Clé privée au format PEM.

    Returns:
        Données en clair (typiquement une clé AES).

    Raises:
        ValueError: Si le déchiffrement échoue.

    Exemple:
        >>> aes_key = decrypt_rsa_oaep(wrapped_key, private_pem)
    """
    try:
        # Charge la clé privée
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )

        # Décode les données depuis Base64
        ciphertext = base64.b64decode(ciphertext_b64)

        # Déchiffre avec RSA-OAEP
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return plaintext

    except Exception as e:
        raise ValueError(f"Échec du déchiffrement RSA : {e}")
