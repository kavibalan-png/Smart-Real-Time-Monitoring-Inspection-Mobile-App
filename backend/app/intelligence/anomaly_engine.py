"""
Anomaly Intelligence Engine
============================
Transparent hybrid anomaly detection using:
- Rule-based detection
- Statistical deviation (z-score / rolling mean)
- Trend analysis
- Pattern detection

Data dictionary:
  Input:  attendance history, reporting records, CCTV events, findings
  Method: statistical deviation + rule-based thresholds
  Output: anomaly_score (0–100), severity, reasons, recommended_action
  Limitation: requires sufficient historical data (>=14 days)

IMPORTANT: Never claims "fraud confirmed". Always returns
"POTENTIAL DISCREPANCY — HUMAN VERIFICATION REQUIRED"
"""
from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class AnomalyReason:
    key: str
    label: str
    score_contribution: float
    evidence: str
    threshold_used: str


@dataclass
class AnomalyResult:
    anomaly_score: float
    severity: str           # LOW / MEDIUM / HIGH / CRITICAL
    reasons: list[AnomalyReason]
    recommended_action: str
    algorithm_version: str = "1.0"
    disclaimer: str = "POTENTIAL DISCREPANCY — HUMAN VERIFICATION REQUIRED"
    explanation: dict = field(default_factory=dict)


def _z_score(value: float, mean: float, std: float) -> float:
    """Compute z-score; returns 0 if std is too small."""
    if std < 0.001:
        return 0.0
    return abs(value - mean) / std


def _attendance_anomaly_score(
    current: float,
    rolling_mean: float,
    rolling_std: float,
    expected_min: float,
    expected_max: float,
) -> tuple[float, str, str]:
    """Score attendance anomaly 0–30."""
    z = _z_score(current, rolling_mean, rolling_std)
    score = 0.0

    if current < expected_min:
        pct_below = (expected_min - current) / max(expected_min, 1) * 100
        score = min(pct_below * 0.6, 28)
        evidence = (
            f"Current {current:.0f} below expected range "
            f"[{expected_min:.0f}–{expected_max:.0f}]. "
            f"Z-score: {z:.2f}"
        )
        threshold = f"Below expected minimum {expected_min:.0f}"
    elif z > 2.0:
        score = min(z * 5, 20)
        evidence = f"Z-score {z:.2f} > 2.0 threshold. Mean: {rolling_mean:.1f}, Std: {rolling_std:.1f}"
        threshold = "Z-score > 2.0"
    else:
        score = 0.0
        evidence = f"Within normal range. Z-score: {z:.2f}"
        threshold = "No threshold breached"

    return round(score, 1), evidence, threshold


def _reporting_anomaly_score(
    inconsistency_count: int,
    mismatch_pct: float,
    late_submission_count: int,
) -> tuple[float, str, str]:
    """Score reporting anomaly 0–25."""
    score = 0.0
    score += min(inconsistency_count * 3, 12)
    score += min(mismatch_pct * 0.2, 10)
    score += min(late_submission_count * 0.8, 6)
    evidence = (
        f"Inconsistencies: {inconsistency_count}, "
        f"Mismatch: {mismatch_pct:.1f}%, "
        f"Late submissions: {late_submission_count}"
    )
    threshold = "Inconsistency count > 0 or mismatch > 10%"
    return round(min(score, 25), 1), evidence, threshold


def _findings_anomaly_score(
    unresolved_critical: int,
    unresolved_high: int,
    oldest_finding_days: int,
    repeated_category: bool,
) -> tuple[float, str, str]:
    """Score unresolved findings anomaly 0–20."""
    score = 0.0
    score += min(unresolved_critical * 5, 12)
    score += min(unresolved_high * 2, 6)
    if oldest_finding_days > 30:
        score += min((oldest_finding_days - 30) * 0.1, 5)
    if repeated_category:
        score += 4
    evidence = (
        f"Unresolved critical: {unresolved_critical}, "
        f"Unresolved high: {unresolved_high}, "
        f"Oldest finding: {oldest_finding_days}d"
    )
    threshold = "Any unresolved critical finding"
    return round(min(score, 20), 1), evidence, threshold


def _cctv_anomaly_score(
    offline_events_last_7d: int,
    current_camera_offline: bool,
    degraded_pct: float,
) -> tuple[float, str, str]:
    """Score CCTV monitoring anomaly 0–15."""
    score = 0.0
    score += min(offline_events_last_7d * 2, 8)
    if current_camera_offline:
        score += 5
    score += min(degraded_pct * 0.1, 4)
    evidence = (
        f"Offline events (7d): {offline_events_last_7d}, "
        f"Currently offline: {current_camera_offline}, "
        f"Degraded: {degraded_pct:.1f}%"
    )
    threshold = "Any camera offline event"
    return round(min(score, 15), 1), evidence, threshold


def _activity_anomaly_score(
    activity_change_pct: float,
    days_no_activity: int,
) -> tuple[float, str, str]:
    """Score sudden activity change 0–10."""
    score = 0.0
    if activity_change_pct > 50:
        score += min(activity_change_pct * 0.1, 6)
    if days_no_activity > 7:
        score += min(days_no_activity * 0.5, 5)
    evidence = (
        f"Activity change: {activity_change_pct:.1f}%, "
        f"No activity days: {days_no_activity}"
    )
    threshold = "Activity change > 50% or no activity > 7d"
    return round(min(score, 10), 1), evidence, threshold


def _classify_severity(score: float) -> str:
    if score >= 70:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    else:
        return "LOW"


def _recommend_action(score: float, severity: str) -> str:
    if severity in ("CRITICAL", "HIGH"):
        return "SURPRISE_INSPECTION"
    elif severity == "MEDIUM":
        return "ENHANCED_MONITORING"
    else:
        return "ROUTINE_MONITORING"


def compute_anomaly_score(
    # Attendance
    current_attendance: float = 0,
    attendance_rolling_mean: float = 0,
    attendance_rolling_std: float = 0,
    attendance_expected_min: float = 0,
    attendance_expected_max: float = 0,
    # Reporting
    reporting_inconsistency_count: int = 0,
    reporting_mismatch_pct: float = 0,
    late_submission_count: int = 0,
    # Findings
    unresolved_critical_findings: int = 0,
    unresolved_high_findings: int = 0,
    oldest_finding_days: int = 0,
    repeated_finding_category: bool = False,
    # CCTV
    cctv_offline_events_7d: int = 0,
    any_camera_currently_offline: bool = False,
    cameras_degraded_pct: float = 0,
    # Activity
    activity_change_pct: float = 0,
    days_no_activity: int = 0,
) -> AnomalyResult:
    """
    Compute an explainable anomaly score (0–100).

    Method: Rule-based thresholds + statistical deviation.
    Each dimension has a capped maximum contribution.
    Total is sum of contributions, capped at 100.
    """
    att_s, att_ev, att_th = _attendance_anomaly_score(
        current_attendance, attendance_rolling_mean, attendance_rolling_std,
        attendance_expected_min, attendance_expected_max
    )
    rep_s, rep_ev, rep_th = _reporting_anomaly_score(
        reporting_inconsistency_count, reporting_mismatch_pct, late_submission_count
    )
    fin_s, fin_ev, fin_th = _findings_anomaly_score(
        unresolved_critical_findings, unresolved_high_findings,
        oldest_finding_days, repeated_finding_category
    )
    cctv_s, cctv_ev, cctv_th = _cctv_anomaly_score(
        cctv_offline_events_7d, any_camera_currently_offline, cameras_degraded_pct
    )
    act_s, act_ev, act_th = _activity_anomaly_score(activity_change_pct, days_no_activity)

    total = round(min(100.0, att_s + rep_s + fin_s + cctv_s + act_s), 1)
    severity = _classify_severity(total)
    action = _recommend_action(total, severity)

    reasons = []
    if att_s > 0:
        reasons.append(AnomalyReason(
            key="attendance_deviation",
            label="Attendance Deviation",
            score_contribution=att_s,
            evidence=att_ev,
            threshold_used=att_th,
        ))
    if rep_s > 0:
        reasons.append(AnomalyReason(
            key="reporting_mismatch",
            label="Reporting Mismatch",
            score_contribution=rep_s,
            evidence=rep_ev,
            threshold_used=rep_th,
        ))
    if fin_s > 0:
        reasons.append(AnomalyReason(
            key="unresolved_findings",
            label="Unresolved Findings",
            score_contribution=fin_s,
            evidence=fin_ev,
            threshold_used=fin_th,
        ))
    if cctv_s > 0:
        reasons.append(AnomalyReason(
            key="cctv_anomaly",
            label="CCTV Monitoring Anomaly",
            score_contribution=cctv_s,
            evidence=cctv_ev,
            threshold_used=cctv_th,
        ))
    if act_s > 0:
        reasons.append(AnomalyReason(
            key="activity_change",
            label="Unusual Activity Pattern",
            score_contribution=act_s,
            evidence=act_ev,
            threshold_used=act_th,
        ))

    # Sort reasons by contribution descending
    reasons.sort(key=lambda r: r.score_contribution, reverse=True)

    return AnomalyResult(
        anomaly_score=total,
        severity=severity,
        reasons=reasons,
        recommended_action=action,
        explanation={
            "method": "Rule-based thresholds + statistical deviation (z-score)",
            "dimensions": {
                "attendance": {"contribution": att_s, "max": 30},
                "reporting": {"contribution": rep_s, "max": 25},
                "findings": {"contribution": fin_s, "max": 20},
                "cctv": {"contribution": cctv_s, "max": 15},
                "activity": {"contribution": act_s, "max": 10},
            },
            "limitation": (
                "Requires >=14 days of historical data for statistical accuracy. "
                "Results are indicative, not conclusive."
            ),
            "disclaimer": "POTENTIAL DISCREPANCY — HUMAN VERIFICATION REQUIRED",
        },
    )
