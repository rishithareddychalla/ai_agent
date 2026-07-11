/**
 * Analytics Page – Interactive charts and usage statistics
 */

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Line, Bar, Doughnut
} from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import {
  BarChart3, TrendingUp, CheckCircle2, XCircle,
  Clock, Globe, Zap, Activity
} from 'lucide-react';
import { analyticsApi } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler,
);

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#94a3b8', font: { size: 11, family: 'Inter' } },
    },
    tooltip: {
      backgroundColor: '#1a1a2e',
      borderColor: '#2a2a3d',
      borderWidth: 1,
      titleColor: '#e2e8f0',
      bodyColor: '#94a3b8',
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(99,102,241,0.05)' },
      ticks: { color: '#475569', font: { size: 10 } },
    },
    y: {
      grid: { color: 'rgba(99,102,241,0.05)' },
      ticks: { color: '#475569', font: { size: 10 } },
    },
  },
};

export function AnalyticsPage() {
  const { data: summary } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsApi.getSummary,
    refetchInterval: 30000,
  });

  const { data: dailyData = [] } = useQuery({
    queryKey: ['analytics-daily'],
    queryFn: () => analyticsApi.getDailyTasks(30),
  });

  const { data: sites = [] } = useQuery({
    queryKey: ['analytics-sites'],
    queryFn: () => analyticsApi.getTopSites(8),
  });

  const { data: execTimes = [] } = useQuery({
    queryKey: ['analytics-exec-times'],
    queryFn: analyticsApi.getExecutionTimes,
  });

  // Chart data
  const dailyChartData = {
    labels: dailyData.slice(-14).map((d) => {
      const date = new Date(d.date);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    }),
    datasets: [
      {
        label: 'Completed',
        data: dailyData.slice(-14).map((d) => d.completed),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.4,
      },
      {
        label: 'Failed',
        data: dailyData.slice(-14).map((d) => d.failed),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const sitesChartData = {
    labels: sites.map((s) => s.domain.replace('www.', '').substring(0, 15)),
    datasets: [
      {
        data: sites.map((s) => s.visit_count),
        backgroundColor: [
          'rgba(99,102,241,0.8)', 'rgba(139,92,246,0.8)', 'rgba(236,72,153,0.8)',
          'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(59,130,246,0.8)',
          'rgba(168,85,247,0.8)', 'rgba(249,115,22,0.8)',
        ],
        borderWidth: 0,
      },
    ],
  };

  const successRate = summary ? Math.round(summary.avg_success_rate * 100) : 0;
  const successRingData = {
    labels: ['Success', 'Failed'],
    datasets: [{
      data: [successRate, 100 - successRate],
      backgroundColor: ['rgba(16,185,129,0.8)', 'rgba(239,68,68,0.15)'],
      borderWidth: 0,
    }],
  };

  const execTimeData = {
    labels: execTimes.slice(-10).map((t: any) => `#${t.task_id}`),
    datasets: [{
      label: 'Execution Time (s)',
      data: execTimes.slice(-10).map((t: any) => (t.execution_time_ms / 1000).toFixed(1)),
      backgroundColor: 'rgba(99,102,241,0.6)',
      borderColor: '#6366f1',
      borderWidth: 1,
      borderRadius: 6,
    }],
  };

  const statCards = [
    { label: 'Total Tasks', value: summary?.total_tasks ?? 0, icon: Activity, color: 'brand' },
    { label: 'Completed', value: summary?.completed_tasks ?? 0, icon: CheckCircle2, color: 'emerald' },
    { label: 'Failed', value: summary?.failed_tasks ?? 0, icon: XCircle, color: 'red' },
    { label: 'Running', value: summary?.running_tasks ?? 0, icon: Zap, color: 'amber' },
    { label: 'Avg Success Rate', value: `${successRate}%`, icon: TrendingUp, color: 'emerald' },
    {
      label: 'Avg Duration',
      value: summary ? `${(summary.avg_execution_time_ms / 1000).toFixed(1)}s` : '0s',
      icon: Clock,
      color: 'blue',
    },
  ];

  return (
    <div className="flex-1 overflow-auto p-6 page-enter">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">Analytics</h1>
        <p className="text-slate-400 text-sm">Track your automation performance and usage patterns</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {statCards.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
            className="glass-card p-4 text-center"
          >
            <div className={`w-8 h-8 rounded-lg bg-${stat.color}-500/10 border border-${stat.color}-500/20 flex items-center justify-center mx-auto mb-2`}>
              <stat.icon size={15} className={`text-${stat.color}-400`} />
            </div>
            <p className="text-xl font-bold text-white">{stat.value}</p>
            <p className="text-slate-500 text-xs mt-0.5">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        {/* Daily Activity – takes 2 cols */}
        <div className="lg:col-span-2 glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={16} className="text-brand-400" />
            <h2 className="text-sm font-semibold text-white">Daily Activity (last 14 days)</h2>
          </div>
          <div style={{ height: '220px' }}>
            <Line data={dailyChartData} options={CHART_DEFAULTS as any} />
          </div>
        </div>

        {/* Success Rate Ring */}
        <div className="glass-card p-5 flex flex-col">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Success Rate</h2>
          </div>
          <div className="flex-1 flex items-center justify-center" style={{ height: '180px' }}>
            <div className="relative">
              <Doughnut
                data={successRingData}
                options={{
                  ...CHART_DEFAULTS,
                  cutout: '75%',
                  plugins: {
                    ...CHART_DEFAULTS.plugins,
                    legend: { display: false },
                  },
                } as any}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-3xl font-black text-white">{successRate}%</p>
                  <p className="text-xs text-slate-500">Success</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Execution Times */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Clock size={16} className="text-blue-400" />
            <h2 className="text-sm font-semibold text-white">Execution Times (last 10 tasks)</h2>
          </div>
          <div style={{ height: '200px' }}>
            {execTimes.length > 0 ? (
              <Bar data={execTimeData} options={CHART_DEFAULTS as any} />
            ) : (
              <div className="h-full flex items-center justify-center text-slate-600 text-sm">
                No completed tasks yet
              </div>
            )}
          </div>
        </div>

        {/* Top Sites */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Globe size={16} className="text-violet-400" />
            <h2 className="text-sm font-semibold text-white">Most Visited Sites</h2>
          </div>
          {sites.length > 0 ? (
            <div className="space-y-2">
              {sites.map((site, i) => {
                const maxCount = sites[0]?.visit_count || 1;
                const pct = (site.visit_count / maxCount) * 100;
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 w-5">{i + 1}</span>
                    <div className="flex-1">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-300 truncate">{site.domain}</span>
                        <span className="text-slate-500">{site.visit_count}</span>
                      </div>
                      <div className="progress-bar">
                        <motion.div
                          className="progress-bar-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ delay: i * 0.05, duration: 0.5 }}
                          style={{
                            background: `hsl(${250 + i * 20}, 70%, 60%)`,
                            boxShadow: 'none',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-40 flex items-center justify-center text-slate-600 text-sm">
              No site data yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
