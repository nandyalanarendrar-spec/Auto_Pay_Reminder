import React from 'react';
import { PieChart, Clock } from 'lucide-react';
import {
  getDaysUntil,
  parseDateOnly,
  toMonthlyAmount,
  subRenewalDate,
  isSubCounted,
  formatINR
} from '../utils/finance';

export default function MonthlySummaryCard({ subscriptions, userEmis }) {
  const now = new Date();
  const monthName = now.toLocaleString('en-IN', { month: 'long', year: 'numeric' });
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const daysLeftInMonth = daysInMonth - now.getDate();

  const subItems = subscriptions
    .filter(isSubCounted)
    .map((s) => ({ name: s.name || s.merchant_name, monthly: toMonthlyAmount(s), amount: parseFloat(s.amount) || 0, date: subRenewalDate(s), kind: 'Subscription' }));
  const emiItems = userEmis
    .filter((e) => (e.installments_paid || 0) < (e.total_installments || 0))
    .map((e) => ({ name: e.loan_name, monthly: parseFloat(e.installment_amount) || 0, amount: parseFloat(e.installment_amount) || 0, date: e.next_due_date, kind: 'EMI' }));

  const subTotal = subItems.reduce((a, i) => a + i.monthly, 0);
  const emiTotal = emiItems.reduce((a, i) => a + i.monthly, 0);
  const total = subTotal + emiTotal;
  const subPct = total > 0 ? Math.round((subTotal / total) * 100) : 0;

  const dueThisMonth = [...subItems, ...emiItems]
    .filter((i) => {
      const d = parseDateOnly(i.date);
      return d && d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && getDaysUntil(i.date) >= 0;
    })
    .sort((a, b) => getDaysUntil(a.date) - getDaysUntil(b.date));
  const stillToPay = dueThisMonth.reduce((a, i) => a + i.amount, 0);

  const top = [...subItems, ...emiItems].sort((a, b) => b.monthly - a.monthly).slice(0, 3);

  return (
    <div className="glass-card-dark rounded-3xl p-5 border border-white/10 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-white flex items-center space-x-2">
          <PieChart className="w-4 h-4 text-cyan-400" />
          <span>Monthly Summary</span>
        </h3>
        <span className="text-[0.6875rem] text-slate-400">{monthName}</span>
      </div>

      <div className="flex items-end justify-between">
        <div>
          <p className="text-[0.6875rem] text-slate-400 uppercase tracking-wider font-semibold">Committed / month</p>
          <p className="text-3xl font-black text-white tracking-tight">{formatINR(total)}</p>
        </div>
        <div className="text-right">
          <p className="text-[0.6875rem] text-slate-400 uppercase tracking-wider font-semibold">Still to pay this month</p>
          <p className="text-lg font-extrabold text-amber-300">{formatINR(stillToPay)}</p>
          <p className="text-[0.625rem] text-slate-500">{daysLeftInMonth} days left</p>
        </div>
      </div>

      <div className="mt-4">
        <div className="w-full h-2.5 rounded-full bg-purple-500/60 overflow-hidden">
          <div className="h-full bg-indigo-500" style={{ width: `${subPct}%` }} />
        </div>
        <div className="flex justify-between text-[0.6875rem] mt-1.5">
          <span className="text-indigo-300 font-semibold">Subscriptions {formatINR(subTotal)}</span>
          <span className="text-purple-300 font-semibold">EMIs {formatINR(emiTotal)}</span>
        </div>
      </div>

      {top.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2">
          <p className="text-[0.6875rem] text-slate-400 uppercase tracking-wider font-semibold">Biggest expenses</p>
          {top.map((i) => (
            <div key={`${i.kind}-${i.name}`} className="flex items-center justify-between text-xs">
              <span className="text-slate-200 font-medium truncate pr-2">
                {i.name} <span className="text-slate-500">· {i.kind}</span>
              </span>
              <span className="text-white font-bold">{formatINR(i.monthly)}</span>
            </div>
          ))}
        </div>
      )}

      {dueThisMonth.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2">
          <p className="text-[0.6875rem] text-slate-400 uppercase tracking-wider font-semibold flex items-center space-x-1">
            <Clock className="w-3 h-3" />
            <span>Coming up this month</span>
          </p>
          {dueThisMonth.slice(0, 4).map((i) => {
            const d = getDaysUntil(i.date);
            return (
              <div key={`due-${i.kind}-${i.name}`} className="flex items-center justify-between text-xs">
                <span className="text-slate-300 truncate pr-2">{i.name}</span>
                <span className="text-slate-400 whitespace-nowrap">
                  {d === 0 ? 'Today' : d === 1 ? 'Tomorrow' : `In ${d} days`} · <span className="text-white font-semibold">{formatINR(i.amount)}</span>
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
