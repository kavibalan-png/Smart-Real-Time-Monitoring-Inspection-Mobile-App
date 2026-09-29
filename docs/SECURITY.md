# Security Architecture — AIIP Prototype

## Authentication Model

- **Password hashing**: bcrypt (work factor 12) via `passlib`
- **Access tokens**: JWT HS256, 30-minute expiry
- **Refresh tokens**: JWT HS256, 7-day expiry, unique JTI
- **Token storage**: Access in `sessionStorage`, refresh in `localStorage`
- **Auto-refresh**: Axios interceptor transparently refreshes on 401

## RBAC (Role-Based Access Control)

Seven roles with least-privilege permissions:

| Role | Key Permissions |
|---|---|
| SUPER_ADMIN | All |
| DEPARTMENT_OFFICIAL | Read all + assign + decision + audit |
| PMU_OFFICER | Read all + assign + review |
| INSPECTION_OFFICER | Own inspections only + evidence upload |
| PROJECT_ADMIN | Own organization projects |
| PROJECT_STAFF | Read own project |
| CITIZEN | Feedback only |

**Enforcement**: Server-side only. Frontend role is never trusted for authorization.

## Authorization

- Every API endpoint verifies: authentication → role → resource access
- Object-level authorization: inspectors cannot access others' inspections
- Project staff cannot access other organizations' data
- Inspectors cannot modify official decisions

## File Upload Security

- MIME type validation (whitelist)
- File extension validation
- Size limit enforcement (10MB)
- Server-generated safe filenames (secrets.token_hex — prevents path traversal)
- Isolated upload directory per inspection
- SHA-256 computed from bytes immediately on upload

## Evidence Integrity

- SHA-256 fingerprint computed from file bytes on upload
- Stored in separate `evidence_hashes` table
- Verification API re-reads file and compares hashes
- Cannot prevent false scene capture — only verifies byte consistency

## Audit Logging

- Append-only — no DELETE or UPDATE on audit_logs
- Logs: LOGIN, LOGOUT, ASSIGNMENT, INSPECTION_START, EVIDENCE_CAPTURE, EVIDENCE_HASH, EVIDENCE_VERIFY, DECISION, FOLLOWUP
- IP address + user agent captured
- Ordinary users cannot access audit API

## Assignment Confidentiality

- Assignment generation is server-side only
- Candidate pool never transmitted to frontend
- Uses Python `secrets.choice()` — cryptographically strong PRNG
- Assignment notifications only sent to selected inspector
- Future assignment dates not disclosed

## Offline Security

- Data stored in IndexedDB (browser-local)
- Device compromise risk acknowledged (see ASSUMPTIONS.md)
- Idempotency via local_id prevents duplicate submissions
- Sync requires valid JWT token

## Privacy

- Privacy-by-design: minimum personal data collected
- No biometric data collected
- No facial recognition
- User IDs used in references where possible
- Synthetic demo data — no real personal information

## STRIDE Threat Model

| ID | Threat | Impact | Mitigation |
|---|---|---|---|
| T1 | Identity spoofing | High | bcrypt + JWT + token expiry |
| T2 | Evidence modification | High | SHA-256 fingerprint verification |
| T3 | Unauthorized decisions | High | RBAC + object-level auth |
| T4 | Information disclosure | Medium | Role-scoped APIs + secure errors |
| T5 | Malicious uploads | High | MIME + extension + size validation |
| T6 | Privilege escalation | High | Server-side role enforcement |
| T7 | Assignment leakage | High | Backend-only selection |
| T8 | GPS manipulation | Medium | Confidence labeling + manual review |
| T9 | Offline device compromise | Medium | Device security (out of scope) |
| T10 | CCTV compromise | High | Demo mode — production requires auth RTSP |
| T11 | Replay/duplicate sync | Medium | Idempotency via local_id |
| T12 | Denial of service | Medium | Rate limiting (production: nginx/cloudflare) |

## Known Limitations (Prototype)

- No rate limiting at application layer
- No HTTPS in development
- JWT revocation not implemented (production: Redis blacklist)
- No security audit performed
