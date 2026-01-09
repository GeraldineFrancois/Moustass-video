"""
JWT Token validation
Centralized JWT verification for all services
"""

import os
from jose import jwt, JWTError
from typing import Optional, Dict

JWT_SECRET = os.getenv('JWT_SECRET', 'devsecret')
JWT_ALGO = 'HS256'


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except JWTError:
        return None


def validate_token(token: str) -> Dict:
    """
    Validate JWT token and return user info
    
    Args:
        token: JWT token string
    
    Returns:
        Dict with user_id, email, role, etc.
    
    Raises:
        ValueError: If token is invalid
    """
    payload = decode_access_token(token)
    if not payload:
        raise ValueError("Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise ValueError("Token missing user_id")
    
    return {
        "user_id": user_id,
        "email": payload.get("sub"),
        "role": payload.get("role"),
        "exp": payload.get("exp")
    }


def extract_user_from_header(authorization_header: str) -> int:
    """
    Extract and validate JWT from Authorization header
    
    Args:
        authorization_header: "Bearer <token>"
    
    Returns:
        User ID
    
    Raises:
        ValueError: If header is invalid or token is bad
    """
    if not authorization_header:
        raise ValueError("Missing Authorization header")
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid Authorization header format")
    
    token = parts[1]
    user_info = validate_token(token)
    
    return user_info["user_id"]
