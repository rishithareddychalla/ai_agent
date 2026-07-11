/**
 * Task History Page – Searchable, filterable task list
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Search, Filter, Clock, Globe, CheckCircle2, XCircle, Loader2, RefreshCw, Eye, Trash2 } from 'lucide-react';
import { tasksApi } from '@/services/api';
import { formatDistanceToNow, format } from 'date-fns';
import type { Task, TaskStatus } from '@/types';

const STATUS_CONFIG: Record<TaskStatus, { label: string; className: string; Icon: React.ElementType }> = {
  pending: { label: 'Pending', className: 'badge-pending', Icon: Clock },
  planning: { label: 'Planning', className: 'badge-info', Icon: Loader2 },
  running: { label: 'Running', className: 'badge-running', Icon: Loader2 },
  paused: { label: 'Paused', className: 'badge-warning', Icon: Clock },
  completed: { label: 'Completed', className: 'badge-success', Icon: CheckCircle2 },
  failed: { label: 'Failed', className: 'badge-error', Icon: XCircle },
  cancelled: { label: 'Cancelled', className: 'badge-pending', Icon: XCircle },
};

export function TaskHistoryPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');

  const { data: tasks = [], isLoading, refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.listTasks(0, 100),
    refetchInterval: 10000,
  });

  const filtered = tasks.filter((task) => {
    const matchesSearch = task.prompt.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex-1 overflow-auto p-6 page-enter">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Task History</h1>
          <p className="text-slate-400 text-sm">{tasks.length} total tasks</p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-ghost flex items-center gap-2 text-sm"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-9 text-sm"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-slate-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TaskStatus | 'all')}
            className="input-field text-sm w-auto pr-8"
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
            <option value="pending">Pending</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Task List */}
      {isLoading ? (
        <div className="space-y-3">
          {[1,2,3].map((i) => (
            <div key={i} className="glass-card p-5 h-24 shimmer" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto mb-4">
            <Clock size={28} className="text-brand-500/40" />
          </div>
          <h3 className="text-white font-semibold mb-2">No tasks found</h3>
          <p className="text-slate-500 text-sm">
            {tasks.length === 0 ? 'Run your first task from the Dashboard' : 'Try adjusting your search filters'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((task, i) => {
            const statusConfig = STATUS_CONFIG[task.status];
            const isActive = ['running', 'planning'].includes(task.status);

            return (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`glass-card p-4 hover:neon-border transition-all group ${isActive ? 'border-brand-500/30' : ''}`}
              >
                <div className="flex items-start gap-4">
                  {/* Task # */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-surface-50 flex items-center justify-center text-xs font-mono text-slate-500">
                    {task.id}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-white text-sm font-medium truncate">{task.prompt}</p>
                      <span className={`badge ${statusConfig.className} flex-shrink-0 flex items-center gap-1`}>
                        <statusConfig.Icon size={10} className={isActive ? 'animate-spin' : ''} />
                        {statusConfig.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <Clock size={11} />
                        {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                      </span>
                      {task.execution_time_ms && (
                        <span className="flex items-center gap-1">
                          ⏱ {(task.execution_time_ms / 1000).toFixed(1)}s
                        </span>
                      )}
                      {task.success_rate !== null && task.success_rate !== undefined && (
                        <span className={task.success_rate >= 0.8 ? 'text-emerald-400' : 'text-amber-400'}>
                          {Math.round(task.success_rate * 100)}% success
                        </span>
                      )}
                      {task.websites_visited && task.websites_visited.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Globe size={11} />
                          {task.websites_visited.length} sites
                        </span>
                      )}
                    </div>

                    {task.result_summary && (
                      <p className="text-slate-400 text-xs mt-2 line-clamp-1">{task.result_summary}</p>
                    )}
                    {task.error_message && (
                      <p className="text-red-400 text-xs mt-1 line-clamp-1">{task.error_message}</p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                    <Link
                      to={`/reports?task=${task.id}`}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
                      title="View reports"
                    >
                      <Eye size={13} />
                    </Link>
                    <button
                      onClick={() => tasksApi.cancelTask(task.id).catch(() => {})}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                      title="Delete task"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                {/* Progress bar for running tasks */}
                {isActive && task.total_steps > 0 && (
                  <div className="mt-3">
                    <div className="progress-bar">
                      <motion.div
                        className="progress-bar-fill"
                        animate={{
                          width: `${(task.current_step / task.total_steps) * 100}%`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-600 mt-1">
                      Step {task.current_step}/{task.total_steps}
                    </p>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
