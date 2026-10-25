import React from 'react';
import { ShieldCheck, LogOut, User, Building2, AlertTriangle } from 'lucide-react';
import { User as UserType } from '../types';
import { authService } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface NavbarProps {
  currentUser: UserType | null;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentUser, onLogout }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    onLogout();
    navigate('/login');
  };

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'compliance_officer':
        return <span className="bg-purple-100 text-purple-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-purple-200">AICTE Compliance Officer</span>;
      case 'college_admin':
        return <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-blue-200">College Administrator</span>;
      case 'verifier':
        return <span className="bg-teal-100 text-teal-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-teal-200">Credential Verifier</span>;
      default:
        return null;
    }
  };

  return (
    <header className="bg-institutional-950 border-b border-institutional-800 text-white sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Titles */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-teal-500 to-blue-600 flex items-center justify-center shadow-inner">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">APAAR GUARDIAN</span>
                {/* Notice Badge */}
                <span className="hidden sm:inline-flex items-center space-x-1 bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  <span>DEMO MODE — Synthetic Data</span>
                </span>
              </div>
              <p className="text-xs text-slate-300 tracking-wide font-normal">Student Data Integrity & Verification Platform</p>
            </div>
          </div>

          {/* User Profile and Controls */}
          <div className="flex items-center space-x-4">
            {currentUser ? (
              <div className="flex items-center space-x-3">
                <div className="hidden md:flex flex-col items-end">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-slate-200">{currentUser.full_name}</span>
                    {getRoleBadge(currentUser.role)}
                  </div>
                  {currentUser.college_name && (
                    <span className="text-xs text-slate-400 flex items-center mt-0.5">
                      <Building2 className="w-3 h-3 mr-1 text-slate-400" />
                      {currentUser.college_name}
                    </span>
                  )}
                </div>

                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => navigate('/login')}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-sm transition"
              >
                Demo Login
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
