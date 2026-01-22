import os
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

PWD_CTX = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-secure')
JWT_ALGO = 'HS256'
JWT_EXP_MIN = int(os.getenv('JWT_EXP_MIN', '60'))


def hash_password(password: str) -> str:
    return PWD_CTX.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return PWD_CTX.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=(expires_minutes or JWT_EXP_MIN))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)
    return token


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except Exception:
        return None
