/**
 * LogViewer – Real-time scrolling log display
 */

import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, AlertCircle, CheckCircle, Info, AlertTriangle, Clock } from 'lucide-react';
import type { LogEntry } from '@/types';
import { format } from 'date-fns';

const LOG_ICONS: Record<string, React.ElementType> = {
  info: Info,
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  debug: Terminal,
};

interface LogViewerProps {
  logs: LogEntry[];
  maxHeight?: number;
  autoScroll?: boolean;
}

export function LogViewer({ logs, maxHeight = 300, autoScroll = true }: LogViewerProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [logs.length, autoScroll]);

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-surface-border">
        <Terminal size={14} className="text-brand-400" />
        <h3 className="text-sm font-semibold text-white">Execution Logs</h3>
        <span className="ml-auto text-xs text-slate-500 font-mono">{logs.length} entries</span>
      </div>

      {/* Log List */}
      <div
        className="overflow-y-auto p-3 space-y-0.5 font-mono"
        style={{ maxHeight }}
      >
        {logs.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-slate-600">
            <div className="text-center">
              <Terminal size={24} className="mx-auto mb-2 opacity-30" />
              <p className="text-xs">Logs will appear here when the task starts</p>
            </div>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {logs.map((log, i) => {
              const Icon = LOG_ICONS[log.level] || Info;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -4 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`log-entry ${log.level}`}
                >
                  <Icon size={11} className={`mt-0.5 flex-shrink-0 ${
                    log.level === 'success' ? 'text-emerald-400' :
                    log.level === 'error' ? 'text-red-400' :
                    log.level === 'warning' ? 'text-amber-400' :
                    'text-brand-400'
                  }`} />
                  <span className="text-slate-600 flex-shrink-0">
                    {format(new Date(log.timestamp), 'HH:mm:ss.SSS')}
                  </span>
                  <span className={`flex-1 ${
                    log.level === 'success' ? 'text-emerald-300' :
                    log.level === 'error' ? 'text-red-300' :
                    log.level === 'warning' ? 'text-amber-300' :
                    'text-slate-300'
                  }`}>
                    {log.message}
                  </span>
                  {log.duration_ms && (
                    <span className="flex-shrink-0 text-slate-600 flex items-center gap-1">
                      <Clock size={9} />
                      {log.duration_ms.toFixed(0)}ms
                    </span>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
