import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Download,
  ArrowRight,
  RefreshCw,
  Eye,
  FileText,
  ShieldCheck,
  Filter
} from 'lucide-react';
import { uploadService } from '../services/api';
import { UploadBatchResult, User, RowValidationDetail } from '../types';
import { StatusBadge } from '../components/StatusBadge';

interface StudentUploadPageProps {
  currentUser: User | null;
}

export const StudentUploadPage: React.FC<StudentUploadPageProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<UploadBatchResult | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [previewRows, setPreviewRows] = useState<any[]>([]);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (selectedFile: File) => {
    setErrorMsg(null);
    setResult(null);

    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext !== 'xlsx' && ext !== 'xls' && ext !== 'csv') {
      setErrorMsg('Unsupported format. Please upload an Excel (.xlsx) or CSV (.csv) file.');
      return;
    }

    if (selectedFile.size > 15 * 1024 * 1024) {
      setErrorMsg('File exceeds 15 MB limit.');
      return;
    }

    setFile(selectedFile);

    // Quick text preview for CSV
    if (ext === 'csv') {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        const lines = text.split('\n').filter((l) => l.trim().length > 0);
        if (lines.length > 1) {
          const headers = lines[0].split(',').map((h) => h.trim().replace(/^["']|["']$/g, ''));
          const rows = lines.slice(1, 6).map((line) => {
            const vals = line.split(',').map((v) => v.trim().replace(/^["']|["']$/g, ''));
            const obj: Record<string, string> = {};
            headers.forEach((h, i) => {
              obj[h] = vals[i] || '';
            });
            return obj;
          });
          setPreviewRows(rows);
        }
      };
      reader.readAsText(selectedFile);
    } else {
      setPreviewRows([
        { 'Student Name': 'Sample Name', 'APAAR ID': '900000000501', 'Programme': 'B.Tech CSE', 'Academic Year': '2024-2025' }
      ]);
    }
  };

  const handleExecuteUpload = async () => {
    if (!file) return;
    try {
      setUploading(true);
      setErrorMsg(null);
      const res = await uploadService.uploadFile(file, currentUser?.college_id || undefined);
      setResult(res);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Gate 1 validation failed: Check schema and column headers.');
    } finally {
      setUploading(false);
    }
  };

  const filteredRows = result?.rows.filter((r) => {
    if (filterStatus === 'all') return true;
    return r.status === filterStatus;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-teal-600 text-xs font-semibold uppercase tracking-wider">
            <UploadCloud className="w-4 h-4" />
            <span>Admission Compliance Ingestion</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Student Data Upload Wizard</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Two-Gate Verification: Gate 1 File & Schema Parsing → Gate 2 Identity & Intake Validation
          </p>
        </div>

        {/* Downloadable Demo Template Buttons */}
        <div className="flex items-center space-x-2">
          <a
            href={uploadService.getSampleTemplateCsvUrl()}
            download
            className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Sample Template (.csv)</span>
          </a>
        </div>
      </div>

      {/* Step 1: Drag & Drop Zone */}
      {!result && (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-teal-500 bg-teal-50/50'
                : file
                ? 'border-teal-500 bg-teal-50/20'
                : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv, .xlsx, .xls"
              onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
              className="hidden"
            />

            <div className="w-14 h-14 rounded-2xl bg-teal-100 text-teal-700 mx-auto flex items-center justify-center mb-4 shadow-xs">
              <FileSpreadsheet className="w-7 h-7" />
            </div>

            {file ? (
              <div>
                <p className="text-sm font-bold text-teal-900">{file.name}</p>
                <p className="text-xs text-slate-500 mt-1">
                  Size: {(file.size / 1024).toFixed(1)} KB | Ready for Gate 1 & 2 Ingestion
                </p>
                <span className="inline-block mt-3 text-xs text-teal-700 font-semibold underline">
                  Click to select a different file
                </span>
              </div>
            ) : (
              <div>
                <p className="text-sm font-bold text-slate-800">
                  Drag and drop student admission file (.xlsx or .csv)
                </p>
                <p className="text-xs text-slate-500 mt-1">or browse files from your computer</p>
                <div className="mt-4 flex flex-wrap justify-center gap-2 text-[11px] text-slate-500">
                  <span className="bg-white px-2 py-1 rounded border border-slate-200">Mandatory: Student Name</span>
                  <span className="bg-white px-2 py-1 rounded border border-slate-200">Mandatory: APAAR ID</span>
                  <span className="bg-white px-2 py-1 rounded border border-slate-200">Mandatory: Programme</span>
                  <span className="bg-white px-2 py-1 rounded border border-slate-200">Mandatory: Academic Year</span>
                </div>
              </div>
            )}
          </div>

          {errorMsg && (
            <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Gate 1 Validation Rejected</p>
                <p className="mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          {/* Preview & Confirmation Action */}
          {file && (
            <div className="mt-6 pt-6 border-t border-slate-200 space-y-4">
              {previewRows.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                    <Eye className="w-3.5 h-3.5 text-slate-500" />
                    <span>Spreadsheet Row Preview (First {previewRows.length} rows)</span>
                  </h3>
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-100 text-slate-600 text-[11px] uppercase">
                        <tr>
                          {Object.keys(previewRows[0] || {}).map((col) => (
                            <th key={col} className="px-3 py-2 border-b border-slate-200">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {previewRows.map((r, i) => (
                          <tr key={i} className="hover:bg-slate-50">
                            {Object.values(r).map((val: any, j) => (
                              <td key={j} className="px-3 py-2 text-slate-700 font-mono text-[11px]">{String(val)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setFile(null);
                    setPreviewRows([]);
                  }}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Clear Selection
                </button>
                <button
                  type="button"
                  onClick={handleExecuteUpload}
                  disabled={uploading}
                  className="flex items-center space-x-2 px-6 py-2.5 text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-md transition disabled:opacity-50"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Validating through Gate 1 & 2...</span>
                    </>
                  ) : (
                    <>
                      <span>Execute Gate 1 & 2 Validation</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Upload Results & Row-Level Error Reports */}
      {result && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Submitted</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">{result.total_records}</p>
              <p className="text-xs text-slate-400 mt-0.5">Rows in upload file</p>
            </div>
            <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200 shadow-xs">
              <span className="text-[11px] font-semibold text-emerald-700 uppercase">Valid Admissions</span>
              <p className="text-2xl font-bold text-emerald-800 mt-1">{result.valid_count}</p>
              <p className="text-xs text-emerald-600 mt-0.5">Passed all rules</p>
            </div>
            <div className="bg-amber-50/60 p-4 rounded-xl border border-amber-200 shadow-xs">
              <span className="text-[11px] font-semibold text-amber-700 uppercase">Review Required</span>
              <p className="text-2xl font-bold text-amber-800 mt-1">{result.warning_count}</p>
              <p className="text-xs text-amber-600 mt-0.5">Human review warnings</p>
            </div>
            <div className="bg-rose-50/60 p-4 rounded-xl border border-rose-200 shadow-xs">
              <span className="text-[11px] font-semibold text-rose-700 uppercase">Rejected Records</span>
              <p className="text-2xl font-bold text-rose-800 mt-1">{result.invalid_count}</p>
              <p className="text-xs text-rose-600 mt-0.5">Critical violations</p>
            </div>
          </div>

          {/* Results Action Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-slate-500" />
              <span className="text-xs font-bold text-slate-700">Filter Validation Results:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-xs border border-slate-300 rounded-lg p-1.5 bg-white"
              >
                <option value="all">All Rows ({result.rows.length})</option>
                <option value="invalid">Invalid Only ({result.invalid_count})</option>
                <option value="warning">Warnings Only ({result.warning_count})</option>
                <option value="valid">Valid Only ({result.valid_count})</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <a
                href={uploadService.getErrorsCsvUrl(result.batch.id)}
                download
                className="flex items-center space-x-1.5 px-3 py-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download CSV Error Report</span>
              </a>
              <button
                onClick={() => {
                  setResult(null);
                  setFile(null);
                }}
                className="px-3 py-2 text-xs font-semibold text-teal-700 hover:bg-teal-50 rounded-lg transition"
              >
                Upload Another Batch
              </button>
            </div>
          </div>

          {/* Row-by-Row Validation Report Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Row-Level Ingestion Results & Recommendations</h2>
              <p className="text-xs text-slate-500">Every issue is traced to its row index and specific compliance rule</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
                  <tr>
                    <th className="px-3 py-3 w-12 text-center">Row</th>
                    <th className="px-3 py-3">Student Name</th>
                    <th className="px-3 py-3">APAAR ID (Masked)</th>
                    <th className="px-3 py-3">Programme</th>
                    <th className="px-3 py-3">Gate 2 Status</th>
                    <th className="px-4 py-3">Detected Irregularity / Rule</th>
                    <th className="px-4 py-3">Recommended Correction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredRows.map((r) => (
                    <tr
                      key={r.row_number}
                      className={r.status === 'invalid' ? 'bg-rose-50/30' : r.status === 'warning' ? 'bg-amber-50/20' : 'hover:bg-slate-50'}
                    >
                      <td className="px-3 py-3 text-center font-mono font-bold text-slate-500">
                        #{r.row_number}
                      </td>
                      <td className="px-3 py-3 font-semibold text-slate-900">{r.student_name}</td>
                      <td className="px-3 py-3 font-mono text-slate-600">{r.masked_apaar_id}</td>
                      <td className="px-3 py-3 text-slate-600 truncate max-w-[160px]">{r.programme}</td>
                      <td className="px-3 py-3">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-xs font-medium text-slate-900">{r.primary_issue}</p>
                        {r.triggered_rules && r.triggered_rules.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {r.triggered_rules.map((rule) => (
                              <span
                                key={rule}
                                className="font-mono text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded border border-slate-200"
                              >
                                {rule}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        {r.recommended_action || 'None required.'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
