"""Inspection schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AssignmentRequest(BaseModel):
    project_id: int
    anomaly_event_id: Optional[int] = None
    max_distance_km: float = 150.0


class AssignmentOut(BaseModel):
    id: int
    assignment_id: str
    project_id: int
    project_name: str
    inspector_id: int
    inspector_name: str
    assigned_by: int
    selection_algorithm: str
    ruleset_version: str
    candidate_pool_size: int
    eligibility_reasons: dict
    status: str
    assigned_at: datetime
    is_demo: bool

    model_config = {"from_attributes": True}


class InspectionOut(BaseModel):
    id: int
    inspection_code: str
    project_id: int
    project_name: str
    inspector_id: int
    status: str
    inspection_type: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    start_latitude: Optional[float]
    start_longitude: Optional[float]
    gps_accuracy: Optional[float]
    offline_captured: bool
    overall_rating: Optional[str]
    summary_notes: Optional[str]
    official_decision: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class InspectionStartRequest(BaseModel):
    latitude: float
    longitude: float
    gps_accuracy: float
    offline: bool = False


class ChecklistItemUpdate(BaseModel):
    item_key: str
    value: str  # PASS / FAIL / PARTIAL / NOT_OBSERVED
    observation: Optional[str] = None
    captured_offline: bool = False


class InspectionSubmitRequest(BaseModel):
    overall_rating: str
    summary_notes: str
    recommendations: Optional[str] = None
    checklist_items: list[ChecklistItemUpdate]


class OfficialDecisionRequest(BaseModel):
    decision: str  # APPROVED / REINSPECTION / ESCALATED / DOCUMENTS_REQUESTED / CLOSED
    decision_notes: Optional[str] = None


class RouteGenerateRequest(BaseModel):
    assignment_id: int


class RouteOut(BaseModel):
    id: int
    route_id: str
    assignment_id: int
    waypoints: list
    total_distance_km: float
    estimated_duration_minutes: int
    generation_algorithm: str
    generated_at: datetime

    model_config = {"from_attributes": True}
