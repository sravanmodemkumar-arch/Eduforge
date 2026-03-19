"""Fee management views."""
import json
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render

from portal.models import FeeRecord, Student


def fee_dashboard(request):
    """Overview of fee collection and outstanding amounts."""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    institution_id = getattr(request, "institution", None)
    today = date.today()

    qs = FeeRecord.objects.all()
    if institution_id:
        qs = qs.filter(institution_id=institution_id)

    # This month's collection
    paid_this_month = (
        qs.filter(
            status=FeeRecord.Status.PAID,
            paid_date__year=today.year,
            paid_date__month=today.month,
        )
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    # Outstanding
    pending_total = (
        qs.filter(status__in=[FeeRecord.Status.PENDING, FeeRecord.Status.OVERDUE])
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    overdue_count = qs.filter(status=FeeRecord.Status.OVERDUE).count()

    # Recent payments
    recent_payments = (
        qs.filter(status=FeeRecord.Status.PAID)
        .select_related("student")
        .order_by("-paid_date")[:20]
    )

    # Students with overdue fees
    overdue_records = (
        qs.filter(status=FeeRecord.Status.OVERDUE)
        .select_related("student")
        .order_by("due_date")[:20]
    )

    context = {
        "paid_this_month": paid_this_month,
        "pending_total": pending_total,
        "overdue_count": overdue_count,
        "recent_payments": recent_payments,
        "overdue_records": overdue_records,
        "today": today,
    }

    return render(request, "portal/dashboard.html", context)


def fee_student_history(request, student_id: uuid.UUID):
    """Fee history for a specific student."""
    student = get_object_or_404(Student, pk=student_id)
    records = student.fee_records.order_by("-due_date")

    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        records = records.filter(status=status_filter)

    total_due = records.filter(
        status__in=[FeeRecord.Status.PENDING, FeeRecord.Status.OVERDUE]
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    total_paid = records.filter(
        status=FeeRecord.Status.PAID
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    context = {
        "student": student,
        "records": records,
        "total_due": total_due,
        "total_paid": total_paid,
        "status_filter": status_filter,
    }

    return render(request, "portal/student_list.html", context)


def fee_record_payment(request):
    """Record a fee payment.

    POST data:
        student_id  – UUID
        fee_type    – string
        amount      – decimal
        due_date    – ISO date
        paid_date   – ISO date (optional, defaults to today)
        payment_id  – external payment reference (optional)
        status      – PAID | PENDING | OVERDUE | WAIVED (defaults to PAID)
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST

        student_id = uuid.UUID(data["student_id"])
        amount = Decimal(data["amount"])
        due_date_str = data.get("due_date", "")
        due_date_val = (
            date.fromisoformat(due_date_str) if due_date_str else date.today()
        )
        paid_date_str = data.get("paid_date", "")
        paid_date_val = (
            date.fromisoformat(paid_date_str) if paid_date_str else date.today()
        )
    except (KeyError, ValueError, InvalidOperation) as exc:
        return HttpResponseBadRequest(f"Invalid data: {exc}")

    institution_id = getattr(request, "institution", "")

    record = FeeRecord.objects.create(
        student_id=student_id,
        institution_id=institution_id,
        fee_type=data.get("fee_type", "TUITION"),
        amount=amount,
        due_date=due_date_val,
        paid_date=paid_date_val,
        payment_id=data.get("payment_id", ""),
        status=data.get("status", FeeRecord.Status.PAID),
    )

    if request.htmx:
        context = {"record": record}
        return render(request, "components/stats_card.html", context)

    return JsonResponse({"id": str(record.id), "status": record.status}, status=201)
