# Assumptions Register — AIIP Prototype

**Project:** Adaptive Inspection Intelligence Platform  
**PS:** 26095 | SIH 2026 | Ministry of Social Justice and Empowerment  
**Version:** 1.0.0-prototype  

---

## Synthetic / Demo Data

| Assumption | Detail |
|---|---|
| All project data is synthetic | 50 fictional projects across Maharashtra, Karnataka, Delhi |
| All user accounts are demo accounts | Created for judging only — password: Demo@1234 |
| Attendance records are algorithmically generated | Hero project injected with deliberate anomalies |
| Hero project (ABC Community Welfare Centre) | Deterministic anomaly scenario for demo |
| DEMO_DATA flag | All seeded records have `is_demo = true` |

## CCTV Integration

| Assumption | Detail |
|---|---|
| No real CCTV integration | Demo feed placeholder only |
| Camera heartbeat is simulated | Not connected to any real RTSP/HLS stream |
| Label shown in UI | "SIMULATED CCTV — DEMO FEED" on all cameras |
| Production requirement | Would need RTSP adapter + HLS transcoder |

## Anomaly Engine

| Assumption | Detail |
|---|---|
| Statistical method | Rule-based + z-score statistical deviation |
| Requires 14+ days of data | Accuracy improves with historical depth |
| Not a trained ML model | Configurable thresholds, transparent logic |
| Thresholds are configurable | Not calibrated against real government data |

## GPS / Location

| Assumption | Detail |
|---|---|
| GPS is evidence metadata | Not absolute proof of physical location |
| Mobile browser GPS | Accuracy varies (3–50m typical) |
| GPS confidence levels | HIGH <5m, MEDIUM <20m, LOW ≥20m |
| Spoofing mitigation | Not implemented — production would require server-side validation |

## Evidence Integrity

| Assumption | Detail |
|---|---|
| SHA-256 verifies byte consistency | Does NOT verify scene authenticity |
| Storage is local filesystem | Production requires object storage (S3/MinIO) |
| No blockchain | SHA-256 hashing with stored records — clear and auditable |

## Authentication / Security

| Assumption | Detail |
|---|---|
| JWT stateless | Refresh token strategy implemented but not revocation list |
| Rate limiting | Not implemented at application layer (nginx/cloudflare in production) |
| HTTPS | Not configured in development (required in production) |
| bcrypt password hashing | Rounds = 12 |

## External Integrations

| Assumption | Detail |
|---|---|
| No production API credentials | All external integrations are mocked |
| Video conferencing (VC) | P2 feature — UI placeholder only |
| SMS/email notifications | Not implemented — push notifications only within app |
| Map tiles | OpenStreetMap (free, no API key required) |

## Prototype Limitations

- This is a demonstration prototype, not a production system
- Has not been security-audited by a qualified cybersecurity firm
- Not legally certified for government production use
- Attendance analytics cannot definitively determine fraud
- Health index scores are illustrative, not official assessments
- All AI/ML outputs require human verification before action
