import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
  colorScheme?: 'blue' | 'teal' | 'amber' | 'rose' | 'purple';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  colorScheme = 'blue',
}) => {
  const getStyles = () => {
    switch (colorScheme) {
      case 'teal':
        return {
          iconBg: 'bg-teal-50 text-teal-700',
          border: 'border-slate-200 hover:border-teal-300',
          badge: 'bg-teal-100 text-teal-800',
        };
      case 'amber':
        return {
          iconBg: 'bg-amber-50 text-amber-700',
          border: 'border-slate-200 hover:border-amber-300',
          badge: 'bg-amber-100 text-amber-800',
        };
      case 'rose':
        return {
          iconBg: 'bg-rose-50 text-rose-700',
          border: 'border-slate-200 hover:border-rose-300',
          badge: 'bg-rose-100 text-rose-800',
        };
      case 'purple':
        return {
          iconBg: 'bg-purple-50 text-purple-700',
          border: 'border-slate-200 hover:border-purple-300',
          badge: 'bg-purple-100 text-purple-800',
        };
      default:
        return {
          iconBg: 'bg-blue-50 text-blue-700',
          border: 'border-slate-200 hover:border-blue-300',
          badge: 'bg-blue-100 text-blue-800',
        };
    }
  };

  const styles = getStyles();

  return (
    <div className={`bg-white rounded-xl border ${styles.border} p-5 shadow-sm transition hover:shadow-md`}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
        <div className={`w-9 h-9 rounded-lg ${styles.iconBg} flex items-center justify-center`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold text-slate-900">{value}</span>
        {badge && (
          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${styles.badge}`}>
            {badge}
          </span>
        )}
      </div>

      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  );
};
