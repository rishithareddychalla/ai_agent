/**
 * Reports Page – Browse and download task reports
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { FileText, Download, Search, File, FileSpreadsheet, FileCode, Clock } from 'lucide-react';
import { tasksApi, reportsApi } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import type { Report } from '@/types';

const FORMAT_ICONS: Record<string, React.ElementType> = {
  pdf: FileText,
  csv: FileSpreadsheet,
  json: FileCode,
};

const FORMAT_COLORS: Record<string, string> = {
  pdf: 'text-red-400 bg-red-500/10 border-red-500/20',
  csv: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  json: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
};

export function ReportsPage() {
  const [search, setSearch] = useState('');
  const [downloading, setDownloading] = useState<string | null>(null);

  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks-with-reports'],
    queryFn: () => tasksApi.listTasks(0, 100),
  });

  const completedTasks = tasks.filter(
    (t) => t.status === 'completed' && (search === '' || t.prompt.toLowerCase().includes(search.toLowerCase()))
  );

  const handleDownload = async (taskId: number, format: 'pdf' | 'csv' | 'json') => {
    const key = `${taskId}-${format}`;
    setDownloading(key);
    try {
      await reportsApi.downloadReport(taskId, format);
      toast.success(`${format.toUpperCase()} downloaded!`);
    } catch (error) {
      toast.error('Download failed');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="flex-1 overflow-auto p-6 page-enter">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">Reports</h1>
        <p className="text-slate-400 text-sm">Download task execution reports in PDF, CSV, or JSON format</p>
      </div>

      {/* Search */}
      <div className="relative max-w-md mb-6">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          placeholder="Search completed tasks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-9 text-sm"
        />
      </div>

      {/* Reports Grid */}
      {completedTasks.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto mb-4">
            <FileText size={28} className="text-brand-500/40" />
          </div>
          <h3 className="text-white font-semibold mb-2">No reports available</h3>
          <p className="text-slate-500 text-sm">Complete a task to generate downloadable reports</p>
        </div>
      ) : (
        <div className="space-y-4">
          {completedTasks.map((task, i) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card p-5"
            >
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-slate-600">#{task.id}</span>
                    <span className="badge badge-success">Completed</span>
                  </div>
                  <p className="text-white text-sm font-medium">{task.prompt}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                    </span>
                    {task.execution_time_ms && (
                      <span>⏱ {(task.execution_time_ms / 1000).toFixed(1)}s</span>
                    )}
                    {task.success_rate !== undefined && task.success_rate !== null && (
                      <span className="text-emerald-400">
                        {Math.round(task.success_rate * 100)}% success
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Summary */}
              {task.result_summary && (
                <p className="text-slate-400 text-xs mb-4 line-clamp-2">{task.result_summary}</p>
              )}

              {/* Download Buttons */}
              <div className="flex items-center gap-2 flex-wrap">
                {(['pdf', 'csv', 'json'] as const).map((fmt) => {
                  const Icon = FORMAT_ICONS[fmt];
                  const colorClass = FORMAT_COLORS[fmt];
                  const key = `${task.id}-${fmt}`;
                  const isLoading = downloading === key;

                  return (
                    <motion.button
                      key={fmt}
                      whileTap={{ scale: 0.97 }}
                      onClick={() => handleDownload(task.id, fmt)}
                      disabled={isLoading}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-xs font-semibold uppercase tracking-wide transition-all ${colorClass} hover:opacity-80 disabled:opacity-50`}
                    >
                      {isLoading ? (
                        <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Icon size={13} />
                      )}
                      {fmt}
                      <Download size={11} />
                    </motion.button>
                  );
                })}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
