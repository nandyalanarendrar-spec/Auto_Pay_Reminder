import React from 'react';
import { Repeat, Landmark, Bell, CalendarDays, ArrowUpRight } from 'lucide-react';
import {
  getDaysUntil,
  toMonthlyAmount,
  subRenewalDate,
  isSubCounted,
  formatINR
} from '../utils/finance';

const TILE_STYLES = {
  subscriptions: {
    gradient: 'from-indigo-500 to-cyan-500',
    glow: 'hover:shadow-indigo-500/25 hover:border-indigo-400/60',
    text: 'group-hover:text-cyan-300'
  },
  emis: {
    gradient: 'from-purple-500 to-pink-500',
    glow: 'hover:shadow-purple-500/25 hover:border-purple-400/60',
    text: 'group-hover:text-pink-300'
  },
  reminders: {
    gradient: 'from-amber-500 to-orange-500',
    glow: 'hover:shadow-amber-500/25 hover:border-amber-400/60',
    text: 'group-hover:text-amber-300'
  },
  calendar: {
    gradient: 'from-emerald-500 to-teal-500',
    glow: 'hover:shadow-emerald-500/25 hover:border-emerald-400/60',
    text: 'group-hover:text-emerald-300'
  }
};

function Tile({ id, icon: Icon, title, stat, caption, badge, onClick }) {
  const s = TILE_STYLES[id];
  return (
    <button
      onClick={onClick}
      className={`group relative text-left glass-card-dark rounded-3xl p-4 sm:p-5 border border-white/10 shadow-xl hover:-translate-y-1 hover:shadow-2xl transition-all cursor-pointer overflow-hidden ${s.glow}`}
    >
      <div className={`absolute -top-10 -right-10 w-28 h-28 rounded-full bg-gradient-to-br ${s.gradient} opacity-10 group-hover:opacity-25 blur-2xl transition-opacity`} />

      <div className="flex items-start justify-between">
        <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-br ${s.gradient} p-0.5 shadow-lg group-hover:scale-110 group-hover:-rotate-3 transition-transform`}>
          <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
            <Icon className="w-6 h-6 sm:w-7 sm:h-7 text-white" />
          </div>
        </div>
        <span className="w-7 h-7 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 group-hover:text-white group-hover:bg-slate-800 transition-colors">
          <ArrowUpRight className="w-3.5 h-3.5" />
        </span>
      </div>

      <div className="mt-4">
        <h4 className={`text-sm font-bold text-white transition-colors ${s.text}`}>{title}</h4>
        <p className="text-xl sm:text-2xl font-black text-white tracking-tight mt-0.5">{stat}</p>
        <p className="text-[0.6875rem] text-slate-400 mt-0.5 truncate">{caption}</p>
        {badge ? (
          <span className="inline-block mt-2 px-2 py-0.5 rounded-full text-[0.625rem] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
            {badge}
          </span>
        ) : null}
      </div>
    </button>
  );
}

export default function HomeNavTiles({ subscriptions, userEmis, onNavigate }) {
  const activeSubs = subscriptions.filter((s) => s.status === 'active' || s.status === 'trial');
  const subMonthly = subscriptions.filter(isSubCounted).reduce((a, s) => a + toMonthlyAmount(s), 0);
  const subsDueSoon = activeSubs.filter((s) => {
    const d = getDaysUntil(subRenewalDate(s));
    return d >= 0 && d <= 7;
  }).length;

  const activeEmis = userEmis.filter((e) => (e.installments_paid || 0) < (e.total_installments || 0));
  const emiMonthly = activeEmis.reduce((a, e) => a + (parseFloat(e.installment_amount) || 0), 0);
  const emisDueSoon = activeEmis.filter((e) => {
    const d = getDaysUntil(e.next_due_date);
    return d >= 0 && d <= 7;
  }).length;

  const upcoming = [
    ...activeSubs.map((s) => ({ name: s.name || s.merchant_name, days: getDaysUntil(subRenewalDate(s)) })),
    ...activeEmis.map((e) => ({ name: e.loan_name, days: getDaysUntil(e.next_due_date) }))
  ]
    .filter((x) => x.days >= 0 && x.days < 999)
    .sort((a, b) => a.days - b.days)[0];

  const whenLabel = (d) => (d === 0 ? 'today' : d === 1 ? 'tomorrow' : `in ${d} days`);

  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4">
      <Tile
        id="subscriptions"
        icon={Repeat}
        title="Subscriptions"
        stat={`${activeSubs.length} active`}
        caption={`${formatINR(subMonthly)} / month`}
        badge={subsDueSoon ? `${subsDueSoon} due soon` : null}
        onClick={() => onNavigate('subscriptions')}
      />
      <Tile
        id="emis"
        icon={Landmark}
        title="EMIs & Loans"
        stat={`${activeEmis.length} ${activeEmis.length === 1 ? 'loan' : 'loans'}`}
        caption={`${formatINR(emiMonthly)} / month`}
        badge={emisDueSoon ? `${emisDueSoon} due soon` : null}
        onClick={() => onNavigate('emis')}
      />
      <Tile
        id="reminders"
        icon={Bell}
        title="Reminders"
        stat="Tasks"
        caption="Custom multi-time alerts"
        onClick={() => onNavigate('reminders')}
      />
      <Tile
        id="calendar"
        icon={CalendarDays}
        title="Calendar"
        stat={upcoming ? whenLabel(upcoming.days) : 'All clear'}
        caption={upcoming ? `Next: ${upcoming.name}` : 'No upcoming payments'}
        onClick={() => onNavigate('calendar')}
      />
    </div>
  );
}
