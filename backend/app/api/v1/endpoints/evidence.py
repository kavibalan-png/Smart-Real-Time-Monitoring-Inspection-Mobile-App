"""
Evidence management endpoints.
POST /api/evidence/upload      — secure upload with GPS + hash
POST /api/evidence/verify      — integrity verification
GET  /api/evidence/{id}        — evidence detail
"""
import os
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_active_user, require_permission
from app.core.permissions import Permission
from app.core.security import generate_secure_filename
from app.models.inspection import Inspection, Inspector
from app.models.evidence import Evidence, EvidenceHash, EvidenceVerification
from app.intelligence.evidence_integrity import compute_sha256, compute_sha256_bytes, verify_evidence_integrity
from app.services.audit_service import log_action

router = APIRouter(prefix="/evidence", tags=["Evidence"])

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp",
    "video/mp4", "video/webm",
    "application/pdf",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm", ".pdf"}


def _gps_confidence(accuracy: float | None) -> str:
    if accuracy is None:
        return "UNKNOWN"
    if accuracy < 5:
        return "HIGH"
    if accuracy < 20:
        return "MEDIUM"
    return "LOW"


@router.post("/upload")
async def upload_evidence(
    request: Request,
    inspection_id: int = Form(...),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    gps_accuracy: float | None = Form(None),
    captured_offline: bool = Form(False),
    evidence_type: str = Form("PHOTO"),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user=Depends(require_permission(Permission.EVIDENCE_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload evidence file with GPS metadata.
    - Validates MIME type and extension
    - Enforces size limit
    - Generates server-safe filename (never trusts original)
    - Computes SHA-256 fingerprint
    """
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=422,
            detail=f"File type {file.content_type} not allowed",
        )

    # Validate extension
    if file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail=f"Extension {ext} not allowed")
    else:
        ext = ".bin"

    # Read file — enforce size limit
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit",
        )

    # Validate inspection + inspector ownership
    result = await db.execute(
        select(Inspection, Inspector)
        .join(Inspector, Inspection.inspector_id == Inspector.id)
        .where(Inspection.id == inspection_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Inspection not found")

    insp, inspector = row
    if inspector.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this inspection")

    if insp.status not in ("IN_PROGRESS", "ASSIGNED"):
        raise HTTPException(status_code=409, detail="Evidence can only be added to active inspections")

    # Generate safe server-side filename — prevent path traversal
    safe_filename = generate_secure_filename(file.filename or "evidence") + (ext if ext else "")
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(inspection_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)

    # Write file
    with open(file_path, "wb") as f:
        f.write(content)

    # Compute SHA-256 immediately from bytes in memory
    sha256_hash = compute_sha256_bytes(content)

    # Evidence code
    evidence_code = f"EVD-{secrets.token_hex(4).upper()}"

    gps_conf = _gps_confidence(gps_accuracy)

    evidence = Evidence(
        evidence_code=evidence_code,
        inspection_id=inspection_id,
        inspector_id=inspector.id,
        file_path=file_path,
        original_filename=file.filename or "evidence",
        safe_filename=safe_filename,
        mime_type=file.content_type,
        file_size_bytes=len(content),
        latitude=latitude,
        longitude=longitude,
        gps_accuracy=gps_accuracy,
        gps_confidence=gps_conf,
        captured_at=datetime.now(timezone.utc),
        captured_offline=captured_offline,
        synced_at=datetime.now(timezone.utc) if not captured_offline else None,
        evidence_type=evidence_type,
        description=description,
        is_demo=True,
    )
    db.add(evidence)
    await db.flush()

    # Store hash
    hash_record = EvidenceHash(
        evidence_id=evidence.id,
        sha256_hash=sha256_hash,
        algorithm="SHA-256",
        computed_by_system=True,
    )
    db.add(hash_record)

    await log_action(
        db,
        action="EVIDENCE_CAPTURE",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="evidence",
        resource_id=evidence.id,
        metadata={
            "evidence_code": evidence_code,
            "sha256": sha256_hash[:16] + "...",
            "lat": latitude, "lon": longitude,
            "gps_accuracy": gps_accuracy,
            "offline": captured_offline,
        },
    )
    await log_action(
        db,
        action="EVIDENCE_HASH",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="evidence",
        resource_id=evidence.id,
        metadata={"algorithm": "SHA-256", "hash_prefix": sha256_hash[:16]},
    )

    await db.commit()
    await db.refresh(evidence)

    warning = None
    if gps_conf == "LOW":
        warning = "GPS accuracy is low — manual verification of location recommended"
    elif gps_conf == "UNKNOWN":
        warning = "GPS coordinates unavailable — location not verified"

    return {
        "evidence_code": evidence_code,
        "evidence_id": evidence.id,
        "sha256_hash": sha256_hash,
        "gps_confidence": gps_conf,
        "captured_at": evidence.captured_at.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "warning": warning,
        "integrity_status": "HASH_COMPUTED",
        "message": "Evidence uploaded and fingerprint computed",
    }


@router.post("/verify/{evidence_id}")
async def verify_evidence(
    evidence_id: int,
    current_user=Depends(require_permission(Permission.EVIDENCE_VERIFY)),
    db: AsyncSession = Depends(get_db),
):
    """Verify evidence file integrity by recomputing SHA-256."""
    ev_result = await db.execute(
        select(Evidence, EvidenceHash)
        .join(EvidenceHash, Evidence.id == EvidenceHash.evidence_id)
        .where(Evidence.id == evidence_id)
    )
    row = ev_result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Evidence or hash record not found")

    evidence, hash_record = row

    verification = verify_evidence_integrity(evidence.file_path, hash_record.sha256_hash)

    # Persist verification event
    verif = EvidenceVerification(
        evidence_id=evidence_id,
        verified_by=current_user.id,
        verification_result=verification["result"],
        computed_hash=verification["computed_hash"],
        stored_hash=verification["stored_hash"],
    )
    db.add(verif)

    await log_action(
        db,
        action="EVIDENCE_VERIFY",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="evidence",
        resource_id=evidence_id,
        metadata={"result": verification["result"]},
    )

    await db.commit()
    now = datetime.now(timezone.utc)

    return {
        "evidence_id": evidence_id,
        "evidence_code": evidence.evidence_code,
        "result": verification["result"],
        "computed_hash": verification["computed_hash"],
        "stored_hash": verification["stored_hash"],
        "match": verification["match"],
        "note": verification["note"],
        "algorithm": "SHA-256",
        "disclaimer": verification.get("disclaimer", ""),
        "verified_at": now.isoformat(),
    }


@router.get("/{evidence_id}")
async def get_evidence(
    evidence_id: int,
    current_user=Depends(require_permission(Permission.EVIDENCE_READ)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Evidence, EvidenceHash.sha256_hash)
        .outerjoin(EvidenceHash, Evidence.id == EvidenceHash.evidence_id)
        .where(Evidence.id == evidence_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Evidence not found")

    ev, sha = row
    return {
        "id": ev.id,
        "evidence_code": ev.evidence_code,
        "inspection_id": ev.inspection_id,
        "mime_type": ev.mime_type,
        "file_size_bytes": ev.file_size_bytes,
        "latitude": ev.latitude,
        "longitude": ev.longitude,
        "gps_accuracy": ev.gps_accuracy,
        "gps_confidence": ev.gps_confidence,
        "captured_at": ev.captured_at.isoformat(),
        "captured_offline": ev.captured_offline,
        "evidence_type": ev.evidence_type,
        "description": ev.description,
        "sha256_hash": sha,
        "created_at": ev.created_at.isoformat(),
    }
