# Adaptive Inspection Intelligence Platform (AIIP)

**Smart India Hackathon 2026 | PS 26095**  
**Ministry of Social Justice and Empowerment | Smart Automation**

> Monitor continuously → Detect anomalies → Explain → Securely assign surprise inspections → Capture verifiable evidence → Keep humans in control → Track through resolution.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- OR: Python 3.11+ and Node.js 20+

### Option A: Docker Compose (Recommended)

```bash
cd f:/sih

# Copy environment config
cp .env.example .env

# Start everything
docker compose up --build

# App available at:
# Frontend: http://localhost:3000
# API docs:  http://localhost:8000/api/docs
```

### Option B: Local Development

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Set environment
copy ..\\.env.example .env    # Edit with your PostgreSQL credentials

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.seed.seeder

# Start API server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend

npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
# Frontend: http://localhost:5173
```

**Tests:**
```bash
cd backend
pytest tests/ -v
```

---

## Demo Credentials

| Role | Email | Password |
|---|---|---|
| Department Official | official@aiip.gov.in | Demo@1234 |
| PMU Officer | pmu@aiip.gov.in | Demo@1234 |
| Inspector | insp1@aiip.gov.in | Demo@1234 |
| Super Admin | admin@aiip.gov.in | Demo@1234 |

---

## 5-Minute Judge Demo Script

### 0:00–0:30 — Command Center
1. Login as `official@aiip.gov.in`
2. Command Center loads — immediately shows:
   - **Project ABC Community Welfare Centre**
   - **Health: 58/100 | HIGH ATTENTION**
   - Anomaly Score: 76/100

### 0:30–1:15 — Explain
3. Click **WHY THIS ALERT?**
4. System explains: attendance deviation, reporting mismatch, CCTV anomaly, unresolved finding
5. Note: "POTENTIAL DISCREPANCY — HUMAN VERIFICATION REQUIRED"

### 1:15–1:45 — Initiate Surprise Inspection
6. Click **Initiate Inspection**
7. Click **Review Recommendation** → see system recommendation
8. Click **Initiate Surprise Inspection**
9. Assignment generated with: ID, inspector name, pool size, algorithm
10. Show **WHY THIS INSPECTOR?** rationale

### 1:45–3:00 — Mobile Field Inspection
11. In a new tab/mobile, login as `insp1@aiip.gov.in`
12. Navigate to **My Inspections** → see new assignment
13. Click **Start Inspection**
14. Tap **Capture GPS**
15. Click **Add Photo** — upload any image
16. Note SHA-256 hash computed automatically
17. Complete checklist items (PASS/FAIL/PARTIAL)
18. Add summary notes
19. Toggle browser offline (DevTools → Network → Offline)
20. Show **OFFLINE MODE ACTIVE** banner
21. Submit → "Data saved locally"

### 3:00–3:30 — Sync
22. Re-enable network
23. Navigate to **Sync Pending Data**
24. Click **Sync** — watch records upload

### 3:30–4:00 — Evidence Integrity
25. Back as Official: navigate to Inspections → Review
26. Click **Verify** on uploaded evidence
27. **✓ EVIDENCE INTEGRITY VERIFIED** — SHA-256 match confirmed

### 4:00–4:40 — Evidence Thread + Decision
28. Scroll to **Evidence Digital Thread**
29. Show each event: anomaly → assignment → inspection start → GPS → evidence → hash → submit
30. Scroll to **Official Decision**
31. Note: "AI assists. Authorized official decides."

### 4:40–5:00 — Decision + Follow-up
32. Click **Request Reinspection**
33. Follow-up created automatically
34. Project status updates
35. Audit trail captures every action

---

## Key Differentiators

| Feature | Implementation |
|---|---|
| Explainable AI | Every output has WHY? with evidence and thresholds |
| Controlled assignment | Backend-only secrets.choice() — pool never exposed |
| Evidence integrity | SHA-256 fingerprint computed on upload, verified on demand |
| Digital thread | Every event from anomaly to resolution persisted and displayed |
| Human-in-the-loop | System recommends, official decides |
| Offline-first | IndexedDB queue, idempotent sync |
| Audit trail | Append-only, read-only, comprehensive |

---

## Architecture
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Security
See [docs/SECURITY.md](docs/SECURITY.md)

## Assumptions
See [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)
