/**
 * Dashboard Page – Main workspace for running and monitoring AI tasks
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import {
  Bot, CheckCircle2, XCircle, Globe, Trophy, Clock, RefreshCw
} from 'lucide-react';

import { tasksApi, createTaskWebSocket } from '@/services/api';
import { useActiveTaskStore, useAuthStore } from '@/stores';
import { TaskInput } from '@/components/TaskInput';
import { BrowserPreview } from '@/components/BrowserPreview';
import { ExecutionPlan } from '@/components/ExecutionPlan';
import { LogViewer } from '@/components/LogViewer';
import { ProgressBar } from '@/components/ProgressBar';
import type { TaskEvent, AgentStep, LogEntry } from '@/types';

export function DashboardPage() {
  const { user } = useAuthStore();
  const {
    activeTask, isRunning, isPlanReady, steps, currentStepIndex,
    progress, logs, browserState, taskSummary, recommendation,
    setActiveTask, setSteps, updateStep, setCurrentStep, setProgress,
    addLog, setBrowserState, setResult, resetTask,
  } = useActiveTaskStore();

  const wsRef = useRef<WebSocket | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const activeTaskIdRef = useRef<number | null>(null);
  const pollIntervalRef = useRef<any>(null);

  const clearPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const handleTaskSubmit = useCallback(async (prompt: string) => {
    try {
      resetTask();
      clearPolling();
      setIsPlanning(true);

      const task = await tasksApi.createTask(prompt);
      setActiveTask(task);
      activeTaskIdRef.current = task.id;

      toast.loading(`Task #${task.id} created`, { id: 'task-create' });

      // Connect WebSocket for real-time updates
      const ws = createTaskWebSocket(task.id);
      wsRef.current = ws;

      ws.onopen = () => {
        toast.success(`Connected to task #${task.id}`, { id: 'task-create' });
      };

      ws.onmessage = (event) => {
        try {
          const msg: TaskEvent = JSON.parse(event.data);
          handleTaskEvent(msg);
        } catch (err) {
          console.error('WS parse error:', err);
        }
      };

      ws.onerror = () => {
        toast.error('WebSocket connection error');
      };

      ws.onclose = () => {
        setIsPlanning(false);
        // Start polling fallback if the task is still supposed to be running
        const taskId = activeTaskIdRef.current;
        if (taskId) {
          clearPolling();
          pollIntervalRef.current = setInterval(async () => {
            try {
              const currentTask = await tasksApi.getTask(taskId);
              if (currentTask.status === 'completed') {
                clearPolling();
                setResult(currentTask.result_summary || '', currentTask.recommendation || '');
                addLog({
                  timestamp: new Date().toISOString(),
                  level: 'success',
                  message: '🎉 Task completed successfully! (restored connection)',
                });
                toast.success('Task completed!');
              } else if (currentTask.status === 'failed') {
                clearPolling();
                setResult('', '');
                addLog({
                  timestamp: new Date().toISOString(),
                  level: 'error',
                  message: `❌ Task failed: ${currentTask.error_message || 'Unknown error'}`,
                });
                toast.error(currentTask.error_message || 'Task failed');
                useActiveTaskStore.setState({ isRunning: false });
              } else if (currentTask.status === 'cancelled') {
                clearPolling();
                addLog({
                  timestamp: new Date().toISOString(),
                  level: 'warning',
                  message: '⚠️ Task cancelled.',
                });
                toast.error('Task cancelled');
                useActiveTaskStore.setState({ isRunning: false });
              }
            } catch (err) {
              console.error('Polling error:', err);
            }
          }, 3000);
        }
      };

    } catch (error: any) {
      setIsPlanning(false);
      toast.error(error?.response?.data?.detail || 'Failed to create task');
    }
  }, []);

  const handleTaskEvent = useCallback((event: TaskEvent) => {
    const { type, data, timestamp } = event;

    const logEntry: LogEntry = {
      timestamp,
      level: 'info',
      message: '',
    };

    switch (type) {
      case 'planning':
        setIsPlanning(true);
        addLog({ ...logEntry, message: '🧠 AI is planning...', level: 'info' });
        break;

      case 'plan_ready':
        setIsPlanning(false);
        const planSteps = (data.steps as AgentStep[]).map((s) => ({
          ...s,
          status: 'pending' as const,
        }));
        setSteps(planSteps);
        addLog({
          ...logEntry,
          message: `✅ Plan ready: ${planSteps.length} steps`,
          level: 'success',
        });
        break;

      case 'step_start':
        const startIdx = data.step_index as number;
        updateStep(startIdx, { status: 'running' });
        setCurrentStep(startIdx);
        addLog({
          ...logEntry,
          message: `▶ Step ${startIdx + 1}: ${data.description}`,
          level: 'info',
          step_index: startIdx,
          action: data.action as string,
        });
        break;

      case 'step_complete':
        const doneIdx = data.step_index as number;
        updateStep(doneIdx, {
          status: 'completed',
          duration_ms: data.duration_ms as number,
          result: data.result,
        });
        addLog({
          ...logEntry,
          message: `✓ ${data.description}`,
          level: 'success',
          duration_ms: data.duration_ms as number,
          url: data.url as string,
        });
        break;

      case 'step_failed':
        const failIdx = data.step_index as number;
        updateStep(failIdx, {
          status: 'failed',
          error: data.error as string,
        });
        addLog({
          ...logEntry,
          message: `✗ Step ${failIdx + 1} failed: ${data.error}`,
          level: 'error',
        });
        break;

      case 'step_recovery':
        addLog({
          ...logEntry,
          message: `🔄 ${data.message}`,
          level: 'warning',
        });
        break;

      case 'log':
        addLog({
          ...logEntry,
          message: data.message as string,
          level: (data.level as LogEntry['level']) || 'info',
        });
        break;

      case 'browser_update':
        setBrowserState({
          screenshot: data.screenshot as string,
          url: data.url as string,
          title: data.title as string,
        });
        break;

      case 'progress':
        setProgress(data.pct as number);
        break;

      case 'complete':
        const summary = data.summary as string;
        const rec = data.recommendation as string;
        setResult(summary, rec);
        addLog({
          ...logEntry,
          message: '🎉 Task completed successfully!',
          level: 'success',
        });
        toast.success('Task completed!');
        wsRef.current?.close();
        break;

      case 'error':
        addLog({
          ...logEntry,
          message: `❌ Error: ${data.message}`,
          level: 'error',
        });
        toast.error(data.message as string || 'Task failed');
        wsRef.current?.close();
        break;
    }
  }, []);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      clearPolling();
    };
  }, []);

  const currentStep = steps[currentStepIndex];

  return (
    <div className="flex-1 overflow-auto p-6 page-enter">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">
          Welcome back, {user?.full_name || user?.email?.split('@')[0]} 👋
        </h1>
        <p className="text-slate-400 text-sm">
          Describe a browser task in plain English and WebPilot AI will execute it autonomously.
        </p>
      </div>

      {/* Task Input */}
      <div className="mb-6">
        <TaskInput onSubmit={handleTaskSubmit} isRunning={isRunning} />
      </div>

      {/* Running task progress */}
      <AnimatePresence>
        {(isRunning || progress > 0) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6"
          >
            <ProgressBar
              progress={progress}
              completed={steps.filter((s) => s.status === 'completed').length}
              total={steps.length}
              isComplete={!isRunning && progress === 100}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Left: Browser Preview */}
        <div className="space-y-4">
          <BrowserPreview
            browserState={browserState}
            isConnected={isRunning}
            isRunning={isRunning}
            currentAction={currentStep?.description}
          />

          {/* Result card */}
          <AnimatePresence>
            {taskSummary && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Trophy size={16} className="text-amber-400" />
                  <h3 className="text-white font-semibold text-sm">Task Result</h3>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed mb-4">{taskSummary}</p>
                {recommendation && (
                  <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                    <p className="text-xs font-medium text-emerald-400 mb-1">💡 AI Recommendation</p>
                    <p className="text-slate-300 text-sm">{recommendation}</p>
                  </div>
                )}
                <div className="flex items-center gap-3 mt-4">
                  {activeTask && ['pdf', 'csv', 'json'].map((fmt) => (
                    <a
                      key={fmt}
                      href={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/reports/${activeTask.id}/download/${fmt}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-ghost text-xs flex items-center gap-1"
                    >
                      ↓ {fmt.toUpperCase()}
                    </a>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right: Execution Plan + Logs */}
        <div className="space-y-4">
          <ExecutionPlan
            steps={steps}
            currentStepIndex={currentStepIndex}
            isPlanning={isPlanning}
          />

          <LogViewer
            logs={logs}
            maxHeight={300}
            autoScroll
          />
        </div>
      </div>

      {/* Idle state / stats when no task running */}
      {!isRunning && !isPlanReady && logs.length === 0 && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Globe, label: 'Websites Supported', value: '100+', color: 'brand' },
            { icon: Clock, label: 'Avg Task Duration', value: '< 2 min', color: 'violet' },
            { icon: CheckCircle2, label: 'Recovery Strategies', value: '5 layers', color: 'emerald' },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-5 text-center"
            >
              <div className={`w-10 h-10 rounded-xl bg-${stat.color}-500/10 border border-${stat.color}-500/20 flex items-center justify-center mx-auto mb-3`}>
                <stat.icon size={20} className={`text-${stat.color}-400`} />
              </div>
              <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
              <p className="text-slate-500 text-xs">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
