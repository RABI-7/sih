import React from 'react';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

interface RiskBadgeProps {
  score: number;
  level?: string;
  showIcon?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score, level, showIcon = true }) => {
  let computedLevel = level;
  if (!computedLevel) {
    if (score < 20) computedLevel = 'Low';
    else if (score < 50) computedLevel = 'Moderate';
    else if (score < 75) computedLevel = 'High';
    else computedLevel = 'Critical';
  }

  const getStyle = () => {
    switch (computedLevel) {
      case 'Critical':
        return {
          bg: 'bg-red-50 text-red-700 border-red-200',
          dot: 'bg-red-500',
          icon: ShieldAlert,
        };
      case 'High':
        return {
          bg: 'bg-orange-50 text-orange-700 border-orange-200',
          dot: 'bg-orange-500',
          icon: ShieldAlert,
        };
      case 'Moderate':
        return {
          bg: 'bg-amber-50 text-amber-700 border-amber-200',
          dot: 'bg-amber-500',
          icon: Shield,
        };
      default:
        return {
          bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          dot: 'bg-emerald-500',
          icon: ShieldCheck,
        };
    }
  };

  const style = getStyle();
  const Icon = style.icon;

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold ${style.bg}`}>
      {showIcon && <Icon className="w-3.5 h-3.5" />}
      <span>{computedLevel}</span>
      <span className="font-mono text-[11px] opacity-80">({Math.round(score)})</span>
    </span>
  );
};
