"""Report generation service with cross-schema queries."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def generate_attendance_report(
    session: AsyncSession, institution_id: UUID, start_date: str, end_date: str
) -> dict:
    """Generate attendance report using cross-schema query to portal.attendance."""
    query = text("""
        SELECT
            a.date,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE a.status = 'PRESENT') AS present,
            COUNT(*) FILTER (WHERE a.status = 'ABSENT') AS absent,
            COUNT(*) FILTER (WHERE a.status = 'LATE') AS late
        FROM portal.attendance a
        WHERE a.institution_id = :institution_id
            AND a.date BETWEEN :start_date AND :end_date
        GROUP BY a.date
        ORDER BY a.date
    """)
    result = await session.execute(
        query,
        {
            "institution_id": str(institution_id),
            "start_date": start_date,
            "end_date": end_date,
        },
    )
    rows = result.fetchall()
    return {
        "daily_breakdown": [
            {
                "date": str(row.date),
                "total": row.total,
                "present": row.present,
                "absent": row.absent,
                "late": row.late,
                "attendance_pct": round(row.present / row.total * 100, 1) if row.total > 0 else 0,
            }
            for row in rows
        ]
    }


async def generate_exam_performance_report(
    session: AsyncSession, institution_id: UUID, test_id: UUID | None = None
) -> dict:
    """Generate exam performance report using cross-schema query to exam.results."""
    query = text("""
        SELECT
            r.test_id,
            COUNT(*) AS participants,
            AVG(r.percentage) AS avg_percentage,
            MAX(r.percentage) AS max_percentage,
            MIN(r.percentage) AS min_percentage
        FROM exam.results r
        WHERE r.institution_id = :institution_id
            AND (:test_id IS NULL OR r.test_id = :test_id)
        GROUP BY r.test_id
    """)
    result = await session.execute(
        query,
        {"institution_id": str(institution_id), "test_id": str(test_id) if test_id else None},
    )
    rows = result.fetchall()
    return {
        "tests": [
            {
                "test_id": str(row.test_id),
                "participants": row.participants,
                "avg_percentage": round(float(row.avg_percentage), 1),
                "max_percentage": round(float(row.max_percentage), 1),
                "min_percentage": round(float(row.min_percentage), 1),
            }
            for row in rows
        ]
    }
