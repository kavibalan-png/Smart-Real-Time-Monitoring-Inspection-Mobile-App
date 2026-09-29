"""
Health index computation service.
Gathers data from DB and calls the health engine.
"""
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.project import Project
from app.models.attendance import AttendanceRecord
from app.models.inspection import Inspection, InspectionFinding
from app.models.followup import Followup
from app.models.evidence import Evidence, EvidenceVerification
from app.intelligence.health_engine import compute_health_score, HealthScoreResult
from app.models.monitoring import HealthScore


async def compute_project_health(
    db: AsyncSession, project: Project
) -> HealthScoreResult:
    """Gather metrics and compute health score for a project."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).date()

    # Attendance metrics
    att_result = await db.execute(
        select(
            func.avg(AttendanceRecord.deviation_score).label("avg_dev"),
            func.count(AttendanceRecord.id).filter(AttendanceRecord.anomaly_flag == True).label("anomaly_days"),
        ).where(
            and_(
                AttendanceRecord.project_id == project.id,
                AttendanceRecord.record_date >= thirty_days_ago,
            )
        )
    )
    att_row = att_result.one()
    avg_deviation = float(att_row.avg_dev or 0)
    anomaly_days = int(att_row.anomaly_days or 0)

    # Days since last inspection
    days_since_inspection = 999
    last_rating = None
    if project.last_inspection:
        days_since_inspection = (now - project.last_inspection).days

    last_insp = await db.execute(
        select(Inspection).where(
            Inspection.project_id == project.id
        ).order_by(Inspection.created_at.desc()).limit(1)
    )
    last_insp_rec = last_insp.scalar_one_or_none()
    if last_insp_rec:
        last_rating = last_insp_rec.overall_rating

    # Open findings
    findings_result = await db.execute(
        select(
            func.count(InspectionFinding.id).filter(
                and_(InspectionFinding.severity == "CRITICAL", InspectionFinding.status == "OPEN")
            ).label("critical"),
            func.count(InspectionFinding.id).filter(
                and_(InspectionFinding.severity == "HIGH", InspectionFinding.status == "OPEN")
            ).label("high"),
            func.count(InspectionFinding.id).filter(
                InspectionFinding.status.in_(["OPEN", "IN_PROGRESS"])
            ).label("total"),
        ).join(Inspection).where(Inspection.project_id == project.id)
    )
    f_row = findings_result.one()

    # Overdue followups
    overdue_fu = await db.execute(
        select(func.count(Followup.id)).where(
            and_(
                Followup.project_id == project.id,
                Followup.status.in_(["OPEN", "IN_PROGRESS"]),
                Followup.due_date < now,
            )
        )
    )
    overdue_count = int(overdue_fu.scalar() or 0)

    # Reporting rate (last 30 days)
    expected_reports = 30
    submitted_reports = await db.execute(
        select(func.count(AttendanceRecord.id)).where(
            and_(
                AttendanceRecord.project_id == project.id,
                AttendanceRecord.record_date >= thirty_days_ago,
            )
        )
    )
    submitted = int(submitted_reports.scalar() or 0)
    report_rate = min(100.0, (submitted / max(expected_reports, 1)) * 100)

    result = compute_health_score(
        attendance_deviation_pct=avg_deviation,
        attendance_anomaly_days=anomaly_days,
        reports_submitted_pct=report_rate,
        reporting_inconsistencies=max(0, 30 - submitted),  # proxy for missing reports
        days_since_last_inspection=days_since_inspection,
        last_inspection_rating=last_rating,
        inspection_overdue=(days_since_inspection > 90),
        evidence_completeness_pct=85.0 if project.open_findings == 0 else 70.0,
        evidence_integrity_failures=0,
        avg_response_days=3.0 if overdue_count == 0 else 10.0,
        overdue_followups=overdue_count,
        open_critical_findings=int(f_row.critical or 0),
        open_high_findings=int(f_row.high or 0),
        unresolved_findings_total=int(f_row.total or 0),
    )
    return result


async def save_health_score(
    db: AsyncSession, project_id: int, result: HealthScoreResult
) -> HealthScore:
    """Persist a health score snapshot."""
    hs = HealthScore(
        project_id=project_id,
        total_score=result.total_score,
        attendance_score=result.attendance_score,
        reporting_score=result.reporting_score,
        inspection_score=result.inspection_score,
        evidence_score=result.evidence_score,
        timeliness_score=result.timeliness_score,
        findings_score=result.findings_score,
        score_explanation=result.explanation,
        computed_at=result.computed_at,
        is_demo=True,
    )
    db.add(hs)
    return hs
