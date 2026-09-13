import React from 'react';
import { AlertTriangle, CheckCircle, HelpCircle, ShieldAlert, Sparkles } from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '', size = 'md' }) => {
  let bg = 'bg-slate-100 text-slate-700 border-slate-200';
  let Icon = HelpCircle;
  let label = status;

  switch (status) {
    case 'CONSENSUS_SIF':
      bg = 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
      Icon = ShieldAlert;
      label = 'Consensus: SIF precursor';
      break;
    case 'CONSENSUS_NON_SIF':
      bg = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold';
      Icon = CheckCircle;
      label = 'Consensus: Non-SIF';
      break;
    case 'RULE_UNCERTAIN_ML_SIGNAL':
      bg = 'bg-amber-50 text-amber-700 border-amber-200 font-semibold';
      Icon = Sparkles;
      label = 'Human review required (ML signal)';
      break;
    case 'RULE_UNCERTAIN_NO_ML_SIGNAL':
      bg = 'bg-slate-100 text-slate-700 border-slate-200 font-medium';
      Icon = HelpCircle;
      label = 'Human review required';
      break;
    case 'DIRECT_DISAGREEMENT':
      bg = 'bg-purple-50 text-purple-700 border-purple-200 font-bold';
      Icon = AlertTriangle;
      label = 'Disagreement — Review required';
      break;
    default:
      bg = 'bg-slate-100 text-slate-700 border-slate-200';
      Icon = HelpCircle;
      label = status || 'Unknown';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border ${bg} ${sizeClasses[size]} ${className}`}
    >
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{label}</span>
    </span>
  );
};

