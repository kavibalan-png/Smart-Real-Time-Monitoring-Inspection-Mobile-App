"""
CCTV monitoring endpoints.
GET  /api/cctv              — all cameras
GET  /api/cctv/{id}         — camera detail
POST /api/cctv/{id}/heartbeat — update heartbeat
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.models.camera import Camera, CameraEvent

router = APIRouter(prefix="/cctv", tags=["CCTV"])


@router.get("", response_model=list)
async def list_cameras(
    project_id: int | None = None,
    current_user=Depends(require_permission(Permission.CCTV_READ)),
    db: AsyncSession = Depends(get_db),
):
    q = select(Camera)
    if project_id:
        q = q.where(Camera.project_id == project_id)
    q = q.order_by(Camera.project_id)
    result = await db.execute(q)
    cameras = result.scalars().all()

    return [
        {
            "id": c.id,
            "project_id": c.project_id,
            "camera_name": c.camera_name,
            "location_description": c.location_description,
            "status": c.status,
            "demo_video_url": c.demo_video_url,
            "last_heartbeat": c.last_heartbeat.isoformat() if c.last_heartbeat else None,
            "is_demo": c.is_demo,
            "label": "SIMULATED CCTV — DEMO FEED" if c.is_demo else "LIVE FEED",
        }
        for c in cameras
    ]


@router.get("/summary", response_model=dict)
async def get_cctv_summary(
    current_user=Depends(require_permission(Permission.CCTV_READ)),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count(Camera.id)))
    live = await db.scalar(select(func.count(Camera.id)).where(Camera.status == "LIVE"))
    offline = await db.scalar(select(func.count(Camera.id)).where(Camera.status == "OFFLINE"))
    degraded = await db.scalar(select(func.count(Camera.id)).where(Camera.status == "DEGRADED"))
    return {
        "total": total or 0,
        "live": live or 0,
        "offline": offline or 0,
        "degraded": degraded or 0,
        "health_pct": round((live or 0) / max(total or 1, 1) * 100, 1),
    }


@router.get("/{camera_id}", response_model=dict)
async def get_camera(
    camera_id: int,
    current_user=Depends(require_permission(Permission.CCTV_READ)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Recent events
    events_result = await db.execute(
        select(CameraEvent)
        .where(CameraEvent.camera_id == camera_id)
        .order_by(CameraEvent.created_at.desc())
        .limit(10)
    )
    events = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "description": e.description,
            "severity": e.severity,
            "created_at": e.created_at.isoformat(),
        }
        for e in events_result.scalars().all()
    ]

    return {
        "id": camera.id,
        "project_id": camera.project_id,
        "camera_name": camera.camera_name,
        "location_description": camera.location_description,
        "status": camera.status,
        "demo_video_url": camera.demo_video_url,
        "last_heartbeat": camera.last_heartbeat.isoformat() if camera.last_heartbeat else None,
        "recent_events": events,
        "is_demo": camera.is_demo,
        "notice": "SIMULATED CCTV — Demo feed only. Not connected to production CCTV infrastructure.",
    }


@router.post("/{camera_id}/heartbeat")
async def camera_heartbeat(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Update camera heartbeat — called by CCTV adapter."""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera.last_heartbeat = datetime.now(timezone.utc)
    if camera.status == "OFFLINE":
        camera.status = "LIVE"
        event = CameraEvent(
            camera_id=camera_id,
            event_type="ONLINE",
            description="Camera came back online",
            severity="INFO",
        )
        db.add(event)

    await db.commit()
    return {"status": camera.status, "heartbeat": camera.last_heartbeat.isoformat()}
