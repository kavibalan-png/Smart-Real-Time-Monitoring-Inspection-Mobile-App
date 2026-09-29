"""
Notification endpoints.
GET /api/notifications           — list for current user
PUT /api/notifications/{id}/read — mark as read
PUT /api/notifications/read-all  — mark all read
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
async def list_notifications(
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Notification.user_id == current_user.id]
    if unread_only:
        filters.append(Notification.is_read == False)

    q = select(Notification).where(and_(*filters))
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    q = q.order_by(Notification.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    items = result.scalars().all()

    unread_count = await db.scalar(
        select(func.count(Notification.id)).where(
            and_(Notification.user_id == current_user.id, Notification.is_read == False)
        )
    ) or 0

    return {
        "items": [
            {
                "id": n.id,
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "priority": n.priority,
                "resource_type": n.resource_type,
                "resource_id": n.resource_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ],
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "per_page": per_page,
    }


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,  # ownership check
            )
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "read"}


@router.put("/read-all")
async def mark_all_read(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            and_(Notification.user_id == current_user.id, Notification.is_read == False)
        )
    )
    unread = result.scalars().all()
    now = datetime.now(timezone.utc)
    for n in unread:
        n.is_read = True
        n.read_at = now
    await db.commit()
    return {"marked_read": len(unread)}
