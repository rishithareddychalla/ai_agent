/**
 * ExecutionPlan – Animated step-by-step plan display
 */

import { motion, AnimatePresence } from 'framer-motion';
import {
  Globe, Search, MousePointer, Type, ArrowDown, Clock,
  Download, BarChart2, AlignLeft, Filter, Navigation,
  Layers, CheckCircle2, XCircle, Loader2, Circle, Zap
} from 'lucide-react';
import type { AgentStep, ActionType } from '@/types';

const ACTION_ICONS: Record<ActionType, React.ElementType> = {
  navigate: Globe,
  search: Search,
  click: MousePointer,
  type: Type,
  scroll: ArrowDown,
  wait: Clock,
  extract: Layers,
  screenshot: Zap,
  download: Download,
  compare: BarChart2,
  summarize: AlignLeft,
  filter: Filter,
  hover: MousePointer,
  select: Filter,
  new_tab: Navigation,
  close_tab: XCircle,
  back: Navigation,
  refresh: Loader2,
  evaluate: Zap,
};

const ACTION_COLORS: Record<ActionType, string> = {
  navigate: 'text-blue-400',
  search: 'text-purple-400',
  click: 'text-pink-400',
  type: 'text-emerald-400',
  scroll: 'text-slate-400',
  wait: 'text-amber-400',
  extract: 'text-cyan-400',
  screenshot: 'text-violet-400',
  download: 'text-green-400',
  compare: 'text-orange-400',
  summarize: 'text-indigo-400',
  filter: 'text-teal-400',
  hover: 'text-pink-300',
  select: 'text-teal-300',
  new_tab: 'text-blue-300',
  close_tab: 'text-red-400',
  back: 'text-slate-400',
  refresh: 'text-yellow-400',
  evaluate: 'text-violet-300',
};

interface ExecutionPlanProps {
  steps: AgentStep[];
  currentStepIndex?: number;
  taskUnderstanding?: string;
  goal?: string;
  isPlanning?: boolean;
}

export function ExecutionPlan({
  steps,
  currentStepIndex = -1,
  taskUnderstanding,
  goal,
  isPlanning = false,
}: ExecutionPlanProps) {
  if (isPlanning) {
    return (
      <div className="glass-card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="relative">
            <div className="w-8 h-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center">
              <Loader2 size={16} className="text-brand-400 animate-spin" />
            </div>
          </div>
          <div>
            <h3 className="text-white font-semibold text-sm">AI is Planning</h3>
            <p className="text-slate-500 text-xs">Analyzing your request...</p>
          </div>
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full shimmer flex-shrink-0" />
              <div className={`h-4 rounded shimmer flex-1 ${i % 2 === 0 ? 'max-w-48' : 'max-w-72'}`} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (steps.length === 0) return null;

  const completedCount = steps.filter((s) => s.status === 'completed').length;
  const progress = steps.length > 0 ? (completedCount / steps.length) * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold text-sm">Execution Plan</h3>
          {goal && <p className="text-slate-400 text-xs mt-0.5">{goal}</p>}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{completedCount}/{steps.length}</span>
          <div className="w-16">
            <div className="progress-bar">
              <motion.div
                className="progress-bar-fill"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* AI Understanding */}
      {taskUnderstanding && (
        <div className="mb-4 p-3 rounded-xl bg-brand-500/5 border border-brand-500/15">
          <p className="text-xs text-slate-400 leading-relaxed">{taskUnderstanding}</p>
        </div>
      )}

      {/* Steps List */}
      <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
        <AnimatePresence>
          {steps.map((step, i) => {
            const Icon = ACTION_ICONS[step.action] || Globe;
            const iconColor = ACTION_COLORS[step.action] || 'text-slate-400';
            const isActive = step.index === currentStepIndex;
            const isCompleted = step.status === 'completed';
            const isFailed = step.status === 'failed';

            return (
              <motion.div
                key={step.index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`flex items-start gap-3 p-2.5 rounded-xl transition-all ${
                  isActive ? 'bg-brand-500/10 border border-brand-500/20' :
                  isCompleted ? 'bg-emerald-500/5' :
                  isFailed ? 'bg-red-500/5' : ''
                }`}
              >
                {/* Status dot */}
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted ? (
                    <CheckCircle2 size={14} className="text-emerald-400" />
                  ) : isFailed ? (
                    <XCircle size={14} className="text-red-400" />
                  ) : isActive ? (
                    <Loader2 size={14} className="text-brand-400 animate-spin" />
                  ) : (
                    <Circle size={14} className="text-slate-600" />
                  )}
                </div>

                {/* Icon */}
                <div className={`flex-shrink-0 ${iconColor}`}>
                  <Icon size={13} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-medium truncate ${
                    isCompleted ? 'text-slate-400 line-through' :
                    isActive ? 'text-white' :
                    isFailed ? 'text-red-400' :
                    'text-slate-400'
                  }`}>
                    {step.description}
                  </p>
                  {step.url && (
                    <p className="text-[10px] text-slate-600 truncate mt-0.5">{step.url}</p>
                  )}
                  {step.duration_ms && (
                    <p className="text-[10px] text-slate-500 mt-0.5">{step.duration_ms.toFixed(0)}ms</p>
                  )}
                </div>

                {/* Action label */}
                <span className={`flex-shrink-0 text-[10px] font-mono uppercase tracking-wider ${iconColor} opacity-70`}>
                  {step.action}
                </span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
