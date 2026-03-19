"""Portal service URL configuration."""
from django.urls import include, path

from portal.views.dashboard import dashboard_view
from portal.views.students import (
    student_create,
    student_detail,
    student_list,
    student_update,
)
from portal.views.attendance import (
    attendance_grid,
    attendance_mark,
    attendance_report,
)
from portal.views.fees import (
    fee_dashboard,
    fee_record_payment,
    fee_student_history,
)
from portal.views.health import health_check

urlpatterns = [
    # Dashboard
    path("dashboard/", dashboard_view, name="dashboard"),
    # Students
    path("students/", student_list, name="student-list"),
    path("students/create/", student_create, name="student-create"),
    path("students/<uuid:student_id>/", student_detail, name="student-detail"),
    path("students/<uuid:student_id>/update/", student_update, name="student-update"),
    # Attendance
    path("attendance/", attendance_grid, name="attendance-grid"),
    path("attendance/mark/", attendance_mark, name="attendance-mark"),
    path("attendance/report/", attendance_report, name="attendance-report"),
    # Fees
    path("fees/", fee_dashboard, name="fee-dashboard"),
    path("fees/student/<uuid:student_id>/", fee_student_history, name="fee-student-history"),
    path("fees/record/", fee_record_payment, name="fee-record-payment"),
    # Staff / Timetable – placeholders
    path("staff/", dashboard_view, name="staff"),
    path("timetable/", dashboard_view, name="timetable"),
    # Health
    path("health/", health_check, name="health"),
    # Super Admin
    path("sa/", include("portal.sa_urls")),
]
