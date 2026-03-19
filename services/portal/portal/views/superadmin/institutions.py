"""Super Admin Institution Management views."""

import uuid
from datetime import datetime, timedelta

from django.http import JsonResponse
from django.shortcuts import render

from portal.views.superadmin.decorators import require_admin, require_super_admin


# ---------------------------------------------------------------------------
# Demo data (replaced by API calls in production)
# ---------------------------------------------------------------------------

DEMO_INSTITUTIONS = [
    {
        "id": str(uuid.uuid4()),
        "name": "Sri Venkateswara Engineering College",
        "code": "SVEC-HYD-001",
        "institution_type": "COLLEGE",
        "group_name": "SV University Group",
        "state": "Telangana",
        "city": "Hyderabad",
        "students": 4832,
        "staff": 210,
        "plan": "Enterprise",
        "plan_amount": "₹2.5L/yr",
        "subscription_expiry": "2026-08-15",
        "health_score": 87,
        "health_status": "healthy",
        "status": "ACTIVE",
        "last_activity": "2 min ago",
        "contact_email": "admin@svec.edu",
        "dau": 2134,
        "dau_pct": 44,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Allen Career Institute Hyderabad",
        "code": "ALLEN-HYD-001",
        "institution_type": "COACHING",
        "group_name": "Allen Group",
        "state": "Telangana",
        "city": "Hyderabad",
        "students": 8200,
        "staff": 45,
        "plan": "Pro",
        "plan_amount": "₹1.8L/yr",
        "subscription_expiry": "2026-06-20",
        "health_score": 92,
        "health_status": "healthy",
        "status": "ACTIVE",
        "last_activity": "1 min ago",
        "contact_email": "hyd@allen.ac.in",
        "dau": 6100,
        "dau_pct": 74,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Delhi Public School Bangalore",
        "code": "DPS-BLR-001",
        "institution_type": "SCHOOL",
        "group_name": "",
        "state": "Karnataka",
        "city": "Bangalore",
        "students": 1200,
        "staff": 85,
        "plan": "Basic",
        "plan_amount": "₹1.2L/yr",
        "subscription_expiry": "2026-12-01",
        "health_score": 71,
        "health_status": "at_risk",
        "status": "ACTIVE",
        "last_activity": "15 min ago",
        "contact_email": "admin@dpsbangalore.edu",
        "dau": 340,
        "dau_pct": 28,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "SSC Exam Prep",
        "code": "SSC-PREP-001",
        "institution_type": "MOCK_TEST_DOMAIN",
        "group_name": "",
        "state": "",
        "city": "",
        "students": 120000,
        "staff": 15,
        "plan": "Mock Test Site",
        "plan_amount": "Custom",
        "subscription_expiry": "2027-01-01",
        "health_score": 95,
        "health_status": "healthy",
        "status": "ACTIVE",
        "last_activity": "Now",
        "contact_email": "admin@sscexamprep.com",
        "dau": 42000,
        "dau_pct": 35,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "RRB Mock Test",
        "code": "RRB-MOCK-001",
        "institution_type": "MOCK_TEST_DOMAIN",
        "group_name": "",
        "state": "",
        "city": "",
        "students": 85000,
        "staff": 10,
        "plan": "Mock Test Site",
        "plan_amount": "Custom",
        "subscription_expiry": "2027-01-01",
        "health_score": 91,
        "health_status": "healthy",
        "status": "ACTIVE",
        "last_activity": "Now",
        "contact_email": "admin@rrbmocktest.in",
        "dau": 28000,
        "dau_pct": 33,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Narayana Junior College",
        "code": "NARA-HYD-001",
        "institution_type": "COLLEGE",
        "group_name": "Narayana Group",
        "state": "Telangana",
        "city": "Hyderabad",
        "students": 6500,
        "staff": 180,
        "plan": "Enterprise",
        "plan_amount": "₹2.5L/yr",
        "subscription_expiry": "2026-09-30",
        "health_score": 84,
        "health_status": "healthy",
        "status": "ACTIVE",
        "last_activity": "5 min ago",
        "contact_email": "admin@narayana.edu",
        "dau": 3200,
        "dau_pct": 49,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Kendriya Vidyalaya No. 1",
        "code": "KV-DEL-001",
        "institution_type": "SCHOOL",
        "group_name": "KVS",
        "state": "Delhi",
        "city": "New Delhi",
        "students": 800,
        "staff": 42,
        "plan": "Starter",
        "plan_amount": "₹50K/yr",
        "subscription_expiry": "2026-04-15",
        "health_score": 38,
        "health_status": "critical",
        "status": "ACTIVE",
        "last_activity": "3 days ago",
        "contact_email": "kv1@kvs.gov.in",
        "dau": 45,
        "dau_pct": 6,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "FIITJEE Mumbai Centre",
        "code": "FIIT-MUM-001",
        "institution_type": "COACHING",
        "group_name": "FIITJEE Group",
        "state": "Maharashtra",
        "city": "Mumbai",
        "students": 3200,
        "staff": 28,
        "plan": "Pro",
        "plan_amount": "₹1.8L/yr",
        "subscription_expiry": "2026-07-20",
        "health_score": 79,
        "health_status": "at_risk",
        "status": "ACTIVE",
        "last_activity": "30 min ago",
        "contact_email": "mumbai@fiitjee.com",
        "dau": 1800,
        "dau_pct": 56,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Bank Exam Hub",
        "code": "BANK-HUB-001",
        "institution_type": "MOCK_TEST_DOMAIN",
        "group_name": "",
        "state": "",
        "city": "",
        "students": 110000,
        "staff": 12,
        "plan": "Mock Test Site",
        "plan_amount": "Custom",
        "subscription_expiry": "2027-01-01",
        "health_score": 93,
        "health_status": "healthy",
        "status": "ACTIVE",
        "last_activity": "Now",
        "contact_email": "admin@bankexamhub.com",
        "dau": 38000,
        "dau_pct": 35,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "PQR Academy (Trial)",
        "code": "PQR-CHN-001",
        "institution_type": "COACHING",
        "group_name": "",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "students": 200,
        "staff": 8,
        "plan": "Free Trial",
        "plan_amount": "₹0",
        "subscription_expiry": "2026-04-05",
        "health_score": 55,
        "health_status": "at_risk",
        "status": "TRIAL",
        "last_activity": "1 hr ago",
        "contact_email": "admin@pqracademy.com",
        "dau": 80,
        "dau_pct": 40,
    },
]

DEMO_GROUPS = [
    {
        "id": str(uuid.uuid4()),
        "name": "SV University Group",
        "group_type": "University",
        "institution_count": 8,
        "total_students": 28400,
        "owner": "Dr. Ramana",
        "plan": "Enterprise Group",
        "plan_amount": "₹15L/yr",
        "status": "ACTIVE",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Allen Group",
        "group_type": "Coaching Chain",
        "institution_count": 12,
        "total_students": 85000,
        "owner": "Rajesh Maheshwari",
        "plan": "Enterprise Group",
        "plan_amount": "₹25L/yr",
        "status": "ACTIVE",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Narayana Group",
        "group_type": "College Chain",
        "institution_count": 15,
        "total_students": 72000,
        "owner": "P. Narayana Reddy",
        "plan": "Enterprise Group",
        "plan_amount": "₹22L/yr",
        "status": "ACTIVE",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "KVS",
        "group_type": "Government",
        "institution_count": 25,
        "total_students": 18000,
        "owner": "Commissioner KVS",
        "plan": "Group",
        "plan_amount": "₹8L/yr",
        "status": "ACTIVE",
    },
    {
        "id": str(uuid.uuid4()),
        "name": "FIITJEE Group",
        "group_type": "Coaching Chain",
        "institution_count": 10,
        "total_students": 32000,
        "owner": "D.K. Goel",
        "plan": "Enterprise Group",
        "plan_amount": "₹18L/yr",
        "status": "ACTIVE",
    },
]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@require_admin
def institution_list(request):
    """Institution list page with filtering."""
    # Apply filters
    institutions = DEMO_INSTITUTIONS
    inst_type = request.GET.get("type", "")
    status = request.GET.get("status", "")
    search = request.GET.get("search", "")
    view = request.GET.get("view", "all")

    if inst_type:
        institutions = [i for i in institutions if i["institution_type"] == inst_type]
    if status:
        institutions = [i for i in institutions if i["status"] == status]
    if search:
        q = search.lower()
        institutions = [
            i
            for i in institutions
            if q in i["name"].lower() or q in i["code"].lower()
        ]
    if view == "schools":
        institutions = [i for i in institutions if i["institution_type"] == "SCHOOL"]
    elif view == "colleges":
        institutions = [i for i in institutions if i["institution_type"] == "COLLEGE"]
    elif view == "coaching":
        institutions = [i for i in institutions if i["institution_type"] == "COACHING"]
    elif view == "mock_sites":
        institutions = [
            i for i in institutions if i["institution_type"] == "MOCK_TEST_DOMAIN"
        ]
    elif view == "at_risk":
        institutions = [i for i in institutions if i["health_status"] == "at_risk"]
    elif view == "critical":
        institutions = [i for i in institutions if i["health_status"] == "critical"]

    context = {
        "page_title": "Institution Management",
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Institutions", "url": ""},
        ],
        "institutions": institutions,
        "total": len(institutions),
        "view": view,
        "search": search,
        "filter_type": inst_type,
        "filter_status": status,
        "counts": {
            "all": len(DEMO_INSTITUTIONS),
            "schools": sum(
                1 for i in DEMO_INSTITUTIONS if i["institution_type"] == "SCHOOL"
            ),
            "colleges": sum(
                1 for i in DEMO_INSTITUTIONS if i["institution_type"] == "COLLEGE"
            ),
            "coaching": sum(
                1 for i in DEMO_INSTITUTIONS if i["institution_type"] == "COACHING"
            ),
            "mock_sites": sum(
                1
                for i in DEMO_INSTITUTIONS
                if i["institution_type"] == "MOCK_TEST_DOMAIN"
            ),
            "at_risk": sum(
                1 for i in DEMO_INSTITUTIONS if i["health_status"] == "at_risk"
            ),
            "critical": sum(
                1 for i in DEMO_INSTITUTIONS if i["health_status"] == "critical"
            ),
        },
    }

    if request.htmx:
        return render(
            request, "superadmin/institutions/partials/table.html", context
        )
    return render(request, "superadmin/institutions/list.html", context)


@require_admin
def institution_detail(request, institution_id):
    """Institution detail page."""
    inst = next((i for i in DEMO_INSTITUTIONS if i["id"] == str(institution_id)), None)
    if not inst:
        inst = DEMO_INSTITUTIONS[0]

    context = {
        "page_title": inst["name"],
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Institutions", "url": "/sa/institutions/"},
            {"label": inst["name"], "url": ""},
        ],
        "inst": inst,
        "tab": request.GET.get("tab", "overview"),
        # Overview stats
        "tests_created": 890,
        "questions_in_bank": 45000,
        "notes_created": 2300,
        "videos_mapped": 1800,
        "storage_used": 12.4,
        "storage_limit": 50,
        "api_calls_today": 34200,
        "avg_student_score": 64.2,
    }

    if request.htmx:
        tab = request.GET.get("tab", "overview")
        return render(
            request, f"superadmin/institutions/partials/tab_{tab}.html", context
        )
    return render(request, "superadmin/institutions/detail.html", context)


@require_admin
def institution_create(request):
    """Institution creation wizard page."""
    if request.method == "POST":
        return JsonResponse({"success": True, "message": "Institution created"})
    context = {
        "page_title": "Create Institution",
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Institutions", "url": "/sa/institutions/"},
            {"label": "Create", "url": ""},
        ],
        "groups": DEMO_GROUPS,
    }
    return render(request, "superadmin/institutions/create.html", context)


@require_admin
def institution_groups(request):
    """Institution groups list page."""
    context = {
        "page_title": "Institution Groups",
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Institutions", "url": "/sa/institutions/"},
            {"label": "Groups", "url": ""},
        ],
        "groups": DEMO_GROUPS,
    }
    if request.htmx:
        return render(request, "superadmin/institutions/partials/groups_table.html", context)
    return render(request, "superadmin/institutions/groups.html", context)
