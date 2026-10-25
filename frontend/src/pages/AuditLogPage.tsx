import React, { useEffect, useState } from 'react';
import {
  History,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Hash,
  Filter,
  User,
  Clock
} from 'lucide-react';
import { auditService } from '../services/api';
import { AuditLog, AuditIntegrity } from '../types';

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('all');
  const [integrityResult, setIntegrityResult] = useState<AuditIntegrity | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    loadAuditLogs();
  }, [actionFilter]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const data = await auditService.getLogs({
        action: actionFilter === 'all' ? undefined : actionFilter,
        limit: 100,
      });
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    try {
      setVerifying(true);
      const result = await auditService.verifyIntegrity();
      setIntegrityResult(result);
      // Reload logs to reflect the integrity verification audit log itself!
      await loadAuditLogs();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to verify audit chain');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-teal-600 text-xs font-semibold uppercase tracking-wider">
            <History className="w-4 h-4" />
            <span>Cryptographic Proof of Authenticity</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Tamper-Evident Audit Trail</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable SHA-256 hash chaining links every administrative action, upload batch, and consent grant.
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          className="flex items-center space-x-2 px-5 py-2.5 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-sm transition disabled:opacity-50"
        >
          {verifying ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-teal-400" />
              <span>Verifying Cryptographic Chain...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4 text-teal-400" />
              <span>Verify Audit Chain Integrity</span>
            </>
          )}
        </button>
      </div>

      {/* Integrity Verification Result Banner */}
      {integrityResult && (
        <div
          className={`p-4 rounded-xl border flex items-start space-x-3 transition-all ${
            integrityResult.is_valid
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
              : 'bg-rose-50 border-rose-300 text-rose-900'
          }`}
        >
          <div className="p-1 rounded-full bg-white/80 mt-0.5">
            {integrityResult.is_valid ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600" />
            )}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xs uppercase tracking-wider">
                {integrityResult.is_valid ? 'Cryptographic Integrity Confirmed' : 'Chain Integrity Alert'}
              </span>
              <span className="text-[11px] font-mono opacity-80">
                Verified {integrityResult.total_entries_verified} consecutive hash links
              </span>
            </div>
            <p className="text-xs mt-1 font-medium">{integrityResult.verification_message}</p>
          </div>
        </div>
      )}

      {/* Action Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-bold text-slate-700">Filter Event Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white"
          >
            <option value="all">All Audit Actions</option>
            <option value="USER_LOGIN">User Logins</option>
            <option value="BATCH_UPLOAD_COMPLETED">Upload Batches</option>
            <option value="FLAG_STATUS_CHANGE">Flag Review Decisions</option>
            <option value="VERIFICATION_REQUESTED">Verification Invocations</option>
            <option value="CONSENT_GRANTED">Consent Grants</option>
            <option value="CONSENT_REVOKED">Consent Revocations</option>
            <option value="CERTIFICATE_ISSUED">QR Certificates Issued</option>
            <option value="INTEGRITY_CHECK_EXECUTED">Integrity Verifications</option>
          </select>
        </div>

        <button
          onClick={loadAuditLogs}
          className="text-xs text-slate-600 hover:text-slate-900 font-semibold flex items-center space-x-1"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Live Trail</span>
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading audit ledger...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No audit events found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 w-16">Entry</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Event Action</th>
                  <th className="px-4 py-3">Entity Reference</th>
                  <th className="px-4 py-3">Previous SHA-256 Link</th>
                  <th className="px-4 py-3">Entry SHA-256 Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 font-mono font-bold text-slate-500">#{log.id}</td>
                    <td className="px-4 py-3 text-slate-500 text-[11px] flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-slate-400 flex-shrink-0" />
                      <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800">{log.actor_name}</td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200 font-semibold">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {log.entity_type} {log.entity_id ? `(#${log.entity_id})` : ''}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-slate-400" title={log.previous_hash}>
                      {log.previous_hash === '0'.repeat(64)
                        ? 'GENESIS_ROOT'
                        : `${log.previous_hash.slice(0, 10)}...`}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-teal-700 font-bold" title={log.entry_hash}>
                      {log.entry_hash.slice(0, 12)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Explanatory Technical Note */}
      <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-600 leading-relaxed">
        <p className="font-semibold text-slate-800 mb-1">Architecture Note on Hash Chaining:</p>
        Each audit record incorporates the SHA-256 hash of the preceding entry in canonical JSON representation. Any retroactive tampering or row deletion invalidates all subsequent hashes, providing continuous, mathematical tamper evidence for judicial and regulatory inquiries.
      </div>
    </div>
  );
};
