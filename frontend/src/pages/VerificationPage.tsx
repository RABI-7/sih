import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  QrCode,
  ShieldCheck,
  ShieldAlert,
  KeyRound,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Building,
  GraduationCap,
  Calendar,
  Lock,
  Unlock,
  RefreshCw,
  Search
} from 'lucide-react';
import { verificationService, certificateService } from '../services/api';
import { VerificationRequest, VerificationResult, CertificateVerifyResult } from '../types';

export const VerificationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const certRefParam = searchParams.get('cert_ref');

  const [activeTab, setActiveTab] = useState<'qr_verify' | 'consent_flow'>(
    certRefParam ? 'qr_verify' : 'consent_flow'
  );

  // Tab 1: Direct QR Certificate Authenticator
  const [certRefInput, setCertRefInput] = useState(certRefParam || '');
  const [certVerifyResult, setCertVerifyResult] = useState<CertificateVerifyResult | null>(null);
  const [certLoading, setCertLoading] = useState(false);

  // Tab 2: Consent-Based Verification Flow
  const [studentInput, setStudentInput] = useState('1'); // default to student #1
  const [purpose, setPurpose] = useState('Academic Credential Background Verification for Employment');
  const [verifierOrg, setVerifierOrg] = useState('Tata Consultancy Services Ltd.');
  const [reqLoading, setReqLoading] = useState(false);
  const [activeReq, setActiveReq] = useState<VerificationRequest | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);

  // Permitted Fields Selection for Simulated Consent
  const [permittedFields, setPermittedFields] = useState<string[]>([
    'student_name',
    'programme',
    'college_name',
    'academic_year',
  ]);
  const [durationDays, setDurationDays] = useState(7);
  const [consentActionLoading, setConsentActionLoading] = useState(false);

  useEffect(() => {
    if (certRefParam) {
      handleVerifyCertificate(certRefParam);
    }
  }, [certRefParam]);

  const handleVerifyCertificate = async (refToVerify?: string) => {
    const ref = refToVerify || certRefInput;
    if (!ref.trim()) return;

    try {
      setCertLoading(true);
      const res = await certificateService.verifyCertificate(ref.trim());
      setCertVerifyResult(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to verify certificate');
    } finally {
      setCertLoading(false);
    }
  };

  const handleCreateVerificationRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setReqLoading(true);
      const res = await verificationService.createRequest(studentInput, purpose, verifierOrg);
      setActiveReq(res);
      // Fetch initial status
      const resultData = await verificationService.getResult(res.request_reference);
      setVerificationResult(resultData);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create verification request');
    } finally {
      setReqLoading(false);
    }
  };

  const handleGrantConsent = async () => {
    if (!activeReq) return;
    try {
      setConsentActionLoading(true);
      await verificationService.grantDemoConsent(activeReq.request_reference, permittedFields, durationDays);
      const updatedResult = await verificationService.getResult(activeReq.request_reference);
      setVerificationResult(updatedResult);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to grant consent');
    } finally {
      setConsentActionLoading(false);
    }
  };

  const handleRevokeConsent = async () => {
    if (!activeReq) return;
    try {
      setConsentActionLoading(true);
      await verificationService.revokeConsent(activeReq.request_reference);
      const updatedResult = await verificationService.getResult(activeReq.request_reference);
      setVerificationResult(updatedResult);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to revoke consent');
    } finally {
      setConsentActionLoading(false);
    }
  };

  const toggleField = (field: string) => {
    if (permittedFields.includes(field)) {
      setPermittedFields(permittedFields.filter((f) => f !== field));
    } else {
      setPermittedFields([...permittedFields, field]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-teal-600 text-xs font-semibold uppercase tracking-wider">
            <QrCode className="w-4 h-4" />
            <span>Cryptographic Trust & Consent Engine</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Academic Credential Verification Portal</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Student-controlled field access permissions and HMAC-SHA256 signed QR certificates.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setActiveTab('consent_flow')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
              activeTab === 'consent_flow'
                ? 'bg-white text-teal-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Consent-Based Verification
          </button>
          <button
            onClick={() => setActiveTab('qr_verify')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
              activeTab === 'qr_verify'
                ? 'bg-white text-teal-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Signed QR Authenticator
          </button>
        </div>
      </div>

      {/* TAB 1: Signed QR Authenticator */}
      {activeTab === 'qr_verify' && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="max-w-2xl">
            <h2 className="text-sm font-bold text-slate-900">Cryptographic Certificate Signature Validation</h2>
            <p className="text-xs text-slate-500 mt-1">
              Enter or scan a digital certificate reference string to verify its canonical HMAC-SHA256 digital signature, expiration, and revocation status without exposing sensitive personal data.
            </p>

            <div className="mt-4 flex gap-2">
              <input
                type="text"
                value={certRefInput}
                onChange={(e) => setCertRefInput(e.target.value)}
                placeholder="e.g. CERT-APAAR-202610-8A7B6C5D"
                className="flex-1 text-xs border border-slate-300 rounded-lg p-2.5 font-mono focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
              />
              <button
                onClick={() => handleVerifyCertificate()}
                disabled={certLoading}
                className="px-4 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-sm transition disabled:opacity-50 flex items-center space-x-1"
              >
                {certLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Verify Authenticity</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Certificate Verification Result Card */}
          {certVerifyResult && (
            <div
              className={`p-6 rounded-2xl border ${
                certVerifyResult.is_valid
                  ? 'bg-emerald-50/50 border-emerald-300'
                  : certVerifyResult.status === 'EXPIRED'
                  ? 'bg-amber-50/50 border-amber-300'
                  : 'bg-rose-50/50 border-rose-300'
              } space-y-4 max-w-2xl transition-all`}
            >
              <div className="flex items-center space-x-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    certVerifyResult.is_valid
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-rose-100 text-rose-700'
                  }`}
                >
                  {certVerifyResult.is_valid ? (
                    <CheckCircle2 className="w-7 h-7" />
                  ) : (
                    <XCircle className="w-7 h-7" />
                  )}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-xs font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                        certVerifyResult.is_valid
                          ? 'bg-emerald-200 text-emerald-900'
                          : 'bg-rose-200 text-rose-900'
                      }`}
                    >
                      {certVerifyResult.status}
                    </span>
                    <span className="text-xs text-slate-500">
                      Signature Verified: {certVerifyResult.digital_signature_verified ? 'Yes (Authentic)' : 'No'}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-slate-900 mt-1">{certVerifyResult.message}</p>
                </div>
              </div>

              {certVerifyResult.is_valid && (
                <div className="bg-white p-4 rounded-xl border border-slate-200/80 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">Issuing Institution</span>
                    <p className="font-semibold text-slate-800 mt-0.5">{certVerifyResult.institution}</p>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">Academic Programme</span>
                    <p className="font-semibold text-slate-800 mt-0.5">{certVerifyResult.programme}</p>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">Student Reference</span>
                    <p className="font-mono text-slate-800 mt-0.5">{certVerifyResult.student_reference}</p>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase">Validity Period</span>
                    <p className="text-slate-800 mt-0.5">
                      Valid until {new Date(certVerifyResult.expires_at || '').toLocaleDateString()}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Consent-Based Verification Flow */}
      {activeTab === 'consent_flow' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Step 1: Create Verification Request */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div>
              <div className="flex items-center space-x-1.5 text-xs font-bold text-teal-700 uppercase tracking-wider">
                <Lock className="w-3.5 h-3.5" />
                <span>Step 1: Initiation</span>
              </div>
              <h2 className="text-sm font-bold text-slate-900 mt-1">Initiate Credential Verification</h2>
              <p className="text-xs text-slate-500">
                A short-lived verification reference is issued. No personal student data is exposed until student consent is granted.
              </p>
            </div>

            <form onSubmit={handleCreateVerificationRequest} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Student Record Identifier
                </label>
                <input
                  type="text"
                  value={studentInput}
                  onChange={(e) => setStudentInput(e.target.value)}
                  placeholder="Student ID (e.g. 1) or APAAR ID (e.g. 900000000501)"
                  required
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Verification Purpose
                </label>
                <input
                  type="text"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  required
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  Requesting Organization
                </label>
                <input
                  type="text"
                  value={verifierOrg}
                  onChange={(e) => setVerifierOrg(e.target.value)}
                  required
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
                />
              </div>

              <button
                type="submit"
                disabled={reqLoading}
                className="w-full py-2.5 px-4 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-sm transition disabled:opacity-50"
              >
                {reqLoading ? 'Creating Request...' : 'Generate Single-Purpose Verification Request'}
              </button>
            </form>

            {/* Active Request Details */}
            {activeReq && (
              <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Request Reference:</span>
                  <span className="font-mono font-bold text-teal-700">{activeReq.request_reference}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Target Student:</span>
                  <span className="font-semibold text-slate-900">{activeReq.student_name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Access Status:</span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded-full text-[11px] ${
                      activeReq.status === 'consent_granted'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {activeReq.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Step 2: Simulated Student Consent Dialog */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div>
                <div className="flex items-center space-x-1.5 text-xs font-bold text-amber-700 uppercase tracking-wider">
                  <Unlock className="w-3.5 h-3.5" />
                  <span>Step 2: Student Consent Simulation</span>
                </div>
                <h2 className="text-sm font-bold text-slate-900 mt-1">Student Consent Delegation</h2>
                <p className="text-xs text-slate-500">
                  Simulates student reviewing the request and selecting precisely which fields are authorized.
                </p>
                <div className="mt-2 text-[10px] bg-amber-50 text-amber-800 border border-amber-200 p-2 rounded">
                  Notice: Clearly labeled as simulated demo consent, not legally valid or government-authenticated consent.
                </div>
              </div>

              {activeReq ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase mb-2">
                      Permitted Data Fields:
                    </label>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {[
                        { id: 'student_name', label: 'Full Student Name' },
                        { id: 'programme', label: 'Enrolled Programme' },
                        { id: 'college_name', label: 'College / Institution Name' },
                        { id: 'academic_year', label: 'Academic Year' },
                        { id: 'admission_category', label: 'Admission Category (Quota)' },
                        { id: 'apaar_id', label: 'Raw APAAR ID (Unmasked)' },
                      ].map((item) => (
                        <label
                          key={item.id}
                          className="flex items-center space-x-2 p-2 rounded-lg border border-slate-200 hover:bg-slate-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={permittedFields.includes(item.id)}
                            onChange={() => toggleField(item.id)}
                            className="rounded text-teal-600 focus:ring-teal-500"
                          />
                          <span className="text-slate-700 text-xs">{item.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 pt-2">
                    <button
                      onClick={handleGrantConsent}
                      disabled={consentActionLoading}
                      className="flex-1 py-2 px-3 text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-sm transition disabled:opacity-50"
                    >
                      {consentActionLoading ? 'Processing...' : 'Grant Simulated Consent'}
                    </button>
                    <button
                      onClick={handleRevokeConsent}
                      disabled={consentActionLoading}
                      className="py-2 px-3 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-lg border border-rose-200 transition disabled:opacity-50"
                    >
                      Revoke Consent
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-400 text-xs">
                  Initiate a verification request in Step 1 to activate consent controls.
                </div>
              )}
            </div>

            {/* Step 3: Verifier Privacy-Filtered View */}
            {verificationResult && (
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Step 3: Verifier Output (Field-Filtered)
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">{verificationResult.message}</p>
                  </div>
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      verificationResult.is_valid_access
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {verificationResult.is_valid_access ? 'Access Granted' : 'Access Restricted'}
                  </span>
                </div>

                {verificationResult.is_valid_access ? (
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                    {Object.entries(verificationResult.student_data).map(([key, val]) => (
                      <div key={key} className="flex items-center justify-between py-1 border-b border-slate-200/60 last:border-0">
                        <span className="text-slate-500 font-semibold capitalize">
                          {key.replace('_', ' ')}:
                        </span>
                        <span className="font-bold text-slate-900">{String(val)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
                    Student profile locked. Access requires active consent from the student.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
