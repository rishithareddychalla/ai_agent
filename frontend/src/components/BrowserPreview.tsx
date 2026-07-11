/**
 * BrowserPreview – Live browser screenshot stream display
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Wifi, WifiOff, Maximize2, Cpu, Eye } from 'lucide-react';
import type { BrowserUpdateEvent } from '@/types';

interface BrowserPreviewProps {
  browserState?: BrowserUpdateEvent | null;
  isConnected?: boolean;
  isRunning?: boolean;
  currentAction?: string;
}

export function BrowserPreview({
  browserState,
  isConnected = false,
  isRunning = false,
  currentAction,
}: BrowserPreviewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card overflow-hidden"
    >
      {/* Browser Toolbar */}
      <div className="browser-toolbar flex items-center gap-3">
        {/* Traffic lights */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <div className="browser-dot w-3 h-3 bg-red-500 rounded-full" />
          <div className="browser-dot w-3 h-3 bg-amber-500 rounded-full" />
          <div className="browser-dot w-3 h-3 bg-emerald-500 rounded-full" />
        </div>

        {/* URL bar */}
        <div className="flex-1 flex items-center gap-2 bg-surface-DEFAULT/60 rounded-lg px-3 py-1.5 text-xs border border-surface-border">
          <Globe size={11} className="text-slate-500 flex-shrink-0" />
          <span className="text-slate-400 truncate font-mono">
            {browserState?.url || 'about:blank'}
          </span>
          {isRunning && (
            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse flex-shrink-0" />
          )}
        </div>

        {/* Status */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {isConnected ? (
            <Wifi size={13} className="text-emerald-400" />
          ) : (
            <WifiOff size={13} className="text-slate-600" />
          )}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1 rounded text-slate-500 hover:text-white transition-colors"
          >
            <Maximize2 size={13} />
          </button>
        </div>
      </div>

      {/* Current action bar */}
      <AnimatePresence>
        {currentAction && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-brand-500/10 border-b border-brand-500/20 px-4 py-1.5 flex items-center gap-2 overflow-hidden"
          >
            <Cpu size={11} className="text-brand-400 animate-pulse" />
            <span className="text-xs text-brand-300 font-medium truncate">{currentAction}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Screenshot area */}
      <div
        className={`relative bg-slate-950 overflow-hidden transition-all duration-200 ${
          isFullscreen ? 'h-[600px]' : 'h-[380px]'
        }`}
      >
        <AnimatePresence mode="sync">
          {browserState?.screenshot ? (
            <motion.img
              key={browserState.screenshot.slice(0, 20)} // Key change triggers animation
              initial={{ opacity: 0.8 }}
              animate={{ opacity: 1 }}
              src={`data:image/png;base64,${browserState.screenshot}`}
              alt="Browser live preview"
              className="w-full h-full object-contain object-top"
              style={{ imageRendering: 'auto' }}
            />
          ) : (
            <motion.div
              key="placeholder"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 flex flex-col items-center justify-center"
            >
              {/* Grid pattern */}
              <div
                className="absolute inset-0 opacity-5"
                style={{
                  backgroundImage: `
                    linear-gradient(rgba(99,102,241,0.5) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(99,102,241,0.5) 1px, transparent 1px)
                  `,
                  backgroundSize: '40px 40px',
                }}
              />
              
              {/* Center content */}
              <div className="relative z-10 flex flex-col items-center gap-4 text-center">
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                    <Eye size={28} className="text-brand-500/60" />
                  </div>
                  {isRunning && (
                    <div className="absolute inset-0 rounded-2xl border-2 border-brand-400 animate-ping opacity-20" />
                  )}
                </div>
                <div>
                  <p className="text-slate-400 text-sm font-medium">
                    {isRunning ? 'Browser starting...' : 'No active browser session'}
                  </p>
                  <p className="text-slate-600 text-xs mt-1">
                    {isRunning ? 'Live preview will appear here' : 'Submit a task to begin'}
                  </p>
                </div>
              </div>

              {/* Scan line animation */}
              {isRunning && (
                <motion.div
                  className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-brand-400 to-transparent opacity-40"
                  animate={{ top: ['0%', '100%'] }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Scan overlay for running state */}
        {isRunning && browserState?.screenshot && (
          <motion.div
            className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-brand-400 to-transparent opacity-30 pointer-events-none"
            animate={{ top: ['0%', '100%'] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
          />
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-surface-border flex items-center justify-between">
        <span className="text-xs text-slate-600 truncate max-w-xs">
          {browserState?.title || 'No page loaded'}
        </span>
        <span className={`text-xs font-medium ${isRunning ? 'text-brand-400' : 'text-slate-600'}`}>
          {isRunning ? 'Live' : 'Idle'}
        </span>
      </div>
    </motion.div>
  );
}
