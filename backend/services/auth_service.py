"""
Authentication & Authorization Service
JWT Token Generation, Password Hashing, Role Verification
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.services.security import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    """Extract and validate current authenticated user via signed cryptographic JWT. Returns None if unauthenticated."""
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    username: str = payload.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user

def require_auth(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Dependency for endpoints that require an authenticated user (either ADMIN or VIEWER)."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_admin(current_user: User = Depends(require_auth)) -> User:
    """Dependency for endpoints restricted exclusively to administrators."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to perform this action.",
        )
    return current_user

def get_user_from_token_str(token_str: Optional[str], db: Session) -> Optional[User]:
    """Helper to validate a token string (from query param, header, or websocket)."""
    if not token_str:
        return None
    payload = decode_access_token(token_str)
    if not payload:
        return None
    username: str = payload.get("sub")
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()
