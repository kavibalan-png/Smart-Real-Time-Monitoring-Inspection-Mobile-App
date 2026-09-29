"""
Security utilities: password hashing, JWT creation/verification.
Uses bcrypt directly for password hashing and HS256 JWT tokens.
Drops passlib to avoid bcrypt version incompatibility.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt (cost factor 12)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(subject: Any, extra_claims: dict = None) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(
        payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate an access token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate a refresh token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a cryptographically safe server-side filename.
    Strips all path components and sanitizes extension.
    Prevents path traversal attacks.
    """
    base = os.path.basename(original_filename or "")
    ext = ""
    if "." in base:
        raw_ext = base.rsplit(".", 1)[-1].lower()
        # Only keep alphanumeric chars, max 5 — e.g. "jpg", "png", "mp4"
        safe_ext = "".join(c for c in raw_ext if c.isalnum())[:5]
        if safe_ext:
            ext = "." + safe_ext
    return secrets.token_hex(24) + ext
