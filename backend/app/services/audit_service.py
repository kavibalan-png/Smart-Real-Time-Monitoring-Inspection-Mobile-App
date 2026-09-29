"""
Audit logging service.
Append-only — never modifies existing records.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    user_id: Optional[int] = None,
    role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    result: str = "SUCCESS",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None,
    is_demo: bool = True,
) -> AuditLog:
    """Create an immutable audit log entry."""
    log = AuditLog(
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        role=role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        ip_address=ip_address,
        user_agent=user_agent,
        event_metadata=metadata or {},
        is_demo=is_demo,
    )
    db.add(log)
    # Note: caller must commit — allows batching with parent transaction
    return log
