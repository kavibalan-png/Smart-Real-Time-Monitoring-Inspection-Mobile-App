# System Architecture — AIIP

## Overview

```
React PWA (TypeScript + Vite + Tailwind)
    ↕ REST/JSON + WebSockets
FastAPI (Python 3.11 + SQLAlchemy async)
    ↕ asyncpg
PostgreSQL 15
```

## Component Map

```
frontend/src/
├── pages/
│   ├── auth/          LoginPage
│   ├── official/      CommandCenter, ProjectDetail, InspectionsList,
│   │                  EvidenceReview, SurpriseAssignment, FollowupPage, AuditPage
│   └── inspector/     InspectorHome, FieldInspection, OfflineSync
├── components/
│   ├── layout/        AppShell, NotificationBell
│   └── shared/        HealthIndexRing, WhyExplainer, StatusBadge,
│                      EvidenceIntegrityBadge, DemoBanner
├── services/          api.ts (typed Axios client)
├── offline/           offlineDB.ts (IndexedDB), syncService.ts
└── store/             AuthProvider, authStore

backend/app/
├── api/v1/endpoints/  auth, projects, monitoring, analytics,
│                      inspections, evidence, cctv, followup,
│                      notifications, audit, websocket
├── intelligence/      health_engine, anomaly_engine,
│                      assignment_engine, evidence_integrity
├── models/            14 SQLAlchemy ORM models
├── services/          audit_service, notification_service, health_service
├── core/              config, database, security, permissions, dependencies
└── seed/              seeder.py (50 projects + hero scenario)
```

## Core Workflows

### Anomaly Detection Flow
```
Attendance records → AttendanceAnomalyScorer (z-score)
Reporting records  → ReportingConsistencyCheck
Camera events      → CCTVAnomalyDetector
Open findings      → FindingsAnomalyScorer
                   ↓
           AnomalyEvent (persisted)
                   ↓
        Project.risk_level updated
                   ↓
      WebSocket broadcast to command center
```

### Surprise Assignment Flow
```
Official clicks "Initiate Inspection"
        ↓
POST /api/inspections/assign
        ↓ (server-side only)
Load all available Inspector records
        ↓
EligibilityFilter: availability + workload + geography
        ↓
secrets.choice(eligible_pool)  ← cryptographic PRNG
        ↓
InspectionAssignment persisted (full audit trail)
        ↓
Notification sent to inspector only
        ↓
Response: assignment_id + inspector_name + pool_size
          (candidate pool never returned)
```

### Evidence Integrity Flow
```
Inspector uploads file
        ↓
Server: MIME + extension + size validation
        ↓
Server: generate safe filename (secrets.token_hex)
        ↓
Write to upload_dir/{inspection_id}/{safe_filename}
        ↓
compute_sha256_bytes(content) — from memory
        ↓
EvidenceHash record persisted
        ↓
Official clicks "Verify"
        ↓
POST /api/evidence/verify/{id}
        ↓
re-read file → compute_sha256(file_path)
        ↓
compare with stored hash
        ↓
VERIFIED or MISMATCH
```

### Offline Sync Flow
```
Network unavailable detected (navigator.onLine = false)
        ↓
UI shows "OFFLINE MODE"
        ↓
Inspector actions → queueOperation(type, payload) → IndexedDB
Evidence files   → queueEvidenceFile(inspectionId, blob) → IndexedDB
        ↓
Network returns
        ↓
User taps "Sync Now" (or auto-trigger)
        ↓
getPendingOperations() → ordered queue
        ↓
For each: POST to API (idempotency via local_id)
        ↓
updateOperationStatus(SUCCESS/FAILED/RETRY)
        ↓
No data loss — failed items retry up to 3 times
```

## Database Schema (key relationships)

```
users ──────────────── organizations
  │                         │
  └── inspectors        projects ──── cameras
         │                   │         └── camera_events
         └── inspection_assignments   attendance_records
                  │                   monitoring_signals
                  └── inspections ─── anomaly_events
                           │          health_scores
                           ├── inspection_checklists
                           ├── inspection_findings
                           └── evidence ─── evidence_hashes
                                            └── evidence_verifications
projects ──── followups
users    ──── notifications
users    ──── audit_logs
```
