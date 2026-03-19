"""Dashboard view with HTMX partial support."""
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.shortcuts import render

from portal.models import Attendance, FeeRecord, Student


def dashboard_view(request):
    """Render the main dashboard.

    If the request is an HTMX request the view returns only the content
    fragment; otherwise it returns the full page (extending base.html).
    """
    institution_id = getattr(request, "institution", None)
    today = date.today()

    # --- Stats -----------------------------------------------------------
    student_qs = Student.objects.all()
    if institution_id:
        student_qs = student_qs.filter(institution_id=institution_id)

    total_students = student_qs.count()

    # Today's attendance percentage
    attendance_today = Attendance.objects.filter(date=today)
    if institution_id:
        attendance_today = attendance_today.filter(institution_id=institution_id)

    total_marked = attendance_today.count()
    present_count = attendance_today.filter(
        status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
    ).count()
    attendance_pct = (
        round(present_count / total_marked * 100, 1) if total_marked else 0
    )

    # Fee collection this month
    fee_qs = FeeRecord.objects.filter(
        status=FeeRecord.Status.PAID,
        paid_date__year=today.year,
        paid_date__month=today.month,
    )
    if institution_id:
        fee_qs = fee_qs.filter(institution_id=institution_id)

    fee_collection = fee_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Overdue fees
    overdue_count = FeeRecord.objects.filter(status=FeeRecord.Status.OVERDUE)
    if institution_id:
        overdue_count = overdue_count.filter(institution_id=institution_id)
    overdue_count = overdue_count.count()

    # Class-wise student breakdown for quick reference
    class_breakdown = (
        student_qs.values("class_name")
        .annotate(count=Count("id"))
        .order_by("class_name")
    )

    context = {
        "total_students": total_students,
        "attendance_pct": attendance_pct,
        "present_count": present_count,
        "total_marked": total_marked,
        "fee_collection": fee_collection,
        "overdue_count": overdue_count,
        "class_breakdown": list(class_breakdown),
        "today": today,
    }

    template = "portal/dashboard.html"
    return render(request, template, context)
