/**
 * Settings Page – User configuration
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Settings, Globe, Cpu, Save, Loader2, Moon, Sun, RefreshCw, Camera, AlertTriangle } from 'lucide-react';
import { settingsApi } from '@/services/api';
import { useAuthStore } from '@/stores';
import toast from 'react-hot-toast';
import type { UserSettings } from '@/types';

const SECTION_CLASS = 'glass-card p-5 mb-4';
const LABEL_CLASS = 'text-xs font-medium text-slate-400 mb-1.5 block';
const SELECT_CLASS = 'input-field text-sm';

export function SettingsPage() {
  const { user } = useAuthStore();
  const qc = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.getSettings,
  });

  const [form, setForm] = useState<Partial<UserSettings>>({});

  useEffect(() => {
    if (settings) setForm(settings);
  }, [settings]);

  const mutation = useMutation({
    mutationFn: settingsApi.updateSettings,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings'] });
      toast.success('Settings saved!');
    },
    onError: () => toast.error('Failed to save settings'),
  });

  const updateField = <K extends keyof UserSettings>(key: K, value: UserSettings[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    mutation.mutate(form);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 size={24} className="text-brand-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6 page-enter">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
          <p className="text-slate-400 text-sm">Configure your WebPilot AI preferences</p>
        </div>
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={handleSave}
          disabled={mutation.isPending}
          className="btn-brand flex items-center gap-2 text-sm"
        >
          {mutation.isPending ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Save size={14} />
          )}
          Save Settings
        </motion.button>
      </div>

      {/* Account Info */}
      <div className={SECTION_CLASS}>
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Settings size={14} className="text-brand-400" />
          Account
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={LABEL_CLASS}>Email</label>
            <input type="email" value={user?.email || ''} disabled className="input-field text-sm opacity-60 cursor-not-allowed" />
          </div>
          <div>
            <label className={LABEL_CLASS}>Display Name</label>
            <input type="text" value={user?.full_name || ''} disabled className="input-field text-sm opacity-60 cursor-not-allowed" />
          </div>
        </div>
      </div>

      {/* Browser Settings */}
      <div className={SECTION_CLASS}>
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Globe size={14} className="text-blue-400" />
          Browser Configuration
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={LABEL_CLASS}>Browser Engine</label>
            <select
              value={form.browser || 'chromium'}
              onChange={(e) => updateField('browser', e.target.value as any)}
              className={SELECT_CLASS}
            >
              <option value="chromium">Chromium (Recommended)</option>
              <option value="firefox">Firefox</option>
              <option value="edge">Microsoft Edge</option>
            </select>
          </div>
          <div>
            <label className={LABEL_CLASS}>Browser Mode</label>
            <select
              value={form.headless ? 'headless' : 'headed'}
              onChange={(e) => updateField('headless', e.target.value === 'headless')}
              className={SELECT_CLASS}
            >
              <option value="headless">Headless (Faster)</option>
              <option value="headed">Headed (Visible)</option>
            </select>
          </div>
          <div>
            <label className={LABEL_CLASS}>Default Timeout (ms)</label>
            <input
              type="number"
              value={form.default_timeout || 30000}
              onChange={(e) => updateField('default_timeout', parseInt(e.target.value))}
              className="input-field text-sm"
              min={5000}
              max={120000}
              step={1000}
            />
          </div>
          <div>
            <label className={LABEL_CLASS}>Max Retry Count</label>
            <input
              type="number"
              value={form.retry_count || 3}
              onChange={(e) => updateField('retry_count', parseInt(e.target.value))}
              className="input-field text-sm"
              min={1}
              max={10}
            />
          </div>
        </div>
      </div>

      {/* AI Provider */}
      <div className={SECTION_CLASS}>
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Cpu size={14} className="text-violet-400" />
          AI Configuration
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={LABEL_CLASS}>AI Provider</label>
            <select
              value={form.ai_provider || 'gemini'}
              onChange={(e) => updateField('ai_provider', e.target.value as any)}
              className={SELECT_CLASS}
            >
              <option value="gemini">Google Gemini (Recommended)</option>
              <option value="openai">OpenAI GPT-4</option>
            </select>
          </div>
        </div>
        <div className="mt-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/15 flex items-start gap-2">
          <AlertTriangle size={13} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-amber-300/80">
            API keys are configured server-side via environment variables. Contact your administrator to change AI providers.
          </p>
        </div>
      </div>

      {/* Display Settings */}
      <div className={SECTION_CLASS}>
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Camera size={14} className="text-pink-400" />
          Screenshots & Display
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={LABEL_CLASS}>Screenshot Frequency (ms)</label>
            <input
              type="number"
              value={form.screenshot_frequency || 500}
              onChange={(e) => updateField('screenshot_frequency', parseInt(e.target.value))}
              className="input-field text-sm"
              min={200}
              max={5000}
              step={100}
            />
            <p className="text-xs text-slate-600 mt-1">Lower = faster live preview, higher CPU usage</p>
          </div>
          <div>
            <label className={LABEL_CLASS}>Theme</label>
            <select
              value={form.theme || 'dark'}
              onChange={(e) => updateField('theme', e.target.value as any)}
              className={SELECT_CLASS}
            >
              <option value="dark">Dark Mode</option>
              <option value="light">Light Mode</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
