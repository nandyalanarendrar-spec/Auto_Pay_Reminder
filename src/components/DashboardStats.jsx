import React from 'react';
import { Sparkles, ChevronRight, Zap } from 'lucide-react';
import { toMonthlyAmount, isSubCounted } from '../utils/finance';

export default function DashboardStats({ subscriptions, onToggleAiChat, onOpenSubscriptions }) {
  const totalMonthlySpend = subscriptions.filter(isSubCounted).reduce((acc, sub) => acc + toMonthlyAmount(sub), 0);
  const activeCount = subscriptions.filter((s) => s.status === 'active' || s.status === 'trial').length;

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black tracking-widest text-white uppercase">MY SPENDING</h2>
        <div className="w-9 h-9 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-indigo-400">
          <Zap className="w-4 h-4 text-indigo-400" />
        </div>
      </div>

      <div
        onClick={onOpenSubscriptions}
        className="glass-card-dark rounded-3xl p-6 relative overflow-hidden border border-white/10 shadow-2xl cursor-pointer hover:border-indigo-400/50 transition-all"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">ESTIMATED SPEND</p>
            <p className="text-[0.6875rem] text-slate-500">Subscriptions · current monthly cycle</p>
            <div className="flex items-baseline space-x-2 mt-2">
              <h3 className="text-4xl font-black text-white tracking-tight">₹{totalMonthlySpend.toFixed(0)}</h3>
              <ChevronRight className="w-5 h-5 text-slate-500" />
            </div>
          </div>

          <button
            onClick={(e) => { e.stopPropagation(); onToggleAiChat(); }}
            className="w-10 h-10 rounded-full bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-indigo-300 hover:text-white transition-all shadow-lg"
            title="Ask AI"
          >
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-200">{activeCount} Active</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400 font-medium">
            {activeCount === 0 ? 'Add your first subscription' : `${subscriptions.length} Tracked`}
          </span>
        </div>

        <div className="absolute top-0 right-0 w-48 h-48 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      <button
        onClick={onToggleAiChat}
        className="w-full glass-card-dark rounded-3xl p-4 border border-white/10 hover:border-cyan-500/50 flex items-center justify-between text-left shadow-xl hover:shadow-cyan-500/10 transition-all cursor-pointer group"
      >
        <div className="flex items-center space-x-4">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 p-0.5 shadow-md group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-cyan-300 animate-pulse" />
            </div>
          </div>
          <div>
            <h4 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors">Ask AutopayGuard AI</h4>
            <p className="text-xs text-slate-400 mt-0.5">Questions about renewals, costs or savings</p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-300 group-hover:translate-x-1 transition-all" />
      </button>
    </>
  );
}
