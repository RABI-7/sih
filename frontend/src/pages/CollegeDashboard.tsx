import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Building,
  ArrowUpRight,
  Download,
  Search,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';
import { KPICard } from '../components/KPICard';
import { StatusBadge } from '../components/StatusBadge';
import { RiskBadge } from '../components/RiskBadge';
import { StudentDetailModal } from '../components/StudentDetailModal';
import { collegeService, studentService, uploadService } from '../services/api';
import { Student, StudentDetail, College, User } from '../types';

interface CollegeDashboardProps {
  currentUser: User | null;
}

export const CollegeDashboard: React.FC<CollegeDashboardProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const [collegeData, setCollegeData] = useState<College | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const collegeId = currentUser?.college_id || 1;

  useEffect(() => {
    loadDashboardData();
  }, [collegeId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const colleges = await collegeService.getColleges();
      const current = colleges.find((c) => c.id === collegeId) || colleges[0];
      setCollegeData(current);

      const studentList = await studentService.getStudents({ college_id: collegeId, limit: 10 });
      setStudents(studentList);
    } catch (err) {
      console.error('Failed to load college dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectStudent = async (studentId: number) => {
    try {
      const detail = await studentService.getStudentDetail(studentId);
      setSelectedStudent(detail);
    } catch (err) {
      console.error('Failed to load student details', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    );
  }

  const approved = collegeData?.approved_intake || 120;
  const enrolled = collegeData?.enrolled_count || students.length;
  const utilRate = collegeData?.utilization_rate || Math.round((enrolled / approved) * 100);
  const isOver = utilRate > 100;

  return (
    <div className="space-y-6">
      {/* Institution Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-institutional-900 text-white rounded-2xl p-6 shadow-sm border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-teal-400 text-xs font-semibold uppercase tracking-wider">
            <Building className="w-4 h-4" />
            <span>Institutional Dashboard</span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1">
            {collegeData?.name || 'Delhi Institute of Technology & Applied Sciences'}
          </h1>
          <p className="text-xs text-slate-300 mt-0.5">
            Institution Code: <span className="font-mono text-teal-300 font-semibold">{collegeData?.institution_code}</span> | Sanctioned Intake: {approved} Seats
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <a
            href={uploadService.getSampleTemplateCsvUrl()}
            download
            className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Template (.csv)</span>
          </a>
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-sm transition"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Student Batch</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Sanctioned Intake Quota"
          value={approved}
          subtitle="Approved maximum admissions"
          icon={Building}
          colorScheme="blue"
        />
        <KPICard
          title="Admitted Students"
          value={enrolled}
          subtitle="Total verified records"
          icon={Users}
          badge={`${enrolled} Active`}
          colorScheme="teal"
        />
        <KPICard
          title="Intake Capacity Utilization"
          value={`${utilRate}%`}
          subtitle={isOver ? 'Exceeds sanctioned seat limit' : 'Within statutory capacity'}
          icon={CheckCircle2}
          badge={isOver ? 'Over-Intake Alert' : 'Compliant'}
          colorScheme={isOver ? 'rose' : 'teal'}
        />
        <KPICard
          title="Upload Gate Security"
          value="Gate 1 & 2"
          subtitle="Schema & APAAR validation"
          icon={ShieldCheck}
          badge="Active"
          colorScheme="purple"
        />
      </div>

      {/* Capacity Utilization Progress Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Approved Intake Capacity Tracker
          </span>
          <span className={`text-xs font-bold ${isOver ? 'text-rose-600' : 'text-slate-700'}`}>
            {enrolled} / {approved} Seats ({utilRate}%)
          </span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              isOver ? 'bg-rose-500' : utilRate >= 90 ? 'bg-amber-500' : 'bg-teal-500'
            }`}
            style={{ width: `${Math.min(100, utilRate)}%` }}
          />
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
          <span>0 Seats</span>
          <span>Approved: {approved}</span>
          <span>Capacity Limit: 100%</span>
        </div>
      </div>

      {/* Recent Admitted Students Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Recent Admitted Student Records</h2>
            <p className="text-xs text-slate-500">Live synchronized records verified via Gate 1 & Gate 2</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => navigate('/students')}
              className="text-xs text-teal-600 hover:text-teal-700 font-semibold flex items-center space-x-1"
            >
              <span>View All Records</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Student Name</th>
                <th className="px-4 py-3">Masked APAAR ID</th>
                <th className="px-4 py-3">Programme</th>
                <th className="px-4 py-3">Academic Year</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Risk Assessment</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-slate-50/80 transition">
                  <td className="px-4 py-3 font-semibold text-slate-900">{student.student_name}</td>
                  <td className="px-4 py-3 font-mono text-slate-600">{student.masked_apaar_id}</td>
                  <td className="px-4 py-3 text-slate-600">{student.programme}</td>
                  <td className="px-4 py-3 text-slate-500">{student.academic_year}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={student.record_status} />
                  </td>
                  <td className="px-4 py-3">
                    <RiskBadge score={student.risk_score} level={student.risk_level} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleInspectStudent(student.id)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center space-x-1"
                    >
                      <span>Inspect</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
