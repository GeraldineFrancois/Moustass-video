"""
Tests unitaires pour le module src/security/crypto.py.

Ce module teste les opérations cryptographiques :
- Génération de paires de clés RSA
- Signature et vérification RSA-PSS
- Génération de clés AES
- Chiffrement/déchiffrement AES-GCM
- Chiffrement/déchiffrement RSA-OAEP (key wrapping)

Auteur: Équipe Moustass Video
"""

import base64
import os

import pytest


# =============================================================================
# TESTS : GÉNÉRATION DE CLÉS RSA
# =============================================================================

def test_generate_rsa_keypair():
    """
    Vérifie la génération d'une paire de clés RSA.

    Contrôle que les clés sont au format PEM et ont une taille raisonnable.
    """
    from src.security.crypto import generate_rsa_keypair

    private_pem, public_pem = generate_rsa_keypair(key_size=2048)

    # Vérifier le format PEM
    assert private_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")

    # Vérifier la taille minimale
    assert len(private_pem) > 1000, "La clé privée semble trop courte"
    assert len(public_pem) > 400, "La clé publique semble trop courte"


# =============================================================================
# TESTS : SIGNATURE ET VÉRIFICATION RSA-PSS
# =============================================================================

def test_sign_and_verify_valid():
    """
    Vérifie la signature et la vérification avec des données valides.

    Scénarios :
    - Signature avec clé privée
    - Vérification avec clé publique correspondante → succès
    - Vérification avec données altérées → échec
    """
    from src.security.crypto import generate_rsa_keypair, sign_data, verify_signature

    private_pem, public_pem = generate_rsa_keypair(key_size=2048)
    data = b"Message important a signer"

    # Signer les données
    signature = sign_data(data, private_pem)

    assert isinstance(signature, str), "La signature doit être en base64"
    assert len(signature) > 0, "La signature ne doit pas être vide"

    # Vérifier avec la bonne clé → succès
    assert verify_signature(data, signature, public_pem) is True

    # Vérifier avec données modifiées → échec
    assert verify_signature(b"donnees falsifiees", signature, public_pem) is False


def test_sign_data_with_invalid_key():
    """
    Vérifie qu'une clé privée invalide lève une ValueError.
    """
    from src.security.crypto import sign_data

    with pytest.raises(ValueError) as exc_info:
        sign_data(b"data", "cle-privee-invalide")

    # Message traduit en français
    assert "Échec de la signature" in str(exc_info.value)


def test_verify_signature_invalid():
    """
    Vérifie qu'une signature invalide retourne False (pas d'exception).
    """
    from src.security.crypto import generate_rsa_keypair, verify_signature

    _, public_pem = generate_rsa_keypair(key_size=2048)
    data = b"donnees de test"
    bad_signature = base64.b64encode(b"signature_bidon").decode()

    # Doit retourner False, pas lever d'exception
    assert verify_signature(data, bad_signature, public_pem) is False


# =============================================================================
# TESTS : GÉNÉRATION DE CLÉS AES
# =============================================================================

def test_generate_aes_key_256bits():
    """Vérifie la génération d'une clé AES-256 (32 bytes)."""
    from src.security.crypto import generate_aes_key

    key_b64 = generate_aes_key(key_size=256)
    key_bytes = base64.b64decode(key_b64)

    assert len(key_bytes) == 32, "AES-256 = 32 bytes"


def test_generate_aes_key_128bits():
    """Vérifie la génération d'une clé AES-128 (16 bytes)."""
    from src.security.crypto import generate_aes_key

    key_b64 = generate_aes_key(key_size=128)
    key_bytes = base64.b64decode(key_b64)

    assert len(key_bytes) == 16, "AES-128 = 16 bytes"


# =============================================================================
# TESTS : CHIFFREMENT/DÉCHIFFREMENT AES-GCM
# =============================================================================

def test_aes_gcm_encrypt_decrypt():
    """
    Vérifie le chiffrement et déchiffrement AES-GCM.

    AES-GCM fournit confidentialité + intégrité (AEAD).
    """
    from src.security.crypto import generate_aes_key, encrypt_aes_gcm, decrypt_aes_gcm

    key = generate_aes_key(key_size=256)
    plaintext = b"Metadonnees video sensibles!"

    # Chiffrer
    ciphertext, iv = encrypt_aes_gcm(plaintext, key)

    assert ciphertext != plaintext, "Le ciphertext doit être différent"
    assert len(iv) == 12, "L'IV GCM standard fait 12 bytes"

    # Déchiffrer
    decrypted = decrypt_aes_gcm(ciphertext, key, iv)

    assert decrypted == plaintext, "Le déchiffrement doit retrouver l'original"


def test_aes_gcm_with_custom_iv():
    """
    Vérifie le chiffrement AES-GCM avec un IV personnalisé.
    """
    from src.security.crypto import generate_aes_key, encrypt_aes_gcm, decrypt_aes_gcm

    key = generate_aes_key()
    plaintext = b"Test avec IV personnalise"
    custom_iv = os.urandom(12)

    # Chiffrer avec IV personnalisé
    ciphertext, returned_iv = encrypt_aes_gcm(plaintext, key, iv=custom_iv)

    assert returned_iv == custom_iv, "L'IV retourné doit correspondre"

    # Déchiffrer
    decrypted = decrypt_aes_gcm(ciphertext, key, custom_iv)

    assert decrypted == plaintext


def test_aes_gcm_decrypt_wrong_key():
    """
    Vérifie que le déchiffrement avec une mauvaise clé lève une ValueError.

    AES-GCM détecte l'intégrité compromise via le tag d'authentification.
    """
    from src.security.crypto import generate_aes_key, encrypt_aes_gcm, decrypt_aes_gcm

    key_correct = generate_aes_key()
    key_incorrect = generate_aes_key()
    plaintext = b"Donnees confidentielles"

    ciphertext, iv = encrypt_aes_gcm(plaintext, key_correct)

    # Tentative de déchiffrement avec mauvaise clé
    with pytest.raises(ValueError) as exc_info:
        decrypt_aes_gcm(ciphertext, key_incorrect, iv)

    # Message traduit en français
    assert "Échec du déchiffrement" in str(exc_info.value)


# =============================================================================
# TESTS : CHIFFREMENT/DÉCHIFFREMENT RSA-OAEP (KEY WRAPPING)
# =============================================================================

def test_rsa_oaep_encrypt_decrypt():
    """
    Vérifie le chiffrement et déchiffrement RSA-OAEP.

    Utilisé pour le key wrapping : chiffrer une clé AES avec RSA.
    """
    from src.security.crypto import (
        generate_rsa_keypair,
        generate_aes_key,
        encrypt_rsa_oaep,
        decrypt_rsa_oaep,
    )

    private_pem, public_pem = generate_rsa_keypair(key_size=2048)
    aes_key = generate_aes_key()
    aes_key_bytes = base64.b64decode(aes_key)

    # Chiffrer la clé AES avec RSA
    encrypted_key = encrypt_rsa_oaep(aes_key_bytes, public_pem)

    assert isinstance(encrypted_key, str), "Le résultat doit être en base64"
    assert len(encrypted_key) > 0

    # Déchiffrer
    decrypted_key_bytes = decrypt_rsa_oaep(encrypted_key, private_pem)

    assert decrypted_key_bytes == aes_key_bytes, "La clé déchiffrée doit correspondre"


def test_rsa_oaep_encrypt_invalid_key():
    """
    Vérifie qu'une clé publique invalide lève une ValueError.
    """
    from src.security.crypto import encrypt_rsa_oaep

    with pytest.raises(ValueError) as exc_info:
        encrypt_rsa_oaep(b"data", "cle-publique-invalide")

    # Message traduit en français
    assert "Échec du chiffrement RSA" in str(exc_info.value)


def test_rsa_oaep_decrypt_invalid_key():
    """
    Vérifie qu'une clé privée invalide lève une ValueError.
    """
    from src.security.crypto import decrypt_rsa_oaep

    fake_ciphertext = base64.b64encode(b"fake").decode()

    with pytest.raises(ValueError) as exc_info:
        decrypt_rsa_oaep(fake_ciphertext, "cle-privee-invalide")

    # Message traduit en français
    assert "Échec du déchiffrement RSA" in str(exc_info.value)


def test_rsa_oaep_decrypt_wrong_key():
    """
    Vérifie que le déchiffrement avec une mauvaise clé privée lève une ValueError.
    """
    from src.security.crypto import generate_rsa_keypair, encrypt_rsa_oaep, decrypt_rsa_oaep

    # Deux paires de clés différentes
    private1, public1 = generate_rsa_keypair(key_size=2048)
    private2, _ = generate_rsa_keypair(key_size=2048)

    # Chiffrer avec clé 1
    encrypted = encrypt_rsa_oaep(b"secret", public1)

    # Tenter de déchiffrer avec clé 2
    with pytest.raises(ValueError) as exc_info:
        decrypt_rsa_oaep(encrypted, private2)

    # Message traduit en français
    assert "Échec du déchiffrement RSA" in str(exc_info.value)
