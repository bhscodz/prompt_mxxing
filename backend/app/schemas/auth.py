# File: backend/app/schemas/auth.py
# Description: Pydantic v2 schemas for all authentication and RBAC
#              endpoints in SwasthyaGrid AI. Used for request validation
#              and response serialization.

from __future__ import annotations
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.auth import UserRole, SupportedLanguage


# ---------------------------------------------------------------------------
# Shared / Base Schemas
# ---------------------------------------------------------------------------
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=80,
                          pattern=r"^[a-zA-Z0-9_.-]+$",
                          description="Alphanumeric username (letters, digits, _ . -)")
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    preferred_language: SupportedLanguage = SupportedLanguage.EN


# ---------------------------------------------------------------------------
# Registration / User Creation
# ---------------------------------------------------------------------------
class UserCreate(UserBase):
    """Used by DISTRICT_ADMIN+ to create a new user."""
    password: str = Field(..., min_length=8, max_length=128,
                          description="Minimum 8 character password")
    role: UserRole = UserRole.DATA_ENTRY
    facility_id: Optional[str] = None  # NULL = district-wide user

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Ensure password has at least one digit and one letter."""
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one digit.")
        return v


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int          # seconds until access token expires
    user: "UserOut"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# User Output (safe – no password)
# ---------------------------------------------------------------------------
class UserOut(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    facility_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    preferred_language: SupportedLanguage
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Profile Update
# ---------------------------------------------------------------------------
class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    preferred_language: Optional[SupportedLanguage] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128,
                                    description="Leave blank to keep current password")

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one digit.")
        return v


# ---------------------------------------------------------------------------
# Role Update (by DISTRICT_ADMIN+)
# ---------------------------------------------------------------------------
class UserRoleUpdate(BaseModel):
    role: UserRole
    facility_id: Optional[str] = None   # Optionally re-scope facility


# ---------------------------------------------------------------------------
# Audit Log Output
# ---------------------------------------------------------------------------
class AuditLogOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Any] = None       # parsed JSON or raw string
    ip_address: Optional[str] = None
    created_at: datetime

    # Include the acting user's username for readability
    username: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Generic paginated response wrapper
# ---------------------------------------------------------------------------
class PaginatedUsers(BaseModel):
    total: int
    items: list[UserOut]


class PaginatedAuditLogs(BaseModel):
    total: int
    items: list[AuditLogOut]


# Resolve forward reference in TokenResponse
TokenResponse.model_rebuild()
