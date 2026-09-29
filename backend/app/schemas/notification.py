"""Notification schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    priority: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
