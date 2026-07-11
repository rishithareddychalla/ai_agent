/**
 * ProgressBar – Animated progress indicator
 */

import { motion } from 'framer-motion';
import { Loader2, CheckCircle2 } from 'lucide-react';

interface ProgressBarProps {
  progress: number;  // 0-100
  completed?: number;
  total?: number;
  label?: string;
  isComplete?: boolean;
}

export function ProgressBar({
  progress,
  completed,
  total,
  label,
  isComplete = false,
}: ProgressBarProps) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isComplete ? (
            <CheckCircle2 size={14} className="text-emerald-400" />
          ) : (
            <Loader2 size={14} className="text-brand-400 animate-spin" />
          )}
          <span className="text-sm font-medium text-white">
            {label || (isComplete ? 'Completed' : 'Executing...')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {completed !== undefined && total !== undefined && (
            <span className="text-xs text-slate-500">
              {completed} / {total} steps
            </span>
          )}
          <span className={`text-sm font-bold ${
            isComplete ? 'text-emerald-400' : 'text-brand-400'
          }`}>
            {Math.round(progress)}%
          </span>
        </div>
      </div>

      <div className="progress-bar">
        <motion.div
          className="progress-bar-fill"
          style={{
            background: isComplete
              ? 'linear-gradient(90deg, #10b981, #34d399)'
              : 'linear-gradient(90deg, #6366f1, #a78bfa)',
            boxShadow: isComplete
              ? '0 0 10px rgba(16, 185, 129, 0.5)'
              : '0 0 10px rgba(99, 102, 241, 0.5)',
          }}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}
