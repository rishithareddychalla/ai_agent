/**
 * API Service Layer – All backend HTTP calls with axios
 */

import axios from 'axios';
import type {
  LoginResponse, User, UserSettings,
  Task, Report, AnalyticsSummary, DailyTaskCount, SiteVisit,
} from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8001';

// ─── Axios Instance ───────────────────────────────────────

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Auth token injection
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('webpilot_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Auth ─────────────────────────────────────────────────

export const authApi = {
  register: async (email: string, password: string, fullName?: string): Promise<LoginResponse> => {
    const { data } = await api.post('/auth/register', { email, password, full_name: fullName });
    return data;
  },

  login: async (email: string, password: string): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const { data } = await api.post('/auth/login', formData);
    return data;
  },

  getMe: async (): Promise<User> => {
    const { data } = await api.get('/auth/me');
    return data;
  },
};

// ─── Tasks ────────────────────────────────────────────────

export const tasksApi = {
  createTask: async (prompt: string, browser?: string, headless?: boolean): Promise<Task> => {
    const { data } = await api.post('/tasks', { prompt, browser, headless });
    return data;
  },

  listTasks: async (skip = 0, limit = 50): Promise<Task[]> => {
    const { data } = await api.get('/tasks', { params: { skip, limit } });
    return data;
  },

  getTask: async (taskId: number): Promise<Task> => {
    const { data } = await api.get(`/tasks/${taskId}`);
    return data;
  },

  cancelTask: async (taskId: number): Promise<void> => {
    await api.delete(`/tasks/${taskId}`);
  },
};

// ─── Reports ─────────────────────────────────────────────

export const reportsApi = {
  listReports: async (taskId: number): Promise<Report[]> => {
    const { data } = await api.get(`/reports/${taskId}`);
    return data;
  },

  getDownloadUrl: (taskId: number, format: 'pdf' | 'csv' | 'json'): string => {
    const token = localStorage.getItem('webpilot_token');
    return `${API_BASE}/reports/${taskId}/download/${format}?token=${token}`;
  },

  downloadReport: async (taskId: number, format: 'pdf' | 'csv' | 'json'): Promise<void> => {
    const token = localStorage.getItem('webpilot_token');
    const response = await api.get(`/reports/${taskId}/download/${format}`, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` },
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `webpilot_task_${taskId}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

// ─── Analytics ────────────────────────────────────────────

export const analyticsApi = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const { data } = await api.get('/analytics/summary');
    return data;
  },

  getDailyTasks: async (days = 30): Promise<DailyTaskCount[]> => {
    const { data } = await api.get('/analytics/daily', { params: { days } });
    return data;
  },

  getTopSites: async (limit = 10): Promise<SiteVisit[]> => {
    const { data } = await api.get('/analytics/sites', { params: { limit } });
    return data;
  },

  getExecutionTimes: async () => {
    const { data } = await api.get('/analytics/execution-times');
    return data;
  },
};

// ─── Settings ─────────────────────────────────────────────

export const settingsApi = {
  getSettings: async (): Promise<UserSettings> => {
    const { data } = await api.get('/settings');
    return data;
  },

  updateSettings: async (settings: Partial<UserSettings>): Promise<UserSettings> => {
    const { data } = await api.put('/settings', settings);
    return data.settings;
  },
};

// ─── WebSocket ────────────────────────────────────────────

export const createTaskWebSocket = (taskId: number): WebSocket => {
  const token = localStorage.getItem('webpilot_token') || '';
  const wsUrl = `${WS_BASE}/tasks/ws/${taskId}?token=${token}`;
  return new WebSocket(wsUrl);
};

export const createBrowserWebSocket = (taskId: number): WebSocket => {
  const token = localStorage.getItem('webpilot_token') || '';
  const wsUrl = `${WS_BASE}/browser/ws/live/${taskId}?token=${token}`;
  return new WebSocket(wsUrl);
};

export default api;
