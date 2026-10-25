import os
import hashlib
import io
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.core.security import is_valid_apaar_format, mask_apaar_id
from app.services.registry_service import registry_service
from app.services.duplicate_service import (
    check_batch_duplicates,
    check_intra_college_duplicate,
    check_cross_college_duplicate
)
from app.services.intake_service import get_college_intake_status
from app.services.risk_service import calculate_risk_score, calculate_experimental_anomaly_score
from app.models.student import Student
from app.models.validation_flag import ValidationFlag
from app.models.upload_batch import UploadBatch
from app.models.college import College

COLUMN_MAPPINGS = {
    "student_name": ["student name", "student_name", "name", "candidate name", "candidate_name"],
    "apaar_id": ["apaar id", "apaar_id", "apaar", "apaar_number", "student apaar id"],
    "programme": ["programme", "program", "course", "branch", "stream", "degree"],
    "academic_year": ["academic year", "academic_year", "year", "session", "batch"],
    "admission_date": ["admission date", "admission_date", "date of admission", "date_of_admission", "admission_dt"],
    "admission_category": ["admission category", "admission_category", "category", "quota"]
}


def compute_file_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_columns(columns: List[str]) -> Dict[str, str]:
    """Maps actual input column names to standardized canonical field names."""
    mapping = {}
    cleaned_cols = {col.strip().lower(): col for col in columns}
    
    for canon_field, aliases in COLUMN_MAPPINGS.items():
        found = False
        for alias in aliases:
            if alias in cleaned_cols:
                mapping[canon_field] = cleaned_cols[alias]
                found = True
                break
        if not found and canon_field in ["student_name", "apaar_id", "programme", "academic_year"]:
            # Required field missing
            pass
    return mapping


def parse_and_validate_gate1(
    filename: str,
    file_bytes: bytes,
    max_size_bytes: int = 15 * 1024 * 1024
) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Gate 1: File & Schema validation.
    Checks file extension, size, uncorrupted parsing, and presence of mandatory columns.
    Returns: (is_valid, error_message, dataframe)
    """
    # 1. Size check
    if len(file_bytes) > max_size_bytes:
        return False, f"File exceeds maximum allowed size of {max_size_bytes // (1024 * 1024)} MB.", None

    if len(file_bytes) == 0:
        return False, "Uploaded file is empty (0 bytes).", None

    # 2. Extension check
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        return False, "Unsupported file format. Please upload a standard .xlsx or .csv spreadsheet.", None

    # 3. Read DataFrame
    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
    except Exception as e:
        return False, f"Unable to parse file. Corrupted or malformed spreadsheet content: {str(e)}", None

    if df.empty:
        return False, "Spreadsheet contains no data rows.", None

    # 4. Mandatory columns check
    col_mapping = normalize_columns(list(df.columns))
    required_fields = ["student_name", "apaar_id", "programme", "academic_year"]
    missing = [rf for rf in required_fields if rf not in col_mapping]
    
    if missing:
        readable_missing = [m.replace("_", " ").title() for m in missing]
        return False, f"Missing required column(s): {', '.join(readable_missing)}. Please check the column headers.", None

    return True, None, df


def process_gate2_and_save(
    db: Session,
    college_id: int,
    batch: UploadBatch,
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Gate 2: Student identity & record validation.
    Processes rows, executes validation checks, computes risk scores, records flags, and updates batch.
    """
    col_mapping = normalize_columns(list(df.columns))
    college = db.query(College).filter(College.id == college_id).first()
    intake_status = get_college_intake_status(db, college_id)

    # Standardize DataFrame rows
    standardized_rows = []
    for idx, raw_row in df.iterrows():
        std_row = {
            "row_number": idx + 1,
            "student_name": str(raw_row.get(col_mapping.get("student_name", ""), "")).strip(),
            "apaar_id": str(raw_row.get(col_mapping.get("apaar_id", ""), "")).strip() if pd.notna(raw_row.get(col_mapping.get("apaar_id", ""))) else "",
            "programme": str(raw_row.get(col_mapping.get("programme", ""), "")).strip(),
            "academic_year": str(raw_row.get(col_mapping.get("academic_year", ""), "")).strip(),
            "admission_date": str(raw_row.get(col_mapping.get("admission_date", ""), "2024-08-01")).strip() if col_mapping.get("admission_date") and pd.notna(raw_row.get(col_mapping["admission_date"])) else "2024-08-01",
            "admission_category": str(raw_row.get(col_mapping.get("admission_category", ""), "General")).strip() if col_mapping.get("admission_category") and pd.notna(raw_row.get(col_mapping["admission_category"])) else "General"
        }
        # Clean up 'nan' string artifacts
        for k, v in std_row.items():
            if str(v).lower() in ["nan", "none", "null"]:
                std_row[k] = "" if k != "admission_category" else "General"
        standardized_rows.append(std_row)

    # Precompute in-batch duplicates
    in_batch_duplicates = check_batch_duplicates(standardized_rows)

    accepted_rows = 0
    rejected_rows = 0
    warning_rows = 0

    row_details = []
    new_students = []

    current_college_count = intake_status["current_enrolled"]
    approved_limit = college.approved_intake if college else 120

    for std_row in standardized_rows:
        row_num = std_row["row_number"]
        apaar = std_row["apaar_id"]
        name = std_row["student_name"]
        prog = std_row["programme"]
        acad_year = std_row["academic_year"]
        adm_date = std_row["admission_date"]
        category = std_row["admission_category"]

        triggered_rules = []
        flags_data = []

        # 1. Missing APAAR Check
        if not apaar:
            triggered_rules.append("APAAR_MISSING")
            flags_data.append({
                "rule_code": "APAAR_MISSING",
                "severity": "critical",
                "explanation": "Missing APAAR identifier. Indian academic compliance mandates a 12-digit APAAR ID.",
                "suggested_action": "Verify enrollment documents and retrieve student's registered APAAR ID from the institution portal."
            })
        elif not is_valid_apaar_format(apaar):
            # 2. Invalid format check
            triggered_rules.append("APAAR_FORMAT_INVALID")
            flags_data.append({
                "rule_code": "APAAR_FORMAT_INVALID",
                "severity": "high",
                "explanation": f"Invalid format '{apaar}'. APAAR ID must be exactly 12 numeric digits without letters or punctuation.",
                "suggested_action": "Correct student APAAR ID to a standard 12-digit numeric sequence."
            })

        # 3. In-batch duplicate check
        if apaar and apaar in in_batch_duplicates:
            conflict_rows = in_batch_duplicates[apaar]
            triggered_rules.append("DUPLICATE_IN_BATCH")
            flags_data.append({
                "rule_code": "DUPLICATE_IN_BATCH",
                "severity": "critical",
                "explanation": f"Identifier duplicated across rows {conflict_rows} in the current upload batch.",
                "suggested_action": "Remove duplicate entries from the admission file before final submission."
            })

        # 4. Intra-college duplicate check
        if apaar:
            existing_local = check_intra_college_duplicate(db, college_id, apaar)
            if existing_local:
                triggered_rules.append("DUPLICATE_INTRA_COLLEGE")
                flags_data.append({
                    "rule_code": "DUPLICATE_INTRA_COLLEGE",
                    "severity": "critical",
                    "explanation": f"Student '{existing_local.student_name}' with APAAR ID {mask_apaar_id(apaar)} is already enrolled in this college.",
                    "suggested_action": "Verify if this is a repeat submission or readmission."
                })

        # 5. Cross-college duplicate check
        if apaar:
            cross_conflicts = check_cross_college_duplicate(db, college_id, apaar)
            if cross_conflicts:
                conflict_colleges = ", ".join([c["college_name"] for c in cross_conflicts])
                triggered_rules.append("DUPLICATE_CROSS_COLLEGE")
                flags_data.append({
                    "rule_code": "DUPLICATE_CROSS_COLLEGE",
                    "severity": "high",
                    "explanation": f"Potential dual enrolment detected: identifier also registered at {conflict_colleges}.",
                    "suggested_action": "Initiate inter-institutional verification and request transfer/migration certificate."
                })

        # 6. Mock Registry check
        has_registry = False
        if apaar and is_valid_apaar_format(apaar):
            reg_record = registry_service.lookup_apaar_registry(apaar)
            if reg_record:
                has_registry = True
                # Check name similarity or mismatch
                reg_name = reg_record.get("full_name", "")
                if reg_name and name.strip().lower() != reg_name.strip().lower():
                    triggered_rules.append("REGISTRY_MISMATCH")
                    flags_data.append({
                        "rule_code": "REGISTRY_MISMATCH",
                        "severity": "moderate",
                        "explanation": f"Name mismatch: Submitted name '{name}' differs from central mock registry name '{reg_name}'.",
                        "suggested_action": "Verify government photo identity card and update institutional records."
                    })

        # 7. Mock Counselling check
        has_counselling = False
        if apaar and is_valid_apaar_format(apaar):
            counselling_record = registry_service.lookup_counselling_record(apaar)
            if counselling_record:
                has_counselling = True
                allotted_prog = counselling_record.get("allotted_programme", "")
                if allotted_prog and allotted_prog.lower() not in prog.lower() and prog.lower() not in allotted_prog.lower():
                    triggered_rules.append("COUNSELLING_MISMATCH")
                    flags_data.append({
                        "rule_code": "COUNSELLING_MISMATCH",
                        "severity": "moderate",
                        "explanation": f"Programme mismatch: Enrolled in '{prog}' but counselling allotment was for '{allotted_prog}'.",
                        "suggested_action": "Review branch change or spot-round allotment authorization letter."
                    })

        # 8. Qualifying Exam record check
        if apaar and is_valid_apaar_format(apaar):
            exam_record = registry_service.lookup_exam_record(apaar)
            if not exam_record:
                triggered_rules.append("EXAM_RECORD_MISSING")
                flags_data.append({
                    "rule_code": "EXAM_RECORD_MISSING",
                    "severity": "low",
                    "explanation": "No qualifying 10+2 / examination board marksheet found in the mock verification dataset.",
                    "suggested_action": "Collect and archive verified secondary/higher-secondary certificates."
                })

        # 9. Fee payment record check
        if apaar and is_valid_apaar_format(apaar):
            fee_record = registry_service.lookup_fee_record(apaar)
            if not fee_record or fee_record.get("payment_status", "").upper() != "SUCCESS":
                triggered_rules.append("FEE_RECORD_MISSING")
                flags_data.append({
                    "rule_code": "FEE_RECORD_MISSING",
                    "severity": "low",
                    "explanation": "Unreconciled fee payment: No confirmed transaction challan found in mock payment repository.",
                    "suggested_action": "Verify physical fee receipt or finance portal payment transaction."
                })

        # 10. Intake Capacity check
        current_college_count += 1
        if current_college_count > approved_limit:
            triggered_rules.append("INTAKE_LIMIT_EXCEEDED")
            flags_data.append({
                "rule_code": "INTAKE_LIMIT_EXCEEDED",
                "severity": "high",
                "explanation": f"Admission pushes college enrollment to {current_college_count}, exceeding sanctioned quota of {approved_limit}.",
                "suggested_action": "Confirm AICTE additional intake approval or supernumerary quota seat sanction."
            })

        # Calculate risk score
        risk_score, risk_level, _ = calculate_risk_score(triggered_rules)
        anomaly_score = calculate_experimental_anomaly_score(
            risk_score=risk_score,
            flag_count=len(flags_data),
            apaar_length=len(apaar) if apaar else 0,
            has_registry_match=has_registry,
            has_counselling_match=has_counselling
        )

        # Determine record status
        has_critical = any(f["severity"] == "critical" for f in flags_data)
        has_high_or_mod = any(f["severity"] in ["high", "moderate"] for f in flags_data)

        if has_critical:
            status = "invalid"
            rejected_rows += 1
        elif has_high_or_mod:
            status = "warning"
            warning_rows += 1
        else:
            status = "valid"
            accepted_rows += 1

        # Create Student record in database
        student = Student(
            college_id=college_id,
            apaar_id=apaar if apaar else None,
            student_name=name,
            programme=prog,
            academic_year=acad_year,
            admission_date=adm_date,
            admission_category=category,
            source_batch_id=batch.id,
            record_status=status,
            risk_score=risk_score,
            anomaly_score=anomaly_score,
            raw_data=pd.Series(std_row).to_json()
        )
        db.add(student)
        db.flush()  # to obtain student.id

        # Create ValidationFlag records
        for f in flags_data:
            flag = ValidationFlag(
                student_id=student.id,
                batch_id=batch.id,
                row_index=row_num,
                rule_code=f["rule_code"],
                severity=f["severity"],
                explanation=f["explanation"],
                suggested_action=f["suggested_action"],
                status="open"
            )
            db.add(flag)

        primary_issue = flags_data[0]["explanation"] if flags_data else "All identity and compliance criteria passed."
        action = flags_data[0]["suggested_action"] if flags_data else "None required."

        row_details.append({
            "row_number": row_num,
            "apaar_id_raw": apaar,
            "masked_apaar_id": mask_apaar_id(apaar),
            "student_name": name,
            "programme": prog,
            "academic_year": acad_year,
            "admission_date": adm_date,
            "admission_category": category,
            "status": status,
            "primary_issue": primary_issue,
            "recommended_action": action,
            "triggered_rules": triggered_rules,
            "flags": flags_data
        })

    # Update batch summary
    batch.total_rows = len(standardized_rows)
    batch.accepted_rows = accepted_rows
    batch.rejected_rows = rejected_rows
    batch.warning_rows = warning_rows
    batch.processing_status = "completed"
    db.commit()

    return {
        "batch_id": batch.id,
        "total_records": len(standardized_rows),
        "valid_count": accepted_rows,
        "warning_count": warning_rows,
        "invalid_count": rejected_rows,
        "rows": row_details
    }
