"""Follow-up schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FollowupCreate(BaseModel):
    project_id: int
    inspection_id: Optional[int] = None
    action_type: str
    description: str
    due_date: Optional[datetime] = None


class FollowupOut(BaseModel):
    id: int
    followup_code: str
    project_id: int
    inspection_id: Optional[int]
    action_type: str
    description: str
    due_date: Optional[datetime]
    status: str
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowupResolve(BaseModel):
    resolution_notes: str
