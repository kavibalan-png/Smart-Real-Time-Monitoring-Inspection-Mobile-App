"""Citizen/beneficiary feedback model."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    submitted_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # GENERAL / SERVICE_QUALITY / STAFF_BEHAVIOR / FACILITY / OTHER
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="RECEIVED")
    # RECEIVED / REVIEWED / ACTIONED / CLOSED
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
