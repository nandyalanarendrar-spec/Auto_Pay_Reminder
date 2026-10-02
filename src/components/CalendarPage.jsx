import React, { useState, useEffect, useMemo } from 'react';
import { ArrowLeft, ChevronLeft, ChevronRight, CalendarDays } from 'lucide-react';
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient';
import { API_BASE_URL } from '../config/api';
import { parseDateOnly, subRenewalDate, isSubCounted, formatINR } from '../utils/finance';

const KIND_STYLE = {
  subscription: { dot: 'bg-indigo-400', label: 'Subscription', text: 'text-indigo-300' },
  trial: { dot: 'bg-rose-400', label: 'Free trial ends', text: 'text-rose-300' },
  emi: { dot: 'bg-purple-400', label: 'EMI', text: 'text-purple-300' },
  reminder: { dot: 'bg-amber-400', label: 'Reminder', text: 'text-amber-300' }
};

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const monthKey = (y, m) => y * 12 + m;

// Project a recurring charge onto the given month.
function subscriptionDaysInMonth(baseDate, cycle, year, month) {
  const base = parseDateOnly(baseDate);
  if (!base) return [];
  const lastDay = new Date(year, month + 1, 0).getDate();
  if (cycle === 'weekly') {
    const days = [];
    const cur = new Date(base);
    let guard = 0;
    while (cur < new Date(year, month + 1, 1) && guard < 2000) {
      if (cur.getFullYear() === year && cur.getMonth() === month) days.push(cur.getDate());
      cur.setDate(cur.getDate() + 7);
      guard++;
    }
    return days;
  }
  if (monthKey(year, month) < monthKey(base.getFullYear(), base.getMonth())) return [];
  if (cycle === 'yearly') {
    return base.getMonth() === month && year >= base.getFullYear() ? [base.getDate()] : [];
  }
  return [Math.min(base.getDate(), lastDay)];
}

export default function CalendarPage({ subscriptions, userEmis, onBack }) {
  const today = new Date();
  const [cursor, setCursor] = useState({ year: today.getFullYear(), month: today.getMonth() });
  const [selectedDay, setSelectedDay] = useState(today.getDate());
  const [reminders, setReminders] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        let token = null;
        if (isSupabaseConfigured && supabase) {
          const { data: { session } } = await supabase.auth.getSession();
          token = session?.access_token;
        }
        const res = await fetch(`${API_BASE_URL}/personal-reminders`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (res.ok) setReminders(await res.json());
      } catch (e) {
        console.warn('Calendar reminders fetch note:', e);
      }
    })();
  }, []);

  const eventsByDay = useMemo(() => {
    const { year, month } = cursor;
    const map = {};
    const add = (day, ev) => {
      (map[day] = map[day] || []).push(ev);
    };

    subscriptions.filter(isSubCounted).forEach((s) => {
      const isTrial = s.is_free_trial || s.status === 'trial';
      const name = s.name || s.merchant_name;
      if (isTrial) {
        const d = parseDateOnly(s.trial_end_date || subRenewalDate(s));
        if (d && d.getFullYear() === year && d.getMonth() === month) {
          add(d.getDate(), { kind: 'trial', name, amount: parseFloat(s.amount) || 0 });
        }
        return;
      }
      subscriptionDaysInMonth(subRenewalDate(s), s.billing_cycle, year, month).forEach((day) =>
        add(day, { kind: 'subscription', name, amount: parseFloat(s.amount) || 0 })
      );
    });

    userEmis.forEach((e) => {
      const remaining = Math.max(0, (e.total_installments || 0) - (e.installments_paid || 0));
      const first = parseDateOnly(e.next_due_date);
      if (!first || remaining === 0) return;
      for (let i = 0; i < remaining; i++) {
        const lastDayOfTarget = new Date(first.getFullYear(), first.getMonth() + i + 1, 0).getDate();
        const d = new Date(first.getFullYear(), first.getMonth() + i, Math.min(first.getDate(), lastDayOfTarget));
        if (d.getFullYear() === year && d.getMonth() === month) {
          add(d.getDate(), {
            kind: 'emi',
            name: e.loan_name,
            amount: parseFloat(e.installment_amount) || 0,
            note: `Installment ${(e.installments_paid || 0) + i + 1}/${e.total_installments}`
          });
        }
      }
    });

    reminders.filter((r) => !r.is_completed && r.due_datetime).forEach((r) => {
      const d = new Date(r.due_datetime);
      if (!isNaN(d) && d.getFullYear() === year && d.getMonth() === month) {
        add(d.getDate(), {
          kind: 'reminder',
          name: r.title,
          amount: 0,
          note: d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }) +
            (r.repeat && r.repeat !== 'none' ? ` · repeats ${r.repeat}` : '')
        });
      }
    });

    return map;
  }, [cursor, subscriptions, userEmis, reminders]);

  const firstWeekday = new Date(cursor.year, cursor.month, 1).getDay();
  const daysInMonth = new Date(cursor.year, cursor.month + 1, 0).getDate();
  const cells = [...Array(firstWeekday).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)];

  const monthLabel = new Date(cursor.year, cursor.month, 1).toLocaleString('en-IN', { month: 'long', year: 'numeric' });
  const isToday = (day) => day && cursor.year === today.getFullYear() && cursor.month === today.getMonth() && day === today.getDate();

  const shiftMonth = (delta) => {
    const d = new Date(cursor.year, cursor.month + delta, 1);
    setCursor({ year: d.getFullYear(), month: d.getMonth() });
    setSelectedDay(1);
  };

  const goToday = () => {
    setCursor({ year: today.getFullYear(), month: today.getMonth() });
    setSelectedDay(today.getDate());
  };

  const monthTotal = Object.values(eventsByDay).flat().reduce((a, e) => a + e.amount, 0);
  const selectedEvents = eventsByDay[selectedDay] || [];

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/60 text-slate-300 hover:text-white transition-all cursor-pointer"
            title="Back to Home"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 p-0.5">
            <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
              <CalendarDays className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">Payment Calendar</h2>
            <p className="text-[11px] text-slate-400 hidden sm:block">Renewals, EMIs, trials and reminders on one view</p>
          </div>
        </div>
        <button
          onClick={goToday}
          className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white hover:border-emerald-500/50 cursor-pointer transition-all"
        >
          Today
        </button>
      </div>

      <div className="glass-card-dark rounded-3xl p-4 sm:p-6 border border-white/10 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <button onClick={() => shiftMonth(-1)} className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white cursor-pointer" title="Previous month">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div className="text-center">
            <h3 className="text-base font-bold text-white">{monthLabel}</h3>
            <p className="text-[11px] text-slate-400">{formatINR(monthTotal)} scheduled</p>
          </div>
          <button onClick={() => shiftMonth(1)} className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white cursor-pointer" title="Next month">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-7 gap-1 sm:gap-1.5 text-center">
          {WEEKDAYS.map((w) => (
            <div key={w} className="text-[10px] sm:text-[11px] font-bold text-slate-500 uppercase py-1">{w}</div>
          ))}
          {cells.map((day, idx) => {
            if (!day) return <div key={`empty-${idx}`} />;
            const evs = eventsByDay[day] || [];
            const selected = day === selectedDay;
            return (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`aspect-square rounded-xl border flex flex-col items-center justify-center gap-1 transition-all cursor-pointer ${
                  selected
                    ? 'bg-emerald-500/20 border-emerald-400'
                    : isToday(day)
                    ? 'bg-indigo-500/15 border-indigo-400/60'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-600'
                }`}
              >
                <span className={`text-xs sm:text-sm font-bold ${isToday(day) ? 'text-indigo-300' : 'text-slate-200'}`}>{day}</span>
                <span className="flex items-center gap-0.5 h-1.5">
                  {evs.slice(0, 4).map((ev, i) => (
                    <span key={i} className={`w-1.5 h-1.5 rounded-full ${KIND_STYLE[ev.kind].dot}`} />
                  ))}
                </span>
              </button>
            );
          })}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 mt-4 text-[11px] text-slate-400">
          {Object.values(KIND_STYLE).map((k) => (
            <span key={k.label} className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${k.dot}`} />
              <span>{k.label}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="glass-card-dark rounded-3xl p-5 border border-white/10 shadow-xl">
        <h3 className="text-sm font-bold text-white mb-3">
          {new Date(cursor.year, cursor.month, selectedDay).toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
        </h3>
        {selectedEvents.length === 0 ? (
          <p className="text-xs text-slate-500">Nothing scheduled on this day.</p>
        ) : (
          <div className="space-y-2">
            {selectedEvents.map((ev, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-900/70 border border-slate-800 rounded-xl px-3.5 py-2.5">
                <div className="flex items-center space-x-3 min-w-0">
                  <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${KIND_STYLE[ev.kind].dot}`} />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">{ev.name}</p>
                    <p className={`text-[11px] ${KIND_STYLE[ev.kind].text}`}>
                      {KIND_STYLE[ev.kind].label}{ev.note ? ` · ${ev.note}` : ''}
                    </p>
                  </div>
                </div>
                {ev.amount > 0 && <span className="text-sm font-bold text-white whitespace-nowrap">{formatINR(ev.amount)}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
