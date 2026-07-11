/**
 * Landing Page – Hero section with animated typewriter
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bot, Zap, Shield, Globe, ArrowRight, CheckCircle,
  Play, Star, Cpu, Eye, BarChart3, FileText
} from 'lucide-react';

const TYPEWRITER_TEXTS = [
  'Compare iPhone 16 prices on Amazon...',
  'Find Flutter internships in Hyderabad...',
  'Research top Python AI libraries...',
  'Find Computer Science scholarships...',
  'Search flights Hyderabad to Bangalore...',
];

const FEATURES = [
  { icon: Cpu, title: 'AI Planning Engine', desc: 'Gemini AI analyzes your request and creates an intelligent execution plan before any action' },
  { icon: Eye, title: 'Live Browser Preview', desc: 'Watch the AI navigate in real-time with a live browser screenshot stream' },
  { icon: Bot, title: 'Self-Healing Automation', desc: 'Automatically recovers from failures with 5 escalating recovery strategies' },
  { icon: BarChart3, title: 'Analytics Dashboard', desc: 'Track task history, success rates, and frequently visited sites' },
  { icon: FileText, title: 'Downloadable Reports', desc: 'Generate PDF, CSV, and JSON reports of every task execution' },
  { icon: Shield, title: 'Enterprise Security', desc: 'JWT authentication, encrypted sessions, and secure browser sandboxing' },
];

const USE_CASES = [
  '🛒 Product price comparison',
  '💼 Job & internship search',
  '📚 Research & summarization',
  '✈️ Flight & hotel booking',
  '🎓 Scholarship discovery',
  '📊 Market research & leads',
  '🏛️ Government portal navigation',
  '📥 PDF & file downloads',
];

export function LandingPage() {
  const [textIndex, setTextIndex] = useState(0);
  const [displayText, setDisplayText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const target = TYPEWRITER_TEXTS[textIndex];
    const delay = isDeleting ? 30 : 60;

    const timer = setTimeout(() => {
      if (!isDeleting) {
        if (displayText.length < target.length) {
          setDisplayText(target.slice(0, displayText.length + 1));
        } else {
          setTimeout(() => setIsDeleting(true), 1500);
        }
      } else {
        if (displayText.length > 0) {
          setDisplayText(displayText.slice(0, -1));
        } else {
          setIsDeleting(false);
          setTextIndex((prev) => (prev + 1) % TYPEWRITER_TEXTS.length);
        }
      }
    }, delay);

    return () => clearTimeout(timer);
  }, [displayText, isDeleting, textIndex]);

  return (
    <div className="min-h-screen overflow-x-hidden" style={{ background: 'radial-gradient(ellipse at top, #1a1a3e 0%, #0a0a15 50%)' }}>
      {/* Grid background */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(99,102,241,1) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,1) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Navbar */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 flex items-center justify-center shadow-brand">
            <Bot size={20} className="text-white" />
          </div>
          <span className="text-xl font-bold gradient-text-brand">WebPilot AI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="btn-ghost text-sm">Sign In</Link>
          <Link to="/register" className="btn-brand text-sm">Get Started →</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 max-w-6xl mx-auto px-8 pt-24 pb-16 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-sm mb-8"
        >
          <Star size={14} className="text-brand-400" />
          <span>AI-Powered Browser Automation</span>
          <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-5xl md:text-7xl font-black mb-6 leading-tight"
        >
          Your AI Browser
          <br />
          <span className="gradient-text">Digital Employee</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10"
        >
          Just describe what you need in plain English. WebPilot AI plans, executes, and delivers results — no code required.
        </motion.p>

        {/* Typewriter demo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="max-w-2xl mx-auto mb-10"
        >
          <div className="glass-card p-5 text-left neon-border">
            <div className="flex items-center gap-2 mb-3">
              <Bot size={16} className="text-brand-400" />
              <span className="text-xs text-slate-500 font-medium">Ask WebPilot to...</span>
            </div>
            <div className="text-white text-lg font-medium min-h-[28px]">
              {displayText}
              <span className="animate-blink text-brand-400">|</span>
            </div>
          </div>
        </motion.div>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex items-center justify-center gap-4"
        >
          <Link to="/register" className="btn-brand flex items-center gap-2 text-base px-8 py-4">
            <Zap size={18} />
            Start Free
          </Link>
          <Link to="/login" className="btn-ghost flex items-center gap-2 text-base px-8 py-4">
            <Play size={18} />
            Watch Demo
          </Link>
        </motion.div>

        {/* Checkmarks */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex items-center justify-center gap-6 mt-8 text-sm text-slate-500"
        >
          {['No code needed', 'Real browser automation', 'AI-powered planning'].map((item) => (
            <div key={item} className="flex items-center gap-1.5">
              <CheckCircle size={14} className="text-emerald-400" />
              {item}
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 max-w-6xl mx-auto px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-3">Everything You Need</h2>
          <p className="text-slate-400">Enterprise-grade browser automation, powered by AI</p>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="glass-card p-6 hover:neon-border transition-all duration-300 group"
            >
              <div className="w-10 h-10 rounded-xl bg-brand-500/15 border border-brand-500/20 flex items-center justify-center mb-4 group-hover:bg-brand-500/25 transition-colors">
                <feature.icon size={20} className="text-brand-400" />
              </div>
              <h3 className="text-white font-semibold mb-2">{feature.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Use Cases */}
      <section className="relative z-10 max-w-6xl mx-auto px-8 py-16">
        <div className="glass-card p-10">
          <div className="flex flex-col md:flex-row items-center gap-10">
            <div className="flex-1">
              <h2 className="text-3xl font-bold text-white mb-4">
                Automate Any Browser Task
              </h2>
              <p className="text-slate-400 mb-6">
                WebPilot AI handles complex, multi-step browser workflows that would normally take hours.
              </p>
              <Link to="/register" className="btn-brand inline-flex items-center gap-2">
                Get Started Free <ArrowRight size={16} />
              </Link>
            </div>
            <div className="flex-1 grid grid-cols-2 gap-3">
              {USE_CASES.map((useCase, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  className="px-4 py-3 rounded-xl bg-brand-500/5 border border-brand-500/10 text-slate-300 text-sm"
                >
                  {useCase}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 text-center py-10 border-t border-white/5 text-slate-600 text-sm">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Bot size={16} className="text-brand-500" />
          <span className="gradient-text-brand font-semibold">WebPilot AI</span>
        </div>
        <p>Built for the hackathon · Enterprise-grade autonomous browser agent</p>
      </footer>
    </div>
  );
}
