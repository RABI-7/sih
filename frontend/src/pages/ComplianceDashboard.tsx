import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Building,
  Users,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Copy,
  ArrowUpRight,
  TrendingUp,
  FileCheck2,
  RefreshCw
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { KPICard } from '../components/KPICard';
import { FlagReviewModal } from '../components/FlagReviewModal';
import { StudentDetailModal } from '../components/StudentDetailModal';
import { complianceService, studentService } from '../services/api';
import { ComplianceSummary, ValidationFlag, StudentDetail } from '../types';

export const ComplianceDashboard: React.FC = () => {
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFlag, setActiveFlag] = useState<ValidationFlag | null>(null);
  const [inspectStudent, setInspectStudent] = useState<StudentDetail | null>(null);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await complianceService.getSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load compliance summary', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectStudentById = async (studentId: number) => {
    try {
      const detail = await studentService.getStudentDetail(studentId);
      setInspectStudent(detail);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    );
  }

  // Prepare chart data for intake comparison
  const intakeChartData = summary.over_intake_institutions.length > 0
    ? summary.over_intake_institutions.map((inst) => ({
        name: inst.college_name.split(' ')[0],
        approved: inst.approved_intake,
        admitted: inst.admitted_count,
        utilization: inst.utilization_rate,
      }))
    : [
        { name: 'Delhi Tech', approved: 120, admitted: 105, utilization: 87.5 },
        { name: 'National Engg', approved: 150, admitted: 135, utilization: 90.0 },
        { name: 'Apex Academy', approved: 80, admitted: 88, utilization: 110.0 },
      ];

  const COLORS = ['#10B981', '#F59E0B', '#F97316', '#EF4444'];

  return (
    <div className="space-y-6">
      {/* Central Compliance Banner */}
      <div className="bg-gradient-to-r from-institutional-950 to-slate-900 text-white rounded-2xl p-6 shadow-sm border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-teal-400 text-xs font-semibold uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-purple-400" />
            <span>AICTE Central Oversight & Regulatory Compliance</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1">Cross-Institutional Compliance Center</h1>
          <p className="text-xs text-slate-300 mt-0.5">
            Automated monitoring of approved intake caps, multi-college dual enrollment, and identity irregularities.
          </p>
        </div>

        <button
          onClick={loadSummary}
          className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Synchronize Live Audit Metrics</span>
        </button>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Participating Institutions"
          value={summary.total_institutions}
          subtitle="Monitored colleges in network"
          icon={Building}
          colorScheme="blue"
        />
        <KPICard
          title="Total Student Admissions"
          value={summary.total_students}
          subtitle={`${summary.valid_records} Verified Normal`}
          icon={Users}
          badge={`${Math.round((summary.valid_records / Math.max(1, summary.total_students)) * 100)}% Valid`}
          colorScheme="teal"
        />
        <KPICard
          title="Dual Enrolment Detections"
          value={summary.potential_cross_college_duplicates}
          subtitle="Students in multiple colleges"
          icon={Copy}
          badge={summary.potential_cross_college_duplicates > 0 ? 'Requires Action' : 'Clear'}
          colorScheme={summary.potential_cross_college_duplicates > 0 ? 'rose' : 'teal'}
        />
        <KPICard
          title="Capacity Overruns"
          value={summary.institutions_exceeding_intake}
          subtitle="Colleges over statutory limit"
          icon={AlertTriangle}
          badge={summary.institutions_exceeding_intake > 0 ? 'Quota Exceeded' : 'Compliant'}
          colorScheme={summary.institutions_exceeding_intake > 0 ? 'rose' : 'teal'}
        />
      </div>

      {/* Analytics Visualizations via Recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Approved Intake vs Admitted Bar Chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Approved Intake vs Admitted Headcount
              </h3>
              <p className="text-xs text-slate-500">Statutory capacity cap enforcement per institution</p>
            </div>
            <span className="text-xs font-semibold text-slate-600">
              Avg Utilization: {summary.average_utilization_rate}%
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intakeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="approved" name="Sanctioned Intake" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="admitted" name="Admitted Enrolment" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Pie Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1">
              Admission Risk Distribution
            </h3>
            <p className="text-xs text-slate-500 mb-2">Rules-based transparency severity bands</p>
          </div>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={summary.risk_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="count"
                  nameKey="category"
                >
                  {summary.risk_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] pt-3 border-t border-slate-100">
            {summary.risk_distribution.map((item, index) => (
              <div key={item.category} className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index] }} />
                <span className="text-slate-600 truncate">{item.category}</span>
                <span className="font-bold text-slate-900 ml-auto">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Over-Intake Alerts Table */}
      {summary.over_intake_institutions.length > 0 && (
        <div className="bg-white rounded-xl border border-rose-200 shadow-xs overflow-hidden">
          <div className="bg-rose-50/70 p-4 border-b border-rose-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <h2 className="text-sm font-bold text-rose-900">Institutions Exceeding Approved Quota Limits</h2>
            </div>
            <span className="text-xs font-bold text-rose-800 bg-rose-100 px-2 py-0.5 rounded-full">
              {summary.over_intake_institutions.length} Institutions Flagged
            </span>
          </div>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Institution Name</th>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3 text-center">Approved Cap</th>
                <th className="px-4 py-3 text-center">Admitted Count</th>
                <th className="px-4 py-3 text-center text-rose-700">Excess Seats</th>
                <th className="px-4 py-3 text-center">Utilization</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summary.over_intake_institutions.map((inst) => (
                <tr key={inst.college_id} className="hover:bg-rose-50/20">
                  <td className="px-4 py-3 font-semibold text-slate-900">{inst.college_name}</td>
                  <td className="px-4 py-3 font-mono text-slate-600">{inst.institution_code}</td>
                  <td className="px-4 py-3 text-center font-bold text-slate-700">{inst.approved_intake}</td>
                  <td className="px-4 py-3 text-center font-bold text-slate-900">{inst.admitted_count}</td>
                  <td className="px-4 py-3 text-center font-bold text-rose-600">+{inst.over_intake_count} Seats</td>
                  <td className="px-4 py-3 text-center">
                    <span className="bg-rose-100 text-rose-800 text-[11px] font-bold px-2 py-0.5 rounded-full">
                      {inst.utilization_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Cross-College Duplicate Dual Enrollment Table */}
      {summary.cross_college_duplicates.length > 0 && (
        <div className="bg-white rounded-xl border border-amber-200 shadow-xs overflow-hidden">
          <div className="bg-amber-50/70 p-4 border-b border-amber-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Copy className="w-4 h-4 text-amber-600" />
              <h2 className="text-sm font-bold text-amber-900">
                Potential Cross-College Dual Enrollment Detected
              </h2>
            </div>
            <span className="text-xs font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full">
              {summary.cross_college_duplicates.length} Conflict Groups
            </span>
          </div>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Student Name</th>
                <th className="px-4 py-3">Masked APAAR ID</th>
                <th className="px-4 py-3">Conflicting Institutions</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summary.cross_college_duplicates.map((dup, i) => (
                <tr key={i} className="hover:bg-amber-50/20">
                  <td className="px-4 py-3 font-semibold text-slate-900">{dup.student_name}</td>
                  <td className="px-4 py-3 font-mono text-slate-600">{dup.masked_apaar_id}</td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      {dup.colleges.map((c, j) => (
                        <div key={j} className="flex items-center space-x-2 text-[11px]">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                          <span className="font-semibold text-slate-800">{c.college_name}:</span>
                          <span className="text-slate-600">{c.programme}</span>
                        </div>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[11px] text-teal-700 font-bold bg-teal-50 px-2 py-1 rounded border border-teal-200">
                      Under Regulatory Review
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      {activeFlag && (
        <FlagReviewModal
          flag={activeFlag}
          onClose={() => setActiveFlag(null)}
          onFlagUpdated={() => loadSummary()}
        />
      )}

      {inspectStudent && (
        <StudentDetailModal
          student={inspectStudent}
          onClose={() => setInspectStudent(null)}
        />
      )}
    </div>
  );
};
