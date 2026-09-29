"""
Inspection endpoints — full P0 workflow.

POST /api/inspections/recommend         — AI recommendation
POST /api/inspections/assign            — secure random assignment
GET  /api/inspections                   — list inspections
GET  /api/inspections/{id}              — inspection detail
POST /api/inspections/{id}/start        — inspector starts field work
POST /api/inspections/{id}/submit       — inspector submits
POST /api/inspections/{id}/decision     — official decision
GET  /api/inspections/{id}/timeline     — digital thread
POST /api/routes/generate               — route generation
GET  /api/routes/{id}                   — route detail
"""
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.core.permissions import Permission, UserRole, has_permission
from app.models.project import Project
from app.models.inspection import (
    Inspector, InspectionAssignment, InspectionRoute,
    Inspection, InspectionChecklist, InspectionFinding
)
from app.models.monitoring import AnomalyEvent
from app.models.evidence import Evidence, EvidenceHash
from app.models.followup import Followup
from app.models.audit import AuditLog
from app.schemas.inspection import (
    AssignmentRequest, AssignmentOut, InspectionOut,
    InspectionStartRequest, InspectionSubmitRequest,
    OfficialDecisionRequest, RouteGenerateRequest, RouteOut
)
from app.intelligence.assignment_engine import (
    InspectorCandidate, run_assignment_pipeline
)
from app.services.audit_service import log_action
from app.services.notification_service import create_notification

router = APIRouter(tags=["Inspections"])


# ─── Recommendation ──────────────────────────────────────────────────────────

@router.post("/inspections/recommend")
async def recommend_inspection(
    project_id: int,
    current_user=Depends(require_permission(Permission.INSPECTION_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    """Get AI recommendation for a project inspection."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest anomaly
    anomaly_result = await db.execute(
        select(AnomalyEvent)
        .where(AnomalyEvent.project_id == project_id)
        .order_by(AnomalyEvent.created_at.desc())
        .limit(1)
    )
    anomaly = anomaly_result.scalar_one_or_none()

    return {
        "project_id": project_id,
        "project_name": project.project_name,
        "health_index": project.health_index,
        "risk_level": project.risk_level,
        "status": project.status,
        "anomaly_score": anomaly.anomaly_score if anomaly else None,
        "anomaly_severity": anomaly.severity if anomaly else None,
        "recommendation": "SURPRISE_INSPECTION" if project.risk_level in ("HIGH", "CRITICAL") else "ENHANCED_MONITORING",
        "reasons": anomaly.reasons if anomaly else {},
        "recommended_by": "Anomaly Intelligence Engine v1.0",
        "disclaimer": "SYSTEM RECOMMENDATION — OFFICIAL DECISION REQUIRED",
    }


# ─── Surprise Assignment ──────────────────────────────────────────────────────

@router.post("/inspections/assign", response_model=AssignmentOut)
async def assign_inspection(
    request: Request,
    body: AssignmentRequest,
    current_user=Depends(require_permission(Permission.INSPECTION_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Secure surprise inspection assignment.
    Backend-only random selection — candidate pool never exposed to client.
    """
    # Validate project
    proj_result = await db.execute(select(Project).where(Project.id == body.project_id))
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check no active unresolved assignment
    existing = await db.execute(
        select(InspectionAssignment).where(
            and_(
                InspectionAssignment.project_id == body.project_id,
                InspectionAssignment.status.in_(["ASSIGNED", "NOTIFIED", "ACKNOWLEDGED", "IN_PROGRESS"]),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Active inspection assignment already exists for this project",
        )

    # Gather all candidate inspectors (server-side only)
    insp_result = await db.execute(
        select(Inspector).where(Inspector.is_available == True)
    )
    all_inspectors = insp_result.scalars().all()

    candidates = []
    for insp in all_inspectors:
        # Get inspector's user name
        from app.models.user import User
        user_result = await db.execute(select(User).where(User.id == insp.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            continue
        candidates.append(InspectorCandidate(
            inspector_id=insp.id,
            user_id=insp.user_id,
            name=user.full_name,
            district=insp.district,
            state=insp.state,
            latitude=insp.latitude,
            longitude=insp.longitude,
            is_available=insp.is_available,
            current_workload=insp.current_workload,
            max_workload=insp.max_workload,
            specializations=insp.specializations or [],
        ))

    # Run secure assignment pipeline
    decision = run_assignment_pipeline(
        candidates=candidates,
        project_lat=project.latitude,
        project_lon=project.longitude,
        max_distance_km=body.max_distance_km,
    )

    if not decision:
        raise HTTPException(
            status_code=422,
            detail="No eligible inspectors available for this project. Check availability and workload.",
        )

    # Create assignment record
    assignment_id = f"INS-{datetime.now(timezone.utc).year}-{secrets.token_hex(3).upper()}"

    assignment = InspectionAssignment(
        assignment_id=assignment_id,
        project_id=body.project_id,
        inspector_id=decision.selected_inspector_id,
        assigned_by=current_user.id,
        anomaly_event_id=body.anomaly_event_id,
        selection_algorithm=decision.selection_algorithm,
        ruleset_version=decision.ruleset_version,
        candidate_pool_size=decision.candidate_pool_size,
        eligibility_reasons=decision.eligibility_reasons,
        status="ASSIGNED",
        assigned_at=datetime.now(timezone.utc),
        is_demo=True,
    )
    db.add(assignment)

    # Update inspector workload
    insp_to_update = await db.execute(
        select(Inspector).where(Inspector.id == decision.selected_inspector_id)
    )
    selected_inspector = insp_to_update.scalar_one()
    selected_inspector.current_workload += 1

    # Update project status
    project.status = "INSPECTION_REQUIRED"

    await db.flush()

    # Get inspector's user for notification
    from app.models.user import User
    insp_user_result = await db.execute(
        select(User).where(User.id == selected_inspector.user_id)
    )
    insp_user = insp_user_result.scalar_one()

    # Notify inspector (but don't expose which project it's for until they open it)
    await create_notification(
        db,
        user_id=insp_user.id,
        notification_type="INSPECTION_ASSIGNED",
        title="New Surprise Inspection Assignment",
        message=f"You have been assigned a surprise inspection. Assignment ID: {assignment_id}",
        priority="HIGH",
        resource_type="assignment",
        resource_id=assignment.id,
    )

    # Audit log
    await log_action(
        db,
        action="ASSIGNMENT",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="inspection_assignment",
        resource_id=assignment.id,
        metadata={
            "assignment_id": assignment_id,
            "project_id": body.project_id,
            "inspector_id": decision.selected_inspector_id,
            "pool_size": decision.candidate_pool_size,
            "algorithm": decision.selection_algorithm,
        },
    )

    await db.commit()
    await db.refresh(assignment)

    # Broadcast real-time event to command center
    from app.core.websocket_manager import emit_event
    import asyncio
    asyncio.create_task(emit_event("INSPECTION_ASSIGNED", {
        "assignment_id": assignment_id,
        "project_id": body.project_id,
        "project_name": project.project_name,
    }))

    return AssignmentOut(
        id=assignment.id,
        assignment_id=assignment.assignment_id,
        project_id=assignment.project_id,
        project_name=project.project_name,
        inspector_id=assignment.inspector_id,
        inspector_name=insp_user.full_name,
        assigned_by=assignment.assigned_by,
        selection_algorithm=assignment.selection_algorithm,
        ruleset_version=assignment.ruleset_version,
        candidate_pool_size=assignment.candidate_pool_size,
        eligibility_reasons=assignment.eligibility_reasons,
        status=assignment.status,
        assigned_at=assignment.assigned_at,
        is_demo=assignment.is_demo,
    )


# ─── List & Detail ────────────────────────────────────────────────────────────

@router.get("/inspections", response_model=dict)
async def list_inspections(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List inspections — role-scoped."""
    role = UserRole(current_user.role)

    q = select(Inspection, Project.project_name).join(Project)

    # Inspector sees only their own
    if role == UserRole.INSPECTION_OFFICER:
        insp_result = await db.execute(
            select(Inspector).where(Inspector.user_id == current_user.id)
        )
        inspector = insp_result.scalar_one_or_none()
        if inspector:
            q = q.where(Inspection.inspector_id == inspector.id)
        else:
            return {"items": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}

    if status_filter:
        q = q.where(Inspection.status == status_filter)

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q) or 0

    q = q.order_by(Inspection.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    rows = result.all()

    items = []
    for insp, pname in rows:
        items.append({
            "id": insp.id,
            "inspection_code": insp.inspection_code,
            "project_id": insp.project_id,
            "project_name": pname,
            "inspector_id": insp.inspector_id,
            "status": insp.status,
            "inspection_type": insp.inspection_type,
            "overall_rating": insp.overall_rating,
            "start_time": insp.start_time.isoformat() if insp.start_time else None,
            "created_at": insp.created_at.isoformat(),
        })

    return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": (total + per_page - 1) // per_page}


@router.get("/inspections/{inspection_id}", response_model=dict)
async def get_inspection(
    inspection_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get inspection detail with checklist, findings, evidence."""
    result = await db.execute(
        select(Inspection, Project.project_name)
        .join(Project)
        .where(Inspection.id == inspection_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Inspection not found")

    insp, pname = row

    # Object-level auth — inspector sees only own
    role = UserRole(current_user.role)
    if role == UserRole.INSPECTION_OFFICER:
        insp_result = await db.execute(
            select(Inspector).where(Inspector.user_id == current_user.id)
        )
        inspector = insp_result.scalar_one_or_none()
        if not inspector or inspector.id != insp.inspector_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Checklist
    cl_result = await db.execute(
        select(InspectionChecklist).where(InspectionChecklist.inspection_id == inspection_id)
    )
    checklist = [
        {
            "id": c.id, "category": c.category, "item_key": c.item_key,
            "item_label": c.item_label, "value": c.value, "observation": c.observation,
            "is_critical": c.is_critical,
        }
        for c in cl_result.scalars().all()
    ]

    # Findings
    findings_result = await db.execute(
        select(InspectionFinding).where(InspectionFinding.inspection_id == inspection_id)
    )
    findings = [
        {
            "id": f.id, "finding_code": f.finding_code, "category": f.category,
            "description": f.description, "severity": f.severity, "status": f.status,
        }
        for f in findings_result.scalars().all()
    ]

    # Evidence
    ev_result = await db.execute(
        select(Evidence, EvidenceHash.sha256_hash)
        .outerjoin(EvidenceHash, Evidence.id == EvidenceHash.evidence_id)
        .where(Evidence.inspection_id == inspection_id)
    )
    evidence_list = [
        {
            "id": e.id, "evidence_code": e.evidence_code,
            "evidence_type": e.evidence_type,
            "latitude": e.latitude, "longitude": e.longitude,
            "gps_confidence": e.gps_confidence,
            "captured_at": e.captured_at.isoformat(),
            "captured_offline": e.captured_offline,
            "sha256_hash": h,
            "description": e.description,
        }
        for e, h in ev_result.all()
    ]

    return {
        "id": insp.id,
        "inspection_code": insp.inspection_code,
        "project_id": insp.project_id,
        "project_name": pname,
        "inspector_id": insp.inspector_id,
        "status": insp.status,
        "inspection_type": insp.inspection_type,
        "start_time": insp.start_time.isoformat() if insp.start_time else None,
        "end_time": insp.end_time.isoformat() if insp.end_time else None,
        "start_latitude": insp.start_latitude,
        "start_longitude": insp.start_longitude,
        "gps_accuracy": insp.gps_accuracy,
        "offline_captured": insp.offline_captured,
        "overall_rating": insp.overall_rating,
        "summary_notes": insp.summary_notes,
        "recommendations": insp.recommendations,
        "official_decision": insp.official_decision,
        "decision_notes": insp.decision_notes,
        "checklist": checklist,
        "findings": findings,
        "evidence": evidence_list,
        "created_at": insp.created_at.isoformat(),
    }


# ─── Inspector Workflow ───────────────────────────────────────────────────────

@router.post("/inspections/{inspection_id}/start")
async def start_inspection(
    inspection_id: int,
    body: InspectionStartRequest,
    current_user=Depends(require_permission(Permission.INSPECTION_CONDUCT)),
    db: AsyncSession = Depends(get_db),
):
    """Inspector starts field inspection — captures GPS and timestamp."""
    result = await db.execute(
        select(Inspection, Inspector)
        .join(Inspector, Inspection.inspector_id == Inspector.id)
        .where(Inspection.id == inspection_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Inspection not found")

    insp, inspector = row

    # Verify this inspector owns this inspection
    if inspector.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this inspection")

    if insp.status not in ("ASSIGNED", "NOTIFIED", "ACKNOWLEDGED"):
        raise HTTPException(status_code=409, detail=f"Cannot start inspection in status: {insp.status}")

    insp.status = "IN_PROGRESS"
    insp.start_time = datetime.now(timezone.utc)
    insp.start_latitude = body.latitude
    insp.start_longitude = body.longitude
    insp.gps_accuracy = body.gps_accuracy
    insp.offline_captured = body.offline

    # Create default checklist if empty
    existing_cl = await db.execute(
        select(func.count(InspectionChecklist.id)).where(
            InspectionChecklist.inspection_id == inspection_id
        )
    )
    if (existing_cl.scalar() or 0) == 0:
        checklist_template = [
            ("OPERATIONAL", "operational_status", "Project is operationally active", True),
            ("STAFF", "staff_presence", "Required staff present on site", True),
            ("BENEFICIARY", "beneficiary_presence", "Beneficiaries present as reported", True),
            ("FACILITY", "facility_condition", "Facility in satisfactory condition", False),
            ("RECORDS", "records_maintained", "Required records and registers maintained", True),
            ("SERVICES", "services_delivered", "Services being delivered as per mandate", True),
            ("SAFETY", "safety_compliance", "Safety and infrastructure compliance", False),
            ("EVIDENCE", "supporting_evidence", "Supporting evidence and documentation available", False),
        ]
        for cat, key, label, critical in checklist_template:
            db.add(InspectionChecklist(
                inspection_id=inspection_id,
                category=cat,
                item_key=key,
                item_label=label,
                value=None,
                is_critical=critical,
                is_demo=True,
            ))

    await log_action(
        db,
        action="INSPECTION_START",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="inspection",
        resource_id=inspection_id,
        metadata={
            "lat": body.latitude, "lon": body.longitude,
            "accuracy": body.gps_accuracy, "offline": body.offline,
        },
    )

    await db.commit()
    return {"status": "IN_PROGRESS", "started_at": insp.start_time.isoformat()}


@router.post("/inspections/{inspection_id}/submit")
async def submit_inspection(
    inspection_id: int,
    body: InspectionSubmitRequest,
    current_user=Depends(require_permission(Permission.INSPECTION_CONDUCT)),
    db: AsyncSession = Depends(get_db),
):
    """Inspector submits completed inspection."""
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
        raise HTTPException(status_code=403, detail="Not authorized")

    if insp.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Inspection not in progress")

    # Update inspection
    insp.status = "SUBMITTED"
    insp.end_time = datetime.now(timezone.utc)
    insp.overall_rating = body.overall_rating
    insp.summary_notes = body.summary_notes
    insp.recommendations = body.recommendations

    # Update checklist items
    for item_update in body.checklist_items:
        cl_result = await db.execute(
            select(InspectionChecklist).where(
                and_(
                    InspectionChecklist.inspection_id == inspection_id,
                    InspectionChecklist.item_key == item_update.item_key,
                )
            )
        )
        cl_item = cl_result.scalar_one_or_none()
        if cl_item:
            cl_item.value = item_update.value
            cl_item.observation = item_update.observation
            cl_item.captured_offline = item_update.captured_offline
            cl_item.captured_at = datetime.now(timezone.utc)

    await log_action(
        db,
        action="INSPECTION_START",  # reuse — distinct from START
        user_id=current_user.id,
        role=current_user.role,
        resource_type="inspection",
        resource_id=inspection_id,
        metadata={"action": "SUBMIT", "rating": body.overall_rating},
    )
    await db.commit()
    return {"status": "SUBMITTED", "submitted_at": insp.end_time.isoformat()}


# ─── Official Decision ────────────────────────────────────────────────────────

@router.post("/inspections/{inspection_id}/decision")
async def make_decision(
    inspection_id: int,
    body: OfficialDecisionRequest,
    current_user=Depends(require_permission(Permission.DECISION_MAKE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Official makes a decision on a submitted inspection.
    APPROVED / REINSPECTION / ESCALATED / DOCUMENTS_REQUESTED / CLOSED
    """
    valid_decisions = {"APPROVED", "REINSPECTION", "ESCALATED", "DOCUMENTS_REQUESTED", "CLOSED"}
    if body.decision not in valid_decisions:
        raise HTTPException(status_code=422, detail=f"Invalid decision: {body.decision}")

    result = await db.execute(
        select(Inspection).where(Inspection.id == inspection_id)
    )
    insp = result.scalar_one_or_none()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    if insp.status not in ("SUBMITTED", "UNDER_REVIEW"):
        raise HTTPException(status_code=409, detail="Inspection not available for decision")

    insp.status = "APPROVED" if body.decision == "APPROVED" else body.decision
    insp.official_decision = body.decision
    insp.decision_notes = body.decision_notes
    insp.reviewed_by = current_user.id
    insp.reviewed_at = datetime.now(timezone.utc)

    # Update project status
    proj_result = await db.execute(select(Project).where(Project.id == insp.project_id))
    project = proj_result.scalar_one()

    if body.decision == "APPROVED":
        project.status = "MONITORING"
        project.risk_level = "LOW"
        project.last_inspection = datetime.now(timezone.utc)
    elif body.decision in ("ESCALATED", "REINSPECTION"):
        project.status = "ACTION_REQUIRED"

    # Automatically create follow-up for certain decisions
    if body.decision in ("REINSPECTION", "ESCALATED", "DOCUMENTS_REQUESTED"):
        import random
        fu_code = f"FU-{datetime.now(timezone.utc).year}-{secrets.token_hex(3).upper()}"
        followup = Followup(
            followup_code=fu_code,
            project_id=insp.project_id,
            inspection_id=inspection_id,
            created_by=current_user.id,
            action_type=body.decision,
            description=body.decision_notes or f"Follow-up action: {body.decision}",
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status="OPEN",
            is_demo=True,
        )
        db.add(followup)

    await log_action(
        db,
        action="DECISION",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="inspection",
        resource_id=inspection_id,
        metadata={"decision": body.decision, "notes": body.decision_notes},
    )
    await db.commit()

    return {
        "status": insp.status,
        "decision": body.decision,
        "reviewed_at": insp.reviewed_at.isoformat(),
        "project_status": project.status,
    }


# ─── Digital Thread / Timeline ────────────────────────────────────────────────

@router.get("/inspections/{inspection_id}/timeline", response_model=list)
async def get_inspection_timeline(
    inspection_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Digital evidence thread — every event from anomaly detection
    to final decision, from actual persisted data.
    """
    result = await db.execute(
        select(Inspection, Project)
        .join(Project)
        .where(Inspection.id == inspection_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Inspection not found")

    insp, project = row
    events = []

    # Assignment event
    if insp.assignment_id:
        assign_result = await db.execute(
            select(InspectionAssignment).where(InspectionAssignment.id == insp.assignment_id)
        )
        assignment = assign_result.scalar_one_or_none()
        if assignment:
            events.append({
                "timestamp": assignment.assigned_at.isoformat(),
                "event_type": "ASSIGNMENT",
                "description": f"Surprise inspection assigned (ID: {assignment.assignment_id})",
                "actor": "Department Official",
                "resource_type": "assignment",
                "resource_id": assignment.id,
            })

    # Start event
    if insp.start_time:
        events.append({
            "timestamp": insp.start_time.isoformat(),
            "event_type": "INSPECTION_START",
            "description": "Field inspection started by inspector",
            "actor": "Inspector",
            "resource_type": "inspection",
            "resource_id": insp.id,
        })

    # Evidence events
    ev_result = await db.execute(
        select(Evidence, EvidenceHash.sha256_hash, EvidenceHash.computed_at)
        .outerjoin(EvidenceHash, Evidence.id == EvidenceHash.evidence_id)
        .where(Evidence.inspection_id == inspection_id)
        .order_by(Evidence.captured_at)
    )
    for ev, h, hash_time in ev_result.all():
        events.append({
            "timestamp": ev.captured_at.isoformat(),
            "event_type": "EVIDENCE_CAPTURE",
            "description": f"Evidence captured ({ev.evidence_type}){' [OFFLINE]' if ev.captured_offline else ''}",
            "actor": "Inspector",
            "resource_type": "evidence",
            "resource_id": ev.id,
        })
        if h:
            events.append({
                "timestamp": hash_time.isoformat() if hash_time else ev.captured_at.isoformat(),
                "event_type": "EVIDENCE_HASH",
                "description": f"SHA-256 fingerprint computed: {h[:16]}...",
                "actor": "System",
                "resource_type": "evidence",
                "resource_id": ev.id,
            })

    # Submit event
    if insp.end_time:
        events.append({
            "timestamp": insp.end_time.isoformat(),
            "event_type": "INSPECTION_SUBMITTED",
            "description": f"Inspection submitted. Rating: {insp.overall_rating or 'Pending'}",
            "actor": "Inspector",
            "resource_type": "inspection",
            "resource_id": insp.id,
        })

    # Official review
    if insp.reviewed_at:
        events.append({
            "timestamp": insp.reviewed_at.isoformat(),
            "event_type": "OFFICIAL_REVIEW",
            "description": f"Official reviewed inspection. Decision: {insp.official_decision or 'Pending'}",
            "actor": "Department Official",
            "resource_type": "inspection",
            "resource_id": insp.id,
        })

    # Follow-ups
    fu_result = await db.execute(
        select(Followup).where(Followup.inspection_id == inspection_id)
    )
    for fu in fu_result.scalars().all():
        events.append({
            "timestamp": fu.created_at.isoformat(),
            "event_type": "FOLLOWUP",
            "description": f"Follow-up created: {fu.action_type} (Code: {fu.followup_code})",
            "actor": "Department Official",
            "resource_type": "followup",
            "resource_id": fu.id,
        })

    # Sort by timestamp
    events.sort(key=lambda e: e["timestamp"])
    return events


# ─── Routes ───────────────────────────────────────────────────────────────────

route_router = APIRouter(prefix="/routes", tags=["Routes"])


@route_router.post("/generate", response_model=RouteOut)
async def generate_route(
    body: RouteGenerateRequest,
    current_user=Depends(require_permission(Permission.INSPECTION_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    """Generate an inspection route for an assignment."""
    assign_result = await db.execute(
        select(InspectionAssignment, Project)
        .join(Project)
        .where(InspectionAssignment.id == body.assignment_id)
    )
    row = assign_result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment, project = row

    route_id = f"RTE-{secrets.token_hex(4).upper()}"
    waypoints = [
        {
            "sequence": 1,
            "project_id": project.id,
            "name": project.project_name,
            "latitude": project.latitude,
            "longitude": project.longitude,
            "estimated_arrival": "On departure",
        }
    ]

    route = InspectionRoute(
        route_id=route_id,
        assignment_id=body.assignment_id,
        waypoints=waypoints,
        total_distance_km=0.0,
        estimated_duration_minutes=60,
        generation_algorithm="GEOGRAPHIC_PROXIMITY_V1",
        is_demo=True,
    )
    db.add(route)

    await log_action(
        db,
        action="ROUTE_GENERATION",
        user_id=current_user.id,
        role=current_user.role,
        resource_type="route",
        metadata={"route_id": route_id, "assignment_id": body.assignment_id},
    )

    await db.commit()
    await db.refresh(route)
    return route


@route_router.get("/{route_id}", response_model=RouteOut)
async def get_route(
    route_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(InspectionRoute).where(InspectionRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route
