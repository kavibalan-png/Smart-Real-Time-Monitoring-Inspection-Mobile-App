"""Follow-up and compliance tracking model."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Followup(Base):
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    followup_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    inspection_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("inspections.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # APPROVE / REINSPECTION / ESCALATE / DOCUMENTS_REQUESTED / CLOSE
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    # OPEN / IN_PROGRESS / RESOLVED / CLOSED / OVERDUE

    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="followups")

    __table_args__ = (
        Index("ix_followup_project_status", "project_id", "status"),
    )
