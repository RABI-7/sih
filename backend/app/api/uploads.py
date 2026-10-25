import io
import csv
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from app.database.session import get_db
from app.models.upload_batch import UploadBatch
from app.models.college import College
from app.models.student import Student
from app.models.validation_flag import ValidationFlag
from app.schemas.upload import UploadBatchResponse, UploadBatchResultResponse, RowValidationDetail
from app.core.permissions import get_current_user, enforce_college_tenant
from app.core.security import mask_apaar_id
from app.services.validation_service import (
    compute_file_sha256,
    parse_and_validate_gate1,
    process_gate2_and_save
)
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/uploads", tags=["Uploads"])


def sanitize_csv_field(val: Any) -> str:
    """Prevents spreadsheet formula injection by prepending single quote if starting with =, +, -, @."""
    s = str(val or "")
    if s.startswith(("=", "+", "-", "@")):
        return f"'{s}"
    return s


@router.post("", response_model=UploadBatchResultResponse)
async def upload_student_batch(
    file: UploadFile = File(...),
    college_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Determine target college
    target_college_id = current_user.college_id
    if current_user.role == "compliance_officer":
        if not college_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="college_id is required for compliance officers")
        target_college_id = college_id
    elif not target_college_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not affiliated with any college")

    # Enforce tenant isolation
    enforce_college_tenant(current_user, target_college_id)

    college = db.query(College).filter(College.id == target_college_id).first()
    if not college:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target college not found")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes).")

    file_sha256 = compute_file_sha256(file_bytes)

    # Gate 1: File and schema validation
    is_valid_g1, g1_error, df = parse_and_validate_gate1(
        filename=file.filename or "upload.xlsx",
        file_bytes=file_bytes
    )

    if not is_valid_g1 or df is None:
        # Create failed batch record for audit trail
        failed_batch = UploadBatch(
            college_id=target_college_id,
            filename=file.filename or "unknown",
            file_sha256=file_sha256,
            uploaded_by=current_user.id,
            processing_status="failed",
            total_rows=0,
            notes=f"Gate 1 Validation Error: {g1_error}"
        )
        db.add(failed_batch)
        db.commit()

        log_audit_event(
            db=db,
            action="BATCH_UPLOAD_FAILED",
            entity_type="UPLOAD_BATCH",
            entity_id=str(failed_batch.id),
            actor_id=current_user.id,
            actor_name=current_user.full_name,
            college_id=target_college_id,
            metadata={"filename": file.filename, "file_sha256": file_sha256, "reason": g1_error}
        )

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=g1_error)

    # Create active batch
    batch = UploadBatch(
        college_id=target_college_id,
        filename=file.filename or "uploaded_data.xlsx",
        file_sha256=file_sha256,
        uploaded_by=current_user.id,
        processing_status="processing",
        total_rows=len(df),
        notes="Gate 1 schema validation passed. Proceeding through Gate 2 identity checks."
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Gate 2: Student identity & record validation
    gate2_results = process_gate2_and_save(
        db=db,
        college_id=target_college_id,
        batch=batch,
        df=df
    )

    log_audit_event(
        db=db,
        action="BATCH_UPLOAD_COMPLETED",
        entity_type="UPLOAD_BATCH",
        entity_id=str(batch.id),
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        college_id=target_college_id,
        metadata={
            "filename": batch.filename,
            "file_sha256": file_sha256,
            "total_records": gate2_results["total_records"],
            "valid_count": gate2_results["valid_count"],
            "warning_count": gate2_results["warning_count"],
            "invalid_count": gate2_results["invalid_count"]
        }
    )

    batch_resp = UploadBatchResponse(
        id=batch.id,
        college_id=batch.college_id,
        college_name=college.name,
        filename=batch.filename,
        file_sha256=batch.file_sha256,
        upload_timestamp=batch.upload_timestamp,
        uploaded_by=batch.uploaded_by,
        uploader_name=current_user.full_name,
        processing_status=batch.processing_status,
        total_rows=batch.total_rows,
        accepted_rows=batch.accepted_rows,
        rejected_rows=batch.rejected_rows,
        warning_rows=batch.warning_rows,
        notes=batch.notes
    )

    row_models = [RowValidationDetail(**r) for r in gate2_results["rows"]]

    return UploadBatchResultResponse(
        batch=batch_resp,
        total_records=gate2_results["total_records"],
        valid_count=gate2_results["valid_count"],
        warning_count=gate2_results["warning_count"],
        invalid_count=gate2_results["invalid_count"],
        rows=row_models
    )


@router.get("", response_model=List[UploadBatchResponse])
def get_upload_batches(
    college_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    target_college_id = college_id
    if current_user.role == "college_admin":
        target_college_id = current_user.college_id

    query = db.query(UploadBatch)
    if target_college_id:
        query = query.filter(UploadBatch.college_id == target_college_id)

    batches = query.order_by(UploadBatch.id.desc()).all()
    results = []
    for b in batches:
        results.append(UploadBatchResponse(
            id=b.id,
            college_id=b.college_id,
            college_name=b.college.name if b.college else "Unknown",
            filename=b.filename,
            file_sha256=b.file_sha256,
            upload_timestamp=b.upload_timestamp,
            uploaded_by=b.uploaded_by,
            uploader_name=current_user.full_name if b.uploaded_by == current_user.id else "Administrator",
            processing_status=b.processing_status,
            total_rows=b.total_rows,
            accepted_rows=b.accepted_rows,
            rejected_rows=b.rejected_rows,
            warning_rows=b.warning_rows,
            notes=b.notes
        ))
    return results


@router.get("/{batch_id}", response_model=UploadBatchResponse)
def get_upload_batch(batch_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    enforce_college_tenant(current_user, batch.college_id)

    return UploadBatchResponse(
        id=batch.id,
        college_id=batch.college_id,
        college_name=batch.college.name if batch.college else "Unknown",
        filename=batch.filename,
        file_sha256=batch.file_sha256,
        upload_timestamp=batch.upload_timestamp,
        uploaded_by=batch.uploaded_by,
        uploader_name="Administrator",
        processing_status=batch.processing_status,
        total_rows=batch.total_rows,
        accepted_rows=batch.accepted_rows,
        rejected_rows=batch.rejected_rows,
        warning_rows=batch.warning_rows,
        notes=batch.notes
    )


@router.get("/{batch_id}/results", response_model=UploadBatchResultResponse)
def get_batch_results(batch_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    enforce_college_tenant(current_user, batch.college_id)

    students = db.query(Student).filter(Student.source_batch_id == batch.id).all()
    flags = db.query(ValidationFlag).filter(ValidationFlag.batch_id == batch.id).all()

    # Map flags to student_id
    flags_by_student = {}
    for f in flags:
        flags_by_student.setdefault(f.student_id, []).append(f)

    row_models = []
    for idx, s in enumerate(students, start=1):
        s_flags = flags_by_student.get(s.id, [])
        primary_issue = s_flags[0].explanation if s_flags else "All criteria passed."
        action = s_flags[0].suggested_action if s_flags else "None required."

        flag_dicts = [
            {
                "rule_code": f.rule_code,
                "severity": f.severity,
                "explanation": f.explanation,
                "suggested_action": f.suggested_action
            }
            for f in s_flags
        ]

        row_models.append(RowValidationDetail(
            row_number=idx,
            apaar_id_raw=s.apaar_id,
            masked_apaar_id=mask_apaar_id(s.apaar_id),
            student_name=s.student_name,
            programme=s.programme,
            academic_year=s.academic_year,
            admission_date=s.admission_date,
            admission_category=s.admission_category,
            status=s.record_status,
            primary_issue=primary_issue,
            recommended_action=action,
            triggered_rules=[f.rule_code for f in s_flags],
            flags=flag_dicts
        ))

    batch_resp = UploadBatchResponse(
        id=batch.id,
        college_id=batch.college_id,
        college_name=batch.college.name if batch.college else "Unknown",
        filename=batch.filename,
        file_sha256=batch.file_sha256,
        upload_timestamp=batch.upload_timestamp,
        uploaded_by=batch.uploaded_by,
        uploader_name="Administrator",
        processing_status=batch.processing_status,
        total_rows=batch.total_rows,
        accepted_rows=batch.accepted_rows,
        rejected_rows=batch.rejected_rows,
        warning_rows=batch.warning_rows,
        notes=batch.notes
    )

    return UploadBatchResultResponse(
        batch=batch_resp,
        total_records=len(students),
        valid_count=batch.accepted_rows,
        warning_count=batch.warning_rows,
        invalid_count=batch.rejected_rows,
        rows=row_models
    )


@router.get("/{batch_id}/errors.csv")
def download_batch_errors_csv(batch_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Downloads an error report CSV with spreadsheet formula injection sanitization."""
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    enforce_college_tenant(current_user, batch.college_id)

    students = db.query(Student).filter(
        Student.source_batch_id == batch.id,
        Student.record_status.in_(["invalid", "warning"])
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID",
        "Student Name",
        "Masked APAAR ID",
        "Programme",
        "Academic Year",
        "Status",
        "Risk Score",
        "Error / Warning Codes",
        "Explanations",
        "Recommended Corrections"
    ])

    for s in students:
        flags = db.query(ValidationFlag).filter(ValidationFlag.student_id == s.id).all()
        codes = "; ".join([f.rule_code for f in flags])
        explanations = " | ".join([f.explanation for f in flags])
        actions = " | ".join([f.suggested_action or "" for f in flags if f.suggested_action])

        writer.writerow([
            sanitize_csv_field(s.id),
            sanitize_csv_field(s.student_name),
            sanitize_csv_field(mask_apaar_id(s.apaar_id)),
            sanitize_csv_field(s.programme),
            sanitize_csv_field(s.academic_year),
            sanitize_csv_field(s.record_status),
            sanitize_csv_field(s.risk_score),
            sanitize_csv_field(codes),
            sanitize_csv_field(explanations),
            sanitize_csv_field(actions)
        ])

    output.seek(0)
    filename = f"upload_errors_batch_{batch.id}_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/template/sample-csv")
def download_sample_template_csv():
    """Generates standard CSV upload template with guidance headers."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "APAAR ID", "Programme", "Academic Year", "Admission Date", "Admission Category"])
    writer.writerow(["Aarav Sharma", "901234567890", "B.Tech Computer Science & Engineering", "2024-2025", "2024-08-01", "General"])
    writer.writerow(["Pooja Nair", "901234567891", "B.Tech Electronics & Communication", "2024-2025", "2024-08-01", "OBC"])
    writer.writerow(["Rohan Gupta", "901234567892", "B.Tech Mechanical Engineering", "2024-2025", "2024-08-02", "General"])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=apaar_guardian_student_template.csv"}
    )
