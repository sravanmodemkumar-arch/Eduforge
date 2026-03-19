import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    AuthenticationError,
    OTPExpiredError,
    OTPInvalidError,
    RateLimitExceededError,
    SessionExpiredError,
    UserNotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_otp,
    hash_token,
    verify_otp_hash,
    verify_token_hash,
)
from app.models.otp import OTP
from app.models.rate_limit import RateLimit
from app.models.session import Session
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)

MAX_OTP_REQUESTS_PER_HOUR = 5
MAX_OTP_VERIFY_ATTEMPTS = 3


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


async def _check_rate_limit(db: AsyncSession, phone: str) -> None:
    """Check if the phone number has exceeded OTP request rate limits."""
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    result = await db.execute(
        select(func.coalesce(func.sum(RateLimit.count), 0)).where(
            RateLimit.key == f"otp:{phone}",
            RateLimit.action == "otp_request",
            RateLimit.window_start >= one_hour_ago,
        )
    )
    total_count = result.scalar()
    if total_count is not None and total_count >= MAX_OTP_REQUESTS_PER_HOUR:
        raise RateLimitExceededError()


async def _increment_rate_limit(db: AsyncSession, phone: str) -> None:
    """Increment the OTP request counter for rate limiting."""
    now = datetime.now(timezone.utc)
    rate_limit = RateLimit(
        key=f"otp:{phone}",
        action="otp_request",
        window_start=now,
        count=1,
    )
    db.add(rate_limit)
    await db.flush()


async def _send_otp_whatsapp(phone: str, otp: str) -> bool:
    """Send OTP via WhatsApp API. Returns True on success."""
    if not settings.WHATSAPP_API_URL or not settings.WHATSAPP_API_TOKEN:
        logger.warning("WhatsApp API not configured, skipping WhatsApp delivery")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.WHATSAPP_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "template",
                    "template": {
                        "name": "otp_verification",
                        "language": {"code": "en"},
                        "components": [
                            {
                                "type": "body",
                                "parameters": [{"type": "text", "text": otp}],
                            }
                        ],
                    },
                },
            )
            return response.status_code == 200
    except Exception:
        logger.exception("Failed to send OTP via WhatsApp")
        return False


async def _send_otp_sms(phone: str, otp: str) -> bool:
    """Send OTP via MSG91 SMS as fallback. Returns True on success."""
    if not settings.MSG91_API_KEY:
        logger.warning("MSG91 API not configured, skipping SMS delivery")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.msg91.com/api/v5/otp",
                headers={
                    "authkey": settings.MSG91_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "mobile": phone,
                    "otp": otp,
                    "sender": settings.MSG91_SENDER_ID,
                    "message": f"Your EduForge verification code is {otp}. Valid for 5 minutes.",
                },
            )
            return response.status_code == 200
    except Exception:
        logger.exception("Failed to send OTP via SMS")
        return False


async def request_otp(db: AsyncSession, phone: str) -> dict:
    """Generate OTP, hash it, store in DB, and send via WhatsApp (fallback SMS)."""
    await _check_rate_limit(db, phone)

    otp = _generate_otp()
    otp_hashed = hash_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    otp_record = OTP(
        phone=phone,
        otp_hash=otp_hashed,
        expires_at=expires_at,
    )
    db.add(otp_record)
    await _increment_rate_limit(db, phone)
    await db.flush()

    # Send via WhatsApp, fallback to SMS
    sent = await _send_otp_whatsapp(phone, otp)
    if not sent:
        sent = await _send_otp_sms(phone, otp)

    channel = "whatsapp" if sent else "sms"
    if not sent:
        logger.warning(f"OTP generated for {phone} but delivery failed on all channels")
        channel = "none"

    return {
        "message": "OTP sent successfully",
        "channel": channel,
        "expires_in": settings.OTP_EXPIRE_SECONDS,
    }


async def verify_otp(
    db: AsyncSession,
    phone: str,
    otp: str,
    ip_address: str | None = None,
    device_info: dict | None = None,
) -> TokenResponse:
    """Verify OTP, create or fetch user, issue JWT tokens."""
    now = datetime.now(timezone.utc)

    # Fetch the most recent unused OTP for this phone
    result = await db.execute(
        select(OTP)
        .where(
            OTP.phone == phone,
            OTP.is_used == False,  # noqa: E712
            OTP.expires_at > now,
        )
        .order_by(OTP.created_at.desc())
        .limit(1)
    )
    otp_record = result.scalar_one_or_none()

    if otp_record is None:
        raise OTPExpiredError("No valid OTP found. Please request a new one.")

    # Check verification attempts
    if otp_record.attempts >= MAX_OTP_VERIFY_ATTEMPTS:
        otp_record.is_used = True
        await db.flush()
        raise OTPInvalidError("Maximum verification attempts exceeded. Please request a new OTP.")

    otp_record.attempts += 1

    if not verify_otp_hash(otp, otp_record.otp_hash):
        await db.flush()
        raise OTPInvalidError()

    # Mark OTP as used
    otp_record.is_used = True
    await db.flush()

    # Get or create user
    user_result = await db.execute(select(User).where(User.phone == phone))
    user = user_result.scalar_one_or_none()

    if user is None:
        user = User(phone=phone, role=UserRole.STUDENT)
        db.add(user)
        await db.flush()

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "phone": user.phone}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    # Store session
    session = Session(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        device_info=device_info,
        ip_address=ip_address,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    await db.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Validate refresh token and issue a new access token."""
    payload = decode_token(refresh_token_str)
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Find active session with matching refresh token
    result = await db.execute(
        select(Session).where(
            Session.user_id == uuid.UUID(user_id),
            Session.is_revoked == False,  # noqa: E712
            Session.expires_at > datetime.now(timezone.utc),
        )
    )
    sessions = result.scalars().all()

    valid_session = None
    for session in sessions:
        if verify_token_hash(refresh_token_str, session.refresh_token_hash):
            valid_session = session
            break

    if valid_session is None:
        raise SessionExpiredError("Refresh token is invalid or expired")

    # Fetch user
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UserNotFoundError("User not found or inactive")

    # Issue new access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value, "phone": user.phone}
    )

    # Issue new refresh token (rotate)
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Revoke old session, create new one
    valid_session.is_revoked = True
    new_session = Session(
        user_id=user.id,
        refresh_token_hash=hash_token(new_refresh_token),
        device_info=valid_session.device_info,
        ip_address=valid_session.ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_session)
    await db.flush()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def revoke_session(db: AsyncSession, user_id: uuid.UUID, refresh_token_str: str) -> None:
    """Revoke a specific session by invalidating the refresh token."""
    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.is_revoked == False,  # noqa: E712
        )
    )
    sessions = result.scalars().all()

    for session in sessions:
        if verify_token_hash(refresh_token_str, session.refresh_token_hash):
            session.is_revoked = True
            await db.flush()
            return

    raise AuthenticationError("Session not found")
