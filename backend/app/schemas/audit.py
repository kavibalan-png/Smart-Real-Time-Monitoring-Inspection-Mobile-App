"""Audit log schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    user_id: Optional[int]
    role: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    result: str
    metadata: Optional[dict]

    model_config = {"from_attributes": True}
