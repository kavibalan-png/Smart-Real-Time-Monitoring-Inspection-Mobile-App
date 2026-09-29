"""Monitoring signals, anomaly events, health scores."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class MonitoringSignal(Base):
    """Raw monitoring data points ingested from various sources."""
    __tablename__ = "monitoring_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # ATTENDANCE / REPORTING / CCTV / COMPLIANCE / ACTIVITY
    signal_value: Mapped[float] = mapped_column(Float, nullable=False)
    signal_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="SYSTEM")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped["Project"] = relationship("Project", back_populates="monitoring_signals")

    __table_args__ = (
        Index("ix_signal_project_type_time", "project_id", "signal_type", "created_at"),
    )


class AnomalyEvent(Base):
    """Detected anomaly events — output of the anomaly intelligence engine."""
    __tablename__ = "anomaly_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    # LOW / MEDIUM / HIGH / CRITICAL
    reasons: Mapped[dict] = mapped_column(JSON, nullable=False)
    # {reason_key: {score, description, evidence}}
    recommended_action: Mapped[str] = mapped_column(String(100), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="1.0")
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="anomaly_events")

    __table_args__ = (
        Index("ix_anomaly_project_severity", "project_id", "severity"),
    )


class HealthScore(Base):
    """Historical health score snapshots for trend tracking."""
    __tablename__ = "health_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    attendance_score: Mapped[float] = mapped_column(Float, default=0.0)
    reporting_score: Mapped[float] = mapped_column(Float, default=0.0)
    inspection_score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    timeliness_score: Mapped[float] = mapped_column(Float, default=0.0)
    findings_score: Mapped[float] = mapped_column(Float, default=0.0)
    score_explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped["Project"] = relationship("Project", back_populates="health_scores")

    __table_args__ = (
        Index("ix_health_project_time", "project_id", "computed_at"),
    )
