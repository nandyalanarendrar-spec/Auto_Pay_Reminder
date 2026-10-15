import React from 'react';
import { ArrowLeft, BarChart3 } from 'lucide-react';
import SpendAnalytics from './SpendAnalytics';
import { summarizeSubscriptions, formatINR } from '../utils/finance';

export default function SubscriptionAnalysisPage({ subscriptions, onBack }) {
  const { activeCount, monthly, dueSoon } = summarizeSubscriptions(subscriptions);

  return (
    <div className="w-full lg:max-w-4xl lg:mx-auto space-y-6">
      <div className="flex items-center space-x-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 text-slate-300 hover:text-white transition-all cursor-pointer flex-shrink-0"
          title="Back to Subscriptions"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 p-0.5 flex-shrink-0">
          <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
        </div>
        <div className="min-w-0">
          <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">Dashboard &amp; analysis</h2>
          <p className="text-[0.6875rem] text-slate-400">Where your subscription money goes</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Active', value: activeCount },
          { label: 'Per month', value: formatINR(monthly) },
          { label: 'Due in 7 days', value: dueSoon, warn: dueSoon > 0 }
        ].map((c) => (
          <div key={c.label} className="glass-card-dark rounded-2xl p-3 sm:p-4 border border-white/10 text-center">
            <p className={`text-lg sm:text-2xl font-black ${c.warn ? 'text-amber-300' : 'text-white'}`}>{c.value}</p>
            <p className="text-[0.625rem] sm:text-[0.6875rem] text-slate-400 uppercase tracking-wider font-semibold mt-0.5">{c.label}</p>
          </div>
        ))}
      </div>

      <div className="glass-card-dark rounded-2xl p-4 border border-white/10 flex items-center justify-between gap-3">
        <span className="text-xs font-semibold text-slate-300">Yearly cost at this pace</span>
        <span className="text-lg font-black text-white">{formatINR(monthly * 12)}</span>
      </div>

      <SpendAnalytics subscriptions={subscriptions} />
    </div>
  );
}
