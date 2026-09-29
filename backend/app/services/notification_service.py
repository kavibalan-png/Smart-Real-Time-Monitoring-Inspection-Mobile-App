"""Notification creation service."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "MEDIUM",
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    extra_data: Optional[dict] = None,
) -> Notification:
    """Create a notification for a user."""
    notif = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        priority=priority,
        resource_type=resource_type,
        resource_id=resource_id,
        extra_data=extra_data,
        is_demo=True,
    )
    db.add(notif)
    return notif
