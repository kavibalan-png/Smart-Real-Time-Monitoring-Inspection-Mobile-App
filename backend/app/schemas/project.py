"""Project schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProjectListItem(BaseModel):
    id: int
    project_code: str
    project_name: str
    scheme: str
    district: str
    state: str
    latitude: float
    longitude: float
    health_index: float
    risk_level: str
    status: str
    attendance_status: str
    cctv_status: str
    open_findings: int
    last_inspection: Optional[datetime]
    is_hero_project: bool

    model_config = {"from_attributes": True}


class ProjectDetail(BaseModel):
    id: int
    project_code: str
    project_name: str
    organization_id: int
    scheme: str
    district: str
    state: str
    address: Optional[str]
    latitude: float
    longitude: float
    beneficiary_count: int
    staff_count: int
    project_type: str
    health_index: float
    risk_level: str
    status: str
    attendance_status: str
    cctv_status: str
    compliance_status: str
    open_findings: int
    last_inspection: Optional[datetime]
    last_report: Optional[datetime]
    is_demo: bool
    is_hero_project: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    project_name: str
    organization_id: int
    scheme: str
    district: str
    state: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    beneficiary_count: int
    staff_count: int
    project_type: str


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    beneficiary_count: Optional[int] = None
    staff_count: Optional[int] = None
    address: Optional[str] = None
