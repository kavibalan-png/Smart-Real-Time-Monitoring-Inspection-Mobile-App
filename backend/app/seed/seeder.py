"""
Demo Data Seeder — SIH 2026 Prototype
=======================================
Creates all synthetic demo data including the hero scenario.
All data is fictional. DEMO_DATA = True flag is set on all records.

Run: python -m app.seed.seeder
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta, date
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, engine
from app.core.database import Base
from app.core.security import hash_password
import app.models  # register all models


# Deterministic seed for reproducible demo data
random.seed(42)


SCHEMES = [
    "Pradhan Mantri Awas Yojana",
    "Integrated Child Development Services",
    "National Social Assistance Programme",
    "Swachh Bharat Mission",
    "PM SHRI Schools",
    "Rehabilitation Council of India",
    "National Trust",
    "Scholarship for SC/ST/OBC",
    "Deendayal Disability Rehabilitation Scheme",
    "Assistive Devices Scheme",
]

DISTRICTS = [
    "Mumbai", "Pune", "Nagpur", "Nashik", "Thane",
    "Aurangabad", "Solapur", "Kolhapur", "Satara", "Latur",
    "Delhi", "Gurugram", "Faridabad",
    "Bengaluru", "Mysuru", "Hubballi",
    "Chennai", "Coimbatore", "Madurai",
    "Hyderabad", "Warangal",
]

PROJECT_TYPES = [
    "Welfare Centre", "Rehabilitation Centre", "School", "Hostel",
    "Community Kitchen", "Vocational Training Centre", "Day Care Centre",
    "Special School", "Short Stay Home", "Old Age Home",
]

ORG_TYPES = ["NGO", "TRUST", "SOCIETY", "GOVT"]


async def clear_demo_data(db: AsyncSession):
    """Remove existing demo data (idempotent seeder)."""
    tables = [
        "audit_logs", "notifications", "feedback",
        "evidence_verifications", "evidence_hashes", "evidence",
        "inspection_checklists", "inspection_findings",
        "inspections", "inspection_routes", "inspection_assignments",
        "health_scores", "anomaly_events", "monitoring_signals",
        "attendance_records", "camera_events", "cameras",
        "followups", "inspectors", "projects", "users", "organizations",
    ]
    for table in tables:
        await db.execute(text(f"DELETE FROM {table} WHERE is_demo = true"))
    await db.commit()
    print("Cleared existing demo data.")


async def seed_organizations(db: AsyncSession) -> List:
    from app.models.organization import Organization
    orgs = []
    org_names = [
        "Sahyog Welfare Foundation", "Asha Trust", "Prayas Society",
        "Jan Seva NGO", "Umeed Foundation", "Samridhi Trust",
        "Navodaya Society", "Seva Bharati", "Kalyan Foundation",
        "Disha NGO",
    ]
    for i, name in enumerate(org_names):
        org = Organization(
            name=name,
            org_type=ORG_TYPES[i % len(ORG_TYPES)],
            registration_number=f"REG{2020 + i:04d}{i:04d}",
            district=DISTRICTS[i % len(DISTRICTS)],
            state="Maharashtra" if i < 5 else "Karnataka",
            contact_email=f"contact@{name.lower().replace(' ', '')}.org",
            contact_phone=f"9{random.randint(100000000, 999999999)}",
            is_demo=True,
        )
        db.add(org)
        orgs.append(org)
    await db.flush()
    return orgs


async def seed_users(db: AsyncSession, orgs: List) -> dict:
    from app.models.user import User
    users = {}

    # Fixed demo users
    demo_accounts = [
        {
            "email": "admin@aiip.gov.in",
            "full_name": "Rajesh Kumar (Super Admin)",
            "role": "SUPER_ADMIN",
            "district": "Delhi",
            "state": "Delhi",
        },
        {
            "email": "official@aiip.gov.in",
            "full_name": "Priya Sharma (Department Official)",
            "role": "DEPARTMENT_OFFICIAL",
            "district": "Delhi",
            "state": "Delhi",
        },
        {
            "email": "pmu@aiip.gov.in",
            "full_name": "Amit Verma (PMU Officer)",
            "role": "PMU_OFFICER",
            "district": "Mumbai",
            "state": "Maharashtra",
        },
    ]

    for account in demo_accounts:
        user = User(
            email=account["email"],
            full_name=account["full_name"],
            hashed_password=hash_password("Demo@1234"),
            role=account["role"],
            district=account["district"],
            state=account["state"],
            is_active=True,
            is_demo=True,
        )
        db.add(user)
        users[account["role"]] = user

    # Inspection officers
    inspector_data = [
        ("insp1@aiip.gov.in", "Sanjay Patil", "Mumbai", "Maharashtra", 19.076, 72.877),
        ("insp2@aiip.gov.in", "Kavitha Reddy", "Pune", "Maharashtra", 18.520, 73.856),
        ("insp3@aiip.gov.in", "Mohan Das", "Nagpur", "Maharashtra", 21.145, 79.088),
        ("insp4@aiip.gov.in", "Sunita Nair", "Nashik", "Maharashtra", 20.012, 73.790),
        ("insp5@aiip.gov.in", "Ravi Shankar", "Thane", "Maharashtra", 19.218, 72.978),
        ("insp6@aiip.gov.in", "Deepa Krishnan", "Bengaluru", "Karnataka", 12.971, 77.594),
        ("insp7@aiip.gov.in", "Prakash Joshi", "Mumbai", "Maharashtra", 19.100, 72.900),
        ("insp8@aiip.gov.in", "Meera Iyer", "Pune", "Maharashtra", 18.530, 73.870),
        ("insp9@aiip.gov.in", "Vikram Singh", "Delhi", "Delhi", 28.704, 77.102),
        ("insp10@aiip.gov.in", "Anita Rao", "Chennai", "Tamil Nadu", 13.083, 80.270),
        ("insp11@aiip.gov.in", "Suresh Menon", "Hyderabad", "Telangana", 17.385, 78.486),
        ("insp12@aiip.gov.in", "Padma Lakshmi", "Kolhapur", "Maharashtra", 16.705, 74.243),
    ]

    inspector_users = []
    for email, name, district, state, lat, lon in inspector_data:
        user = User(
            email=email,
            full_name=name,
            hashed_password=hash_password("Demo@1234"),
            role="INSPECTION_OFFICER",
            district=district,
            state=state,
            is_active=True,
            is_demo=True,
        )
        db.add(user)
        inspector_users.append((user, district, state, lat, lon))

    # Project staff
    for i, org in enumerate(orgs[:5]):
        user = User(
            email=f"staff{i+1}@aiip.gov.in",
            full_name=f"Project Staff {i+1}",
            hashed_password=hash_password("Demo@1234"),
            role="PROJECT_STAFF",
            organization_id=org.id,
            district=org.district,
            state=org.state,
            is_active=True,
            is_demo=True,
        )
        db.add(user)

    await db.flush()
    users["inspector_users"] = inspector_users
    return users


async def seed_inspectors(db: AsyncSession, inspector_users: list) -> List:
    from app.models.inspection import Inspector
    inspectors = []
    for i, (user, district, state, lat, lon) in enumerate(inspector_users):
        inspector = Inspector(
            user_id=user.id,
            employee_id=f"EMP{2000 + i:04d}",
            district=district,
            state=state,
            latitude=lat,
            longitude=lon,
            is_available=True,
            current_workload=random.randint(0, 2),
            max_workload=3,
            specializations=["WELFARE", "REHABILITATION"] if i % 2 == 0 else ["EDUCATION", "HEALTH"],
            is_demo=True,
        )
        db.add(inspector)
        inspectors.append(inspector)
    await db.flush()
    return inspectors


async def seed_projects(db: AsyncSession, orgs: List) -> List:
    from app.models.project import Project

    projects = []

    # Hero project — deterministic state
    hero = Project(
        project_code="ABC-CWC-001",
        project_name="ABC Community Welfare Centre",
        organization_id=orgs[0].id,
        scheme="Deendayal Disability Rehabilitation Scheme",
        district="Mumbai",
        state="Maharashtra",
        address="Survey No. 47, Dharavi Road, Mumbai - 400017",
        latitude=19.0448,
        longitude=72.8558,
        beneficiary_count=65,
        staff_count=8,
        project_type="Welfare Centre",
        health_index=58.0,
        risk_level="HIGH",
        status="HIGH_ATTENTION",
        attendance_status="ANOMALY",
        cctv_status="DEGRADED",
        compliance_status="NON_COMPLIANT",
        open_findings=3,
        last_inspection=datetime.now(timezone.utc) - timedelta(days=45),
        last_report=datetime.now(timezone.utc) - timedelta(days=12),
        is_demo=True,
        is_hero_project=True,
    )
    db.add(hero)
    projects.append(hero)

    # 49 additional projects across districts
    project_names = [
        f"{random.choice(['Sahyog', 'Asha', 'Prayas', 'Umeed', 'Kalyan', 'Navodaya', 'Seva', 'Jan', 'Disha', 'Samridhi'])} "
        f"{random.choice(PROJECT_TYPES)}"
        for _ in range(49)
    ]

    for i, name in enumerate(project_names):
        district = DISTRICTS[(i + 1) % len(DISTRICTS)]
        base_lat = 18.5 + random.uniform(-2, 4)
        base_lon = 73.0 + random.uniform(-5, 8)

        health = random.uniform(40, 95)
        if health >= 80:
            risk = "LOW"; status = "MONITORING"
        elif health >= 65:
            risk = "MEDIUM"; status = "WATCH"
        elif health >= 45:
            risk = "HIGH"; status = "HIGH_ATTENTION"
        else:
            risk = "CRITICAL"; status = "INSPECTION_REQUIRED"

        p = Project(
            project_code=f"PROJ-{2000 + i:04d}",
            project_name=name,
            organization_id=orgs[i % len(orgs)].id,
            scheme=SCHEMES[i % len(SCHEMES)],
            district=district,
            state="Maharashtra" if i < 20 else ("Karnataka" if i < 35 else "Delhi"),
            latitude=base_lat,
            longitude=base_lon,
            beneficiary_count=random.randint(20, 200),
            staff_count=random.randint(3, 20),
            project_type=PROJECT_TYPES[i % len(PROJECT_TYPES)],
            health_index=round(health, 1),
            risk_level=risk,
            status=status,
            attendance_status=random.choice(["NORMAL", "NORMAL", "NORMAL", "WATCH", "ANOMALY"]),
            cctv_status=random.choice(["LIVE", "LIVE", "LIVE", "DEGRADED", "OFFLINE"]),
            compliance_status=random.choice(["COMPLIANT", "COMPLIANT", "PARTIAL", "NON_COMPLIANT"]),
            open_findings=random.randint(0, 5),
            last_inspection=datetime.now(timezone.utc) - timedelta(days=random.randint(5, 120)),
            last_report=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            is_demo=True,
            is_hero_project=False,
        )
        db.add(p)
        projects.append(p)

    await db.flush()
    return projects


async def seed_cameras(db: AsyncSession, projects: List):
    from app.models.camera import Camera, CameraEvent

    for project in projects[:20]:  # cameras for first 20 projects
        cam_count = 2 if project.is_hero_project else random.randint(1, 3)
        for j in range(cam_count):
            if project.is_hero_project:
                status = "DEGRADED" if j == 0 else "OFFLINE"
            else:
                status = random.choice(["LIVE", "LIVE", "LIVE", "DEGRADED", "OFFLINE"])

            cam = Camera(
                project_id=project.id,
                camera_name=f"CAM-{j+1:02d}",
                location_description=random.choice([
                    "Main entrance", "Common area", "Activity room",
                    "Dining hall", "Dormitory corridor", "Office area"
                ]),
                stream_url=None,
                demo_video_url="/demo/cctv_feed.mp4",
                status=status,
                last_heartbeat=(
                    datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 48))
                ),
                is_demo=True,
            )
            db.add(cam)
            await db.flush()

            # Camera events for hero project
            if project.is_hero_project and status in ("OFFLINE", "DEGRADED"):
                event = CameraEvent(
                    camera_id=cam.id,
                    event_type="OFFLINE" if status == "OFFLINE" else "DEGRADED",
                    description="CCTV signal lost — possible tampering or network failure",
                    severity="HIGH",
                    created_at=datetime.now(timezone.utc) - timedelta(hours=6),
                )
                db.add(event)


async def seed_attendance(db: AsyncSession, projects: List):
    from app.models.attendance import AttendanceRecord

    today = date.today()
    for project in projects:
        expected = project.beneficiary_count
        for d in range(60):
            record_date = today - timedelta(days=d)
            if project.is_hero_project and d < 14:
                # Inject anomaly for last 14 days
                reported = int(expected * random.uniform(0.70, 0.80))
                observed = int(expected * random.uniform(0.45, 0.55)) if d < 5 else None
                deviation = abs(reported - expected) / max(expected, 1) * 100
                flag = deviation > 20
            else:
                reported = int(expected * random.uniform(0.88, 0.98))
                observed = None
                deviation = abs(reported - expected) / max(expected, 1) * 100
                flag = deviation > 25

            rec = AttendanceRecord(
                project_id=project.id,
                record_date=record_date,
                reported_beneficiaries=max(0, reported),
                reported_staff=max(0, int(project.staff_count * random.uniform(0.8, 1.0))),
                expected_beneficiaries=expected,
                expected_staff=project.staff_count,
                observed_beneficiaries=observed,
                deviation_score=round(deviation, 2),
                anomaly_flag=flag,
                source="SELF_REPORT",
                is_demo=True,
            )
            db.add(rec)


async def seed_monitoring_signals(db: AsyncSession, projects: List):
    from app.models.monitoring import MonitoringSignal, AnomalyEvent, HealthScore
    from app.intelligence.anomaly_engine import compute_anomaly_score
    from app.intelligence.health_engine import compute_health_score

    for project in projects[:25]:
        # Health score history (last 30 days)
        for d in range(30, 0, -3):
            if project.is_hero_project:
                base_score = 74 - (30 - d) * 0.6  # declining trend
            else:
                base_score = project.health_index + random.uniform(-5, 5)

            hs = HealthScore(
                project_id=project.id,
                total_score=round(max(0, min(100, base_score)), 1),
                attendance_score=round(random.uniform(12, 23), 1),
                reporting_score=round(random.uniform(10, 19), 1),
                inspection_score=round(random.uniform(10, 18), 1),
                evidence_score=round(random.uniform(8, 14), 1),
                timeliness_score=round(random.uniform(5, 9), 1),
                findings_score=round(random.uniform(3, 8), 1),
                computed_at=datetime.now(timezone.utc) - timedelta(days=d),
                is_demo=True,
            )
            db.add(hs)

        # Anomaly event for hero project and high-risk projects
        if project.is_hero_project or project.risk_level in ("HIGH", "CRITICAL"):
            result = compute_anomaly_score(
                current_attendance=30 if project.is_hero_project else project.beneficiary_count * 0.7,
                attendance_rolling_mean=project.beneficiary_count * 0.92,
                attendance_rolling_std=project.beneficiary_count * 0.04,
                attendance_expected_min=project.beneficiary_count * 0.85,
                attendance_expected_max=project.beneficiary_count * 1.0,
                reporting_inconsistency_count=3 if project.is_hero_project else random.randint(1, 3),
                reporting_mismatch_pct=35 if project.is_hero_project else random.uniform(15, 35),
                late_submission_count=2 if project.is_hero_project else random.randint(0, 3),
                unresolved_critical_findings=1 if project.is_hero_project else random.randint(0, 1),
                unresolved_high_findings=2 if project.is_hero_project else random.randint(0, 2),
                oldest_finding_days=45 if project.is_hero_project else random.randint(10, 50),
                repeated_finding_category=True if project.is_hero_project else False,
                cctv_offline_events_7d=3 if project.is_hero_project else random.randint(0, 2),
                any_camera_currently_offline=True if project.is_hero_project else False,
                cameras_degraded_pct=50 if project.is_hero_project else 0,
            )

            anomaly = AnomalyEvent(
                project_id=project.id,
                anomaly_score=76.0 if project.is_hero_project else result.anomaly_score,
                severity="HIGH" if project.is_hero_project else result.severity,
                reasons={
                    r.key: {
                        "label": r.label,
                        "score": r.score_contribution,
                        "evidence": r.evidence,
                        "threshold": r.threshold_used,
                    }
                    for r in result.reasons
                },
                recommended_action=result.recommended_action,
                is_demo=True,
                created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
            db.add(anomaly)


async def seed_inspections_and_findings(db: AsyncSession, projects: List, inspectors: List):
    from app.models.inspection import (
        InspectionAssignment, Inspection, InspectionFinding
    )

    for i, project in enumerate(projects[:15]):
        inspector = inspectors[i % len(inspectors)]

        # Past inspection
        past_assign = InspectionAssignment(
            assignment_id=f"INS-2026-{1000 + i:04d}",
            project_id=project.id,
            inspector_id=inspector.id,
            assigned_by=1,  # super admin
            selection_algorithm="SECURE_RANDOM_V1",
            ruleset_version="1.0",
            candidate_pool_size=random.randint(3, 8),
            eligibility_reasons={
                "selected_inspector": {"eligible": True, "reasons": ["Available", "Workload OK", "Geography OK"]},
                "total_eligible": random.randint(3, 8),
            },
            status="COMPLETED",
            assigned_at=datetime.now(timezone.utc) - timedelta(days=45 if project.is_hero_project else random.randint(10, 90)),
            is_demo=True,
        )
        db.add(past_assign)
        await db.flush()

        insp = Inspection(
            inspection_code=f"INSP-{2026:04d}-{1000 + i:04d}",
            project_id=project.id,
            assignment_id=past_assign.id,
            inspector_id=inspector.id,
            status="APPROVED" if not project.is_hero_project else "UNDER_REVIEW",
            inspection_type="SURPRISE",
            start_time=datetime.now(timezone.utc) - timedelta(days=45, hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(days=45, hours=1),
            start_latitude=project.latitude + random.uniform(-0.001, 0.001),
            start_longitude=project.longitude + random.uniform(-0.001, 0.001),
            gps_accuracy=random.uniform(3, 15),
            offline_captured=random.choice([True, False]),
            overall_rating=random.choice([
                "SATISFACTORY", "NEEDS_IMPROVEMENT", "UNSATISFACTORY"
            ]) if not project.is_hero_project else "UNSATISFACTORY",
            summary_notes="Routine inspection completed. Minor irregularities observed." if not project.is_hero_project else
            "Significant attendance discrepancy observed. Reported beneficiaries do not match physical headcount.",
            is_demo=True,
        )
        db.add(insp)
        await db.flush()

        # Findings for hero project
        if project.is_hero_project:
            findings_data = [
                ("ATTENDANCE", "Attendance discrepancy", "HIGH", "OPEN",
                 "Reported 58 beneficiaries but only 31 observed during inspection."),
                ("DOCUMENTATION", "Incomplete records", "MEDIUM", "IN_PROGRESS",
                 "Daily activity registers not maintained for past 2 weeks."),
                ("FACILITY", "Infrastructure deficiency", "LOW", "OPEN",
                 "Drinking water supply disrupted in south wing."),
            ]
        else:
            findings_data = [
                (random.choice(["ATTENDANCE", "DOCUMENTATION", "FACILITY", "STAFF"]),
                 f"Finding {j+1}",
                 random.choice(["LOW", "MEDIUM", "HIGH"]),
                 random.choice(["OPEN", "IN_PROGRESS", "RESOLVED"]),
                 "Observation from routine inspection.")
                for j in range(random.randint(1, 3))
            ]

        for j, (cat, desc, sev, status, notes) in enumerate(findings_data):
            finding = InspectionFinding(
                inspection_id=insp.id,
                finding_code=f"FND-{2026:04d}-{1000 + i:04d}-{j+1:02d}",
                category=cat,
                description=desc,
                severity=sev,
                status=status,
                resolution_notes=notes if status != "OPEN" else None,
                due_date=datetime.now(timezone.utc) + timedelta(days=14),
                is_demo=True,
            )
            db.add(finding)


async def seed_followups(db: AsyncSession, projects: List):
    from app.models.followup import Followup

    for i, project in enumerate(projects[:10]):
        fu = Followup(
            followup_code=f"FU-2026-{1000 + i:04d}",
            project_id=project.id,
            created_by=1,
            action_type="REINSPECTION" if project.is_hero_project else random.choice([
                "APPROVE", "DOCUMENTS_REQUESTED", "CLOSE"
            ]),
            description=(
                "Reinspection required due to significant attendance discrepancy and unresolved findings."
                if project.is_hero_project
                else f"Follow-up action for project {project.project_name}"
            ),
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            status="OPEN" if project.is_hero_project else random.choice(["OPEN", "RESOLVED", "CLOSED"]),
            is_demo=True,
        )
        db.add(fu)


async def seed_notifications(db: AsyncSession):
    from app.models.notification import Notification

    notifs = [
        (2, "HIGH_ANOMALY", "High Anomaly Detected", "ABC Community Welfare Centre has crossed HIGH anomaly threshold (Score: 76/100)", "HIGH", "project", 1),
        (2, "CAMERA_OFFLINE", "Camera Offline", "2 cameras are offline at ABC Community Welfare Centre", "HIGH", "project", 1),
        (2, "INSPECTION_ASSIGNED", "Inspection Assigned", "Surprise inspection has been assigned for ABC Community Welfare Centre", "MEDIUM", "inspection", 1),
        (3, "FOLLOWUP_REQUIRED", "Follow-up Required", "3 open findings require follow-up action", "MEDIUM", "project", 1),
        (2, "EVIDENCE_VERIFIED", "Evidence Integrity Verified", "Inspection evidence hash verified successfully", "LOW", "evidence", 1),
    ]

    for user_id, ntype, title, msg, priority, rtype, rid in notifs:
        n = Notification(
            user_id=user_id,
            notification_type=ntype,
            title=title,
            message=msg,
            priority=priority,
            resource_type=rtype,
            resource_id=rid,
            is_read=False,
            is_demo=True,
        )
        db.add(n)


async def seed_audit_logs(db: AsyncSession):
    from app.models.audit import AuditLog

    audit_entries = [
        (1, "SUPER_ADMIN", "LOGIN", None, None, "SUCCESS", "System initialized"),
        (2, "DEPARTMENT_OFFICIAL", "LOGIN", None, None, "SUCCESS", "Official logged in"),
        (2, "DEPARTMENT_OFFICIAL", "ANOMALY", "project", 1, "SUCCESS", "Anomaly reviewed for ABC CWC"),
        (2, "DEPARTMENT_OFFICIAL", "ASSIGNMENT", "inspection", 1, "SUCCESS", "Surprise inspection assigned INS-2026-1000"),
        (4, "INSPECTION_OFFICER", "INSPECTION_START", "inspection", 1, "SUCCESS", "Field inspection started"),
        (4, "INSPECTION_OFFICER", "EVIDENCE_CAPTURE", "evidence", 1, "SUCCESS", "Photo evidence captured"),
        (4, "INSPECTION_OFFICER", "EVIDENCE_HASH", "evidence", 1, "SUCCESS", "SHA-256 computed"),
        (2, "DEPARTMENT_OFFICIAL", "EVIDENCE_VERIFY", "evidence", 1, "SUCCESS", "Evidence integrity verified"),
        (2, "DEPARTMENT_OFFICIAL", "OFFICIAL_REVIEW", "inspection", 1, "SUCCESS", "Inspection reviewed"),
        (2, "DEPARTMENT_OFFICIAL", "DECISION", "inspection", 1, "SUCCESS", "Decision: REINSPECTION"),
        (2, "DEPARTMENT_OFFICIAL", "FOLLOWUP", "followup", 1, "SUCCESS", "Follow-up created FU-2026-1000"),
    ]

    base_time = datetime.now(timezone.utc) - timedelta(hours=3)
    for i, (uid, role, action, rtype, rid, result, notes) in enumerate(audit_entries):
        log = AuditLog(
            timestamp=base_time + timedelta(minutes=i * 8),
            user_id=uid,
            role=role,
            action=action,
            resource_type=rtype,
            resource_id=rid,
            result=result,
            metadata={"notes": notes, "demo": True},
            is_demo=True,
        )
        db.add(log)


async def run_seed():
    """Main seeder entry point."""
    async with AsyncSessionLocal() as db:
        try:
            print("Starting demo data seed...")
            await clear_demo_data(db)

            orgs = await seed_organizations(db)
            users_map = await seed_users(db, orgs)
            inspectors = await seed_inspectors(db, users_map["inspector_users"])
            projects = await seed_projects(db, orgs)
            await seed_cameras(db, projects)
            await seed_attendance(db, projects)
            await seed_monitoring_signals(db, projects)
            await seed_inspections_and_findings(db, projects, inspectors)
            await seed_followups(db, projects)
            await seed_notifications(db)
            await seed_audit_logs(db)

            await db.commit()
            print("[OK] Demo data seeded successfully.")
            print("\nDemo credentials:")
            print("  Super Admin:   admin@aiip.gov.in / Demo@1234")
            print("  Official:      official@aiip.gov.in / Demo@1234")
            print("  PMU Officer:   pmu@aiip.gov.in / Demo@1234")
            print("  Inspector 1:   insp1@aiip.gov.in / Demo@1234")
            print("\nHero Project:  ABC Community Welfare Centre (ID: 1)")
            print("  Health: 58/100 | Status: HIGH_ATTENTION | Anomaly: 76/100")

        except Exception as e:
            await db.rollback()
            print(f"Seed error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
