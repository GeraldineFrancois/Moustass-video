"""
Cryptography module - RSA & AES operations
Centralized cryptographic functions for all services
"""

import base64
import os
from typing import Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ============================================================================
# RSA KEY GENERATION
# ============================================================================

def generate_rsa_keypair(key_size: int = 3072) -> Tuple[str, str]:
    """
    Generate RSA keypair (3072-bit default for high security)
    
    Args:
        key_size: Size of RSA key (3072 recommended)
    
    Returns:
        Tuple of (private_key_pem, public_key_pem)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode('utf-8')

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('utf-8')

    return private_pem, public_pem


# ============================================================================
# RSA SIGNATURE
# ============================================================================

def sign_data(data: bytes, private_key_pem: str) -> str:
    """
    Sign data with RSA private key using PSS padding
    
    Args:
        data: Bytes to sign (typically file hash)
        private_key_pem: Private key in PEM format
    
    Returns:
        Base64-encoded signature string
    
    Raises:
        ValueError: If signing fails
    """
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to sign data: {str(e)}")


def verify_signature(data: bytes, signature_b64: str, public_key_pem: str) -> bool:
    """
    Verify RSA signature with public key
    
    Args:
        data: Original bytes that were signed
        signature_b64: Base64-encoded signature
        public_key_pem: Public key in PEM format
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        signature = base64.b64decode(signature_b64)
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
        return False


# ============================================================================
# AES-GCM ENCRYPTION
# ============================================================================

def generate_aes_key(key_size: int = 256) -> str:
    """
    Generate random AES key
    
    Args:
        key_size: Key size in bits (128, 192, or 256)
    
    Returns:
        Base64-encoded AES key
    """
    key_bytes = os.urandom(key_size // 8)
    return base64.b64encode(key_bytes).decode('utf-8')


def encrypt_aes_gcm(data: bytes, key_b64: str, iv: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Encrypt data using AES-GCM
    
    Args:
        data: Plaintext bytes to encrypt
        key_b64: Base64-encoded AES key
        iv: Initialization vector (12 bytes). If None, generates random IV
    
    Returns:
        Tuple of (ciphertext, iv)
    """
    key = base64.b64decode(key_b64)
    if iv is None:
        iv = os.urandom(12)  # GCM standard IV size
    
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)
    
    return ciphertext, iv


def decrypt_aes_gcm(ciphertext: bytes, key_b64: str, iv: bytes) -> bytes:
    """
    Decrypt data using AES-GCM
    
    Args:
        ciphertext: Encrypted bytes
        key_b64: Base64-encoded AES key
        iv: Initialization vector (12 bytes)
    
    Returns:
        Plaintext bytes
    
    Raises:
        ValueError: If decryption fails (wrong key, corrupted data, etc.)
    """
    try:
        key = base64.b64decode(key_b64)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


# ============================================================================
# RSA ENCRYPTION (for key wrapping)
# ============================================================================

def encrypt_rsa_oaep(data: bytes, public_key_pem: str) -> str:
    """
    Encrypt data with RSA-OAEP (typically for encrypting AES keys)
    
    Args:
        data: Bytes to encrypt (max ~380 bytes for RSA-3072)
        public_key_pem: Public key in PEM format
    
    Returns:
        Base64-encoded ciphertext
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(ciphertext).decode('utf-8')
    except Exception as e:
        raise ValueError(f"RSA encryption failed: {str(e)}")


def decrypt_rsa_oaep(ciphertext_b64: str, private_key_pem: str) -> bytes:
    """
    Decrypt data with RSA-OAEP
    
    Args:
        ciphertext_b64: Base64-encoded ciphertext
        private_key_pem: Private key in PEM format
    
    Returns:
        Plaintext bytes
    """
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )
        ciphertext = base64.b64decode(ciphertext_b64)
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
        raise ValueError(f"RSA decryption failed: {str(e)}")
