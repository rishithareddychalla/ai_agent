/**
 * TypeScript types for WebPilot AI
 */

// ─── Auth ─────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  settings: UserSettings;
}

export interface UserSettings {
  browser: 'chromium' | 'firefox' | 'edge';
  theme: 'dark' | 'light';
  ai_provider: 'gemini' | 'openai';
  download_folder: string;
  default_timeout: number;
  screenshot_frequency: number;
  retry_count: number;
  headless: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  email: string;
  full_name?: string;
}

// ─── Task ─────────────────────────────────────────────────

export type TaskStatus =
  | 'pending'
  | 'planning'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface Task {
  id: number;
  prompt: string;
  status: TaskStatus;
  current_step: number;
  total_steps: number;
  result_summary?: string;
  recommendation?: string;
  execution_time_ms?: number;
  success_rate?: number;
  websites_visited?: string[];
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

// ─── Agent Plan ───────────────────────────────────────────

export type ActionType =
  | 'navigate' | 'search' | 'click' | 'type' | 'scroll'
  | 'wait' | 'extract' | 'screenshot' | 'download' | 'compare'
  | 'summarize' | 'filter' | 'hover' | 'select' | 'new_tab'
  | 'close_tab' | 'back' | 'refresh' | 'evaluate';

export interface AgentStep {
  index: number;
  action: ActionType;
  description: string;
  url?: string;
  query?: string;
  selector?: string;
  value?: string;
  wait_ms?: number;
  scroll_direction?: string;
  extract_schema?: Record<string, string>;
  expected_result?: string;
  is_optional?: boolean;
  depends_on?: number[];
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  result?: unknown;
  error?: string;
  duration_ms?: number;
}

export interface ExecutionPlan {
  task_understanding: string;
  goal: string;
  approach: string;
  risk_level: 'low' | 'medium' | 'high';
  estimated_duration_ms?: number;
  notes?: string;
  steps: AgentStep[];
}

// ─── WebSocket Events ─────────────────────────────────────

export type EventType =
  | 'planning' | 'plan_ready' | 'step_start' | 'step_complete'
  | 'step_failed' | 'step_recovery' | 'log' | 'screenshot'
  | 'data_extracted' | 'browser_update' | 'complete' | 'error'
  | 'progress' | 'ping';

export interface TaskEvent {
  type: EventType;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface BrowserUpdateEvent {
  screenshot: string;  // base64
  url: string;
  title: string;
}

export interface StepCompleteEvent {
  step_index: number;
  action: ActionType;
  description: string;
  duration_ms: number;
  url: string;
  result: unknown;
}

export interface ProgressEvent {
  completed: number;
  total: number;
  pct: number;
}

// ─── Analytics ────────────────────────────────────────────

export interface AnalyticsSummary {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  running_tasks: number;
  avg_success_rate: number;
  avg_execution_time_ms: number;
  total_execution_time_ms: number;
}

export interface DailyTaskCount {
  date: string;
  total: number;
  completed: number;
  failed: number;
}

export interface SiteVisit {
  domain: string;
  visit_count: number;
}

// ─── Reports ─────────────────────────────────────────────

export interface Report {
  id: number;
  task_id: number;
  format: 'pdf' | 'csv' | 'json';
  filename: string;
  file_size: number;
  created_at: string;
}

// ─── Log Entry ────────────────────────────────────────────

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error' | 'debug';
  message: string;
  step_index?: number;
  action?: string;
  url?: string;
  duration_ms?: number;
}
