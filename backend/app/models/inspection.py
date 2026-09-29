"""Inspection-related models: inspectors, assignments, routes, checklists, findings."""
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, DateTime, Integer, Float, Text, ForeignKey, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Inspector(Base):
    """Inspector profile — links a user to inspection capability."""
    __tablename__ = "inspectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    current_workload: Mapped[int] = mapped_column(Integer, default=0)
    max_workload: Mapped[int] = mapped_column(Integer, default=3)
    specializations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User")
    assignments: Mapped[list["InspectionAssignment"]] = relationship(
        "InspectionAssignment", back_populates="inspector"
    )


class InspectionAssignment(Base):
    """Secure randomized inspection assignment record."""
    __tablename__ = "inspection_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assignment_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    inspector_id: Mapped[int] = mapped_column(Integer, ForeignKey("inspectors.id"), index=True)
    assigned_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    anomaly_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("anomaly_events.id"), nullable=True
    )

    # Assignment rationale (full audit trail)
    selection_algorithm: Mapped[str] = mapped_column(String(50), default="SECURE_RANDOM_V1")
    ruleset_version: Mapped[str] = mapped_column(String(20), default="1.0")
    eligibility_reasons: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    candidate_pool_size: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(50), default="ASSIGNED")
    # ASSIGNED / NOTIFIED / ACKNOWLEDGED / IN_PROGRESS / COMPLETED / CANCELLED

    # Confidentiality: inspection_date not disclosed until day-of
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped["Project"] = relationship("Project", back_populates="inspection_assignments")
    inspector: Mapped["Inspector"] = relationship("Inspector", back_populates="assignments")
    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="assignment", uselist=False)

    __table_args__ = (
        Index("ix_assignment_project_status", "project_id", "status"),
    )


class InspectionRoute(Base):
    """Generated inspection route."""
    __tablename__ = "inspection_routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspection_assignments.id"), index=True
    )
    waypoints: Mapped[list] = mapped_column(JSON, nullable=False)
    # [{project_id, name, lat, lng, sequence, estimated_time}]
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    generation_algorithm: Mapped[str] = mapped_column(String(50), default="GEOGRAPHIC_PROXIMITY_V1")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Inspection(Base):
    """Actual field inspection record."""
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    assignment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("inspection_assignments.id"), nullable=True
    )
    inspector_id: Mapped[int] = mapped_column(Integer, ForeignKey("inspectors.id"), index=True)

    status: Mapped[str] = mapped_column(String(50), default="ASSIGNED")
    # ASSIGNED / IN_PROGRESS / SUBMITTED / UNDER_REVIEW / APPROVED / REINSPECTION / CLOSED

    inspection_type: Mapped[str] = mapped_column(String(50), default="SURPRISE")
    # SURPRISE / ROUTINE / FOLLOW_UP / REINSPECTION

    # Field data
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    offline_captured: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Summary
    overall_rating: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # SATISFACTORY / NEEDS_IMPROVEMENT / UNSATISFACTORY / CRITICAL
    summary_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Official review
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    official_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # APPROVED / REINSPECTION / ESCALATED / DOCUMENTS_REQUESTED / CLOSED
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="inspections")
    assignment: Mapped["InspectionAssignment"] = relationship(
        "InspectionAssignment", back_populates="inspection"
    )
    checklists: Mapped[list["InspectionChecklist"]] = relationship(
        "InspectionChecklist", back_populates="inspection"
    )
    findings: Mapped[list["InspectionFinding"]] = relationship(
        "InspectionFinding", back_populates="inspection"
    )
    evidence: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="inspection")

    __table_args__ = (
        Index("ix_inspection_project_status", "project_id", "status"),
    )


class InspectionChecklist(Base):
    """Individual checklist item for an inspection."""
    __tablename__ = "inspection_checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    item_key: Mapped[str] = mapped_column(String(100), nullable=False)
    item_label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # PASS / FAIL / PARTIAL / NOT_OBSERVED
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    captured_offline: Mapped[bool] = mapped_column(Boolean, default=False)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="checklists")


class InspectionFinding(Base):
    """Specific finding raised during an inspection."""
    __tablename__ = "inspection_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inspections.id"), index=True
    )
    finding_code: Mapped[str] = mapped_column(String(50), unique=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    # LOW / MEDIUM / HIGH / CRITICAL
    status: Mapped[str] = mapped_column(String(50), default="OPEN")
    # OPEN / IN_PROGRESS / RESOLVED / CLOSED
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="findings")
