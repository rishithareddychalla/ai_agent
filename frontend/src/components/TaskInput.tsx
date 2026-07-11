/**
 * TaskInput – The main natural language task input component
 */

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles, ChevronDown, Globe, ShoppingCart, Briefcase, GraduationCap, Plane } from 'lucide-react';

const EXAMPLE_PROMPTS = [
  { icon: ShoppingCart, text: 'Compare iPhone 16 prices on Amazon and Flipkart under ₹70,000', category: 'Shopping' },
  { icon: Briefcase, text: 'Find Flutter internships in Hyderabad on LinkedIn and Internshala', category: 'Careers' },
  { icon: Globe, text: 'Search for the top 5 Python web scraping libraries and summarize their features', category: 'Research' },
  { icon: GraduationCap, text: 'Find Computer Science scholarships for Indian students 2025', category: 'Education' },
  { icon: Plane, text: 'Find flights from Hyderabad to Bangalore under ₹3,000 this weekend', category: 'Travel' },
];

interface TaskInputProps {
  onSubmit: (prompt: string) => void;
  isRunning?: boolean;
}

export function TaskInput({ onSubmit, isRunning = false }: TaskInputProps) {
  const [prompt, setPrompt] = useState('');
  const [showExamples, setShowExamples] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    if (!prompt.trim() || isRunning) return;
    onSubmit(prompt.trim());
    setShowExamples(false);
  }, [prompt, isRunning, onSubmit]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  const handleExampleClick = (text: string) => {
    setPrompt(text);
    setShowExamples(false);
    textareaRef.current?.focus();
  };

  const charCount = prompt.length;
  const isValid = prompt.trim().length > 10;

  return (
    <div className="w-full">
      {/* Main Input Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center">
            <Sparkles size={16} className="text-brand-400" />
          </div>
          <div>
            <h2 className="text-white font-semibold text-sm">New Task</h2>
            <p className="text-slate-500 text-xs">Describe what you want the AI to do</p>
          </div>
          <button
            onClick={() => setShowExamples(!showExamples)}
            className="ml-auto flex items-center gap-1.5 text-xs text-slate-400 hover:text-brand-400 transition-colors"
          >
            <Sparkles size={12} />
            Examples
            <ChevronDown
              size={12}
              className={`transition-transform ${showExamples ? 'rotate-180' : ''}`}
            />
          </button>
        </div>

        {/* Examples dropdown */}
        <AnimatePresence>
          {showExamples && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 overflow-hidden"
            >
              <div className="grid gap-2">
                {EXAMPLE_PROMPTS.map((example, i) => (
                  <button
                    key={i}
                    onClick={() => handleExampleClick(example.text)}
                    className="flex items-start gap-3 p-3 rounded-xl bg-white/3 hover:bg-brand-500/10 border border-transparent hover:border-brand-500/20 transition-all text-left group"
                  >
                    <div className="mt-0.5 w-6 h-6 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-brand-500/20 transition-colors">
                      <example.icon size={12} className="text-brand-400" />
                    </div>
                    <div>
                      <span className="text-xs font-medium text-brand-400 uppercase tracking-wide">{example.category}</span>
                      <p className="text-slate-300 text-sm mt-0.5">{example.text}</p>
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Textarea */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="E.g., 'Compare iPhone 16 prices on Amazon and Flipkart under ₹70,000 and give me the best deal'"
            rows={4}
            disabled={isRunning}
            className="input-field resize-none pr-4 text-sm leading-relaxed disabled:opacity-60 disabled:cursor-not-allowed"
            style={{ minHeight: '120px' }}
          />
          
          {/* Char counter */}
          <div className="absolute bottom-3 right-3 text-xs text-slate-600">
            {charCount > 0 && `${charCount}`}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <kbd className="px-1.5 py-0.5 bg-surface-50 border border-surface-border rounded text-[10px] text-slate-400">Ctrl+Enter</kbd>
            <span>to submit</span>
          </div>

          <motion.button
            onClick={handleSubmit}
            disabled={!isValid || isRunning}
            whileTap={{ scale: 0.97 }}
            className={`btn-brand flex items-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none ${
              isRunning ? 'opacity-70' : ''
            }`}
          >
            {isRunning ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Send size={16} />
                <span>Run Task</span>
              </>
            )}
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}
