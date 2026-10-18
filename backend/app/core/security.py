"""Password hashing and JWT helpers."""
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from app.core.config import get_settings


def _prehash(password: str) -> bytes:
    # bcrypt only looks at the first 72 bytes; pre-hashing removes that limit safely.
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(password), hashed.encode("utf-8"))
    except ValueError:
        return False


# Used to keep login timing similar for unknown e-mail addresses.
DUMMY_HASH = hash_password("dummy-password-for-timing")


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or s.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, s.jwt_secret_key, algorithm=s.jwt_algorithm)


def decode_access_token(token: str) -> Optional[str]:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.jwt_secret_key, algorithms=[s.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return str(sub) if sub is not None else None
