"""
Controlled Surprise Assignment Engine
=======================================
Server-side secure randomized inspector assignment.
The frontend NEVER receives the candidate pool — only the final assignment.

Pipeline:
  CANDIDATES → ELIGIBILITY → AVAILABILITY → WORKLOAD →
  GEOGRAPHY → RULE_CONSTRAINTS → SECURE_RANDOMIZATION →
  ASSIGNMENT → AUDIT

Uses secrets.choice() — cryptographically strong PRNG.
"""
import secrets
from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class InspectorCandidate:
    inspector_id: int
    user_id: int
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    is_available: bool
    current_workload: int
    max_workload: int
    specializations: list[str]


@dataclass
class AssignmentDecision:
    selected_inspector_id: int
    candidate_pool_size: int
    eligibility_reasons: dict
    selection_algorithm: str = "SECURE_RANDOM_V1"
    ruleset_version: str = "1.0"
    algorithm_version: str = "1.0"


@dataclass
class EligibilityReport:
    eligible: bool
    reasons: list[str]
    exclusion_reason: Optional[str] = None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _check_eligibility(
    candidate: InspectorCandidate,
    project_lat: float,
    project_lon: float,
    max_distance_km: float = 150.0,
    max_workload_threshold: int = 3,
) -> EligibilityReport:
    """
    Evaluate inspector eligibility for a project assignment.
    Returns a fully auditable eligibility report.
    """
    reasons = []

    # 1. Availability check
    if not candidate.is_available:
        return EligibilityReport(
            eligible=False,
            reasons=[],
            exclusion_reason="Inspector marked unavailable",
        )
    reasons.append("Inspector is available")

    # 2. Workload check
    if candidate.current_workload >= min(candidate.max_workload, max_workload_threshold):
        return EligibilityReport(
            eligible=False,
            reasons=reasons,
            exclusion_reason=f"Workload full: {candidate.current_workload}/{candidate.max_workload}",
        )
    reasons.append(f"Workload acceptable: {candidate.current_workload}/{candidate.max_workload}")

    # 3. Geographic check
    distance = _haversine_km(
        candidate.latitude, candidate.longitude, project_lat, project_lon
    )
    if distance > max_distance_km:
        return EligibilityReport(
            eligible=False,
            reasons=reasons,
            exclusion_reason=f"Distance {distance:.1f}km exceeds limit {max_distance_km}km",
        )
    reasons.append(f"Geographic compatibility: {distance:.1f}km from project")

    return EligibilityReport(eligible=True, reasons=reasons)


def run_assignment_pipeline(
    candidates: list[InspectorCandidate],
    project_lat: float,
    project_lon: float,
    max_distance_km: float = 150.0,
) -> Optional[AssignmentDecision]:
    """
    Run the full assignment pipeline.

    Returns AssignmentDecision with the selected inspector, or None if no
    eligible candidate found.

    Security guarantee: candidate pool is never exposed to callers
    beyond the final selected inspector ID and pool size.
    """
    eligible = []
    eligibility_log = {}

    for candidate in candidates:
        report = _check_eligibility(
            candidate, project_lat, project_lon, max_distance_km
        )
        eligibility_log[candidate.inspector_id] = {
            "eligible": report.eligible,
            "reasons": report.reasons,
            "exclusion_reason": report.exclusion_reason,
        }
        if report.eligible:
            eligible.append(candidate)

    if not eligible:
        return None

    # Secure randomized selection — cryptographically strong
    selected = secrets.choice(eligible)

    return AssignmentDecision(
        selected_inspector_id=selected.inspector_id,
        candidate_pool_size=len(eligible),
        eligibility_reasons={
            "selected_inspector": eligibility_log[selected.inspector_id],
            "total_candidates_evaluated": len(candidates),
            "total_eligible": len(eligible),
            "selection_method": "Cryptographically secure random selection (secrets.choice)",
            "rule_constraints": {
                "max_distance_km": max_distance_km,
                "availability_required": True,
                "workload_limit": 3,
            },
        },
    )
