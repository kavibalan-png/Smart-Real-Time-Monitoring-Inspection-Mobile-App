"""Evidence capture, hash, and verification models."""
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Evidence(Base):
    """Field evidence captured during inspection."""
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evidence_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    inspection_id: Mapped[int] = mapped_column(Integer, ForeignKey("inspections.id"), index=True)
    inspector_id: Mapped[int] = mapped_column(Integer, ForeignKey("inspectors.id"))

    # File info
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    safe_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Geolocation metadata
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)  # metres
    gps_confidence: Mapped[str] = mapped_column(String(20), default="UNKNOWN")
    # HIGH (<5m) / MEDIUM (<20m) / LOW (>=20m) / UNKNOWN

    # Timestamp
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    captured_offline: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence_type: Mapped[str] = mapped_column(String(50), default="PHOTO")
    # PHOTO / VIDEO / DOCUMENT / AUDIO
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="evidence")
    hash_record: Mapped["EvidenceHash"] = relationship(
        "EvidenceHash", back_populates="evidence", uselist=False
    )
    verifications: Mapped[list["EvidenceVerification"]] = relationship(
        "EvidenceVerification", back_populates="evidence"
    )

    __table_args__ = (
        Index("ix_evidence_inspection", "inspection_id"),
    )


class EvidenceHash(Base):
    """SHA-256 fingerprint of evidence file — for integrity verification."""
    __tablename__ = "evidence_hashes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evidence_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("evidence.id"), unique=True, index=True
    )
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(20), default="SHA-256")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    computed_by_system: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    evidence: Mapped["Evidence"] = relationship("Evidence", back_populates="hash_record")


class EvidenceVerification(Base):
    """On-demand integrity verification events."""
    __tablename__ = "evidence_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evidence_id: Mapped[int] = mapped_column(Integer, ForeignKey("evidence.id"), index=True)
    verified_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    verification_result: Mapped[str] = mapped_column(String(20), nullable=False)
    # VERIFIED / MISMATCH / ERROR
    computed_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    stored_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)

    evidence: Mapped["Evidence"] = relationship("Evidence", back_populates="verifications")
