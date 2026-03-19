"""Super Admin Command Center Dashboard views."""

import random
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.shortcuts import render

from portal.views.superadmin.decorators import require_admin


@require_admin
def sa_dashboard(request):
    """Main command center dashboard page."""
    context = _get_dashboard_context()
    if request.htmx:
        return render(request, "superadmin/partials/dashboard_stats.html", context)
    return render(request, "superadmin/dashboard.html", context)


@require_admin
def sa_dashboard_stats(request):
    """HTMX partial: live dashboard stats (auto-refreshes every 30s)."""
    context = _get_dashboard_context()
    return render(request, "superadmin/partials/dashboard_stats.html", context)


@require_admin
def sa_dashboard_alerts(request):
    """HTMX partial: active alerts panel."""
    alerts = [
        {
            "severity": "CRITICAL",
            "message": "Exam service response time > 2s",
            "time": "3 min ago",
            "category": "Infrastructure",
        },
        {
            "severity": "CRITICAL",
            "message": "Razorpay webhook failing for 15 min",
            "time": "15 min ago",
            "category": "Payments",
        },
        {
            "severity": "WARNING",
            "message": "ABC College subscription expires in 3 days",
            "time": "1 hr ago",
            "category": "Billing",
        },
        {
            "severity": "WARNING",
            "message": "47 questions flagged for plagiarism",
            "time": "2 hrs ago",
            "category": "Content",
        },
        {
            "severity": "INFO",
            "message": "New institution registered: PQR Academy",
            "time": "3 hrs ago",
            "category": "Onboarding",
        },
    ]
    return render(request, "superadmin/partials/dashboard_alerts.html", {"alerts": alerts})


@require_admin
def sa_dashboard_activity(request):
    """HTMX partial: recent activity stream."""
    activities = [
        {
            "icon": "check",
            "color": "green",
            "message": 'Student Priya completed "SSC CGL Mock #47"',
            "detail": "Score: 142/200 · Rank: 234/12,400 · SVEC",
            "time": "2 min ago",
        },
        {
            "icon": "edit",
            "color": "blue",
            "message": "Teacher Ramesh created 25 new questions",
            "detail": "Subject: Physics · Topic: Optics · Allen Coaching",
            "time": "5 min ago",
        },
        {
            "icon": "currency",
            "color": "green",
            "message": "Payment ₹1,20,000 received from ABC University",
            "detail": "Plan: Enterprise Annual · Invoice #INV-2026-0342",
            "time": "12 min ago",
        },
        {
            "icon": "user",
            "color": "blue",
            "message": "New student registered: Rahul Kumar",
            "detail": "Institution: DPS School · Batch: Class 10-A",
            "time": "18 min ago",
        },
        {
            "icon": "settings",
            "color": "yellow",
            "message": "PLATFORM_ADMIN Meera changed feature flag",
            "detail": '"new_exam_ui" → 30% → 50% rollout',
            "time": "25 min ago",
        },
    ]
    return render(
        request, "superadmin/partials/dashboard_activity.html", {"activities": activities}
    )


def _get_dashboard_context():
    """Build dashboard context with platform-wide stats."""
    now = datetime.now()
    return {
        "page_title": "Command Center",
        "breadcrumbs": [{"label": "Command Center", "url": ""}],
        # Live counters
        "active_users": 47_832,
        "active_exams": 3_214,
        "institutions_online": 743,
        "institutions_total": 765,
        "api_health": 99.97,
        "unresolved_tickets": 127,
        "revenue_today": 482300,
        # Platform overview
        "total_institutions": 765,
        "active_institutions": 743,
        "trial_institutions": 12,
        "suspended_institutions": 7,
        "expired_institutions": 3,
        "total_users": 534_218,
        "total_students": 500_000,
        "total_teachers": 28_000,
        "total_staff": 4_218,
        "total_parents": 2_000,
        "total_questions": 4_200_000,
        "total_notes": 185_000,
        "total_videos": 72_000,
        "total_tests": 34_500,
        "total_pyps": 8_200,
        "revenue_month": 12_400_000,
        "revenue_last_month": 10_800_000,
        "revenue_growth": 11.1,
        "outstanding": 1_840_000,
        "tests_today": 28_400,
        "tests_week": 182_000,
        "avg_score": 62.3,
        "support_open": 127,
        "support_resolved_today": 89,
        "support_avg_hours": 4.2,
        "support_sla_breached": 3,
    }
