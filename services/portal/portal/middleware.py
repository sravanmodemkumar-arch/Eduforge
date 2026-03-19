"""Custom middleware for JWT authentication and institution resolution."""
import logging
from dataclasses import dataclass, field
from typing import Any

import jwt
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Paths that skip authentication entirely
PUBLIC_PATHS = ("/health/",)


@dataclass
class UserData:
    """Lightweight representation of the authenticated user extracted from JWT."""

    user_id: str = ""
    email: str = ""
    role: str = ""
    institution_id: str = ""
    permissions: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.user_id)


class JWTAuthMiddleware:
    """Validate JWT from the ``Authorization`` header or ``access_token`` cookie.

    On success ``request.user_data`` is populated with a :class:`UserData` instance.
    No network call is made to the identity service -- validation is purely local
    using the shared ``JWT_SECRET_KEY``.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip auth for public endpoints
        if any(request.path.startswith(p) for p in PUBLIC_PATHS):
            request.user_data = UserData()
            return self.get_response(request)

        token = self._extract_token(request)
        if not token:
            request.user_data = UserData()
            return self.get_response(request)

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            request.user_data = UserData(
                user_id=payload.get("sub", ""),
                email=payload.get("email", ""),
                role=payload.get("role", ""),
                institution_id=payload.get("institution_id", ""),
                permissions=payload.get("permissions", []),
                extra=payload,
            )
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError as exc:
            logger.warning("Invalid JWT: %s", exc)
            return JsonResponse({"error": "Invalid token"}, status=401)

        return self.get_response(request)

    @staticmethod
    def _extract_token(request) -> str | None:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return request.COOKIES.get("access_token")


class InstitutionMiddleware:
    """Extract ``institution_id`` from the JWT payload and attach it to the request.

    After :class:`JWTAuthMiddleware` runs, ``request.user_data`` is guaranteed
    to exist.  This middleware simply copies the institution identifier into
    ``request.institution`` for convenient access in views.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_data: UserData = getattr(request, "user_data", None)
        if user_data and user_data.institution_id:
            request.institution = user_data.institution_id
        else:
            request.institution = request.META.get("HTTP_X_INSTITUTION_ID", "")
        return self.get_response(request)
