"""
Unit tests for intelligence engines.
Tests: health engine, anomaly engine, assignment engine, evidence integrity.
"""
import pytest
import tempfile
import os
from app.intelligence.health_engine import compute_health_score
from app.intelligence.anomaly_engine import compute_anomaly_score
from app.intelligence.assignment_engine import (
    InspectorCandidate, run_assignment_pipeline
)
from app.intelligence.evidence_integrity import (
    compute_sha256, compute_sha256_bytes, verify_evidence_integrity
)


# ─── Health Engine Tests ──────────────────────────────────────────────────────

def test_health_score_healthy():
    result = compute_health_score(
        attendance_deviation_pct=2.0,
        reports_submitted_pct=100.0,
        days_since_last_inspection=15,
        last_inspection_rating="SATISFACTORY",
    )
    assert result.total_score > 70
    assert result.status == "HEALTHY"


def test_health_score_critical():
    result = compute_health_score(
        attendance_deviation_pct=50.0,
        attendance_anomaly_days=20,
        reports_submitted_pct=40.0,
        reporting_inconsistencies=10,
        days_since_last_inspection=120,
        last_inspection_rating="CRITICAL",
        inspection_overdue=True,
        open_critical_findings=3,
        open_high_findings=5,
        overdue_followups=5,
    )
    assert result.total_score < 45
    assert result.status == "CRITICAL"


def test_health_score_explanation_present():
    result = compute_health_score()
    assert "attendance" in result.explanation
    assert "weights" in result.explanation
    assert "disclaimer" in result.explanation
    assert result.explanation["attendance"]["max"] == 25


def test_health_score_bounded():
    result = compute_health_score(attendance_deviation_pct=0)
    assert 0 <= result.total_score <= 100


# ─── Anomaly Engine Tests ─────────────────────────────────────────────────────

def test_anomaly_no_anomaly():
    result = compute_anomaly_score(
        current_attendance=100,
        attendance_rolling_mean=100,
        attendance_rolling_std=3,
        attendance_expected_min=90,
        attendance_expected_max=110,
    )
    assert result.anomaly_score == 0.0
    assert result.severity == "LOW"
    assert result.recommended_action == "ROUTINE_MONITORING"


def test_anomaly_high_severity():
    result = compute_anomaly_score(
        current_attendance=30,
        attendance_rolling_mean=100,
        attendance_rolling_std=5,
        attendance_expected_min=90,
        attendance_expected_max=110,
        reporting_inconsistency_count=5,
        reporting_mismatch_pct=40,
        unresolved_critical_findings=2,
        cctv_offline_events_7d=4,
        any_camera_currently_offline=True,
    )
    assert result.anomaly_score >= 50
    assert result.severity in ("HIGH", "CRITICAL")
    assert result.recommended_action == "SURPRISE_INSPECTION"


def test_anomaly_has_reasons():
    result = compute_anomaly_score(
        current_attendance=30,
        attendance_rolling_mean=100,
        attendance_rolling_std=5,
        attendance_expected_min=90,
        attendance_expected_max=110,
    )
    assert len(result.reasons) > 0
    assert all(r.score_contribution >= 0 for r in result.reasons)


def test_anomaly_disclaimer():
    result = compute_anomaly_score()
    assert "HUMAN VERIFICATION REQUIRED" in result.disclaimer


def test_anomaly_score_bounded():
    result = compute_anomaly_score(
        current_attendance=0,
        attendance_rolling_mean=100,
        attendance_rolling_std=1,
        attendance_expected_min=90,
        attendance_expected_max=110,
        reporting_inconsistency_count=100,
        unresolved_critical_findings=100,
        cctv_offline_events_7d=100,
    )
    assert result.anomaly_score <= 100.0


# ─── Assignment Engine Tests ──────────────────────────────────────────────────

def make_candidates(n: int = 5) -> list[InspectorCandidate]:
    return [
        InspectorCandidate(
            inspector_id=i,
            user_id=i + 100,
            name=f"Inspector {i}",
            district="Mumbai",
            state="Maharashtra",
            latitude=19.076 + (i * 0.01),
            longitude=72.877 + (i * 0.01),
            is_available=True,
            current_workload=0,
            max_workload=3,
            specializations=["WELFARE"],
        )
        for i in range(n)
    ]


def test_assignment_selects_one():
    candidates = make_candidates(5)
    decision = run_assignment_pipeline(candidates, 19.044, 72.855)
    assert decision is not None
    assert decision.selected_inspector_id in [c.inspector_id for c in candidates]


def test_assignment_excludes_unavailable():
    candidates = make_candidates(5)
    for c in candidates[:4]:
        c.is_available = False
    decision = run_assignment_pipeline(candidates, 19.044, 72.855)
    assert decision is not None
    assert decision.selected_inspector_id == candidates[4].inspector_id


def test_assignment_no_eligible_returns_none():
    candidates = make_candidates(3)
    for c in candidates:
        c.is_available = False
    decision = run_assignment_pipeline(candidates, 19.044, 72.855)
    assert decision is None


def test_assignment_respects_distance():
    candidates = make_candidates(2)
    candidates[0].latitude = 37.0  # Far away
    candidates[0].longitude = 68.0
    decision = run_assignment_pipeline(candidates, 19.044, 72.855, max_distance_km=50)
    assert decision is not None
    assert decision.selected_inspector_id == candidates[1].inspector_id


def test_assignment_records_pool_size():
    candidates = make_candidates(8)
    candidates[0].is_available = False
    candidates[1].current_workload = 3  # Full workload
    decision = run_assignment_pipeline(candidates, 19.044, 72.855)
    assert decision is not None
    assert decision.candidate_pool_size < len(candidates)


def test_assignment_algorithm_label():
    decision = run_assignment_pipeline(make_candidates(3), 19.044, 72.855)
    assert decision is not None
    assert "SECURE_RANDOM" in decision.selection_algorithm


# ─── Evidence Integrity Tests ─────────────────────────────────────────────────

def test_sha256_bytes():
    data = b"test evidence data"
    h = compute_sha256_bytes(data)
    assert len(h) == 64
    assert h == compute_sha256_bytes(data)  # deterministic


def test_sha256_bytes_different_data():
    h1 = compute_sha256_bytes(b"data1")
    h2 = compute_sha256_bytes(b"data2")
    assert h1 != h2


def test_verify_file_verified():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(b"test image bytes")
        path = f.name
    try:
        stored_hash = compute_sha256(path)
        result = verify_evidence_integrity(path, stored_hash)
        assert result["result"] == "VERIFIED"
        assert result["match"] is True
    finally:
        os.unlink(path)


def test_verify_file_mismatch():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        f.write(b"original content")
        path = f.name
    try:
        result = verify_evidence_integrity(path, "a" * 64)
        assert result["result"] == "MISMATCH"
        assert result["match"] is False
    finally:
        os.unlink(path)


def test_verify_missing_file():
    result = verify_evidence_integrity("/nonexistent/path.jpg", "a" * 64)
    assert result["result"] == "ERROR"


def test_verify_disclaimer():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"data")
        path = f.name
    try:
        h = compute_sha256(path)
        result = verify_evidence_integrity(path, h)
        assert "disclaimer" in result
    finally:
        os.unlink(path)
