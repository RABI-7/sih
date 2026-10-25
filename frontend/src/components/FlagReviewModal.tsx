import React, { useState } from 'react';
import { X, ShieldAlert, Check } from 'lucide-react';
import { ValidationFlag } from '../types';
import { complianceService } from '../services/api';

interface FlagReviewModalProps {
  flag: ValidationFlag | null;
  onClose: () => void;
  onFlagUpdated: (updated: ValidationFlag) => void;
}

export const FlagReviewModal: React.FC<FlagReviewModalProps> = ({ flag, onClose, onFlagUpdated }) => {
  const [newStatus, setNewStatus] = useState<string>(flag?.status || 'under_review');
  const [reviewNotes, setReviewNotes] = useState<string>(flag?.review_notes || '');
  const [loading, setLoading] = useState(false);

  if (!flag) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const updated = await complianceService.updateFlagStatus(flag.id, newStatus, reviewNotes);
      onFlagUpdated(updated);
      onClose();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update flag status');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden">
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold">Review Compliance Flag #{flag.id}</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
            <p className="font-semibold text-slate-800">{flag.rule_code}</p>
            <p className="text-slate-600 mt-1">{flag.explanation}</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Review Status Decision
            </label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
            >
              <option value="open">Open (Unresolved)</option>
              <option value="under_review">Under Active Review</option>
              <option value="resolved">Resolved (Approved / Rectified)</option>
              <option value="false_positive">Mark as False Positive</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
              Officer Audit Notes
            </label>
            <textarea
              rows={3}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Provide justification or verified documentation reference..."
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-500 rounded-lg shadow-sm transition disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{loading ? 'Saving...' : 'Update & Log Audit Trail'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
