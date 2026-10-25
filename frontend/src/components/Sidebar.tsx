import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UploadCloud,
  FileCheck2,
  ShieldAlert,
  History,
  QrCode,
  Building,
  CheckCircle2
} from 'lucide-react';
import { UserRole } from '../types';

interface SidebarProps {
  role?: UserRole;
  collegeName?: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ role, collegeName }) => {
  const getNavItems = () => {
    switch (role) {
      case 'compliance_officer':
        return [
          { to: '/compliance', label: 'Compliance & Oversight', icon: ShieldAlert },
          { to: '/students', label: 'Cross-College Records', icon: Users },
          { to: '/audit', label: 'Tamper-Evident Audit Log', icon: History },
          { to: '/verification', label: 'Record Verifier Portal', icon: QrCode },
        ];
      case 'college_admin':
        return [
          { to: '/college-dashboard', label: 'Institutional Overview', icon: LayoutDashboard },
          { to: '/upload', label: 'Student Upload Wizard', icon: UploadCloud },
          { to: '/students', label: 'Admitted Students', icon: Users },
          { to: '/batches', label: 'Upload Batch History', icon: FileCheck2 },
          { to: '/verification', label: 'Consent & Verification', icon: QrCode },
        ];
      case 'verifier':
        return [
          { to: '/verification', label: 'Academic Verification', icon: QrCode },
        ];
      default:
        return [
          { to: '/compliance', label: 'Compliance Dashboard', icon: ShieldAlert },
          { to: '/students', label: 'Student Directory', icon: Users },
          { to: '/verification', label: 'Verification', icon: QrCode },
        ];
    }
  };

  const navItems = getNavItems();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Context Header */}
      <div className="p-4 border-b border-slate-800">
        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active Workspace</p>
        <p className="text-sm font-semibold text-slate-100 mt-0.5 truncate">
          {collegeName || (role === 'compliance_officer' ? 'AICTE Central Authority' : 'Academic Verification')}
        </p>
      </div>

      {/* Nav list */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 text-xs font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 mr-3 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* System Integrity & Demo Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800/80 rounded-lg p-3 border border-slate-700/60 text-xs">
          <div className="flex items-center space-x-2 text-teal-400 font-semibold mb-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Integrity Guard Active</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            SHA-256 hash chaining & HMAC signatures active on all records.
          </p>
        </div>
      </div>
    </aside>
  );
};
