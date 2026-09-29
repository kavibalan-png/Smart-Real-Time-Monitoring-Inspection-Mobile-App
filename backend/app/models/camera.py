"""CCTV Camera models."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), index=True)
    camera_name: Mapped[str] = mapped_column(String(100), nullable=False)
    location_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stream_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    demo_video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="LIVE")  # LIVE / OFFLINE / DEGRADED
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["Project"] = relationship("Project", back_populates="cameras")
    events: Mapped[list["CameraEvent"]] = relationship("CameraEvent", back_populates="camera")


class CameraEvent(Base):
    __tablename__ = "camera_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camera_id: Mapped[int] = mapped_column(Integer, ForeignKey("cameras.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # OFFLINE / ONLINE / DEGRADED / MOTION / ANOMALY
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="LOW")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="events")
