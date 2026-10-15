import React, { useMemo, useState } from 'react';
import { X, CheckCircle, Calculator } from 'lucide-react';
import { formatINR, isSubCounted, toMonthlyAmount } from '../utils/finance';

const cycleLabel = (sub) => {
  if (sub.billing_cycle === 'yearly') return 'billed yearly';
  if (sub.billing_cycle === 'weekly') return 'billed weekly';
  return 'billed monthly';
};

export default function WhatIfSimulatorModal({ isOpen, onClose, subscriptions }) {
  const [selectedSubIds, setSelectedSubIds] = useState([]);

  // Yearly and weekly plans are converted to a monthly figure so every row is comparable.
  const rows = useMemo(
    () =>
      (subscriptions || [])
        .filter(isSubCounted)
        .map((s) => ({ sub: s, monthly: toMonthlyAmount(s) }))
        .sort((a, b) => b.monthly - a.monthly),
    [subscriptions]
  );

  if (!isOpen) return null;

  const toggleSub = (id) => {
    setSelectedSubIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  };

  const totalMonthly = rows.reduce((acc, r) => acc + r.monthly, 0);
  const savedMonthly = rows.filter((r) => selectedSubIds.includes(r.sub.id)).reduce((acc, r) => acc + r.monthly, 0);
  const savedYearly = savedMonthly * 12;
  const remainingMonthly = totalMonthly - savedMonthly;
  const savedPct = totalMonthly > 0 ? Math.round((savedMonthly / totalMonthly) * 100) : 0;

  const pickTop = (n) => setSelectedSubIds(rows.slice(0, n).map((r) => r.sub.id));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-3xl p-6 shadow-2xl border border-indigo-500/30 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-xl bg-slate-900 border border-slate-800"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Savings Simulator</h3>
            <p className="text-xs text-slate-400">Tick what you could cancel and see what you would keep</p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 mb-3 flex justify-between items-center">
          <div>
            <p className="text-[0.6875rem] uppercase tracking-wider text-slate-400 font-semibold">You pay now</p>
            <p className="text-lg font-extrabold text-white">
              {formatINR(totalMonthly)}
              <span className="text-xs text-slate-400 font-normal">/mo</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-[0.6875rem] uppercase tracking-wider text-slate-400 font-semibold">That is a year</p>
            <p className="text-lg font-extrabold text-white">{formatINR(totalMonthly * 12)}</p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-indigo-950/80 via-purple-950/80 to-slate-900 border border-indigo-500/40 rounded-2xl p-4 mb-5">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-[0.6875rem] uppercase tracking-wider text-indigo-300 font-semibold">Monthly savings</p>
              <p className="text-2xl font-extrabold text-white mt-0.5">
                {formatINR(savedMonthly)}
                <span className="text-xs text-slate-400 font-normal">/mo</span>
              </p>
            </div>
            <div className="text-right border-l border-slate-800 pl-4">
              <p className="text-[0.6875rem] uppercase tracking-wider text-emerald-400 font-semibold">Yearly savings</p>
              <p className="text-lg font-bold text-emerald-300 mt-0.5">
                {formatINR(savedYearly)}
                <span className="text-xs text-slate-400 font-normal">/yr</span>
              </p>
            </div>
          </div>
          {savedMonthly > 0 && (
            <p className="text-xs text-indigo-200/90 mt-3">
              You would keep {formatINR(remainingMonthly)}/mo, {savedPct}% less than today.
            </p>
          )}
        </div>

        {rows.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-6">No active subscriptions to simulate yet.</p>
        ) : (
          <>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-slate-300">Select items to cancel:</p>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => pickTop(3)}
                  className="text-[0.6875rem] font-bold px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-indigo-300 hover:border-indigo-500 cursor-pointer"
                >
                  Top 3 costliest
                </button>
                <button
                  onClick={() => setSelectedSubIds([])}
                  className="text-[0.6875rem] font-bold px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 hover:border-slate-500 cursor-pointer"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="space-y-2 mb-6">
              {rows.map(({ sub, monthly }) => {
                const isSelected = selectedSubIds.includes(sub.id);
                return (
                  <div
                    key={sub.id}
                    onClick={() => toggleSub(sub.id)}
                    className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-indigo-950/50 border-indigo-500 text-white'
                        : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div
                        className={`w-5 h-5 rounded-md border flex items-center justify-center flex-shrink-0 ${
                          isSelected ? 'bg-indigo-600 border-indigo-500 text-white' : 'border-slate-700'
                        }`}
                      >
                        {isSelected && <CheckCircle className="w-3.5 h-3.5" />}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-white truncate">{sub.name || sub.merchant_name}</p>
                        <p className="text-[0.625rem] text-slate-400">
                          {sub.category || 'General'} · {cycleLabel(sub)}
                        </p>
                      </div>
                    </div>

                    <div className="text-right flex-shrink-0 pl-2">
                      <p className="text-xs font-bold text-indigo-300">{formatINR(monthly)}/mo</p>
                      <p className="text-[0.625rem] text-slate-500">{formatINR(monthly * 12)}/yr</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-lg"
        >
          Close Simulator
        </button>
      </div>
    </div>
  );
}
