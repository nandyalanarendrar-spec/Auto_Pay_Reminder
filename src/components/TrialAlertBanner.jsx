import React from 'react';
import { Hourglass, ChevronRight } from 'lucide-react';
import { getDaysUntil, subRenewalDate, formatINR } from '../utils/finance';

export default function TrialAlertBanner({ subscriptions, onNavigate }) {
  const ending = subscriptions
    .filter((s) => s.is_free_trial || s.status === 'trial')
    .map((s) => {
      const endDate = s.trial_end_date || subRenewalDate(s);
      return { sub: s, days: getDaysUntil(endDate) };
    })
    .filter((t) => t.days >= 0 && t.days <= 3)
    .sort((a, b) => a.days - b.days);

  if (ending.length === 0) return null;

  return (
    <div className="space-y-2">
      {ending.map(({ sub, days }) => (
        <button
          key={sub.id}
          onClick={() => onNavigate('subscriptions')}
          className="w-full text-left rounded-2xl p-4 border border-rose-500/50 bg-gradient-to-r from-rose-950/80 via-slate-900 to-slate-900 flex items-center justify-between gap-3 shadow-lg hover:border-rose-400 transition-all cursor-pointer group"
        >
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center flex-shrink-0">
              <Hourglass className="w-5 h-5 text-rose-300 animate-pulse" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-white truncate">
                {sub.name || sub.merchant_name} free trial ends {days === 0 ? 'today' : days === 1 ? 'tomorrow' : `in ${days} days`}
              </p>
              <p className="text-xs text-rose-200/80">
                Cancel before then to avoid being charged {formatINR(parseFloat(sub.amount) || 0)}.
              </p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-rose-300 group-hover:translate-x-1 transition-transform flex-shrink-0" />
        </button>
      ))}
    </div>
  );
}
