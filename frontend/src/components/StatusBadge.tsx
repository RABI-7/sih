import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Clock } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const norm = status.toLowerCase();

  if (norm === 'valid' || norm === 'accepted') {
    return (
      <span className="inline-flex items-center space-x-1 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium px-2.5 py-0.5 rounded-full">
        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        <span>Valid</span>
      </span>
    );
  }

  if (norm === 'warning' || norm === 'under_review' || norm === 'near capacity') {
    return (
      <span className="inline-flex items-center space-x-1 bg-amber-50 text-amber-700 border border-amber-200 text-xs font-medium px-2.5 py-0.5 rounded-full">
        <AlertTriangle className="w-3 h-3 text-amber-600" />
        <span>Review Required</span>
      </span>
    );
  }

  if (norm === 'invalid' || norm === 'rejected' || norm === 'over-intake') {
    return (
      <span className="inline-flex items-center space-x-1 bg-rose-50 text-rose-700 border border-rose-200 text-xs font-medium px-2.5 py-0.5 rounded-full">
        <XCircle className="w-3 h-3 text-rose-600" />
        <span>Invalid</span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center space-x-1 bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium px-2.5 py-0.5 rounded-full">
      <Clock className="w-3 h-3 text-slate-500" />
      <span className="capitalize">{status.replace('_', ' ')}</span>
    </span>
  );
};
