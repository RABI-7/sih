import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  ShieldAlert,
  SearchCheck,
  ArrowRight,
  KeyRound,
  AlertTriangle,
  CheckCircle2
} from 'lucide-react';
import { authService } from '../services/api';
import { User } from '../types';

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [selectedKey, setSelectedKey] = useState<string>('college_admin_1');
  const [otp, setOtp] = useState<string>('123456');
  const [step, setStep] = useState<'select' | 'otp'>('select');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const demoAccounts = [
    {
      key: 'college_admin_1',
      title: 'College Admin — Delhi Tech (INST-001)',
      subtitle: 'Manage admissions, upload batches, track intake for Delhi Institute of Tech',
      icon: Building2,
      role: 'College Administrator',
      badgeColor: 'border-blue-300 bg-blue-50/50 hover:border-blue-500',
    },
    {
      key: 'college_admin_2',
      title: 'College Admin — National Engg (INST-002)',
      subtitle: 'Manage admissions & verify records for National College of Engineering',
      icon: Building2,
      role: 'College Administrator',
      badgeColor: 'border-blue-300 bg-blue-50/50 hover:border-blue-500',
    },
    {
      key: 'compliance_officer',
      title: 'AICTE Compliance Officer',
      subtitle: 'Central regulatory oversight, cross-college duplicate detection & intake monitoring',
      icon: ShieldAlert,
      role: 'AICTE Compliance Officer',
      badgeColor: 'border-purple-300 bg-purple-50/50 hover:border-purple-500',
    },
    {
      key: 'verifier',
      title: 'Academic Record Verifier',
      subtitle: 'Consent-based background verification & signed QR credential authenticator',
      icon: SearchCheck,
      role: 'Credential Verifier',
      badgeColor: 'border-teal-300 bg-teal-50/50 hover:border-teal-500',
    },
  ];

  const handleSelectAccount = (key: string) => {
    setSelectedKey(key);
    setError(null);
    setStep('otp');
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await authService.verifyOtp(selectedKey, otp);
      onLoginSuccess(data.user);
      if (data.user.role === 'compliance_officer') {
        navigate('/compliance');
      } else if (data.user.role === 'verifier') {
        navigate('/verification');
      } else {
        navigate('/college-dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid demo OTP code. Use 123456');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Background Accent */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e3a8a_1px,transparent_1px)] [background-size:16px_16px] opacity-25" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <div className="inline-flex w-14 h-14 rounded-2xl bg-gradient-to-tr from-teal-500 to-blue-600 items-center justify-center shadow-lg shadow-teal-500/20 mb-3">
          <ShieldCheck className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl font-extrabold text-white tracking-tight">APAAR GUARDIAN</h2>
        <p className="text-sm text-slate-300 mt-1">Student Data Integrity & Verification Platform</p>
        <div className="inline-flex items-center space-x-1.5 bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-semibold px-3 py-1 rounded-full mt-3">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>DEMO MODE — Synthetic Data Simulation</span>
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-xl relative z-10">
        <div className="bg-white py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-100">
          {step === 'select' ? (
            <div>
              <div className="mb-5">
                <h3 className="text-base font-bold text-slate-900">Select Demo Persona</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Choose a pre-configured role to inspect tenant isolation and access privileges.
                </p>
              </div>

              <div className="space-y-3">
                {demoAccounts.map((account) => {
                  const Icon = account.icon;
                  return (
                    <button
                      key={account.key}
                      onClick={() => handleSelectAccount(account.key)}
                      className={`w-full text-left p-4 rounded-xl border-2 transition-all flex items-start space-x-4 group ${
                        selectedKey === account.key ? 'border-teal-600 bg-teal-50/50 shadow-xs' : account.badgeColor
                      }`}
                    >
                      <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center flex-shrink-0 mt-0.5 text-slate-700 group-hover:text-teal-600">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900 group-hover:text-teal-700">
                            {account.title}
                          </span>
                          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                            {account.role}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1 leading-relaxed">{account.subtitle}</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-1 transition mt-3" />
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <form onSubmit={handleVerifyOtp} className="space-y-5">
              <div>
                <button
                  type="button"
                  onClick={() => setStep('select')}
                  className="text-xs text-slate-500 hover:text-slate-800 font-medium mb-3 flex items-center space-x-1"
                >
                  <span>← Choose a different account</span>
                </button>
                <h3 className="text-base font-bold text-slate-900">Enter Demo OTP</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Two-factor authentication simulation. For local evaluation, use the prefilled code below.
                </p>
              </div>

              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                  6-Digit OTP Code
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    required
                    className="block w-full pl-10 pr-3 py-2.5 text-base font-mono tracking-widest border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
                  />
                </div>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-emerald-700 font-medium flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Demo OTP: <strong>123456</strong></span>
                  </span>
                  <button
                    type="button"
                    onClick={() => setOtp('123456')}
                    className="text-teal-600 hover:underline font-semibold"
                  >
                    Autofill 123456
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg text-xs font-bold text-white bg-teal-600 hover:bg-teal-500 shadow-md transition disabled:opacity-50"
              >
                <span>{loading ? 'Authenticating...' : 'Sign In to Workspace'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Notice: This platform is a functional prototype operating on synthetic data. Not officially affiliated with APAAR, AICTE, or government portals.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
