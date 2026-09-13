import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Executing analysis pipeline...',
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-12 text-slate-500 ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-sky-600 mb-3" />
      <p className="text-sm font-medium text-slate-700">{message}</p>
      <p className="text-xs text-slate-400 mt-1">Evaluating physical energy forms and lexical feature contributions</p>
    </div>
  );
};

