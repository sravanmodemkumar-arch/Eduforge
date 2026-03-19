"""Super Admin User Management views."""

import uuid

from django.http import JsonResponse
from django.shortcuts import render

from portal.views.superadmin.decorators import require_admin, require_super_admin

DEMO_USERS = [
    {
        "id": str(uuid.uuid4()),
        "full_name": "Ravi Kumar",
        "phone": "+91-9876543210",
        "email": "ravi@eduforge.in",
        "primary_role": "SUPER_ADMIN",
        "roles": ["SUPER_ADMIN"],
        "institution": "Platform",
        "department": "Super Administration",
        "status": "ACTIVE",
        "last_active": "2 min ago",
        "level": "platform",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Meera Sharma",
        "phone": "+91-9876543211",
        "email": "meera@eduforge.in",
        "primary_role": "PLATFORM_ADMIN",
        "roles": ["PLATFORM_ADMIN"],
        "institution": "Platform",
        "department": "Super Administration",
        "status": "ACTIVE",
        "last_active": "10 min ago",
        "level": "platform",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Amit Singh",
        "phone": "+91-9876543212",
        "email": "amit@eduforge.in",
        "primary_role": "QUESTION_CREATOR",
        "roles": ["QUESTION_CREATOR", "NOTES_CREATOR"],
        "institution": "Platform",
        "department": "MCQ / Question Bank",
        "status": "ACTIVE",
        "last_active": "5 min ago",
        "productivity": "3,200 MCQs this month",
        "level": "platform",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Neha Reddy",
        "phone": "+91-9876543213",
        "email": "neha@eduforge.in",
        "primary_role": "CONTENT_REVIEWER",
        "roles": ["QUESTION_REVIEWER", "NOTES_REVIEWER"],
        "institution": "Platform",
        "department": "MCQ / Question Bank",
        "status": "ACTIVE",
        "last_active": "15 min ago",
        "level": "platform",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Ramesh Gupta",
        "phone": "+91-9876543214",
        "email": "ramesh@svec.edu",
        "primary_role": "INSTITUTION_ADMIN",
        "roles": ["INSTITUTION_ADMIN"],
        "institution": "Sri Venkateswara Engineering College",
        "department": "",
        "status": "ACTIVE",
        "last_active": "22 min ago",
        "level": "institution",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Priya Sharma",
        "phone": "+91-9876543215",
        "email": "priya@email.com",
        "primary_role": "STUDENT",
        "roles": ["STUDENT"],
        "institution": "Sri Venkateswara Engineering College",
        "department": "CSE",
        "status": "ACTIVE",
        "last_active": "1 min ago",
        "level": "student",
        "tests_taken": 142,
        "avg_score": 68.4,
        "rank": "234 / 4,832",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Suresh Patel",
        "phone": "+91-9876543216",
        "email": "suresh@eduforge.in",
        "primary_role": "SUPPORT_AGENT",
        "roles": ["SUPPORT_AGENT"],
        "institution": "Platform",
        "department": "Customer Operations",
        "status": "ACTIVE",
        "last_active": "3 min ago",
        "level": "platform",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Dr. Lakshmi Iyer",
        "phone": "+91-9876543217",
        "email": "lakshmi@narayana.edu",
        "primary_role": "TEACHER",
        "roles": ["TEACHER", "EXAM_COORDINATOR"],
        "institution": "Narayana Junior College",
        "department": "Mathematics",
        "status": "ACTIVE",
        "last_active": "45 min ago",
        "level": "institution",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Blocked User",
        "phone": "+91-9876543218",
        "email": "blocked@example.com",
        "primary_role": "STUDENT",
        "roles": ["STUDENT"],
        "institution": "SSC Exam Prep",
        "department": "",
        "status": "BLOCKED",
        "last_active": "7 days ago",
        "level": "student",
    },
    {
        "id": str(uuid.uuid4()),
        "full_name": "Sunita Devi",
        "phone": "+91-9876543219",
        "email": "sunita@parent.com",
        "primary_role": "PARENT",
        "roles": ["PARENT"],
        "institution": "DPS Bangalore",
        "department": "",
        "status": "ACTIVE",
        "last_active": "2 hrs ago",
        "level": "parent",
    },
]

DEMO_IMPERSONATION_LOGS = [
    {
        "admin_name": "Ravi Kumar (SUPER_ADMIN)",
        "target_name": "Student Priya (SVEC)",
        "reason": "Debugging exam session freeze",
        "started_at": "Today 10:23",
        "ended_at": "Today 10:31",
        "duration": "7 min 27s",
        "actions_taken": 3,
        "ip": "103.x.x.x",
    },
    {
        "admin_name": "Meera Sharma (PLATFORM_ADMIN)",
        "target_name": "Admin Ramesh (SVEC)",
        "reason": "Verifying subscription display issue",
        "started_at": "Yesterday 14:10",
        "ended_at": "Yesterday 14:18",
        "duration": "8 min 12s",
        "actions_taken": 5,
        "ip": "182.x.x.x",
    },
]


@require_admin
def user_list(request):
    """All users list with filtering."""
    users = DEMO_USERS
    level = request.GET.get("level", "")
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")
    search = request.GET.get("search", "")

    if level:
        users = [u for u in users if u["level"] == level]
    if role:
        users = [u for u in users if role in u["roles"]]
    if status:
        users = [u for u in users if u["status"] == status]
    if search:
        q = search.lower()
        users = [
            u
            for u in users
            if q in u["full_name"].lower()
            or q in u["email"].lower()
            or q in u["phone"]
        ]

    context = {
        "page_title": "User Management",
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Users", "url": ""},
        ],
        "users": users,
        "total": len(users),
        "search": search,
        "filter_level": level,
        "filter_role": role,
        "filter_status": status,
    }

    if request.htmx:
        return render(request, "superadmin/users/partials/table.html", context)
    return render(request, "superadmin/users/list.html", context)


@require_admin
def user_detail(request, user_id):
    """User detail modal/page."""
    user = next((u for u in DEMO_USERS if u["id"] == str(user_id)), DEMO_USERS[0])
    context = {
        "page_title": user["full_name"],
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Users", "url": "/sa/users/"},
            {"label": user["full_name"], "url": ""},
        ],
        "user": user,
        "tab": request.GET.get("tab", "stats"),
    }
    return render(request, "superadmin/users/detail.html", context)


@require_admin
def platform_staff(request):
    """Platform staff list."""
    staff = [u for u in DEMO_USERS if u["level"] == "platform"]
    context = {
        "page_title": "Platform Staff",
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Users", "url": "/sa/users/"},
            {"label": "Platform Staff", "url": ""},
        ],
        "users": staff,
        "total": len(staff),
    }
    if request.htmx:
        return render(request, "superadmin/users/partials/staff_table.html", context)
    return render(request, "superadmin/users/platform_staff.html", context)


@require_admin
def impersonation_log(request):
    """Impersonation log page."""
    context = {
        "page_title": "Impersonation Log",
        "breadcrumbs": [
            {"label": "Command Center", "url": "/sa/"},
            {"label": "Users", "url": "/sa/users/"},
            {"label": "Impersonation Log", "url": ""},
        ],
        "logs": DEMO_IMPERSONATION_LOGS,
    }
    return render(request, "superadmin/users/impersonation_log.html", context)
