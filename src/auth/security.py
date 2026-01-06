from passlib.context import CryptContext
import re
from datetime import datetime, timedelta, timezone
import os
from jose import jwt, JWTError

# Password hashing configuration
# - We prefer `pbkdf2_sha256` to support long passphrases reliably.
# - `bcrypt` is left as a supported scheme for backwards compatibility.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'devsecret')
JWT_ALGO = 'HS256'
# Token lifetime in minutes (default one day)
JWT_EXPIRES_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    """Hash a plaintext password using the configured password context.

    Returns the full encoded hash string (includes salt and parameters).
    """
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash string.

    This delegates to `passlib` which handles supported schemes.
    """
    return pwd_context.verify(password, password_hash)


def validate_password_strength(password: str) -> bool:
    """Basic password policy checks: length, upper/lowercase, and symbol.

    This is intentionally simple; for production you may want more checks
    (common-password lists, entropy calculation, etc.).
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    return True


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a signed JWT access token containing `data` as the payload.

    The `exp` claim is added using `expires_delta` or the default lifetime.
    """
    to_encode = data.copy()
    # Use timezone-aware UTC datetimes rather than naive `utcnow()`
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=JWT_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)
    return encoded


def decode_access_token(token: str):
    """Decode and verify a JWT token. Returns the payload dict or None on error."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except JWTError:
        return None
