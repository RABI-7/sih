import os
import random
import csv
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.college import College
from app.models.user import User
from app.models.student import Student
from app.models.upload_batch import UploadBatch
from app.models.validation_flag import ValidationFlag
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash, mask_apaar_id
from app.services.audit_service import log_audit_event, compute_audit_hash
from app.services.risk_service import calculate_risk_score, calculate_experimental_anomaly_score

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
os.makedirs(DATA_DIR, exist_ok=True)

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Atharv", "Dhruv", "Kabir", "Rohan", "Ananya", "Diya", "Saanvi", "Aadhya", "Pari",
    "Anushka", "Navya", "Angel", "Myra", "Sara", "Ira", "Riya", "Avni", "Sneha", "Kavya",
    "Tanvi", "Prisha", "Isha", "Meera", "Aanya", "Pooja", "Simran", "Rahul", "Nikhil", "Manish"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Malhotra", "Bhatia", "Saxena", "Mehta", "Chopra", "Joshi", "Kapoor",
    "Nair", "Pillai", "Menon", "Reddy", "Rao", "Patel", "Shah", "Deshmukh", "Kulkarni", "Patil",
    "Singh", "Kaur", "Mukherjee", "Banerjee", "Chatterjee", "Bose", "Ghosh", "Das", "Dutta", "Sen"
]

PROGRAMMES = [
    "B.Tech Computer Science & Engineering",
    "B.Tech Electronics & Communication Engineering",
    "B.Tech Mechanical Engineering",
    "B.Tech Information Technology",
    "B.Tech Civil Engineering",
    "B.Tech Electrical & Electronics Engineering"
]

CATEGORIES = ["General", "OBC", "SC", "ST", "EWS"]


def generate_synthetic_apaar_id(seed_idx: int) -> str:
    """Generates a realistic 12-digit numeric APAAR ID."""
    prefix = 900000000000
    return str(prefix + seed_idx)


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    print("[1/5] Checking existing database records...")
    # Clear existing tables for deterministic idempotent seeding
    db.query(ValidationFlag).delete()
    db.query(Student).delete()
    db.query(UploadBatch).delete()
    db.query(User).delete()
    db.query(College).delete()
    db.query(AuditLog).delete()
    db.commit()

    print("[2/5] Creating 3 Fictional Institutional Colleges...")
    colleges_data = [
        {
            "name": "Delhi Institute of Technology & Applied Sciences",
            "institution_code": "INST-001",
            "approved_intake": 120,
            "category": "Engineering & Technology",
            "state": "Delhi NCT"
        },
        {
            "name": "National College of Engineering & Research",
            "institution_code": "INST-002",
            "approved_intake": 150,
            "category": "Engineering & Technology",
            "state": "Maharashtra"
        },
        {
            "name": "Apex Academy of Technical Education",
            "institution_code": "INST-003",
            "approved_intake": 80,
            "category": "Engineering & Technology",
            "state": "Karnataka"
        }
    ]

    colleges = []
    for c_info in colleges_data:
        c = College(**c_info)
        db.add(c)
        db.flush()
        colleges.append(c)

    print("[3/5] Provisioning Predefined Demo User Accounts...")
    demo_users_data = [
        {
            "email": "admin@delhi-tech.edu.in",
            "full_name": "Prof. R. Sharma (College Admin)",
            "role": "college_admin",
            "college_id": colleges[0].id,
            "hashed_password": get_password_hash("demo123")
        },
        {
            "email": "admin@national-engg.edu.in",
            "full_name": "Dr. Sunita Verma (College Admin)",
            "role": "college_admin",
            "college_id": colleges[1].id,
            "hashed_password": get_password_hash("demo123")
        },
        {
            "email": "compliance@aicte-council.gov.in",
            "full_name": "Vikram Malhotra (AICTE Compliance Officer)",
            "role": "compliance_officer",
            "college_id": None,
            "hashed_password": get_password_hash("demo123")
        },
        {
            "email": "verifier@credential-check.org",
            "full_name": "Ananya Sen (Academic Credential Verifier)",
            "role": "verifier",
            "college_id": None,
            "hashed_password": get_password_hash("demo123")
        }
    ]

    users = []
    for u_info in demo_users_data:
        u = User(**u_info)
        db.add(u)
        db.flush()
        users.append(u)

    print("[4/5] Generating Mock External Registry Datasets (registry.csv, counselling.csv, exams.csv, fees.csv)...")
    random.seed(42)

    # We will generate 600 synthetic identity profiles for external mock datasets
    registry_rows = []
    counselling_rows = []
    exams_rows = []
    fees_rows = []

    for i in range(1, 601):
        apaar = generate_synthetic_apaar_id(i)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        dob = f"{random.randint(2003, 2006)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        gender = random.choice(["Male", "Female"])
        state = random.choice(["Delhi", "Maharashtra", "Karnataka", "Uttar Pradesh", "Tamil Nadu", "Rajasthan"])
        prog = random.choice(PROGRAMMES)

        registry_rows.append({
            "apaar_id": apaar,
            "full_name": full_name,
            "dob": dob,
            "gender": gender,
            "state": state
        })

        allotted_inst = random.choice(["INST-001", "INST-002", "INST-003"])
        counselling_rows.append({
            "apaar_id": apaar,
            "student_name": full_name,
            "allotted_college_code": allotted_inst,
            "allotted_programme": prog,
            "counselling_round": f"Round {random.randint(1, 3)}",
            "quota": random.choice(CATEGORIES),
            "state_rank": random.randint(120, 45000)
        })

        exams_rows.append({
            "apaar_id": apaar,
            "tenth_board": "CBSE",
            "twelfth_board": "CBSE",
            "roll_number": f"ROLL{random.randint(1000000, 9999999)}",
            "qualifying_percent": round(random.uniform(70.0, 98.5), 2),
            "verification_status": "VERIFIED"
        })

        fees_rows.append({
            "apaar_id": apaar,
            "txn_id": f"TXN-{apaar[-6:]}-{random.randint(1000, 9999)}",
            "amount": 85000,
            "payment_status": "SUCCESS",
            "payment_mode": "NET_BANKING",
            "timestamp": "2024-07-28T10:30:00Z"
        })

    # Save CSVs
    pd.DataFrame(registry_rows).to_csv(os.path.join(DATA_DIR, "registry.csv"), index=False)
    pd.DataFrame(counselling_rows).to_csv(os.path.join(DATA_DIR, "counselling.csv"), index=False)
    pd.DataFrame(exams_rows).to_csv(os.path.join(DATA_DIR, "exams.csv"), index=False)
    pd.DataFrame(fees_rows).to_csv(os.path.join(DATA_DIR, "fees.csv"), index=False)

    print("[5/5] Populating 320 Baseline Student Records & Test Cases across Colleges...")
    
    # College 1: 105 students (Approved: 120, Normal utilisation ~87.5%)
    # College 2: 135 students (Approved: 150, Normal utilisation ~90.0%)
    # College 3: 88 students (Approved: 80, Over-intake ~110.0%!)

    college_targets = [
        (colleges[0], 105, 1),
        (colleges[1], 135, 106),
        (colleges[2], 88, 241)
    ]

    total_created_students = 0

    for college, count, start_apaar_idx in college_targets:
        # Create baseline upload batch for historical audit
        batch = UploadBatch(
            college_id=college.id,
            filename=f"initial_admissions_batch_{college.institution_code.lower()}.xlsx",
            file_sha256=f"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85{college.id}",
            uploaded_by=users[0].id if college.id == 1 else users[1].id,
            processing_status="completed",
            total_rows=count,
            accepted_rows=count,
            rejected_rows=0,
            warning_rows=0,
            notes=f"Seeded baseline verified admission submission for {college.name}"
        )
        db.add(batch)
        db.flush()

        for idx in range(count):
            apaar_num = start_apaar_idx + idx
            apaar = generate_synthetic_apaar_id(apaar_num)
            reg_entry = registry_rows[apaar_num - 1]
            couns_entry = counselling_rows[apaar_num - 1]

            student = Student(
                college_id=college.id,
                apaar_id=apaar,
                student_name=reg_entry["full_name"],
                programme=couns_entry["allotted_programme"],
                academic_year="2024-2025",
                admission_date="2024-08-01",
                admission_category=couns_entry["quota"],
                source_batch_id=batch.id,
                record_status="valid",
                risk_score=0.0,
                anomaly_score=0.05
            )
            db.add(student)
            total_created_students += 1

    db.commit()

    # Now Plant the 12 Deterministic Test Cases & Demo Upload File!
    print("Planting 12 Specific Test Cases for Demonstration...")
    # Plant a cross-college duplicate in the database:
    # Student in College 2 with apaar_id 900000000999
    cross_dup_apaar = "900000000999"
    planted_cross = Student(
        college_id=colleges[1].id,
        apaar_id=cross_dup_apaar,
        student_name="Devendra Singhania",
        programme="B.Tech Computer Science & Engineering",
        academic_year="2024-2025",
        admission_date="2024-07-25",
        admission_category="General",
        record_status="valid",
        risk_score=0.0
    )
    db.add(planted_cross)

    # Flag College 3 intake excess flag
    college3_students = db.query(Student).filter(Student.college_id == colleges[2].id).all()
    for s in college3_students[80:]:  # over intake
        s.record_status = "warning"
        s.risk_score = 20.0
        flag = ValidationFlag(
            student_id=s.id,
            batch_id=s.source_batch_id,
            rule_code="INTAKE_LIMIT_EXCEEDED",
            severity="high",
            explanation=f"Admission exceeds approved quota of 80 for {colleges[2].name}.",
            suggested_action="Verify supernumerary quota seat sanction.",
            status="open"
        )
        db.add(flag)

    db.commit()

    # Generate `demo_upload.xlsx` and `demo_upload.csv` with the 12 Planted Test Cases
    demo_upload_rows = [
        # 1. Valid 12-digit APAAR ID passing all checks
        {
            "Student Name": "Aarav Sharma",
            "APAAR ID": "900000000501",
            "Programme": "B.Tech Computer Science & Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-01",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 1: Valid 12-digit APAAR ID passing all checks"
        },
        # 2. Missing APAAR ID
        {
            "Student Name": "Pooja Verma",
            "APAAR ID": "",
            "Programme": "B.Tech Electronics & Communication Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-01",
            "Admission Category": "OBC",
            "Test_Case_Description": "TEST 2: Deliberately missing APAAR ID"
        },
        # 3. 11-digit APAAR ID
        {
            "Student Name": "Kunal Deshmukh",
            "APAAR ID": "90123456789",  # 11 digits
            "Programme": "B.Tech Mechanical Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-02",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 3: 11-digit APAAR ID (format violation)"
        },
        # 4. Invalid-format ID containing non-numeric characters
        {
            "Student Name": "Priyanka Saxena",
            "APAAR ID": "9012-ABCD-7890",
            "Programme": "B.Tech Computer Science & Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-02",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 4: Non-numeric invalid APAAR format"
        },
        # 5. Duplicate APAAR ID within this batch (Entry 1)
        {
            "Student Name": "Sameer Joshi",
            "APAAR ID": "900000000505",
            "Programme": "B.Tech Information Technology",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-03",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 5A: First entry of in-batch duplicate"
        },
        # 5. Duplicate APAAR ID within this batch (Entry 2)
        {
            "Student Name": "Sameer Joshi (Duplicate)",
            "APAAR ID": "900000000505",
            "Programme": "B.Tech Information Technology",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-03",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 5B: Duplicate APAAR repeated in batch"
        },
        # 6. Student record already present in mock registry (Exact match)
        {
            "Student Name": registry_rows[509]["full_name"],
            "APAAR ID": registry_rows[509]["apaar_id"],
            "Programme": counselling_rows[509]["allotted_programme"],
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-03",
            "Admission Category": counselling_rows[509]["quota"],
            "Test_Case_Description": "TEST 6: Authoritative mock registry matched record"
        },
        # 7. Student appearing in two colleges (Cross-college duplicate)
        {
            "Student Name": "Devendra Singhania",
            "APAAR ID": cross_dup_apaar,
            "Programme": "B.Tech Computer Science & Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-04",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 7: Cross-college dual enrollment with INST-002"
        },
        # 8. Admission pushing college over approved intake (Simulated by batch volume)
        {
            "Student Name": "Vikram Rathore",
            "APAAR ID": "900000000512",
            "Programme": "B.Tech Electrical & Electronics Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-04",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 8: Capacity utilization and intake tracking"
        },
        # 9. Mismatch between enrolled programme and counselling allotment
        {
            "Student Name": registry_rows[514]["full_name"],
            "APAAR ID": registry_rows[514]["apaar_id"],
            "Programme": "B.Tech Civil Engineering",  # Counselling says something else
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-04",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 9: Academic programme / counselling discrepancy"
        },
        # 10. Missing examination or fee record
        {
            "Student Name": "Neha Bhatnagar",
            "APAAR ID": "900000000599",  # Not in mock exams or fees
            "Programme": "B.Tech Computer Science & Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-05",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 10: Missing examination / fee payment reconciliation"
        },
        # 11. Suspicious cluster of inconsistent records (multiple flags)
        {
            "Student Name": "Amitabh Roy",
            "APAAR ID": "900000000598",  # multiple discrepancies
            "Programme": "B.Tech Aeronautical Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-05",
            "Admission Category": "Management",
            "Test_Case_Description": "TEST 11: High-risk multi-flag cluster"
        },
        # 12. Completely valid record 2
        {
            "Student Name": "Tanvi Pillai",
            "APAAR ID": "900000000520",
            "Programme": "B.Tech Computer Science & Engineering",
            "Academic Year": "2024-2025",
            "Admission Date": "2024-08-05",
            "Admission Category": "General",
            "Test_Case_Description": "TEST 12: Completely valid clean record"
        }
    ]

    demo_df = pd.DataFrame(demo_upload_rows)
    demo_df.to_excel(os.path.join(DATA_DIR, "demo_upload.xlsx"), index=False)
    demo_df.to_csv(os.path.join(DATA_DIR, "demo_upload.csv"), index=False)

    # Initialize Audit Log Chain with Genesis and Baseline Events
    print("Initializing Hash-Chained Tamper-Evident Audit Trail...")
    log_audit_event(
        db=db,
        action="PLATFORM_INITIALIZED",
        entity_type="SYSTEM",
        entity_id="APAAR_GUARDIAN_CORE",
        actor_name="AICTE Root Authority",
        metadata={"version": "1.0.0", "mode": "DEMO MODE", "institutions_count": 3}
    )

    log_audit_event(
        db=db,
        action="BASELINE_DATA_SEEDED",
        entity_type="DATABASE",
        entity_id="STUDENT_REPOSITORY",
        actor_name="Database Migration Script",
        metadata={"total_students": total_created_students, "test_cases": 12}
    )

    db.close()
    print(f"Successfully seeded database! Total students: {total_created_students + 1}. Demo upload files created in 'data/'.")


if __name__ == "__main__":
    seed_database()
