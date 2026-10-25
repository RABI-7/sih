import axios from 'axios';
import {
  User,
  College,
  Student,
  StudentDetail,
  ValidationFlag,
  UploadBatch,
  UploadBatchResult,
  ComplianceSummary,
  RiskDistributionItem,
  OverIntakeInstitution,
  VerificationRequest,
  VerificationResult,
  Certificate,
  CertificateVerifyResult,
  AuditLog,
  AuditIntegrity
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for JWT Bearer token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('apaar_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Authentication Service
export const authService = {
  demoLogin: async (accountKey: string) => {
    const res = await apiClient.post('/auth/demo-login', { account_key: accountKey });
    return res.data;
  },
  verifyOtp: async (accountKey: string, otp: string) => {
    const res = await apiClient.post<{ access_token: string; token_type: string; user: User }>('/auth/verify-otp', {
      account_key: accountKey,
      otp,
    });
    if (res.data.access_token) {
      localStorage.setItem('apaar_token', res.data.access_token);
      localStorage.setItem('apaar_user', JSON.stringify(res.data.user));
    }
    return res.data;
  },
  getMe: async () => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('apaar_token');
    localStorage.removeItem('apaar_user');
  },
  getCurrentUser: (): User | null => {
    const data = localStorage.getItem('apaar_user');
    return data ? JSON.parse(data) : null;
  }
};

// Colleges Service
export const collegeService = {
  getColleges: async () => {
    const res = await apiClient.get<College[]>('/colleges');
    return res.data;
  },
  getCollegeCompliance: async (collegeId: number) => {
    const res = await apiClient.get(`/colleges/${collegeId}/compliance`);
    return res.data;
  }
};

// Students Service
export const studentService = {
  getStudents: async (params?: { college_id?: number; status?: string; search?: string; programme?: string; limit?: number; offset?: number }) => {
    const res = await apiClient.get<Student[]>('/students', { params });
    return res.data;
  },
  getStudentDetail: async (studentId: number) => {
    const res = await apiClient.get<StudentDetail>(`/students/${studentId}`);
    return res.data;
  },
  getStudentFlags: async (studentId: number) => {
    const res = await apiClient.get<ValidationFlag[]>(`/students/${studentId}/flags`);
    return res.data;
  }
};

// Uploads Service
export const uploadService = {
  uploadFile: async (file: File, collegeId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (collegeId) {
      formData.append('college_id', collegeId.toString());
    }
    const res = await apiClient.post<UploadBatchResult>('/uploads', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  getBatches: async (collegeId?: number) => {
    const res = await apiClient.get<UploadBatch[]>('/uploads', { params: { college_id: collegeId } });
    return res.data;
  },
  getBatch: async (batchId: number) => {
    const res = await apiClient.get<UploadBatch>(`/uploads/${batchId}`);
    return res.data;
  },
  getBatchResults: async (batchId: number) => {
    const res = await apiClient.get<UploadBatchResult>(`/uploads/${batchId}/results`);
    return res.data;
  },
  getErrorsCsvUrl: (batchId: number) => {
    return `${API_BASE_URL}/uploads/${batchId}/errors.csv`;
  },
  getSampleTemplateCsvUrl: () => {
    return `${API_BASE_URL}/uploads/template/sample-csv`;
  }
};

// Compliance Service
export const complianceService = {
  getSummary: async () => {
    const res = await apiClient.get<ComplianceSummary>('/compliance/summary');
    return res.data;
  },
  getRiskDistribution: async () => {
    const res = await apiClient.get<RiskDistributionItem[]>('/compliance/risk-distribution');
    return res.data;
  },
  getOverIntake: async () => {
    const res = await apiClient.get<OverIntakeInstitution[]>('/compliance/over-intake');
    return res.data;
  },
  updateFlagStatus: async (flagId: number, status: string, reviewNotes?: string) => {
    const res = await apiClient.patch<ValidationFlag>(`/flags/${flagId}`, {
      status,
      review_notes: reviewNotes,
    });
    return res.data;
  }
};

// Verification Service
export const verificationService = {
  createRequest: async (studentIdentifier: string, purpose: string, verifierName?: string) => {
    const res = await apiClient.post<VerificationRequest>('/verification-requests', {
      student_identifier: studentIdentifier,
      purpose,
      verifier_name: verifierName,
    });
    return res.data;
  },
  grantDemoConsent: async (requestRef: string, permittedFields: string[], durationDays: number = 7) => {
    const res = await apiClient.post(`/verification-requests/${requestRef}/demo-consent`, {
      permitted_fields: permittedFields,
      duration_days: durationDays,
    });
    return res.data;
  },
  getResult: async (requestRef: string) => {
    const res = await apiClient.get<VerificationResult>(`/verification-requests/${requestRef}/result`);
    return res.data;
  },
  revokeConsent: async (requestRef: string) => {
    const res = await apiClient.post(`/verification-requests/${requestRef}/revoke`);
    return res.data;
  }
};

// Certificates Service
export const certificateService = {
  issueCertificate: async (studentId: number, expiryMonths: number = 12) => {
    const res = await apiClient.post<Certificate>('/certificates', {
      student_id: studentId,
      expiry_months: expiryMonths,
    });
    return res.data;
  },
  getCertificate: async (certId: number) => {
    const res = await apiClient.get<Certificate>(`/certificates/${certId}`);
    return res.data;
  },
  verifyCertificate: async (certRef: string) => {
    const res = await apiClient.get<CertificateVerifyResult>(`/certificates/verify/${certRef}`);
    return res.data;
  }
};

// Audit Service
export const auditService = {
  getLogs: async (params?: { action?: string; college_id?: number; limit?: number; offset?: number }) => {
    const res = await apiClient.get<AuditLog[]>('/audit-logs', { params });
    return res.data;
  },
  verifyIntegrity: async () => {
    const res = await apiClient.post<AuditIntegrity>('/audit-logs/verify-integrity');
    return res.data;
  }
};
