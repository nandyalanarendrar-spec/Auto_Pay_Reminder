import React from 'react';
import { ArrowLeft, Plus, Repeat, BarChart3, ChevronRight } from 'lucide-react';
import SubscriptionList from './SubscriptionList';
import { summarizeSubscriptions, formatINR } from '../utils/finance';

export default function SubscriptionsPage({ subscriptions, onBack, onOpenAddModal, onOpenAnalysis, ...listHandlers }) {
  const { activeCount, monthly, dueSoon } = summarizeSubscriptions(subscriptions);

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
            <p className="text-[0.6875rem] text-slate-400 hidden sm:block">Everything that renews automatically</p>
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

      {/* The numbers and charts live on their own page; this button is the way in. */}
      {onOpenAnalysis && (
        <button
          onClick={onOpenAnalysis}
          className="w-full flex items-center justify-between gap-3 rounded-2xl p-4 border border-indigo-500/40 bg-gradient-to-r from-indigo-950/60 to-slate-900 hover:border-indigo-400 transition-all cursor-pointer group"
        >
          <div className="flex items-center space-x-3 text-left min-w-0">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center flex-shrink-0">
              <BarChart3 className="w-5 h-5 text-indigo-300" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-white">Dashboard &amp; spending analysis</p>
              <p className="text-[0.6875rem] text-indigo-200/80 truncate">
                {activeCount} active · {formatINR(monthly)}/month
                {dueSoon > 0 ? ` · ${dueSoon} due in 7 days` : ''}
              </p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-indigo-300 group-hover:translate-x-1 transition-transform flex-shrink-0" />
        </button>
      )}

      <SubscriptionList subscriptions={subscriptions} {...listHandlers} />
    </div>
  );
}
