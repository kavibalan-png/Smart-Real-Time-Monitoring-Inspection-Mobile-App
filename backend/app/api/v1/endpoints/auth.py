"""
Authentication endpoints.
POST /api/auth/login     — obtain access + refresh tokens
POST /api/auth/refresh   — exchange refresh token for new access token
POST /api/auth/logout    — audit log logout (stateless JWT)
GET  /api/auth/me        — current user profile
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_refresh_token
)
from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, UserProfile
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()

    # Constant-time comparison to prevent timing attacks
    if not user or not verify_password(body.password, user.hashed_password):
        # Log failed attempt
        await log_action(
            db, action="LOGIN",
            result="FAILURE",
            ip_address=request.client.host if request.client else None,
            metadata={"email": body.email, "reason": "Invalid credentials"},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Create tokens
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Audit log
    await log_action(
        db,
        action="LOGIN",
        user_id=user.id,
        role=user.role,
        result="SUCCESS",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", ""),
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    payload = decode_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "email": user.email},
    )
    new_refresh = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Log out — audit trail only (JWT is stateless)."""
    await log_action(
        db,
        action="LOGOUT",
        user_id=current_user.id,
        role=current_user.role,
        result="SUCCESS",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserProfile)
async def get_me(current_user=Depends(get_current_active_user)):
    """Return current user profile."""
    return current_user
