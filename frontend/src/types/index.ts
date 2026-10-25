export type UserRole = 'college_admin' | 'compliance_officer' | 'verifier';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  college_id?: number | null;
  college_name?: string | null;
}

export interface College {
  id: number;
  name: string;
  institution_code: string;
  approved_intake: number;
  category: string;
  state: string;
  is_active: boolean;
  enrolled_count: number;
  utilization_rate: number;
  status: 'Normal' | 'Near Capacity' | 'Over-Intake';
}

export interface ValidationFlag {
  id: number;
  student_id?: number | null;
  batch_id: number;
  row_index?: number | null;
  rule_code: string;
  severity: 'critical' | 'high' | 'moderate' | 'low';
  explanation: string;
  suggested_action?: string | null;
  status: 'open' | 'under_review' | 'resolved' | 'false_positive';
  review_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RiskScoreBreakdownItem {
  rule_code: string;
  rule_name: string;
  points: number;
  severity: string;
  description: string;
}

export interface Student {
  id: number;
  college_id: number;
  college_name?: string | null;
  apaar_id?: string | null;
  masked_apaar_id: string;
  student_name: string;
  programme: string;
  academic_year: string;
  admission_date?: string | null;
  admission_category?: string;
  source_batch_id?: number | null;
  record_status: 'valid' | 'warning' | 'invalid';
  risk_score: number;
  risk_level: 'Low' | 'Moderate' | 'High' | 'Critical';
  anomaly_score?: number | null;
  flags_count: number;
  created_at: string;
}

export interface StudentDetail extends Student {
  flags: ValidationFlag[];
  risk_breakdown: RiskScoreBreakdownItem[];
  has_registry_match: boolean;
  has_counselling_match: boolean;
  has_exam_record: boolean;
  has_fees_record: boolean;
}

export interface UploadBatch {
  id: number;
  college_id: number;
  college_name?: string | null;
  filename: string;
  file_sha256: string;
  upload_timestamp: string;
  uploaded_by?: number | null;
  uploader_name?: string | null;
  processing_status: string;
  total_rows: number;
  accepted_rows: number;
  rejected_rows: number;
  warning_rows: number;
  notes?: string | null;
}

export interface RowValidationDetail {
  row_number: number;
  apaar_id_raw?: string | null;
  masked_apaar_id: string;
  student_name: string;
  programme: string;
  academic_year: string;
  admission_date?: string | null;
  admission_category?: string | null;
  status: 'valid' | 'warning' | 'invalid';
  primary_issue?: string | null;
  recommended_action?: string | null;
  triggered_rules: string[];
  flags: Array<{
    rule_code: string;
    severity: string;
    explanation: string;
    suggested_action?: string;
  }>;
}

export interface UploadBatchResult {
  batch: UploadBatch;
  total_records: number;
  valid_count: number;
  warning_count: number;
  invalid_count: number;
  rows: RowValidationDetail[];
}

export interface RiskDistributionItem {
  category: string;
  count: number;
  percentage: number;
  color: string;
}

export interface OverIntakeInstitution {
  college_id: number;
  college_name: string;
  institution_code: string;
  approved_intake: number;
  admitted_count: number;
  over_intake_count: number;
  utilization_rate: number;
}

export interface CrossCollegeDuplicateGroup {
  apaar_id: string;
  masked_apaar_id: string;
  student_name: string;
  colleges: Array<{
    college_id: number;
    college_name: string;
    programme: string;
    admission_date?: string;
  }>;
}

export interface ComplianceSummary {
  total_institutions: number;
  total_students: number;
  valid_records: number;
  warning_records: number;
  invalid_records: number;
  potential_cross_college_duplicates: number;
  institutions_exceeding_intake: number;
  average_utilization_rate: number;
  total_flags: number;
  open_flags: number;
  resolved_flags: number;
  risk_distribution: RiskDistributionItem[];
  over_intake_institutions: OverIntakeInstitution[];
  cross_college_duplicates: CrossCollegeDuplicateGroup[];
}

export interface VerificationRequest {
  id: number;
  request_reference: string;
  student_id: number;
  student_name: string;
  masked_apaar_id: string;
  purpose: string;
  verifier_name: string;
  status: 'pending_consent' | 'consent_granted' | 'consent_denied' | 'expired' | 'revoked';
  created_at: string;
  expires_at: string;
}

export interface VerificationResult {
  request_reference: string;
  status: string;
  purpose: string;
  verifier_name: string;
  is_valid_access: boolean;
  granted_at?: string | null;
  expires_at?: string | null;
  permitted_fields: string[];
  student_data: Record<string, any>;
  message?: string | null;
}

export interface Certificate {
  id: number;
  certificate_reference: string;
  student_id: number;
  student_name: string;
  college_name: string;
  programme: string;
  academic_year: string;
  canonical_payload: string;
  digital_signature: string;
  signature_algorithm: string;
  qr_code_data_uri: string;
  verification_url: string;
  issued_at: string;
  expires_at: string;
  is_revoked: boolean;
  revocation_reason?: string | null;
}

export interface CertificateVerifyResult {
  is_valid: boolean;
  status: 'VALID' | 'EXPIRED' | 'REVOKED' | 'INVALID_SIGNATURE' | 'NOT_FOUND';
  message: string;
  certificate_reference?: string;
  institution?: string;
  programme?: string;
  student_reference?: string;
  issued_at?: string;
  expires_at?: string;
  digital_signature_verified: boolean;
}

export interface AuditLog {
  id: number;
  actor_id?: number | null;
  actor_name: string;
  college_id?: number | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  timestamp: string;
  previous_hash: string;
  entry_hash: string;
  metadata?: Record<string, any> | null;
}

export interface AuditIntegrity {
  is_valid: boolean;
  total_entries_verified: number;
  genesis_hash_valid: boolean;
  tampered_entry_id?: number | null;
  verification_message: string;
  verified_at: string;
}
