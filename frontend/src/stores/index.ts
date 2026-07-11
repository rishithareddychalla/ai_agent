/**
 * Global State Store – Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Task, AgentStep, LogEntry, BrowserUpdateEvent } from '@/types';

// ─── Auth Store ───────────────────────────────────────────

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) => {
        localStorage.setItem('webpilot_token', token);
        set({ user, token, isAuthenticated: true });
      },
      clearAuth: () => {
        localStorage.removeItem('webpilot_token');
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'webpilot-auth',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);

// ─── Active Task Store ────────────────────────────────────

interface ActiveTaskStore {
  // Current running task
  activeTask: Task | null;
  activeTaskId: number | null;
  
  // Execution state
  isRunning: boolean;
  isPlanReady: boolean;
  steps: AgentStep[];
  currentStepIndex: number;
  progress: number;  // 0-100
  
  // Real-time data
  logs: LogEntry[];
  browserState: BrowserUpdateEvent | null;
  extractedData: Record<string, unknown>;
  
  // Result
  taskSummary: string | null;
  recommendation: string | null;
  
  // Actions
  setActiveTask: (task: Task) => void;
  setSteps: (steps: AgentStep[]) => void;
  updateStep: (index: number, updates: Partial<AgentStep>) => void;
  setCurrentStep: (index: number) => void;
  setProgress: (pct: number) => void;
  addLog: (entry: LogEntry) => void;
  setBrowserState: (state: BrowserUpdateEvent) => void;
  setExtractedData: (data: Record<string, unknown>) => void;
  setResult: (summary: string, recommendation: string) => void;
  resetTask: () => void;
}

const initialActiveState = {
  activeTask: null,
  activeTaskId: null,
  isRunning: false,
  isPlanReady: false,
  steps: [],
  currentStepIndex: -1,
  progress: 0,
  logs: [],
  browserState: null,
  extractedData: {},
  taskSummary: null,
  recommendation: null,
};

export const useActiveTaskStore = create<ActiveTaskStore>((set) => ({
  ...initialActiveState,

  setActiveTask: (task) =>
    set({ activeTask: task, activeTaskId: task.id, isRunning: true }),

  setSteps: (steps) => set({ steps, isPlanReady: true }),

  updateStep: (index, updates) =>
    set((state) => ({
      steps: state.steps.map((s) =>
        s.index === index ? { ...s, ...updates } : s
      ),
    })),

  setCurrentStep: (index) => set({ currentStepIndex: index }),

  setProgress: (pct) => set({ progress: pct }),

  addLog: (entry) =>
    set((state) => ({
      logs: [...state.logs.slice(-499), entry],  // Keep last 500 logs
    })),

  setBrowserState: (browserState) => set({ browserState }),

  setExtractedData: (extractedData) => set({ extractedData }),

  setResult: (taskSummary, recommendation) =>
    set({ taskSummary, recommendation, isRunning: false, progress: 100 }),

  resetTask: () => set(initialActiveState),
}));

// ─── UI Store ─────────────────────────────────────────────

interface UIStore {
  sidebarCollapsed: boolean;
  theme: 'dark' | 'light';
  toggleSidebar: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      theme: 'dark',
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'webpilot-ui' }
  )
);
