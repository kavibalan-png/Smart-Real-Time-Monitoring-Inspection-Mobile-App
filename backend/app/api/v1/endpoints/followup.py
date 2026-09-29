"""
Follow-up / compliance endpoints.
POST /api/followups           — create follow-up
GET  /api/followups           — list follow-ups
GET  /api/followups/{id}      — detail
PUT  /api/followups/{id}/resolve — resolve
"""
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.permissions import Permission
from app.models.followup import Followup
from app.models.project import Project
from app.schemas.followup import FollowupCreate, FollowupOut, FollowupResolve
from app.services.audit_service import log_action

router = APIRouter(prefix="/followups", tags=["Follow-up"])


@router.post("", response_model=FollowupOut, status_code=201)
async def create_followup(
    body: FollowupCreate,
    current_user=Depends(require_permission(Permission.FOLLOWUP_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    proj_result = await db.execute(select(Project).where(Project.id == body.project_id))
    if not proj_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    code = f"FU-{datetime.now(timezone.utc).year}-{secrets.token_hex(3).upper()}"
    fu = Followup(
        followup_code=code,
        project_id=body.project_id,
        inspection_id=body.inspection_id,
        created_by=current_user.id,
        action_type=body.action_type,
        description=body.description,
        due_date=body.due_date,
        status="OPEN",
        is_demo=True,
    )
    db.add(fu)
    await log_action(
        db,
        action="FOLLOWUP",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="followup",
        metadata={"code": code, "action_type": body.action_type},
    )
    await db.commit()
    await db.refresh(fu)
    return fu


@router.get("", response_model=dict)
async def list_followups(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    project_id: int | None = None,
    status: str | None = None,
    current_user=Depends(require_permission(Permission.FOLLOWUP_READ)),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if project_id:
        filters.append(Followup.project_id == project_id)
    if status:
        filters.append(Followup.status == status)

    q = select(Followup)
    if filters:
        q = q.where(and_(*filters))

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    q = q.order_by(Followup.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    return {
        "items": [FollowupOut.model_validate(f) for f in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{followup_id}", response_model=FollowupOut)
async def get_followup(
    followup_id: int,
    current_user=Depends(require_permission(Permission.FOLLOWUP_READ)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Followup).where(Followup.id == followup_id))
    fu = result.scalar_one_or_none()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return fu


@router.put("/{followup_id}/resolve")
async def resolve_followup(
    followup_id: int,
    body: FollowupResolve,
    current_user=Depends(require_permission(Permission.FOLLOWUP_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Followup).where(Followup.id == followup_id))
    fu = result.scalar_one_or_none()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    fu.status = "RESOLVED"
    fu.resolution_notes = body.resolution_notes
    fu.resolved_by = current_user.id
    fu.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    return {"status": "RESOLVED", "resolved_at": fu.resolved_at.isoformat()}
