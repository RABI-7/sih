import React, { useEffect, useState } from 'react';
import { FileCheck2, Download, ExternalLink, Calendar, Hash, FileSpreadsheet } from 'lucide-react';
import { uploadService } from '../services/api';
import { UploadBatch, User } from '../types';

interface UploadBatchesPageProps {
  currentUser: User | null;
}

export const UploadBatchesPage: React.FC<UploadBatchesPageProps> = ({ currentUser }) => {
  const [batches, setBatches] = useState<UploadBatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    try {
      setLoading(true);
      const data = await uploadService.getBatches(currentUser?.college_id || undefined);
      setBatches(data);
    } catch (err) {
      console.error('Failed to load upload batches', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-teal-600 text-xs font-semibold uppercase tracking-wider">
            <FileCheck2 className="w-4 h-4" />
            <span>Immutable Ingestion History</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Upload Batches & File Signatures</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Every submission retains its original file SHA-256 checksum and immutable historical row states.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading batch audit records...</div>
        ) : batches.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No upload batches found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Batch ID</th>
                  <th className="px-4 py-3">File Name</th>
                  <th className="px-4 py-3">File SHA-256 Checksum</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3 text-center">Total</th>
                  <th className="px-4 py-3 text-center text-emerald-700">Valid</th>
                  <th className="px-4 py-3 text-center text-amber-700">Review</th>
                  <th className="px-4 py-3 text-center text-rose-700">Invalid</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {batches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 font-mono font-bold text-slate-700">BATCH-{b.id}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 flex items-center space-x-1.5">
                      <FileSpreadsheet className="w-4 h-4 text-teal-600 flex-shrink-0" />
                      <span className="truncate max-w-[180px]">{b.filename}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500 text-[11px]" title={b.file_sha256}>
                      {b.file_sha256.slice(0, 16)}...
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-[11px]">
                      {new Date(b.upload_timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-slate-800">{b.total_rows}</td>
                    <td className="px-4 py-3 text-center font-bold text-emerald-600">{b.accepted_rows}</td>
                    <td className="px-4 py-3 text-center font-bold text-amber-600">{b.warning_rows}</td>
                    <td className="px-4 py-3 text-center font-bold text-rose-600">{b.rejected_rows}</td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <a
                        href={uploadService.getErrorsCsvUrl(b.id)}
                        download
                        className="inline-flex items-center space-x-1 text-xs text-slate-700 hover:text-slate-900 font-semibold bg-slate-100 px-2 py-1 rounded hover:bg-slate-200 transition"
                      >
                        <Download className="w-3 h-3" />
                        <span>Errors CSV</span>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
