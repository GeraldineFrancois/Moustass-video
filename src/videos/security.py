"""Security module for video service - JWT verification and signature operations."""
import os
from jose import jwt, JWTError
from fastapi import HTTPException, status
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

JWT_SECRET = os.getenv('JWT_SECRET', 'devsecret')
JWT_ALGO = 'HS256'


def decode_access_token(token: str):
    """Decode and verify a JWT token. Returns the payload dict or None on error."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except JWTError:
        return None


def get_current_user(authorization_header: str):
    """Extract and validate JWT token from Authorization header.
    
    Returns user_id from token payload.
    Raises HTTPException if token is missing or invalid.
    """
    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    token = parts[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user_id"
        )
    
    return user_id


def sign_data(data: bytes, private_key_pem: str) -> str:
    """Sign data with a private RSA key.
    
    Args:
        data: Bytes to sign (typically file hash)
        private_key_pem: Private key in PEM format
    
    Returns:
        Base64-encoded signature string
    """
    import base64
    
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
    """Verify signature with a public RSA key.
    
    Args:
        data: Original bytes that were signed
        signature_b64: Base64-encoded signature
        public_key_pem: Public key in PEM format
    
    Returns:
        True if signature is valid, False otherwise
    """
    import base64
    
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
