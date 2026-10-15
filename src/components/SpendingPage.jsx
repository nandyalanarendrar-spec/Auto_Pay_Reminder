import React, { useEffect, useState } from 'react';
import { ArrowLeft, Loader2, TrendingDown, TrendingUp, Store, BarChart3 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { apiRequest } from '../utils/api';
import { formatINR } from '../utils/finance';

const BAR_TOOLTIP = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div className="bg-slate-900/95 border border-slate-700/80 p-3 rounded-2xl shadow-2xl">
      <p className="text-xs font-bold text-slate-300">{row.label}</p>
      <p className="text-sm font-black text-emerald-400">{formatINR(row.total)}</p>
      <p className="text-[0.6875rem] text-slate-400">{row.count} payments</p>
    </div>
  );
};

export default function SpendingPage({ onBack, onOpenReview }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const result = await apiRequest('/bank/spending?months=6');
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const change = data?.change_pct;
  const up = typeof change === 'number' && change > 0;
  const currentMonthKey = data?.this_month?.month;

  return (
    <div className="w-full lg:max-w-4xl lg:mx-auto space-y-5">
      <div className="flex items-center space-x-3">
        <button
          onClick={onBack}
          className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white cursor-pointer"
          aria-label="Back"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-xl font-extrabold text-white">Spending</h2>
          <p className="text-xs text-slate-400">Where your money went in the last 6 months</p>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {!loading && error && (
        <div className="glass-card-dark rounded-3xl p-5 border border-rose-500/30 text-sm text-rose-200">
          Could not load spending: {error}
        </div>
      )}

      {!loading && !error && data && !data.has_data && (
        <div className="glass-card-dark rounded-3xl p-6 border border-white/10 text-center space-y-2">
          <BarChart3 className="w-8 h-8 text-slate-500 mx-auto" />
          <p className="text-sm font-bold text-white">No transactions yet</p>
          <p className="text-xs text-slate-400">
            Connect a bank (sandbox) or load the demo bank data on the home screen to see your spending here.
          </p>
        </div>
      )}

      {!loading && !error && data && data.has_data && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div className="glass-card-dark rounded-3xl p-4 border border-white/10">
              <p className="text-[0.6875rem] uppercase tracking-wider text-slate-400 font-semibold">
                {data.this_month.label} so far
              </p>
              <p className="text-2xl font-black text-white mt-1">{formatINR(data.this_month.total)}</p>
              <p className="text-[0.6875rem] text-slate-400">{data.this_month.count} payments</p>
            </div>
            <div className="glass-card-dark rounded-3xl p-4 border border-white/10">
              <p className="text-[0.6875rem] uppercase tracking-wider text-slate-400 font-semibold">
                {data.last_month.label || 'Last month'}
              </p>
              <p className="text-2xl font-black text-white mt-1">{formatINR(data.last_month.total)}</p>
              {typeof change === 'number' ? (
                <p className={`text-[0.6875rem] font-bold flex items-center space-x-1 ${up ? 'text-rose-300' : 'text-emerald-300'}`}>
                  {up ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  <span>{Math.abs(change)}% {up ? 'more' : 'less'} this month</span>
                </p>
              ) : (
                <p className="text-[0.6875rem] text-slate-400">{data.last_month.count} payments</p>
              )}
            </div>
          </div>

          <div className="glass-card-dark rounded-3xl p-5 border border-white/10 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white">Month by month</h3>
              {data.average_monthly > 0 && (
                <span className="text-[0.6875rem] text-slate-400">avg {formatINR(data.average_monthly)}</span>
              )}
            </div>
            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.months} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <XAxis dataKey="label" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    width={44}
                    tickFormatter={(v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : v)}
                  />
                  <Tooltip content={<BAR_TOOLTIP />} cursor={{ fill: 'rgba(148,163,184,0.08)' }} />
                  <Bar dataKey="total" radius={[8, 8, 0, 0]}>
                    {data.months.map((m) => (
                      <Cell key={m.month} fill={m.month === currentMonthKey ? '#a855f7' : '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-card-dark rounded-3xl p-5 border border-white/10 shadow-xl space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Store className="w-4 h-4 text-indigo-300" />
              <span>Top merchants</span>
              <span className="text-[0.6875rem] font-normal text-slate-400">{formatINR(data.total_spent)} in total</span>
            </h3>
            {data.top_merchants.map((m) => (
              <div key={m.name} className="space-y-1">
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="font-bold text-white truncate">{m.name}</span>
                  <span className="font-black text-white flex-shrink-0">{formatINR(m.total)}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                    style={{ width: `${Math.max(3, Math.min(100, m.share_pct))}%` }}
                  />
                </div>
                <p className="text-[0.6875rem] text-slate-400">{m.share_pct}% · {m.count} payments</p>
              </div>
            ))}
          </div>

          {onOpenReview && (
            <button
              onClick={onOpenReview}
              className="w-full py-3 rounded-2xl bg-slate-900 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-950/50 font-bold text-sm cursor-pointer"
            >
              Review payments found in this data
            </button>
          )}
        </>
      )}
    </div>
  );
}
