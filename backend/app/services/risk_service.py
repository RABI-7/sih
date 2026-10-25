from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest

RULE_WEIGHTS = {
    "APAAR_MISSING": {
        "points": 25,
        "name": "Missing APAAR Identifier",
        "severity": "critical",
        "description": "Student record does not contain an APAAR ID."
    },
    "APAAR_FORMAT_INVALID": {
        "points": 25,
        "name": "Non-Standard APAAR Format",
        "severity": "high",
        "description": "APAAR ID deviates from the standard 12-digit numeric specification."
    },
    "DUPLICATE_IN_BATCH": {
        "points": 30,
        "name": "In-Batch Identifier Duplication",
        "severity": "critical",
        "description": "Same APAAR ID submitted multiple times in the current upload batch."
    },
    "DUPLICATE_INTRA_COLLEGE": {
        "points": 30,
        "name": "Intra-Institutional Duplicate Enrolment",
        "severity": "critical",
        "description": "Identifier matches a student previously enrolled at this institution."
    },
    "DUPLICATE_CROSS_COLLEGE": {
        "points": 25,
        "name": "Potential Cross-College Duplicate Enrolment",
        "severity": "high",
        "description": "Active enrolment with the same identifier discovered at another participating college."
    },
    "INTAKE_LIMIT_EXCEEDED": {
        "points": 20,
        "name": "Sanctioned Intake Capacity Overrun",
        "severity": "high",
        "description": "Admissions exceed the statutory approved intake quota for this institution."
    },
    "REGISTRY_MISMATCH": {
        "points": 15,
        "name": "Authoritative Registry Discrepancy",
        "severity": "moderate",
        "description": "Student identity details differ from the centralized mock registry."
    },
    "COUNSELLING_MISMATCH": {
        "points": 15,
        "name": "Admission Counselling Allotment Mismatch",
        "severity": "moderate",
        "description": "Programme or allotment category differs from the state/central counselling database."
    },
    "EXAM_RECORD_MISSING": {
        "points": 10,
        "name": "Unverified Qualifying Examination Record",
        "severity": "low",
        "description": "Qualifying examination board records could not be reconciled."
    },
    "FEE_RECORD_MISSING": {
        "points": 10,
        "name": "Unreconciled Admission Fee Payment",
        "severity": "low",
        "description": "No corresponding bank/treasury fee payment record was located."
    }
}


def calculate_risk_score(triggered_rule_codes: List[str]) -> Tuple[float, str, List[Dict[str, Any]]]:
    """
    Computes a transparent, deterministic rules-based risk score from 0-100.
    Returns: (score, risk_level, breakdown_items)
    """
    score = 0
    breakdown = []
    seen = set()

    for code in triggered_rule_codes:
        if code in RULE_WEIGHTS and code not in seen:
            seen.add(code)
            rule_info = RULE_WEIGHTS[code]
            score += rule_info["points"]
            breakdown.append({
                "rule_code": code,
                "rule_name": rule_info["name"],
                "points": rule_info["points"],
                "severity": rule_info["severity"],
                "description": rule_info["description"]
            })

    # Clamp to 100
    clamped_score = min(100.0, float(score))

    # Determine severity band
    if clamped_score < 20:
        level = "Low"
    elif clamped_score < 50:
        level = "Moderate"
    elif clamped_score < 75:
        level = "High"
    else:
        level = "Critical"

    return clamped_score, level, breakdown


def calculate_experimental_anomaly_score(
    risk_score: float,
    flag_count: int,
    apaar_length: int,
    has_registry_match: bool,
    has_counselling_match: bool
) -> float:
    """
    Optional scikit-learn Isolation Forest demonstration using synthetic numeric features.
    Clearly labeled as experimental.
    """
    try:
        # Features: [risk_score, flag_count, deviation_from_12_digits, registry_flag, counselling_flag]
        digit_deviation = abs(12 - apaar_length)
        features = np.array([[
            risk_score,
            flag_count,
            digit_deviation,
            0 if has_registry_match else 1,
            0 if has_counselling_match else 1
        ]])
        
        # Fit quick baseline with simulated background distribution
        background = np.array([
            [0, 0, 0, 0, 0],
            [10, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [25, 2, 0, 1, 0],
            [80, 4, 2, 1, 1],
            [0, 0, 0, 0, 0],
        ])
        combined = np.vstack([background, features])
        iso_forest = IsolationForest(random_state=42, contamination=0.2)
        iso_forest.fit(combined)
        # Decision function: lower values mean more anomalous
        raw_score = iso_forest.decision_function(features)[0]
        # Normalize to 0-1 scale where 1 is highest anomaly
        normalized_anomaly = round(float(np.clip(1.0 - (raw_score + 0.5), 0.0, 1.0)), 2)
        return normalized_anomaly
    except Exception:
        return 0.0
