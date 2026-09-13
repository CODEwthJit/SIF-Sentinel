import React from 'react';

interface PriorityBadgeProps {
  priority: string;
  className?: string;
  size?: 'sm' | 'md';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, className = '', size = 'md' }) => {
  let color = 'bg-slate-100 text-slate-700 border-slate-200';

  switch (priority) {
    case 'HIGH':
      color = 'bg-red-100 text-red-800 border-red-300 font-bold';
      break;
    case 'MEDIUM':
      color = 'bg-amber-100 text-amber-800 border-amber-300 font-semibold';
      break;
    case 'LOW':
      color = 'bg-emerald-100 text-emerald-800 border-emerald-300 font-medium';
      break;
  }

  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1';

  return (
    <span className={`inline-flex items-center rounded border tracking-wide uppercase font-mono ${color} ${sizeClasses} ${className}`}>
      {priority} PRIORITY
    </span>
  );
};

