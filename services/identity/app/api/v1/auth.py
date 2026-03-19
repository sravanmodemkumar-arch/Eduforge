from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    OTPRequestSchema,
    OTPVerifySchema,
    RefreshRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/otp/request", response_model=MessageResponse)
async def request_otp(
    body: OTPRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    """Request an OTP for the given phone number. Sends via WhatsApp, falls back to SMS."""
    result = await auth_service.request_otp(db, body.phone)
    return MessageResponse(message=result["message"])


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(
    body: OTPVerifySchema,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and return JWT access + refresh tokens."""
    ip_address = request.client.host if request.client else None
    device_info = {
        "user_agent": request.headers.get("user-agent"),
    }
    return await auth_service.verify_otp(
        db,
        body.phone,
        body.otp,
        ip_address=ip_address,
        device_info=device_info,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using a valid refresh token."""
    return await auth_service.refresh_access_token(db, body.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the refresh token (logout)."""
    await auth_service.revoke_session(db, current_user.id, body.refresh_token)
    return MessageResponse(message="Logged out successfully")
