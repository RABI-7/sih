import pytest
from app.services.duplicate_service import check_batch_duplicates
from app.services.risk_service import calculate_risk_score


def test_batch_duplicate_detection():
    rows = [
        {"row_number": 1, "apaar_id": "900000000001"},
        {"row_number": 2, "apaar_id": "900000000002"},
        {"row_number": 3, "apaar_id": "900000000001"},  # duplicate with row 1
        {"row_number": 4, "apaar_id": "900000000003"}
    ]
    duplicates = check_batch_duplicates(rows)
    assert "900000000001" in duplicates
    assert duplicates["900000000001"] == [1, 3]
    assert "900000000002" not in duplicates


def test_risk_score_deterministic_calculation():
    # Test multiple rule combinations
    score, level, breakdown = calculate_risk_score(["APAAR_MISSING", "DUPLICATE_IN_BATCH"])
    # 25 + 30 = 55 -> High severity
    assert score == 55.0
    assert level == "High"
    assert len(breakdown) == 2


def test_risk_score_clamping():
    # If many flags trigger, maximum score must be capped at 100
    all_rules = [
        "APAAR_MISSING",
        "DUPLICATE_IN_BATCH",
        "DUPLICATE_CROSS_COLLEGE",
        "INTAKE_LIMIT_EXCEEDED",
        "REGISTRY_MISMATCH",
        "COUNSELLING_MISMATCH"
    ]
    score, level, breakdown = calculate_risk_score(all_rules)
    assert score == 100.0
    assert level == "Critical"
