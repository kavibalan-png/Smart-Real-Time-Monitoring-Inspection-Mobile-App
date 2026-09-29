"""Attendance record model."""
from datetime import datetime, date, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    reported_beneficiaries: Mapped[int] = mapped_column(Integer, default=0)
    reported_staff: Mapped[int] = mapped_column(Integer, default=0)
    expected_beneficiaries: Mapped[int] = mapped_column(Integer, default=0)
    expected_staff: Mapped[int] = mapped_column(Integer, default=0)
    observed_beneficiaries: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_staff: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="SELF_REPORT")
    # SELF_REPORT / INSPECTION / SYSTEM
    deviation_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["Project"] = relationship("Project", back_populates="attendance_records")

    __table_args__ = (
        Index("ix_attendance_project_date", "project_id", "record_date"),
    )
