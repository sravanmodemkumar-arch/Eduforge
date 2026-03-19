"""JWT creation and verification using PyJWT with HS256."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt

# ---------------------------------------------------------------------------
# Configuration — override via environment variables
# ---------------------------------------------------------------------------

JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7


def _build_payload(
    data: dict,
    expires_delta: timedelta,
) -> dict:
    """Build a standard JWT payload from *data* and an expiry delta.

    Required keys in *data*: ``sub`` (user_id), ``role``, ``institution_id``.
    The helper adds ``exp``, ``iat``, and ``jti`` automatically.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(data["sub"]),
        "role": data.get("role"),
        "institution_id": str(data["institution_id"]) if data.get("institution_id") else None,
        "exp": now + expires_delta,
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    # Allow callers to add extra claims.
    extra = {k: v for k, v in data.items() if k not in ("sub", "role", "institution_id")}
    payload.update(extra)
    return payload


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token (default 15 min)."""
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = _build_payload(data, delta)
    payload["type"] = "access"
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token (7 days)."""
    delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_payload(data, delta)
    payload["type"] = "refresh"
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT, returning the payload dict.

    Raises ``jwt.ExpiredSignatureError`` or ``jwt.InvalidTokenError`` on
    failure.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
