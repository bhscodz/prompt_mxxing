# File: backend/app/api/auth.py
# Description: Authentication & RBAC REST endpoints for SwasthyaGrid AI.
#   POST /auth/login     — issue JWT pair
#   POST /auth/register  — admin creates new user
#   GET  /auth/me        — current user profile
#   PUT  /auth/me        — update own profile / password
#   POST /auth/refresh   — exchange refresh token for new access token
#   POST /auth/logout    — revoke refresh token / session
#   GET  /auth/users     — list users (DISTRICT_ADMIN+)
#   PUT  /auth/users/{id}/role — update user role (DISTRICT_ADMIN+)
#   GET  /auth/audit-logs — audit trail (FACILITY_ADMIN+)

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.config import settings
from app.models.auth import User, UserSession, AuditLog, UserRole
from app.schemas.auth import (
    UserCreate, LoginRequest, TokenResponse, RefreshTokenRequest,
    AccessTokenResponse, UserOut, UserProfileUpdate, UserRoleUpdate,
    AuditLogOut, PaginatedUsers, PaginatedAuditLogs
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    hash_token, get_current_user, require_roles
)

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])
logger = logging.getLogger("swasthya.api.auth")


# ---------------------------------------------------------------------------
# Helper: write an audit log entry
# ---------------------------------------------------------------------------
async def _audit(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip: Optional[str] = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip,
    )
    db.add(log)
    # commit is handled by the calling transaction


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    acting_user: User = Depends(require_roles([
        UserRole.SUPER_ADMIN.value,
        UserRole.DISTRICT_ADMIN.value,
        UserRole.FACILITY_ADMIN.value
    ])),
):
    """Create a new user account. Only FACILITY_ADMIN and above can register users."""
    # Check uniqueness
    existing = await db.execute(
        select(User).where(
            (User.username == body.username) | (User.email == body.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username or email already exists.",
        )

    # Prevent privilege escalation — FACILITY_ADMIN cannot create DISTRICT_ADMIN/SUPER_ADMIN
    if acting_user.role == UserRole.FACILITY_ADMIN:
        if body.role in (UserRole.SUPER_ADMIN, UserRole.DISTRICT_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FACILITY_ADMIN cannot create users with higher privileges.",
            )

    new_user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        facility_id=body.facility_id,
        preferred_language=body.preferred_language,
        is_active=True,
        is_verified=True,  # Admin-created users are pre-verified
    )
    db.add(new_user)

    await _audit(
        db, acting_user.id, "CREATE_USER",
        resource="users", resource_id=new_user.id,
        details={"created_username": body.username, "role": body.role.value},
        ip=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_user)
    logger.info(f"User '{body.username}' registered by '{acting_user.username}'")
    return new_user


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with username/email + password and receive a JWT token pair."""
    # Accept username or email
    result = await db.execute(
        select(User).where(
            (User.username == body.username) | (User.email == body.username)
        )
    )
    user: Optional[User] = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    # Issue tokens
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        facility_id=user.facility_id,
    )
    refresh_token = create_refresh_token(subject=user.id)

    # Persist hashed refresh token as a session
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        is_active=True,
    )
    db.add(session)

    # Update last_login
    user.last_login = datetime.utcnow()

    await _audit(
        db, user.id, "LOGIN",
        details={"username": user.username},
        ip=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(user)

    logger.info(f"User '{user.username}' logged in.")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


# ---------------------------------------------------------------------------
# PUT /auth/me
# ---------------------------------------------------------------------------
@router.put("/me", response_model=UserOut)
async def update_profile(
    body: UserProfileUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update own profile fields (name, email, preferred language, password)."""
    changes = {}
    if body.full_name is not None:
        current_user.full_name = body.full_name
        changes["full_name"] = body.full_name
    if body.email is not None:
        # Check uniqueness
        existing = await db.execute(
            select(User).where(User.email == body.email, User.id != current_user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already in use by another account.")
        current_user.email = body.email
        changes["email"] = body.email
    if body.preferred_language is not None:
        current_user.preferred_language = body.preferred_language
        changes["preferred_language"] = body.preferred_language.value
    if body.password is not None:
        current_user.hashed_password = hash_password(body.password)
        changes["password"] = "changed"

    await _audit(db, current_user.id, "UPDATE_PROFILE",
                 resource="users", resource_id=current_user.id,
                 details=changes,
                 ip=request.client.host if request.client else None)
    await db.commit()
    await db.refresh(current_user)
    return current_user


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------
@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token.")

    user_id = payload.get("sub")
    token_hash = hash_token(body.refresh_token)

    # Verify session still active
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.token_hash == token_hash,
            UserSession.is_active == True,
        )
    )
    session: Optional[UserSession] = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked or is invalid.")

    if session.expires_at < datetime.utcnow():
        session.is_active = False
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token has expired. Please log in again.")

    # Load user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User account not found or disabled.")

    new_access = create_access_token(
        subject=user.id,
        role=user.role.value,
        facility_id=user.facility_id,
    )
    return AccessTokenResponse(
        access_token=new_access,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke the provided refresh token / session."""
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.token_hash == token_hash,
        )
    )
    session: Optional[UserSession] = result.scalar_one_or_none()
    if session:
        session.is_active = False

    await _audit(db, current_user.id, "LOGOUT",
                 details={"username": current_user.username})
    await db.commit()
    logger.info(f"User '{current_user.username}' logged out.")


# ---------------------------------------------------------------------------
# GET /auth/users  — list all users
# ---------------------------------------------------------------------------
@router.get("/users", response_model=PaginatedUsers)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    facility_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles([
        UserRole.SUPER_ADMIN.value, UserRole.DISTRICT_ADMIN.value, UserRole.FACILITY_ADMIN.value
    ])),
):
    """List all user accounts with optional facility filter. FACILITY_ADMIN and above."""
    q = select(User)
    if facility_id:
        q = q.where(User.facility_id == facility_id)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()
    result = await db.execute(q.offset(skip).limit(limit).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return PaginatedUsers(total=total, items=list(users))


# ---------------------------------------------------------------------------
# PUT /auth/users/{user_id}/role
# ---------------------------------------------------------------------------
@router.put("/users/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: str,
    body: UserRoleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    acting_user: User = Depends(require_roles([
        UserRole.SUPER_ADMIN.value, UserRole.DISTRICT_ADMIN.value
    ])),
):
    """Update a user's role and optional facility scope. DISTRICT_ADMIN+ only."""
    result = await db.execute(select(User).where(User.id == user_id))
    target: Optional[User] = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    old_role = target.role.value
    target.role = body.role
    if body.facility_id is not None:
        target.facility_id = body.facility_id

    await _audit(
        db, acting_user.id, "UPDATE_USER_ROLE",
        resource="users", resource_id=user_id,
        details={"old_role": old_role, "new_role": body.role.value},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(target)
    return target


# ---------------------------------------------------------------------------
# GET /auth/audit-logs
# ---------------------------------------------------------------------------
@router.get("/audit-logs", response_model=PaginatedAuditLogs)
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles([
        UserRole.SUPER_ADMIN.value, UserRole.DISTRICT_ADMIN.value, UserRole.FACILITY_ADMIN.value
    ])),
):
    """Retrieve audit trail entries with optional filters. FACILITY_ADMIN and above."""
    from sqlalchemy.orm import selectinload
    q = select(AuditLog).options(selectinload(AuditLog.user))
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    logs = result.scalars().all()

    # Enrich with username
    out = []
    for log in logs:
        entry = AuditLogOut.model_validate(log)
        entry.username = log.user.username if log.user else None
        out.append(entry)

    return PaginatedAuditLogs(total=total, items=out)
