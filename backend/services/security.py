"""
Security & Cryptographic Utilities
Password hashing and JWT generation (zero database dependencies to prevent circular imports).
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "industrial-iot-secret-key-change-in-production-2026-secure")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and cryptographically validates a JWT token. Returns payload dict or None if invalid/expired."""
    if not token or not isinstance(token, str):
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

APP_ENV = os.getenv("APP_ENV", "development").lower()
if APP_ENV == "production" and "change-in-production" in SECRET_KEY:
    import logging
    logging.getLogger("iot.security").warning(
        "[SECURITY HAZARD] Production environment running with default SECRET_KEY! Set a custom SECRET_KEY in .env immediately."
    )
