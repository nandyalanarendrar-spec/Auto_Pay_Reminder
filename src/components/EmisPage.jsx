import React from 'react';
import { ArrowLeft, Landmark } from 'lucide-react';
import EMITrackerSection from './EMITrackerSection';
import { getDaysUntil, formatINR } from '../utils/finance';

export default function EmisPage({ userEmis, onBack, ...emiHandlers }) {
  const active = userEmis.filter((e) => (e.installments_paid || 0) < (e.total_installments || 0));
  const monthly = active.reduce((a, e) => a + (parseFloat(e.installment_amount) || 0), 0);
  const remaining = active.reduce(
    (a, e) => a + Math.max(0, (e.total_installments || 0) - (e.installments_paid || 0)) * (parseFloat(e.installment_amount) || 0),
    0
  );
  const next = active
    .map((e) => ({ name: e.loan_name, days: getDaysUntil(e.next_due_date) }))
    .filter((x) => x.days >= 0 && x.days < 999)
    .sort((a, b) => a.days - b.days)[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-purple-500/60 text-slate-300 hover:text-white transition-all cursor-pointer"
          title="Back to Home"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 p-0.5">
          <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
            <Landmark className="w-5 h-5 text-white" />
          </div>
        </div>
        <div>
          <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">EMIs & Loans</h2>
          <p className="text-[11px] text-slate-400 hidden sm:block">Installments, payoff progress and due dates</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Per month', value: formatINR(monthly) },
          { label: 'Total remaining', value: formatINR(remaining) },
          { label: next ? `Next: ${next.name}` : 'Next due', value: next ? (next.days === 0 ? 'Today' : `${next.days}d`) : '-', warn: next && next.days <= 3 }
        ].map((c) => (
          <div key={c.label} className="glass-card-dark rounded-2xl p-3 sm:p-4 border border-white/10 text-center">
            <p className={`text-lg sm:text-2xl font-black ${c.warn ? 'text-amber-300' : 'text-white'}`}>{c.value}</p>
            <p className="text-[10px] sm:text-[11px] text-slate-400 uppercase tracking-wider font-semibold mt-0.5 truncate">{c.label}</p>
          </div>
        ))}
      </div>

      <EMITrackerSection userEmis={userEmis} {...emiHandlers} />
    </div>
  );
}
