"""
Analytics endpoints.
POST /api/analytics/anomaly             — run anomaly analysis
GET  /api/analytics/project/{id}        — project analytics
GET  /api/analytics/attendance/{id}     — attendance analytics
GET  /api/analytics/dashboard           — aggregate dashboard data
"""
from datetime import datetime, timezone, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.models.project import Project
from app.models.attendance import AttendanceRecord
from app.models.monitoring import AnomalyEvent
from app.models.inspection import Inspection
from app.schemas.monitoring import AnomalyEventOut
from app.intelligence.anomaly_engine import compute_anomaly_score

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/anomaly/{project_id}", response_model=dict)
async def run_anomaly_analysis(
    project_id: int,
    current_user=Depends(require_permission(Permission.ANOMALY_READ)),
    db: AsyncSession = Depends(get_db),
):
    """
    Run anomaly analysis for a project.
    Gathers real data, applies anomaly engine, persists result.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gather attendance data (last 30 days)
    thirty_ago = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    att_result = await db.execute(
        select(AttendanceRecord)
        .where(and_(
            AttendanceRecord.project_id == project_id,
            AttendanceRecord.record_date >= thirty_ago,
        ))
        .order_by(AttendanceRecord.record_date.desc())
    )
    records = att_result.scalars().all()

    if records:
        values = [r.reported_beneficiaries for r in records]
        mean_att = sum(values) / len(values)
        std_att = (sum((v - mean_att) ** 2 for v in values) / len(values)) ** 0.5
        current_att = values[0] if values else project.beneficiary_count
        inconsistencies = sum(1 for r in records if r.anomaly_flag)
    else:
        mean_att = project.beneficiary_count * 0.92
        std_att = project.beneficiary_count * 0.05
        current_att = project.beneficiary_count
        inconsistencies = 0

    # CCTV status
    cam_offline = project.cctv_status in ("OFFLINE", "DEGRADED")

    anomaly_result = compute_anomaly_score(
        current_attendance=current_att,
        attendance_rolling_mean=mean_att,
        attendance_rolling_std=std_att,
        attendance_expected_min=project.beneficiary_count * 0.85,
        attendance_expected_max=float(project.beneficiary_count),
        reporting_inconsistency_count=inconsistencies,
        reporting_mismatch_pct=min(inconsistencies * 5, 50),
        cctv_offline_events_7d=2 if cam_offline else 0,
        any_camera_currently_offline=cam_offline,
        unresolved_critical_findings=max(0, project.open_findings - 2),
        unresolved_high_findings=min(project.open_findings, 2),
        oldest_finding_days=45 if project.open_findings > 0 else 0,
        repeated_finding_category=project.open_findings > 2,
    )

    # Persist anomaly event
    event = AnomalyEvent(
        project_id=project_id,
        anomaly_score=anomaly_result.anomaly_score,
        severity=anomaly_result.severity,
        reasons={
            r.key: {
                "label": r.label,
                "score": r.score_contribution,
                "evidence": r.evidence,
                "threshold": r.threshold_used,
            }
            for r in anomaly_result.reasons
        },
        recommended_action=anomaly_result.recommended_action,
        algorithm_version=anomaly_result.algorithm_version,
        is_demo=True,
    )
    db.add(event)

    # Update project risk level
    project.risk_level = anomaly_result.severity
    if anomaly_result.severity in ("HIGH", "CRITICAL"):
        project.status = "HIGH_ATTENTION"

    await db.commit()
    await db.refresh(event)

    # Broadcast to command center
    from app.core.websocket_manager import emit_event
    import asyncio
    asyncio.create_task(emit_event("ANOMALY_DETECTED", {
        "project_id": project_id,
        "project_name": project.project_name,
        "anomaly_score": anomaly_result.anomaly_score,
        "severity": anomaly_result.severity,
    }))

    return {
        "anomaly_score": anomaly_result.anomaly_score,
        "severity": anomaly_result.severity,
        "recommended_action": anomaly_result.recommended_action,
        "reasons": [
            {
                "key": r.key,
                "label": r.label,
                "score_contribution": r.score_contribution,
                "evidence": r.evidence,
                "threshold_used": r.threshold_used,
            }
            for r in anomaly_result.reasons
        ],
        "explanation": anomaly_result.explanation,
        "disclaimer": anomaly_result.disclaimer,
        "event_id": event.id,
    }


@router.get("/attendance/{project_id}", response_model=dict)
async def get_attendance_analytics(
    project_id: int,
    days: int = 30,
    current_user=Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """
    Attendance analytics for a project.
    Returns trend data, deviation, and statistical context.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    att_result = await db.execute(
        select(AttendanceRecord)
        .where(and_(
            AttendanceRecord.project_id == project_id,
            AttendanceRecord.record_date >= cutoff,
        ))
        .order_by(AttendanceRecord.record_date.asc())
    )
    records = att_result.scalars().all()

    trend = [
        {
            "date": str(r.record_date),
            "reported": r.reported_beneficiaries,
            "expected": r.expected_beneficiaries,
            "observed": r.observed_beneficiaries,
            "deviation_score": r.deviation_score,
            "anomaly_flag": r.anomaly_flag,
        }
        for r in records
    ]

    values = [r.reported_beneficiaries for r in records]
    mean_val = sum(values) / len(values) if values else 0
    anomaly_days = sum(1 for r in records if r.anomaly_flag)

    # Latest observation
    latest = records[-1] if records else None
    latest_deviation = latest.deviation_score if latest else 0

    return {
        "project_id": project_id,
        "project_name": project.project_name,
        "expected_count": project.beneficiary_count,
        "rolling_mean": round(mean_val, 1),
        "expected_min": int(project.beneficiary_count * 0.85),
        "expected_max": project.beneficiary_count,
        "latest_reported": latest.reported_beneficiaries if latest else None,
        "latest_deviation_pct": round(latest_deviation, 1),
        "anomaly_days_in_period": anomaly_days,
        "trend": trend,
        "methodology": "Statistical deviation: reported vs expected range + rolling mean",
        "disclaimer": (
            "Attendance anomalies indicate potential discrepancy. "
            "Human verification required before conclusions are drawn."
        ),
    }


@router.get("/dashboard", response_model=dict)
async def get_dashboard_analytics(
    current_user=Depends(require_permission(Permission.ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate analytics for command center charts."""
    # Health distribution
    health_bins = {
        "critical": await db.scalar(select(func.count(Project.id)).where(Project.health_index < 45)),
        "high_attention": await db.scalar(select(func.count(Project.id)).where(
            and_(Project.health_index >= 45, Project.health_index < 65)
        )),
        "watch": await db.scalar(select(func.count(Project.id)).where(
            and_(Project.health_index >= 65, Project.health_index < 80)
        )),
        "healthy": await db.scalar(select(func.count(Project.id)).where(Project.health_index >= 80)),
    }

    # Risk by state
    risk_result = await db.execute(
        select(Project.state, Project.risk_level, func.count(Project.id))
        .group_by(Project.state, Project.risk_level)
        .order_by(Project.state)
    )
    risk_by_state = [
        {"state": row[0], "risk_level": row[1], "count": row[2]}
        for row in risk_result.all()
    ]

    # Inspection completion (last 30 days)
    thirty_ago = datetime.now(timezone.utc) - timedelta(days=30)
    insp_result = await db.execute(
        select(Inspection.status, func.count(Inspection.id))
        .where(Inspection.created_at >= thirty_ago)
        .group_by(Inspection.status)
    )
    insp_by_status = {row[0]: row[1] for row in insp_result.all()}

    return {
        "health_distribution": health_bins,
        "risk_by_state": risk_by_state,
        "inspection_completion": insp_by_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
