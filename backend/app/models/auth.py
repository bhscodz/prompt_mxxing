# File: backend/app/models/auth.py
# Description: SQLAlchemy ORM models for User authentication, RBAC roles,
#              user sessions (token tracking), and audit logging for SwasthyaGrid AI.

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey,
    Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


# ---------------------------------------------------------------------------
# Role Enum – maps to healthcare hierarchy access levels
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    SUPER_ADMIN      = "SUPER_ADMIN"       # Platform-level access
    DISTRICT_ADMIN   = "DISTRICT_ADMIN"    # District-wide access
    FACILITY_ADMIN   = "FACILITY_ADMIN"    # Single facility management
    MEDICAL_OFFICER  = "MEDICAL_OFFICER"   # Clinical data, OPD
    PHARMACIST       = "PHARMACIST"        # Inventory/medicine management
    NURSE            = "NURSE"             # Bed & patient care data
    RECEPTIONIST     = "RECEPTIONIST"      # Patient registration & CRM
    DATA_ENTRY       = "DATA_ENTRY"        # Read-mostly, limited writes


# Supported UI languages
class SupportedLanguage(str, enum.Enum):
    EN = "en"   # English
    HI = "hi"   # Hindi
    MR = "mr"   # Marathi
    TA = "ta"   # Tamil
    TE = "te"   # Telugu
    BN = "bn"   # Bengali


# ---------------------------------------------------------------------------
# User Model
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(150), nullable=False)

    # RBAC role – determines accessible endpoints and UI panels
    role = Column(
        SAEnum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.DATA_ENTRY
    )

    # Optional facility scoping – NULL means district-wide access
    facility_id = Column(
        String(36),
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Email verification

    # Preferred UI language for multilingual support
    preferred_language = Column(
        SAEnum(SupportedLanguage, name="supportedlanguage"),
        nullable=False,
        default=SupportedLanguage.EN
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    sessions = relationship(
        "UserSession", back_populates="user",
        cascade="all, delete-orphan", lazy="select"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="user",
        cascade="all, delete-orphan", lazy="select"
    )


# ---------------------------------------------------------------------------
# UserSession Model – tracks issued JWT refresh tokens for revocation
# ---------------------------------------------------------------------------
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Hashed representation of refresh token (never store raw JWT)
    token_hash = Column(String(256), nullable=False, unique=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")


# ---------------------------------------------------------------------------
# AuditLog Model – immutable record of user actions for compliance/tracing
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,   # nullable in case the user was deleted
        index=True
    )

    # Action performed, e.g. "LOGIN", "CREATE_PATIENT", "UPDATE_INVENTORY"
    action = Column(String(100), nullable=False, index=True)

    # Resource type touched, e.g. "inventory", "patient", "user"
    resource = Column(String(100), nullable=True)

    # Specific record that was affected (UUID/int as string)
    resource_id = Column(String(100), nullable=True)

    # Additional JSON context – stored as text for SQLite/PG portability
    details = Column(Text, nullable=True)

    # Client IP for security tracing
    ip_address = Column(String(45), nullable=True)  # supports IPv6

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship – nullable because user may be deleted
    user = relationship("User", back_populates="audit_logs")
