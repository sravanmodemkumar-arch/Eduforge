"""Authentication and authorization dependencies for Super Admin endpoints."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from shared.auth.dependencies import UserToken, get_current_user
from shared.constants.roles import ADMIN_ROLES, SUPER_ADMIN_ROLES


async def require_super_admin(
    current_user: UserToken = Depends(get_current_user),
) -> UserToken:
    """Ensure the authenticated user has the SUPER_ADMIN role.

    Raises ``403 Forbidden`` if the JWT role is not ``SUPER_ADMIN``.
    """
    if current_user.role not in SUPER_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return current_user


async def require_admin(
    current_user: UserToken = Depends(get_current_user),
) -> UserToken:
    """Ensure the authenticated user is SUPER_ADMIN, PLATFORM_ADMIN, or OPERATIONS_MANAGER.

    Raises ``403 Forbidden`` if the JWT role is not one of the admin roles.
    """
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required (SUPER_ADMIN, PLATFORM_ADMIN, or OPERATIONS_MANAGER)",
        )
    return current_user
