"""Health check endpoint for load balancer / container orchestration."""
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """Return service health status as JSON."""
    db_ok = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass

    status = "healthy" if db_ok else "degraded"
    code = 200 if db_ok else 503

    return JsonResponse(
        {
            "service": "portal",
            "status": status,
            "database": "ok" if db_ok else "unavailable",
        },
        status=code,
    )
