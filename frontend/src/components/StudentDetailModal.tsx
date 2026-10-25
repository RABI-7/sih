import React, { useState } from 'react';
import {
  X,
  ShieldAlert,
  ShieldCheck,
  Building,
  GraduationCap,
  Calendar,
  CreditCard,
  FileCheck,
  Award,
  Sparkles,
  QrCode
} from 'lucide-react';
import { StudentDetail } from '../types';
import { RiskBadge } from './RiskBadge';
import { StatusBadge } from './StatusBadge';
import { certificateService } from '../services/api';

interface StudentDetailModalProps {
  student: StudentDetail | null;
  onClose: () => void;
  onOpenFlagReview?: (flagId: number) => void;
  onCertificateIssued?: (cert: any) => void;
}

export const StudentDetailModal: React.FC<StudentDetailModalProps> = ({
  student,
  onClose,
  onOpenFlagReview,
  onCertificateIssued
}) => {
  const [issuingCert, setIssuingCert] = useState(false);
  const [certSuccess, setCertSuccess] = useState<any>(null);

  if (!student) return null;

  const handleIssueCertificate = async () => {
    try {
      setIssuingCert(true);
      const res = await certificateService.issueCertificate(student.id, 12);
      setCertSuccess(res);
      if (onCertificateIssued) {
        onCertificateIssued(res);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to issue digital certificate');
    } finally {
      setIssuingCert(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
              <GraduationCap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{student.student_name}</h3>
              <p className="text-xs text-slate-400 font-mono">
                Record ID: #{student.id} | Masked APAAR: {student.masked_apaar_id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Top Info Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Institution</span>
              <p className="text-xs font-medium text-slate-900 mt-0.5 truncate">{student.college_name}</p>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Academic Programme</span>
              <p className="text-xs font-medium text-slate-900 mt-0.5 truncate">{student.programme}</p>
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Status & Compliance</span>
              <div className="mt-1 flex items-center space-x-2">
                <StatusBadge status={student.record_status} />
                <RiskBadge score={student.risk_score} level={student.risk_level} />
              </div>
            </div>
          </div>

          {/* Explainable Risk Score Breakdown */}
          <div className="border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-slate-700" />
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Transparent Risk Score Breakdown ({Math.round(student.risk_score)}/100)
                </h4>
              </div>
              {student.anomaly_score !== undefined && (
                <span className="inline-flex items-center space-x-1 text-[11px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">
                  <Sparkles className="w-3 h-3 text-purple-500" />
                  <span>Isolation Forest Anomaly: {student.anomaly_score} (Experimental)</span>
                </span>
              )}
            </div>

            {student.risk_breakdown && student.risk_breakdown.length > 0 ? (
              <div className="space-y-2">
                {student.risk_breakdown.map((item, idx) => (
                  <div key={idx} className="flex items-start justify-between bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 text-xs">
                    <div>
                      <span className="font-semibold text-slate-900">{item.rule_name}</span>
                      <p className="text-slate-500 text-[11px] mt-0.5">{item.description}</p>
                    </div>
                    <span className="font-bold text-rose-600 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded text-[11px] ml-3 flex-shrink-0">
                      +{item.points} pts
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 bg-emerald-50/50 rounded-lg border border-emerald-100 text-xs text-emerald-800">
                <ShieldCheck className="w-5 h-5 mx-auto text-emerald-600 mb-1" />
                No compliance or format risk factors detected. Standard compliant admission.
              </div>
            )}
          </div>

          {/* Synthetic External Registry Reconciliation */}
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
              Authoritative Registry Checks (Demo Mock Verification)
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className={`p-3 rounded-lg border ${student.has_registry_match ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-slate-50 border-slate-200 text-slate-600'}`}>
                <p className="font-semibold text-[11px]">Mock APAAR Registry</p>
                <p className="text-xs mt-1 font-bold">{student.has_registry_match ? 'Match Verified' : 'Not Matched'}</p>
              </div>

              <div className={`p-3 rounded-lg border ${student.has_counselling_match ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-amber-50 border-amber-200 text-amber-900'}`}>
                <p className="font-semibold text-[11px]">Central Counselling</p>
                <p className="text-xs mt-1 font-bold">{student.has_counselling_match ? 'Seat Allotted' : 'Discrepancy'}</p>
              </div>

              <div className={`p-3 rounded-lg border ${student.has_exam_record ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-amber-50 border-amber-200 text-amber-900'}`}>
                <p className="font-semibold text-[11px]">Examination Board</p>
                <p className="text-xs mt-1 font-bold">{student.has_exam_record ? 'Marks Reconciled' : 'Missing Record'}</p>
              </div>

              <div className={`p-3 rounded-lg border ${student.has_fees_record ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-amber-50 border-amber-200 text-amber-900'}`}>
                <p className="font-semibold text-[11px]">Admission Fee Challan</p>
                <p className="text-xs mt-1 font-bold">{student.has_fees_record ? 'Confirmed' : 'Unreconciled'}</p>
              </div>
            </div>
          </div>

          {/* Validation Flags List */}
          {student.flags && student.flags.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
                Validation Flags & Compliance Warnings ({student.flags.length})
              </h4>
              <div className="space-y-2">
                {student.flags.map((flag) => (
                  <div key={flag.id} className="p-3 rounded-lg border border-slate-200 bg-white flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-xs text-slate-900">{flag.rule_code}</span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${flag.severity === 'critical' ? 'bg-rose-100 text-rose-800' : flag.severity === 'high' ? 'bg-orange-100 text-orange-800' : 'bg-amber-100 text-amber-800'}`}>
                          {flag.severity}
                        </span>
                        <span className="text-[10px] text-slate-400 capitalize">Status: {flag.status.replace('_', ' ')}</span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">{flag.explanation}</p>
                      {flag.suggested_action && (
                        <p className="text-[11px] text-teal-700 mt-0.5 font-medium">
                          Suggested Action: {flag.suggested_action}
                        </p>
                      )}
                    </div>

                    {onOpenFlagReview && (
                      <button
                        onClick={() => onOpenFlagReview(flag.id)}
                        className="text-xs text-blue-600 hover:text-blue-800 font-semibold px-2 py-1 rounded hover:bg-blue-50 transition ml-3 flex-shrink-0"
                      >
                        Review Flag
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Certificate Generated Preview */}
          {certSuccess && (
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-xl flex items-center space-x-4">
              <img
                src={certSuccess.qr_code_data_uri}
                alt="QR Certificate"
                className="w-24 h-24 rounded-lg border border-teal-300 bg-white p-1"
              />
              <div className="text-xs space-y-1">
                <div className="flex items-center space-x-1.5 text-teal-800 font-bold">
                  <Award className="w-4 h-4 text-teal-600" />
                  <span>Cryptographically Signed QR Certificate Issued!</span>
                </div>
                <p className="text-slate-600 font-mono text-[11px]">Ref: {certSuccess.certificate_reference}</p>
                <p className="text-slate-500">
                  Signature: <span className="font-mono text-[10px]">{certSuccess.digital_signature.slice(0, 24)}...</span>
                </p>
                <a
                  href={certSuccess.verification_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block text-teal-700 font-semibold underline mt-1"
                >
                  Open Direct Verification Link
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="bg-slate-50 px-6 py-3 border-t border-slate-200 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 rounded-lg transition"
          >
            Close
          </button>

          {!certSuccess && (
            <button
              onClick={handleIssueCertificate}
              disabled={issuingCert}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              <QrCode className="w-4 h-4" />
              <span>{issuingCert ? 'Signing...' : 'Issue Signed QR Certificate'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
