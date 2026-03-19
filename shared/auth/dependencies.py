"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Sequence

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.auth.jwt import decode_token

# ---------------------------------------------------------------------------
# Bearer token scheme
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer()


# ---------------------------------------------------------------------------
# UserToken dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UserToken:
    """Represents the authenticated user extracted from a JWT."""

    user_id: uuid.UUID
    role: str
    institution_id: uuid.UUID | None
    permissions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserToken:
    """Decode the Bearer token and return a ``UserToken``.

    Raises ``401`` if the token is missing, expired, or invalid.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    institution_raw = payload.get("institution_id")
    return UserToken(
        user_id=uuid.UUID(payload["sub"]),
        role=payload.get("role", ""),
        institution_id=uuid.UUID(institution_raw) if institution_raw else None,
        permissions=payload.get("permissions", []),
    )


def require_role(*roles: str):
    """Return a dependency that ensures the user has one of the given roles.

    Usage::

        @router.get("/admin", dependencies=[Depends(require_role("admin", "super_admin"))])
        async def admin_endpoint():
            ...
    """

    async def _check_role(
        current_user: UserToken = Depends(get_current_user),
    ) -> UserToken:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not allowed. Required: {', '.join(roles)}",
            )
        return current_user

    return _check_role


def require_institution():
    """Return a dependency that ensures the token carries an ``institution_id``.

    Usage::

        @router.get("/data", dependencies=[Depends(require_institution())])
        async def scoped_endpoint():
            ...
    """

    async def _check_institution(
        current_user: UserToken = Depends(get_current_user),
    ) -> UserToken:
        if current_user.institution_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="An institution context is required for this endpoint",
            )
        return current_user

    return _check_institution
