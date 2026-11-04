"""
security.py
-----------
Everything related to security:
  1. Password hashing/verification (Argon2)
  2. JWT creation/verification (PyJWT)
  3. `get_current_user` dependency that protects routes
"""

from datetime import datetime, timedelta, timezone

import jwt  # PyJWT
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

# ---------------------------------------------------------------------------
# 1. Password hashing
# ---------------------------------------------------------------------------
# PasswordHasher() uses safe Argon2id defaults. Each hash includes its own
# random salt, so two users with the same password get different hashes.
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if the password matches the hash, else False."""
    try:
        return _ph.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# A pre-computed fake hash. When someone logs in with an email that does not
# exist, we still verify against this so the response takes about the same
# time (prevents attackers from discovering which emails are registered).
_DUMMY_HASH = _ph.hash("dummy-password-for-timing-protection")


def fake_verify() -> None:
    verify_password("wrong", _DUMMY_HASH)


# ---------------------------------------------------------------------------
# 2. JWT tokens
# ---------------------------------------------------------------------------
def create_access_token(user_id: int) -> str:
    """Create a signed JWT that expires after ACCESS_TOKEN_EXPIRE_MINUTES."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # "subject" = who the token belongs to (must be a string)
        "iat": now,  # issued at
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),  # expiry
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Verify signature + expiry and return the payload. Raises HTTP 401 if bad."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],  # only allow OUR algorithm
            options={"require": ["exp", "sub"]},  # these claims must exist
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        # Covers bad signature, malformed token, missing claims, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# 3. Reusable authentication dependency
# ---------------------------------------------------------------------------
# auto_error=False lets us return our own 401 (HTTPBearer's default is 403).
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Use on any route: `user: User = Depends(get_current_user)`."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if user is None:
        # Token is valid but the user was deleted
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
