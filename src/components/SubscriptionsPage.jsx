import React, { useState } from 'react';
import { ArrowLeft, Plus, Repeat, BarChart3, ChevronDown } from 'lucide-react';
import SubscriptionList from './SubscriptionList';
import SpendAnalytics from './SpendAnalytics';
import {
  getDaysUntil,
  toMonthlyAmount,
  subRenewalDate,
  isSubCounted,
  formatINR
} from '../utils/finance';

export default function SubscriptionsPage({ subscriptions, onBack, onOpenAddModal, ...listHandlers }) {
  const [showCharts, setShowCharts] = useState(false);

  const active = subscriptions.filter((s) => s.status === 'active' || s.status === 'trial');
  const monthly = subscriptions.filter(isSubCounted).reduce((a, s) => a + toMonthlyAmount(s), 0);
  const dueSoon = active.filter((s) => {
    const d = getDaysUntil(subRenewalDate(s));
    return d >= 0 && d <= 7;
  }).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center space-x-3 min-w-0">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 text-slate-300 hover:text-white transition-all cursor-pointer flex-shrink-0"
            title="Back to Home"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-500 p-0.5 flex-shrink-0">
            <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
              <Repeat className="w-5 h-5 text-white" />
            </div>
          </div>
          <div className="min-w-0">
            <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">Subscriptions</h2>
            <p className="text-[11px] text-slate-400 hidden sm:block">Everything that renews automatically</p>
          </div>
        </div>

        <button
          onClick={onOpenAddModal}
          className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-white font-bold text-xs sm:text-sm shadow-lg transition-all hover:scale-[1.03] cursor-pointer flex-shrink-0"
          style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
        >
          <Plus className="w-4 h-4" />
          <span>Add Subscription</span>
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Active', value: active.length },
          { label: 'Per month', value: formatINR(monthly) },
          { label: 'Due in 7 days', value: dueSoon, warn: dueSoon > 0 }
        ].map((c) => (
          <div key={c.label} className="glass-card-dark rounded-2xl p-3 sm:p-4 border border-white/10 text-center">
            <p className={`text-lg sm:text-2xl font-black ${c.warn ? 'text-amber-300' : 'text-white'}`}>{c.value}</p>
            <p className="text-[10px] sm:text-[11px] text-slate-400 uppercase tracking-wider font-semibold mt-0.5">{c.label}</p>
          </div>
        ))}
      </div>

      <div>
        <button
          onClick={() => setShowCharts(!showCharts)}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-300 hover:text-white transition-colors cursor-pointer"
        >
          <BarChart3 className="w-4 h-4 text-indigo-400" />
          <span>{showCharts ? 'Hide spending charts' : 'Show spending charts'}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${showCharts ? 'rotate-180' : ''}`} />
        </button>
        {showCharts && (
          <div className="mt-4">
            <SpendAnalytics subscriptions={subscriptions} />
          </div>
        )}
      </div>

      <SubscriptionList subscriptions={subscriptions} {...listHandlers} />
    </div>
  );
}
