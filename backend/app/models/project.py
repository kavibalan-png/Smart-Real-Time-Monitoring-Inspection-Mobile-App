"""Project model — the central monitored entity."""
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, DateTime, Integer, Float, Text, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"))
    scheme: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Geographic coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Project metadata
    beneficiary_count: Mapped[int] = mapped_column(Integer, default=0)
    staff_count: Mapped[int] = mapped_column(Integer, default=0)
    project_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Current state
    health_index: Mapped[float] = mapped_column(Float, default=75.0)
    risk_level: Mapped[str] = mapped_column(String(50), default="LOW")  # LOW/MEDIUM/HIGH/CRITICAL
    status: Mapped[str] = mapped_column(String(50), default="MONITORING")
    # MONITORING / WATCH / HIGH_ATTENTION / INSPECTION_REQUIRED / UNDER_REVIEW / ACTION_REQUIRED

    attendance_status: Mapped[str] = mapped_column(String(50), default="NORMAL")
    cctv_status: Mapped[str] = mapped_column(String(50), default="LIVE")
    compliance_status: Mapped[str] = mapped_column(String(50), default="COMPLIANT")
    open_findings: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    last_inspection: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_report: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    is_hero_project: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    cameras: Mapped[list["Camera"]] = relationship("Camera", back_populates="project")
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="project")
    monitoring_signals: Mapped[list["MonitoringSignal"]] = relationship("MonitoringSignal", back_populates="project")
    anomaly_events: Mapped[list["AnomalyEvent"]] = relationship("AnomalyEvent", back_populates="project")
    health_scores: Mapped[list["HealthScore"]] = relationship("HealthScore", back_populates="project")
    inspection_assignments: Mapped[list["InspectionAssignment"]] = relationship("InspectionAssignment", back_populates="project")
    inspections: Mapped[list["Inspection"]] = relationship("Inspection", back_populates="project")
    followups: Mapped[list["Followup"]] = relationship("Followup", back_populates="project")

    __table_args__ = (
        Index("ix_project_district_state", "district", "state"),
        Index("ix_project_risk_status", "risk_level", "status"),
    )
