"""Monitoring, anomaly, health schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MonitoringSummary(BaseModel):
    total_projects: int
    attention_required: int
    high_anomalies: int
    inspections_today: int
    open_findings: int
    pending_followup: int
    cameras_offline: int
    healthy_projects: int
    watch_projects: int
    critical_projects: int


class AnomalyReason(BaseModel):
    key: str
    label: str
    score_contribution: float
    evidence: str
    threshold_used: str


class AnomalyEventOut(BaseModel):
    id: int
    project_id: int
    project_name: str
    anomaly_score: float
    severity: str
    reasons: dict
    recommended_action: str
    algorithm_version: str
    is_acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthScoreOut(BaseModel):
    total_score: float
    status: str
    attendance_score: float
    reporting_score: float
    inspection_score: float
    evidence_score: float
    timeliness_score: float
    findings_score: float
    explanation: dict
    computed_at: datetime


class HealthTrendPoint(BaseModel):
    computed_at: datetime
    total_score: float


class AlertOut(BaseModel):
    id: int
    project_id: int
    project_name: str
    alert_type: str
    message: str
    severity: str
    created_at: datetime
