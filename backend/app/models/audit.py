"""Audit log model — append-only, never modified by ordinary users."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # LOGIN / LOGOUT / ANOMALY / ALERT / ASSIGNMENT / ROUTE_GENERATION
    # INSPECTION_START / EVIDENCE_CAPTURE / EVIDENCE_HASH / EVIDENCE_VERIFY
    # VC_START / OFFICIAL_REVIEW / DECISION / FOLLOWUP / CASE_CLOSE
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    # SUCCESS / FAILURE / DENIED
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_action_time", "action", "timestamp"),
        Index("ix_audit_user_time", "user_id", "timestamp"),
    )
