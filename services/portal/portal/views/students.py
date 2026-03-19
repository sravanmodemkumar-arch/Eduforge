"""Student CRUD views with HTMX support."""
import json
import uuid
from datetime import date

from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render

from portal.models import Student


def student_list(request):
    """List students with optional search and class/section filters.

    HTMX requests receive only the table body partial.
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    institution_id = getattr(request, "institution", None)
    qs = Student.objects.all()
    if institution_id:
        qs = qs.filter(institution_id=institution_id)

    # Search
    search = request.GET.get("q", "").strip()
    if search:
        qs = qs.filter(
            models_q_search(search)
        )

    # Filters
    class_name = request.GET.get("class_name", "").strip()
    if class_name:
        qs = qs.filter(class_name=class_name)

    section = request.GET.get("section", "").strip()
    if section:
        qs = qs.filter(section=section)

    # Pagination (simple offset-limit)
    page = int(request.GET.get("page", 1))
    page_size = 25
    offset = (page - 1) * page_size
    total = qs.count()
    students = qs[offset : offset + page_size]
    total_pages = (total + page_size - 1) // page_size

    # Available filter options
    classes = (
        Student.objects.filter(institution_id=institution_id)
        .values_list("class_name", flat=True)
        .distinct()
        .order_by("class_name")
        if institution_id
        else Student.objects.values_list("class_name", flat=True)
        .distinct()
        .order_by("class_name")
    )
    sections = (
        Student.objects.filter(institution_id=institution_id)
        .values_list("section", flat=True)
        .distinct()
        .order_by("section")
        if institution_id
        else Student.objects.values_list("section", flat=True)
        .distinct()
        .order_by("section")
    )

    context = {
        "students": students,
        "search": search,
        "class_name": class_name,
        "section": section,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "classes": list(classes),
        "sections": list(sections),
    }

    if request.htmx:
        return render(request, "components/student_row.html", context)

    return render(request, "portal/student_list.html", context)


def student_detail(request, student_id: uuid.UUID):
    """Return detail view for a single student."""
    student = get_object_or_404(Student, pk=student_id)
    guardians = student.guardians.all()
    recent_attendance = student.attendance_records.order_by("-date")[:10]
    fee_records = student.fee_records.order_by("-due_date")[:10]

    context = {
        "student": student,
        "guardians": guardians,
        "recent_attendance": recent_attendance,
        "fee_records": fee_records,
    }
    return render(request, "portal/student_list.html", context)


def student_create(request):
    """Create a new student via POST (HTMX form submission)."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
        student = Student.objects.create(
            user_id=data.get("user_id", uuid.uuid4()),
            institution_id=data.get("institution_id", getattr(request, "institution", "")),
            academic_level=data.get("academic_level", ""),
            residential_status=data.get("residential_status", Student.ResidentialStatus.DAY_SCHOLAR),
            class_name=data["class_name"],
            section=data.get("section", ""),
            roll_number=data.get("roll_number", ""),
            admission_date=data.get("admission_date") or date.today(),
            metadata=data.get("metadata", {}),
        )
    except (KeyError, ValueError) as exc:
        return HttpResponseBadRequest(f"Invalid data: {exc}")

    if request.htmx:
        return render(request, "components/student_row.html", {"students": [student]})

    return JsonResponse({"id": str(student.id)}, status=201)


def student_update(request, student_id: uuid.UUID):
    """Update an existing student via PUT."""
    if request.method not in ("PUT", "POST"):
        return HttpResponseNotAllowed(["PUT", "POST"])

    student = get_object_or_404(Student, pk=student_id)

    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    except json.JSONDecodeError:
        data = request.POST

    updatable = [
        "academic_level", "residential_status", "class_name",
        "section", "roll_number", "metadata",
    ]
    for field in updatable:
        if field in data:
            setattr(student, field, data[field])
    student.save()

    if request.htmx:
        return render(request, "components/student_row.html", {"students": [student]})

    return JsonResponse({"id": str(student.id), "status": "updated"})


# ---- helpers ----------------------------------------------------------------

from django.db.models import Q as _Q  # noqa: E402


def models_q_search(term: str):
    """Build a Q object for searching students by name-related fields."""
    return (
        _Q(roll_number__icontains=term)
        | _Q(class_name__icontains=term)
        | _Q(section__icontains=term)
        | _Q(metadata__name__icontains=term)
    )
