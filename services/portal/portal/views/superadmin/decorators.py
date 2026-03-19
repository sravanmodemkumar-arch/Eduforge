"""Decorators for Super Admin view access control."""

import functools
import logging

from django.http import HttpResponseForbidden, JsonResponse

logger = logging.getLogger(__name__)

SUPER_ADMIN_ROLES = {"SUPER_ADMIN"}
ADMIN_ROLES = {"SUPER_ADMIN", "PLATFORM_ADMIN", "OPERATIONS_MANAGER"}


def require_super_admin(view_func):
    """Decorator: only SUPER_ADMIN can access."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_data = getattr(request, "user_data", None)
        if not user_data or not user_data.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        if user_data.role not in SUPER_ADMIN_ROLES:
            return HttpResponseForbidden("Super Admin access required")
        return view_func(request, *args, **kwargs)

    return wrapper


def require_admin(view_func):
    """Decorator: SUPER_ADMIN, PLATFORM_ADMIN, or OPERATIONS_MANAGER can access."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_data = getattr(request, "user_data", None)
        if not user_data or not user_data.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        if user_data.role not in ADMIN_ROLES:
            return HttpResponseForbidden("Admin access required")
        return view_func(request, *args, **kwargs)

    return wrapper
