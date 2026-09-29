"""
Monitoring endpoints.
GET /api/monitoring/summary    — command center metrics
GET /api/monitoring/alerts     — active alerts
GET /api/monitoring/health/{project_id}  — health score + trend
POST /api/monitoring/health/{project_id}/compute  — recompute
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.models.project import Project
from app.models.monitoring import AnomalyEvent, HealthScore
from app.models.inspection import Inspection
from app.models.followup import Followup
from app.models.camera import Camera
from app.schemas.monitoring import MonitoringSummary, AnomalyEventOut, HealthScoreOut, HealthTrendPoint
from app.services.health_service import compute_project_health, save_health_score

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/summary", response_model=MonitoringSummary)
async def get_monitoring_summary(
    current_user=Depends(require_permission(Permission.MONITORING_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Command center summary metrics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = await db.scalar(select(func.count(Project.id)))

    attention = await db.scalar(
        select(func.count(Project.id)).where(
            Project.status.in_(["HIGH_ATTENTION", "INSPECTION_REQUIRED", "ACTION_REQUIRED"])
        )
    )

    high_anomalies = await db.scalar(
        select(func.count(AnomalyEvent.id)).where(
            and_(
                AnomalyEvent.severity.in_(["HIGH", "CRITICAL"]),
                AnomalyEvent.is_acknowledged == False,
            )
        )
    )

    insp_today = await db.scalar(
        select(func.count(Inspection.id)).where(
            Inspection.start_time >= today_start
        )
    )

    open_findings_sum = await db.scalar(
        select(func.sum(Project.open_findings))
    )

    pending_followup = await db.scalar(
        select(func.count(Followup.id)).where(
            Followup.status.in_(["OPEN", "IN_PROGRESS"])
        )
    )

    cameras_offline = await db.scalar(
        select(func.count(Camera.id)).where(Camera.status == "OFFLINE")
    )

    healthy = await db.scalar(
        select(func.count(Project.id)).where(Project.status == "MONITORING")
    )

    watch = await db.scalar(
        select(func.count(Project.id)).where(Project.status == "WATCH")
    )

    critical = await db.scalar(
        select(func.count(Project.id)).where(
            Project.risk_level == "CRITICAL"
        )
    )

    return MonitoringSummary(
        total_projects=total or 0,
        attention_required=attention or 0,
        high_anomalies=high_anomalies or 0,
        inspections_today=insp_today or 0,
        open_findings=int(open_findings_sum or 0),
        pending_followup=pending_followup or 0,
        cameras_offline=cameras_offline or 0,
        healthy_projects=healthy or 0,
        watch_projects=watch or 0,
        critical_projects=critical or 0,
    )


@router.get("/alerts", response_model=list[AnomalyEventOut])
async def get_alerts(
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    current_user=Depends(require_permission(Permission.ANOMALY_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get unacknowledged anomaly alerts."""
    q = (
        select(AnomalyEvent, Project.project_name)
        .join(Project, AnomalyEvent.project_id == Project.id)
        .where(AnomalyEvent.is_acknowledged == False)
    )
    if severity:
        q = q.where(AnomalyEvent.severity == severity)
    q = q.order_by(AnomalyEvent.anomaly_score.desc()).limit(limit)

    result = await db.execute(q)
    rows = result.all()

    alerts = []
    for event, project_name in rows:
        d = {
            "id": event.id,
            "project_id": event.project_id,
            "project_name": project_name,
            "anomaly_score": event.anomaly_score,
            "severity": event.severity,
            "reasons": event.reasons,
            "recommended_action": event.recommended_action,
            "algorithm_version": event.algorithm_version,
            "is_acknowledged": event.is_acknowledged,
            "created_at": event.created_at,
        }
        alerts.append(AnomalyEventOut(**d))
    return alerts


@router.get("/health/{project_id}", response_model=dict)
async def get_project_health(
    project_id: int,
    current_user=Depends(require_permission(Permission.MONITORING_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get latest health score and 30-day trend."""
    # Latest score
    latest = await db.execute(
        select(HealthScore)
        .where(HealthScore.project_id == project_id)
        .order_by(HealthScore.computed_at.desc())
        .limit(1)
    )
    latest_score = latest.scalar_one_or_none()

    # Trend (last 30 days)
    trend_result = await db.execute(
        select(HealthScore)
        .where(HealthScore.project_id == project_id)
        .order_by(HealthScore.computed_at.asc())
        .limit(30)
    )
    trend = trend_result.scalars().all()

    if latest_score:
        score_out = HealthScoreOut(
            total_score=latest_score.total_score,
            status=_score_to_status(latest_score.total_score),
            attendance_score=latest_score.attendance_score,
            reporting_score=latest_score.reporting_score,
            inspection_score=latest_score.inspection_score,
            evidence_score=latest_score.evidence_score,
            timeliness_score=latest_score.timeliness_score,
            findings_score=latest_score.findings_score,
            explanation=latest_score.score_explanation or {},
            computed_at=latest_score.computed_at,
        )
    else:
        score_out = None

    trend_out = [
        {"computed_at": t.computed_at.isoformat(), "total_score": t.total_score}
        for t in trend
    ]

    return {"latest": score_out, "trend": trend_out}


@router.post("/health/{project_id}/compute", response_model=HealthScoreOut)
async def recompute_health(
    project_id: int,
    current_user=Depends(require_permission(Permission.MONITORING_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Recompute health score for a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    score = await compute_project_health(db, project)
    await save_health_score(db, project_id, score)

    # Update project health index
    project.health_index = score.total_score
    project.status = _status_from_health(score.status)

    await db.commit()

    return HealthScoreOut(
        total_score=score.total_score,
        status=score.status,
        attendance_score=score.attendance_score,
        reporting_score=score.reporting_score,
        inspection_score=score.inspection_score,
        evidence_score=score.evidence_score,
        timeliness_score=score.timeliness_score,
        findings_score=score.findings_score,
        explanation=score.explanation,
        computed_at=score.computed_at,
    )


@router.get("/anomaly/{project_id}", response_model=list[AnomalyEventOut])
async def get_project_anomalies(
    project_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(require_permission(Permission.ANOMALY_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get anomaly history for a project."""
    result = await db.execute(
        select(AnomalyEvent, Project.project_name)
        .join(Project)
        .where(AnomalyEvent.project_id == project_id)
        .order_by(AnomalyEvent.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        AnomalyEventOut(
            id=e.id, project_id=e.project_id, project_name=pname,
            anomaly_score=e.anomaly_score, severity=e.severity,
            reasons=e.reasons, recommended_action=e.recommended_action,
            algorithm_version=e.algorithm_version,
            is_acknowledged=e.is_acknowledged, created_at=e.created_at,
        )
        for e, pname in rows
    ]


def _score_to_status(score: float) -> str:
    if score >= 80: return "HEALTHY"
    if score >= 65: return "WATCH"
    if score >= 45: return "HIGH_ATTENTION"
    return "CRITICAL"


def _status_from_health(health_status: str) -> str:
    mapping = {
        "HEALTHY": "MONITORING",
        "WATCH": "WATCH",
        "HIGH_ATTENTION": "HIGH_ATTENTION",
        "CRITICAL": "INSPECTION_REQUIRED",
    }
    return mapping.get(health_status, "WATCH")
