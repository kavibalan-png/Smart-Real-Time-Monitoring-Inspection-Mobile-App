"""Evidence schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EvidenceOut(BaseModel):
    id: int
    evidence_code: str
    inspection_id: int
    mime_type: str
    file_size_bytes: int
    latitude: Optional[float]
    longitude: Optional[float]
    gps_accuracy: Optional[float]
    gps_confidence: str
    captured_at: datetime
    captured_offline: bool
    evidence_type: str
    description: Optional[str]
    sha256_hash: Optional[str]
    integrity_status: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceVerifyOut(BaseModel):
    evidence_id: int
    result: str       # VERIFIED / MISMATCH / ERROR
    computed_hash: str
    stored_hash: str
    match: bool
    note: str
    algorithm: str
    disclaimer: str
    verified_at: datetime


class DigitalThreadEvent(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    actor: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[int]
