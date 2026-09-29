"""
Composite Monitoring Health Index Engine
=========================================
Computes an explainable 0–100 health score from multiple weighted dimensions.

Label: "Composite Monitoring Health Index — Prototype"
This is a configurable rule-based scoring system, not a trained ML model.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone, timedelta


# Configurable weights (must sum to 100)
HEALTH_WEIGHTS = {
    "attendance": 25,
    "reporting": 20,
    "inspection": 20,
    "evidence": 15,
    "timeliness": 10,
    "findings": 10,
}


@dataclass
class HealthScoreResult:
    total_score: float
    status: str  # HEALTHY / WATCH / HIGH_ATTENTION / CRITICAL
    attendance_score: float
    reporting_score: float
    inspection_score: float
    evidence_score: float
    timeliness_score: float
    findings_score: float
    explanation: dict
    computed_at: datetime


def _score_attendance(
    recent_deviation_pct: float,  # % deviation from expected baseline
    anomaly_days_last_30: int,    # days with flagged anomalies
) -> tuple[float, str]:
    """Score attendance consistency 0–25."""
    base = 25.0
    # Penalize for deviation
    if recent_deviation_pct >= 40:
        base -= 15
    elif recent_deviation_pct >= 25:
        base -= 10
    elif recent_deviation_pct >= 15:
        base -= 6
    elif recent_deviation_pct >= 5:
        base -= 3

    # Penalize for repeated anomaly days
    anomaly_penalty = min(anomaly_days_last_30 * 0.8, 8)
    base -= anomaly_penalty

    score = max(0.0, round(base, 1))
    reason = (
        f"Deviation: {recent_deviation_pct:.1f}%, "
        f"Anomaly days (30d): {anomaly_days_last_30}"
    )
    return score, reason


def _score_reporting(
    reports_submitted_pct: float,  # % of expected reports submitted
    inconsistency_count: int,       # reports with data inconsistencies
) -> tuple[float, str]:
    """Score reporting consistency 0–20."""
    base = reports_submitted_pct / 100 * 20
    penalty = min(inconsistency_count * 1.5, 8)
    score = max(0.0, round(base - penalty, 1))
    reason = (
        f"Submission rate: {reports_submitted_pct:.1f}%, "
        f"Inconsistencies: {inconsistency_count}"
    )
    return score, reason


def _score_inspection(
    days_since_last_inspection: int,
    last_rating: Optional[str],
    overdue: bool,
) -> tuple[float, str]:
    """Score inspection compliance 0–20."""
    base = 20.0
    if overdue:
        base -= 8
    if days_since_last_inspection > 90:
        base -= 6
    elif days_since_last_inspection > 60:
        base -= 3

    rating_penalty = {
        "CRITICAL": 8, "UNSATISFACTORY": 5, "NEEDS_IMPROVEMENT": 2,
        "SATISFACTORY": 0, None: 3
    }
    base -= rating_penalty.get(last_rating, 3)
    score = max(0.0, round(base, 1))
    reason = (
        f"Last inspection: {days_since_last_inspection}d ago, "
        f"Rating: {last_rating or 'N/A'}"
    )
    return score, reason


def _score_evidence(
    evidence_completeness_pct: float,
    integrity_failures: int,
) -> tuple[float, str]:
    """Score evidence completeness 0–15."""
    base = evidence_completeness_pct / 100 * 15
    penalty = min(integrity_failures * 3, 9)
    score = max(0.0, round(base - penalty, 1))
    reason = (
        f"Completeness: {evidence_completeness_pct:.1f}%, "
        f"Integrity failures: {integrity_failures}"
    )
    return score, reason


def _score_timeliness(
    avg_response_days: float,
    overdue_followups: int,
) -> tuple[float, str]:
    """Score response timeliness 0–10."""
    base = 10.0
    if avg_response_days > 14:
        base -= 5
    elif avg_response_days > 7:
        base -= 3
    elif avg_response_days > 3:
        base -= 1
    penalty = min(overdue_followups * 1.5, 5)
    score = max(0.0, round(base - penalty, 1))
    reason = (
        f"Avg response: {avg_response_days:.1f}d, "
        f"Overdue follow-ups: {overdue_followups}"
    )
    return score, reason


def _score_findings(
    open_critical: int,
    open_high: int,
    unresolved_total: int,
) -> tuple[float, str]:
    """Score open findings 0–10 (penalty-based)."""
    base = 10.0
    base -= min(open_critical * 3, 6)
    base -= min(open_high * 1.5, 4)
    base -= min(unresolved_total * 0.3, 3)
    score = max(0.0, round(base, 1))
    reason = (
        f"Open critical: {open_critical}, "
        f"Open high: {open_high}, "
        f"Total unresolved: {unresolved_total}"
    )
    return score, reason


def _determine_status(score: float) -> str:
    if score >= 80:
        return "HEALTHY"
    elif score >= 65:
        return "WATCH"
    elif score >= 45:
        return "HIGH_ATTENTION"
    else:
        return "CRITICAL"


def compute_health_score(
    attendance_deviation_pct: float = 0.0,
    attendance_anomaly_days: int = 0,
    reports_submitted_pct: float = 100.0,
    reporting_inconsistencies: int = 0,
    days_since_last_inspection: int = 30,
    last_inspection_rating: Optional[str] = "SATISFACTORY",
    inspection_overdue: bool = False,
    evidence_completeness_pct: float = 100.0,
    evidence_integrity_failures: int = 0,
    avg_response_days: float = 2.0,
    overdue_followups: int = 0,
    open_critical_findings: int = 0,
    open_high_findings: int = 0,
    unresolved_findings_total: int = 0,
) -> HealthScoreResult:
    """
    Compute the Composite Monitoring Health Index.
    Returns a fully explainable score with per-dimension breakdown.
    """
    att_score, att_reason = _score_attendance(attendance_deviation_pct, attendance_anomaly_days)
    rep_score, rep_reason = _score_reporting(reports_submitted_pct, reporting_inconsistencies)
    ins_score, ins_reason = _score_inspection(
        days_since_last_inspection, last_inspection_rating, inspection_overdue
    )
    evi_score, evi_reason = _score_evidence(evidence_completeness_pct, evidence_integrity_failures)
    tim_score, tim_reason = _score_timeliness(avg_response_days, overdue_followups)
    fin_score, fin_reason = _score_findings(
        open_critical_findings, open_high_findings, unresolved_findings_total
    )

    total = att_score + rep_score + ins_score + evi_score + tim_score + fin_score
    total = round(min(100.0, max(0.0, total)), 1)
    status = _determine_status(total)

    return HealthScoreResult(
        total_score=total,
        status=status,
        attendance_score=att_score,
        reporting_score=rep_score,
        inspection_score=ins_score,
        evidence_score=evi_score,
        timeliness_score=tim_score,
        findings_score=fin_score,
        explanation={
            "attendance": {
                "score": att_score,
                "max": HEALTH_WEIGHTS["attendance"],
                "reason": att_reason,
            },
            "reporting": {
                "score": rep_score,
                "max": HEALTH_WEIGHTS["reporting"],
                "reason": rep_reason,
            },
            "inspection": {
                "score": ins_score,
                "max": HEALTH_WEIGHTS["inspection"],
                "reason": ins_reason,
            },
            "evidence": {
                "score": evi_score,
                "max": HEALTH_WEIGHTS["evidence"],
                "reason": evi_reason,
            },
            "timeliness": {
                "score": tim_score,
                "max": HEALTH_WEIGHTS["timeliness"],
                "reason": tim_reason,
            },
            "findings": {
                "score": fin_score,
                "max": HEALTH_WEIGHTS["findings"],
                "reason": fin_reason,
            },
            "weights": HEALTH_WEIGHTS,
            "label": "Composite Monitoring Health Index — Prototype",
            "disclaimer": (
                "This score is computed from configurable rules on synthetic demo data. "
                "It is not an official government assessment."
            ),
        },
        computed_at=datetime.now(timezone.utc),
    )
