"""Attendance views with HTMX-driven interactive grid."""
import json
import uuid
from datetime import date, datetime

from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render

from portal.models import Attendance, Student


def attendance_grid(request):
    """Render today's attendance grid (class x students).

    Query params:
        date       – ISO date string (defaults to today)
        class_name – filter by class
        section    – filter by section
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    institution_id = getattr(request, "institution", None)
    target_date_str = request.GET.get("date", "")
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date() if target_date_str else date.today()
    except ValueError:
        target_date = date.today()

    class_name = request.GET.get("class_name", "").strip()
    section = request.GET.get("section", "").strip()

    # Students
    student_qs = Student.objects.all()
    if institution_id:
        student_qs = student_qs.filter(institution_id=institution_id)
    if class_name:
        student_qs = student_qs.filter(class_name=class_name)
    if section:
        student_qs = student_qs.filter(section=section)

    students = list(student_qs)

    # Existing attendance for this date
    attendance_map: dict[str, Attendance] = {}
    if students:
        records = Attendance.objects.filter(
            student__in=students,
            date=target_date,
        )
        attendance_map = {str(a.student_id): a for a in records}

    # Build grid rows
    grid = []
    for s in students:
        att = attendance_map.get(str(s.id))
        grid.append({
            "student": s,
            "status": att.status if att else "",
            "attendance_id": str(att.id) if att else "",
        })

    # Filter options
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

    context = {
        "grid": grid,
        "target_date": target_date,
        "class_name": class_name,
        "section": section,
        "classes": list(classes),
    }

    if request.htmx:
        return render(request, "portal/attendance.html", context)

    return render(request, "portal/attendance.html", context)


def attendance_mark(request):
    """Mark or update attendance for a single student (HTMX POST).

    Expects form data or JSON:
        student_id   – UUID
        date         – ISO date string
        session_type – MORNING | AFTERNOON | FULL_DAY
        status       – PRESENT | ABSENT | LATE | LEAVE
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST

        student_id = uuid.UUID(data["student_id"])
        att_date_str = data.get("date", "")
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date() if att_date_str else date.today()
        session_type = data.get("session_type", Attendance.SessionType.FULL_DAY)
        status = data["status"]
    except (KeyError, ValueError) as exc:
        return HttpResponseBadRequest(f"Invalid data: {exc}")

    user_data = getattr(request, "user_data", None)
    marked_by = uuid.UUID(user_data.user_id) if user_data and user_data.user_id else uuid.uuid4()
    institution_id = getattr(request, "institution", "")

    attendance, created = Attendance.objects.update_or_create(
        student_id=student_id,
        date=att_date,
        session_type=session_type,
        defaults={
            "status": status,
            "marked_by": marked_by,
            "institution_id": institution_id,
        },
    )

    if request.htmx:
        context = {
            "student": attendance.student,
            "status": attendance.status,
            "attendance_id": str(attendance.id),
            "target_date": att_date,
        }
        return render(request, "components/attendance_cell.html", context)

    return JsonResponse({
        "id": str(attendance.id),
        "status": attendance.status,
        "created": created,
    })


def attendance_report(request):
    """Attendance report for a date range.

    Query params:
        start_date – ISO date
        end_date   – ISO date
        class_name – optional filter
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    institution_id = getattr(request, "institution", None)
    today = date.today()

    try:
        start = datetime.strptime(request.GET.get("start_date", ""), "%Y-%m-%d").date()
    except ValueError:
        start = today.replace(day=1)
    try:
        end = datetime.strptime(request.GET.get("end_date", ""), "%Y-%m-%d").date()
    except ValueError:
        end = today

    qs = Attendance.objects.filter(date__gte=start, date__lte=end)
    if institution_id:
        qs = qs.filter(institution_id=institution_id)

    class_name = request.GET.get("class_name", "").strip()
    if class_name:
        qs = qs.filter(student__class_name=class_name)

    total = qs.count()
    present = qs.filter(status__in=["PRESENT", "LATE"]).count()
    absent = qs.filter(status="ABSENT").count()
    leave = qs.filter(status="LEAVE").count()

    context = {
        "start_date": start,
        "end_date": end,
        "total": total,
        "present": present,
        "absent": absent,
        "leave": leave,
        "attendance_pct": round(present / total * 100, 1) if total else 0,
        "class_name": class_name,
    }

    return render(request, "portal/attendance.html", context)
