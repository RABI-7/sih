import React, { useEffect, useState } from 'react';
import {
  Users,
  Search,
  Filter,
  ExternalLink,
  ShieldCheck,
  Building,
  RefreshCw
} from 'lucide-react';
import { studentService, collegeService } from '../services/api';
import { Student, StudentDetail, College, User } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { RiskBadge } from '../components/RiskBadge';
import { StudentDetailModal } from '../components/StudentDetailModal';

interface StudentRecordsPageProps {
  currentUser: User | null;
}

export const StudentRecordsPage: React.FC<StudentRecordsPageProps> = ({ currentUser }) => {
  const [students, setStudents] = useState<Student[]>([]);
  const [colleges, setColleges] = useState<College[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCollegeId, setSelectedCollegeId] = useState<number | undefined>(
    currentUser?.role === 'compliance_officer' ? undefined : (currentUser?.college_id || undefined)
  );

  useEffect(() => {
    loadColleges();
    loadStudents();
  }, [selectedCollegeId, statusFilter]);

  const loadColleges = async () => {
    try {
      const data = await collegeService.getColleges();
      setColleges(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadStudents = async () => {
    try {
      setLoading(true);
      const data = await studentService.getStudents({
        college_id: selectedCollegeId,
        status: statusFilter,
        search: searchTerm ? searchTerm : undefined,
        limit: 150
      });
      setStudents(data);
    } catch (err) {
      console.error('Failed to load students', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadStudents();
  };

  const handleInspect = async (studentId: number) => {
    try {
      const detail = await studentService.getStudentDetail(studentId);
      setSelectedStudent(detail);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-teal-600 text-xs font-semibold uppercase tracking-wider">
            <Users className="w-4 h-4" />
            <span>Academic Registry Database</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Student Records & Compliance Registry</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Privacy-preserving view with masked APAAR identifiers and transparent explainable risk scores.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[280px] relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by student name or APAAR ID..."
            className="w-full text-xs pl-9 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
        </form>

        <div className="flex flex-wrap items-center gap-2">
          {currentUser?.role === 'compliance_officer' && (
            <select
              value={selectedCollegeId || ''}
              onChange={(e) => setSelectedCollegeId(e.target.value ? Number(e.target.value) : undefined)}
              className="text-xs border border-slate-300 rounded-lg p-2.5 bg-white text-slate-700"
            >
              <option value="">All Institutions (Central View)</option>
              {colleges.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2.5 bg-white text-slate-700"
          >
            <option value="all">All Statuses</option>
            <option value="valid">Valid Records</option>
            <option value="warning">Review Required (Warnings)</option>
            <option value="invalid">Invalid Records</option>
          </select>

          <button
            onClick={loadStudents}
            className="px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg border border-slate-300 flex items-center space-x-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Students Data Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading student records...</div>
        ) : students.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No matching student records found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">Masked APAAR ID</th>
                  <th className="px-4 py-3">Institution</th>
                  <th className="px-4 py-3">Programme</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Risk Assessment</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {students.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900">{s.student_name}</td>
                    <td className="px-4 py-3 font-mono text-slate-600 font-medium">{s.masked_apaar_id}</td>
                    <td className="px-4 py-3 text-slate-600 truncate max-w-[180px]">{s.college_name}</td>
                    <td className="px-4 py-3 text-slate-600 truncate max-w-[180px]">{s.programme}</td>
                    <td className="px-4 py-3 text-slate-500">{s.admission_category || 'General'}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={s.record_status} />
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge score={s.risk_score} level={s.risk_level} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleInspect(s.id)}
                        className="text-xs text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center space-x-1"
                      >
                        <span>Inspect Record</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal
          student={selectedStudent}
          onClose={() => setSelectedStudent(null)}
        />
      )}
    </div>
  );
};
