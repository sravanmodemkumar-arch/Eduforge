"""Portal domain models."""
import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models


class Student(models.Model):
    """Student profile linked to a user in the identity service."""

    class ResidentialStatus(models.TextChoices):
        DAY_SCHOLAR = "DAY_SCHOLAR", "Day Scholar"
        HOSTELER = "HOSTELER", "Hosteler"
        TRANSPORT = "TRANSPORT", "Transport"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(
        help_text="References the user record in the Identity service.",
        db_index=True,
    )
    institution_id = models.UUIDField(db_index=True)
    academic_level = models.CharField(max_length=50, blank=True, default="")
    residential_status = models.CharField(
        max_length=20,
        choices=ResidentialStatus.choices,
        default=ResidentialStatus.DAY_SCHOLAR,
    )
    special_statuses = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="E.g. scholarship, special_needs, sports_quota",
    )
    class_name = models.CharField(max_length=30, db_index=True)
    section = models.CharField(max_length=10, blank=True, default="")
    roll_number = models.CharField(max_length=20, blank=True, default="")
    admission_date = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student"
        ordering = ["class_name", "section", "roll_number"]

    def __str__(self):
        return f"Student {self.roll_number} ({self.class_name}-{self.section})"


class Guardian(models.Model):
    """Guardian / parent linked to a student."""

    class AccessLevel(models.IntegerChoices):
        PRE_PRIMARY_PARENT = 1, "Pre-Primary Parent"
        PRIMARY_PARENT = 2, "Primary Parent"
        SECONDARY_GUARDIAN = 3, "Secondary Guardian"
        LIMITED_ACCESS = 4, "Limited Access"
        EMERGENCY_ONLY = 5, "Emergency Only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="guardians",
    )
    user_id = models.UUIDField(
        help_text="References the guardian user in the Identity service.",
        db_index=True,
    )
    relationship = models.CharField(max_length=30)
    access_level = models.IntegerField(
        choices=AccessLevel.choices,
        default=AccessLevel.PRIMARY_PARENT,
    )
    is_primary = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "guardian"

    def __str__(self):
        return f"Guardian for {self.student_id} ({self.relationship})"


class Attendance(models.Model):
    """Daily attendance record per student per session."""

    class SessionType(models.TextChoices):
        MORNING = "MORNING", "Morning"
        AFTERNOON = "AFTERNOON", "Afternoon"
        FULL_DAY = "FULL_DAY", "Full Day"

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        LEAVE = "LEAVE", "Leave"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)
    session_type = models.CharField(
        max_length=10,
        choices=SessionType.choices,
        default=SessionType.FULL_DAY,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    marked_by = models.UUIDField(
        help_text="User ID of the staff member who marked attendance.",
    )
    institution_id = models.UUIDField(db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date", "session_type"],
                name="uq_attendance_student_date_session",
            ),
        ]

    def __str__(self):
        return f"{self.student_id} {self.date} {self.session_type}: {self.status}"


class WelfareEvent(models.Model):
    """Welfare / incident tracking for students."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="welfare_events",
    )
    event_type = models.CharField(max_length=50)
    severity = models.IntegerField(
        help_text="1 = low, 4 = critical",
        choices=[(i, str(i)) for i in range(1, 5)],
    )
    description = models.TextField(blank=True, default="")
    reported_by = models.UUIDField()
    action_taken = models.TextField(blank=True, default="")
    resolved = models.BooleanField(default=False)
    institution_id = models.UUIDField(db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "welfare_event"
        ordering = ["-created_at"]

    def __str__(self):
        return f"WelfareEvent {self.event_type} (severity={self.severity})"


class Timetable(models.Model):
    """Weekly timetable for a class-section within an institution."""

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField(db_index=True)
    class_name = models.CharField(max_length=30)
    section = models.CharField(max_length=10, blank=True, default="")
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    periods = models.JSONField(
        default=list,
        help_text=(
            'List of period objects, e.g. [{"period": 1, "subject": "Math", '
            '"teacher": "...", "start": "08:00", "end": "08:45"}]'
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "timetable"
        ordering = ["class_name", "section", "day_of_week"]

    def __str__(self):
        return f"Timetable {self.class_name}-{self.section} Day {self.day_of_week}"


class FeeRecord(models.Model):
    """Individual fee line-item for a student."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"
        WAIVED = "WAIVED", "Waived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="fee_records",
    )
    institution_id = models.UUIDField(db_index=True)
    fee_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    payment_id = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fee_record"
        ordering = ["-due_date"]

    def __str__(self):
        return f"Fee {self.fee_type} {self.amount} ({self.status})"
