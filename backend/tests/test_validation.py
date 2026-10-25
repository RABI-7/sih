import pytest
from app.core.security import is_valid_apaar_format, mask_apaar_id
from app.services.validation_service import parse_and_validate_gate1, compute_file_sha256
import pandas as pd
import io


def test_apaar_id_format_valid():
    assert is_valid_apaar_format("900000000001") is True
    assert is_valid_apaar_format("123456789012") is True


def test_apaar_id_format_invalid_lengths():
    assert is_valid_apaar_format("12345678901") is False  # 11 digits
    assert is_valid_apaar_format("1234567890123") is False  # 13 digits
    assert is_valid_apaar_format("") is False
    assert is_valid_apaar_format(None) is False


def test_apaar_id_format_invalid_characters():
    assert is_valid_apaar_format("9012-ABCD-7890") is False
    assert is_valid_apaar_format("90123456789A") is False
    assert is_valid_apaar_format("123 456 789 012") is False


def test_mask_apaar_id():
    assert mask_apaar_id("900000000501") == "XXXX-XXXX-0501"
    assert mask_apaar_id("") == "N/A"
    assert mask_apaar_id(None) == "N/A"


def test_gate1_valid_csv():
    csv_content = b"Student Name,APAAR ID,Programme,Academic Year,Admission Date\nAarav Sharma,900000000501,B.Tech CSE,2024-2025,2024-08-01\n"
    is_valid, err, df = parse_and_validate_gate1("admissions.csv", csv_content)
    assert is_valid is True
    assert err is None
    assert df is not None
    assert len(df) == 1


def test_gate1_missing_mandatory_columns():
    csv_content = b"Student Name,Course\nAarav Sharma,B.Tech CSE\n"
    is_valid, err, df = parse_and_validate_gate1("admissions.csv", csv_content)
    assert is_valid is False
    assert "Missing required column" in err


def test_gate1_unsupported_file_extension():
    csv_content = b"some random text"
    is_valid, err, df = parse_and_validate_gate1("admissions.pdf", csv_content)
    assert is_valid is False
    assert "Unsupported file format" in err


def test_file_sha256_integrity():
    content = b"Sample File Payload"
    sha1 = compute_file_sha256(content)
    sha2 = compute_file_sha256(content)
    assert sha1 == sha2
    assert len(sha1) == 64
