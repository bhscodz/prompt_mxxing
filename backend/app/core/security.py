# File: backend/app/core/security.py
# Description: Security utilities for SwasthyaGrid AI — bcrypt password hashing,
#              JWT creation/decoding, and FastAPI dependency injectors for RBAC.

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger("swasthya.security")

# ── JWT via python-jose ────────────────────────────────────────────────────────
try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    JOSE_AVAILABLE = False
    logger.warning("python-jose not installed; JWT will not work.")

# ── bcrypt via passlib ─────────────────────────────────────────────────────────
try:
    from passlib.context import CryptContext
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    BCRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover
    BCRYPT_AVAILABLE = False
    _pwd_context = None
    logger.warning("passlib not installed; password hashing will use SHA-256 fallback.")

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.auth import User, UserRole

# HTTP Bearer token extractor (reads Authorization: Bearer <token>)
bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password Utilities
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt (or SHA-256 fallback)."""
    if BCRYPT_AVAILABLE and _pwd_context:
        return _pwd_context.hash(plain)
    # Fallback — not suitable for production but keeps the app functional
    return hashlib.sha256(plain.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    if BCRYPT_AVAILABLE and _pwd_context:
        try:
            return _pwd_context.verify(plain, hashed)
        except Exception:
            pass
    # SHA-256 fallback verification
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


# ---------------------------------------------------------------------------
# JWT Utilities
# ---------------------------------------------------------------------------

def _encode(payload: dict) -> str:
    if not JOSE_AVAILABLE:
        raise RuntimeError("python-jose not available; cannot create JWT.")
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _decode(token: str) -> dict:
    if not JOSE_AVAILABLE:
        raise RuntimeError("python-jose not available; cannot decode JWT.")
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def create_access_token(
    subject: str,
    role: str,
    facility_id: Optional[str] = None,
    extra: Optional[dict] = None,
) -> str:
    """
    Create a short-lived access token.
    Payload includes: sub (user_id), role, facility_id, type=access, exp.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": expire,
    }
    if facility_id:
        payload["facility_id"] = str(facility_id)
    if extra:
        payload.update(extra)
    return _encode(payload)


def create_refresh_token(subject: str) -> str:
    """
    Create a long-lived refresh token.
    Payload includes: sub (user_id), type=refresh, exp.
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "exp": expire,
    }
    return _encode(payload)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises HTTPException 401 on any invalid or expired token.
    """
    try:
        return _decode(token)
    except Exception as exc:
        logger.warning(f"JWT decode error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def hash_token(token: str) -> str:
    """Create a SHA-256 hash of a raw token for safe DB storage (refresh tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts + validates the Bearer JWT and loads the
    corresponding User from the database.

    Raises 401 if token is missing, invalid, or expired.
    Raises 403 if the user account is disabled.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh tokens cannot be used as access tokens.",
        )

    user_id: str = payload.get("sub", "")
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or has been deleted.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled. Contact your administrator.",
        )

    return user


def require_roles(allowed_roles: List[str]):
    """
    Returns a FastAPI dependency factory that enforces role-based access control.

    Usage:
        @router.post("/admin-only")
        async def admin_endpoint(
            user: User = Depends(require_roles(["SUPER_ADMIN", "DISTRICT_ADMIN"]))
        ):
            ...
    """
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted to access this resource.",
            )
        return current_user

    return _check_role


# Convenience aliases for common role combinations
AdminOrAbove = require_roles([UserRole.SUPER_ADMIN.value, UserRole.DISTRICT_ADMIN.value, UserRole.FACILITY_ADMIN.value])
DistrictAdminOrAbove = require_roles([UserRole.SUPER_ADMIN.value, UserRole.DISTRICT_ADMIN.value])
AnyAuthenticatedUser = get_current_user  # alias for readability
