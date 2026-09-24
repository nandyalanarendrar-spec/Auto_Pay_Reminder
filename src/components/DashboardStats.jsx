import React from 'react';
import { Sparkles, Shield, AlertCircle, Plus, ChevronRight, Zap, CheckCircle2, Bell, Clock } from 'lucide-react';

export default function DashboardStats({ subscriptions, onOpenAddModal, onToggleAiChat, onOpenPersonalReminders }) {
  // Calculate total monthly expenditure (Excludes cancelled or Autopay OFF items)
  const totalMonthlySpend = subscriptions.reduce((acc, sub) => {
    if (sub.status === 'cancelled' || sub.autopay_enabled === false) return acc;
    let monthlyAmount = parseFloat(sub.amount) || 0;
    if (sub.billing_cycle === 'yearly') monthlyAmount = monthlyAmount / 12;
    if (sub.billing_cycle === 'weekly') monthlyAmount = monthlyAmount * 4;
    return acc + monthlyAmount;
  }, 0);

  const activeCount = subscriptions.filter(s => s.status === 'active' || s.status === 'trial').length;

  return (
    <div className="space-y-6 mb-8 max-w-2xl mx-auto">
      
      {/* Top Title Bar (Matching Photo 2 & 3) */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black tracking-widest text-white uppercase flex items-center space-x-2">
          <span>MY SPENDING</span>
        </h2>
        <div className="w-9 h-9 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-indigo-400">
          <Zap className="w-4 h-4 text-indigo-400" />
        </div>
      </div>

      {/* 1. ESTIMATED SPEND CARD (Matching Photo 3) */}
      <div className="glass-card-dark rounded-3xl p-6 relative overflow-hidden border border-white/10 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase">ESTIMATED SPEND</p>
            <p className="text-[11px] text-slate-500">Current Monthly Cycle</p>
            <div className="flex items-baseline space-x-2 mt-2">
              <h3 className="text-4xl font-black text-white tracking-tight">
                ₹{totalMonthlySpend.toFixed(0)}
              </h3>
              <ChevronRight className="w-5 h-5 text-slate-500" />
            </div>
          </div>
          
          <button 
            onClick={onToggleAiChat}
            className="w-10 h-10 rounded-full bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-indigo-300 hover:text-white transition-all shadow-lg"
          >
            <Sparkles className="w-5 h-5 text-cyan-400" />
          </button>
        </div>

        {/* Status Pills */}
        <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-200">{activeCount} Active</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400 font-medium">
            {activeCount === 0 ? 'All Sorted' : `${subscriptions.length} Tracked`}
          </span>
        </div>

        {/* Ambient Purple Glow Orb behind card */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* 2. ASK PAYLERT AI / AUTOPAYGUARD AI BANNER */}
      <button
        onClick={onToggleAiChat}
        className="w-full glass-card-dark rounded-3xl p-5 border border-white/10 hover:border-cyan-500/50 flex items-center justify-between text-left shadow-xl hover:shadow-cyan-500/10 transition-all cursor-pointer group"
      >
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 p-0.5 shadow-md group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-cyan-300 animate-pulse" />
            </div>
          </div>
          <div>
            <h4 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors flex items-center space-x-2">
              <span>Ask AutopayGuard AI</span>
              <span className="px-2 py-0.5 text-[9px] font-bold bg-cyan-950 text-cyan-400 border border-cyan-500/30 rounded-full">ACTIVE AI</span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Ask anything about your subscriptions, renewal dates, or cost optimization
            </p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-cyan-300 group-hover:translate-x-1 transition-all" />
      </button>

      {/* 3.5 PERSONAL TASK & CUSTOM REMINDERS CARD */}
      <div 
        onClick={onOpenPersonalReminders}
        className="glass-card-dark rounded-3xl p-5 border border-amber-500/20 hover:border-amber-500/50 shadow-2xl transition-all cursor-pointer group bg-gradient-to-r from-amber-950/20 via-slate-900 to-indigo-950/20"
        title="Open Personal Reminders & Multi-Time Alert Vault"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 to-indigo-600 p-0.5 shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                <Bell className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div>
              <h4 className="text-sm font-bold text-white group-hover:text-amber-300 transition-colors flex items-center space-x-1.5">
                <span>Personal Reminders Vault</span>
                <span className="px-2 py-0.5 text-[9px] font-bold bg-amber-950 text-amber-300 border border-amber-500/30 rounded-full">
                  Multi-Time Alerts
                </span>
              </h4>
              <p className="text-xs text-slate-400 mt-0.5">Set custom alerts (10m, 30m, 1h, 1d) for bills, passport, meetings & tasks</p>
            </div>
          </div>
          <button className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-amber-400 group-hover:bg-amber-500 group-hover:text-slate-950 transition-all">
            <Clock className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 4. CONFIRMED SUBSCRIPTIONS & START TRACKING (Matching Photo 2) */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
          <h3 className="text-sm font-bold text-white">Confirmed Subscriptions</h3>
        </div>

        {activeCount === 0 ? (
          <div className="glass-card-dark rounded-3xl p-8 border border-white/10 text-center shadow-2xl space-y-5">
            <div className="w-14 h-14 rounded-full bg-indigo-950/80 border border-indigo-500/30 flex items-center justify-center mx-auto text-indigo-400">
              <Shield className="w-7 h-7" />
            </div>

            <div>
              <h4 className="text-lg font-extrabold text-white">Start Tracking</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-2 leading-relaxed">
                Detect subscriptions from your bank alerts automatically or add them manually to manage your outgoings.
              </p>
            </div>

            <div className="space-y-3 pt-2 max-w-xs mx-auto">
              <button
                onClick={onOpenAddModal}
                className="w-full py-3.5 px-4 rounded-2xl font-bold text-xs text-white btn-gradient-primary flex items-center justify-center space-x-2 shadow-lg"
              >
                <Sparkles className="w-4 h-4" />
                <span>Auto-Detect Bank Alerts</span>
              </button>

              <button
                onClick={onOpenAddModal}
                className="w-full py-3 px-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white text-xs font-semibold flex items-center justify-between transition-all"
              >
                <div className="flex items-center space-x-2">
                  <Plus className="w-4 h-4" />
                  <span>Add Manually</span>
                </div>
                <span className="text-[9px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-bold uppercase">
                  ACTIVE
                </span>
              </button>
            </div>
          </div>
        ) : null}
      </div>

    </div>
  );
}
