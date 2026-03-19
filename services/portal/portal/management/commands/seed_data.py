"""Management command to seed demo data for the portal service."""
import random
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from portal.models import Attendance, FeeRecord, Guardian, Student, Timetable, WelfareEvent


FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh",
    "Ayaan", "Krishna", "Ishaan", "Ananya", "Diya", "Saanvi", "Aadhya",
    "Isha", "Priya", "Kavya", "Meera", "Riya", "Tanvi",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Kumar", "Singh", "Gupta", "Reddy",
    "Nair", "Joshi", "Das", "Mehta", "Rao", "Iyer", "Chopra", "Bhat",
]

SUBJECTS = ["Mathematics", "English", "Science", "Social Studies", "Hindi", "Computer Science", "Physical Education", "Art"]


class Command(BaseCommand):
    help = "Seed the portal database with demo data for one institution."

    def add_arguments(self, parser):
        parser.add_argument(
            "--students",
            type=int,
            default=60,
            help="Number of students to create (default: 60)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            FeeRecord.objects.all().delete()
            WelfareEvent.objects.all().delete()
            Attendance.objects.all().delete()
            Guardian.objects.all().delete()
            Timetable.objects.all().delete()
            Student.objects.all().delete()

        institution_id = uuid.UUID("00000000-0000-4000-a000-000000000001")
        num_students = options["students"]
        today = date.today()

        self.stdout.write(f"Seeding {num_students} students for institution {institution_id}...")

        classes = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        sections = ["A", "B"]

        # Create students
        students = []
        for i in range(num_students):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            cls = random.choice(classes)
            sec = random.choice(sections)
            student = Student(
                user_id=uuid.uuid4(),
                institution_id=institution_id,
                academic_level="K-12",
                residential_status=random.choice(
                    [Student.ResidentialStatus.DAY_SCHOLAR] * 7
                    + [Student.ResidentialStatus.HOSTELER] * 2
                    + [Student.ResidentialStatus.TRANSPORT]
                ),
                class_name=cls,
                section=sec,
                roll_number=f"{cls}{sec}{i + 1:03d}",
                admission_date=today - timedelta(days=random.randint(30, 1000)),
                metadata={"name": f"{first} {last}", "email": f"{first.lower()}.{last.lower()}@example.com"},
            )
            students.append(student)

        Student.objects.bulk_create(students)
        self.stdout.write(self.style.SUCCESS(f"  Created {len(students)} students."))

        # Create guardians for each student
        guardians = []
        for student in students:
            guardian = Guardian(
                student=student,
                user_id=uuid.uuid4(),
                relationship=random.choice(["Father", "Mother", "Guardian"]),
                access_level=random.choice([1, 2]),
                is_primary=True,
                metadata={"phone": f"+91{random.randint(7000000000, 9999999999)}"},
            )
            guardians.append(guardian)

        Guardian.objects.bulk_create(guardians)
        self.stdout.write(self.style.SUCCESS(f"  Created {len(guardians)} guardians."))

        # Create attendance for the past 5 weekdays
        staff_id = uuid.uuid4()
        attendance_records = []
        for days_back in range(5):
            att_date = today - timedelta(days=days_back)
            if att_date.weekday() >= 5:  # skip weekends
                continue
            for student in students:
                status = random.choices(
                    ["PRESENT", "ABSENT", "LATE", "LEAVE"],
                    weights=[80, 10, 7, 3],
                    k=1,
                )[0]
                attendance_records.append(
                    Attendance(
                        student=student,
                        date=att_date,
                        session_type=Attendance.SessionType.FULL_DAY,
                        status=status,
                        marked_by=staff_id,
                        institution_id=institution_id,
                    )
                )

        Attendance.objects.bulk_create(attendance_records, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"  Created {len(attendance_records)} attendance records."))

        # Create fee records
        fee_records = []
        fee_types = ["TUITION", "TRANSPORT", "LAB", "LIBRARY", "SPORTS"]
        for student in students:
            for month_offset in range(3):
                due = today.replace(day=10) - timedelta(days=30 * month_offset)
                is_paid = random.random() < 0.7
                fee_records.append(
                    FeeRecord(
                        student=student,
                        institution_id=institution_id,
                        fee_type=random.choice(fee_types),
                        amount=Decimal(random.choice(["5000", "7500", "10000", "15000"])),
                        due_date=due,
                        paid_date=due + timedelta(days=random.randint(0, 5)) if is_paid else None,
                        status=FeeRecord.Status.PAID if is_paid else (
                            FeeRecord.Status.OVERDUE if due < today else FeeRecord.Status.PENDING
                        ),
                    )
                )

        FeeRecord.objects.bulk_create(fee_records)
        self.stdout.write(self.style.SUCCESS(f"  Created {len(fee_records)} fee records."))

        # Create timetables
        timetables = []
        for cls in classes:
            for sec in sections:
                for day in range(1, 7):  # Mon-Sat
                    periods = []
                    for p in range(1, 9):
                        periods.append({
                            "period": p,
                            "subject": SUBJECTS[(p - 1) % len(SUBJECTS)],
                            "teacher": f"Teacher-{random.randint(1, 20)}",
                            "start": f"{7 + p}:00",
                            "end": f"{7 + p}:45",
                        })
                    timetables.append(
                        Timetable(
                            institution_id=institution_id,
                            class_name=cls,
                            section=sec,
                            day_of_week=day,
                            periods=periods,
                        )
                    )

        Timetable.objects.bulk_create(timetables)
        self.stdout.write(self.style.SUCCESS(f"  Created {len(timetables)} timetable entries."))

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
