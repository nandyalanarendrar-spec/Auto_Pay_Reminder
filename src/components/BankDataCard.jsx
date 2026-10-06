import React, { useState } from 'react';
import { Landmark, Sparkles, Trash2, ChevronRight, Loader2, PlusCircle, FlaskConical } from 'lucide-react';
import { apiRequest } from '../utils/api';

export default function BankDataCard({ status, isEmpty, onAddManually, onOpenReview, onChanged, showToast }) {
  const [busy, setBusy] = useState(false);
  const demoLoaded = !!status?.demo_loaded;
  const pending = status?.pending_review || 0;

  const run = async (fn, successMessage) => {
    setBusy(true);
    try {
      const result = await fn();
      showToast && showToast(typeof successMessage === 'function' ? successMessage(result) : successMessage);
      onChanged && (await onChanged());
    } catch (err) {
      showToast && showToast(`❌ ${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const loadDemo = () =>
    run(() => apiRequest('/bank/demo/load', { method: 'POST' }),
      (r) => `🏦 Demo bank data loaded. ${r.pending_review} payments found for you to review.`);
  const removeDemo = () =>
    run(() => apiRequest('/bank/demo', { method: 'DELETE' }), '🧹 Demo bank data removed.');

  return (
    <div className="glass-card-dark rounded-3xl p-5 border border-white/10 shadow-xl space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 p-0.5 flex-shrink-0">
            <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
              <Landmark className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {isEmpty ? 'Nothing tracked yet' : 'Bank data'}
            </h3>
            <p className="text-xs text-slate-400">
              {isEmpty
                ? 'Add a payment yourself, or try the demo bank to see detection in action.'
                : demoLoaded
                ? 'Sandbox demo bank is connected and updates daily.'
                : 'Find subscriptions and EMIs from bank transactions.'}
            </p>
          </div>
        </div>
        {demoLoaded && (
          <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/40 text-[0.625rem] font-bold text-amber-300 flex-shrink-0">
            <FlaskConical className="w-3 h-3" />
            <span>SANDBOX DEMO</span>
          </span>
        )}
      </div>

      {pending > 0 && (
        <button
          onClick={onOpenReview}
          className="w-full flex items-center justify-between rounded-2xl p-3.5 border border-emerald-500/50 bg-gradient-to-r from-emerald-950/70 to-slate-900 hover:border-emerald-400 transition-all cursor-pointer group"
        >
          <div className="flex items-center space-x-3 text-left">
            <Sparkles className="w-5 h-5 text-emerald-300 animate-pulse" />
            <div>
              <p className="text-sm font-bold text-white">{pending} {pending === 1 ? 'payment' : 'payments'} to review</p>
              <p className="text-[0.6875rem] text-emerald-200/80">Confirm or ignore what was found in your bank data</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-emerald-300 group-hover:translate-x-1 transition-transform" />
        </button>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {isEmpty && (
          <button
            onClick={onAddManually}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl text-white font-bold text-sm shadow-lg cursor-pointer"
            style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add manually</span>
          </button>
        )}
        {demoLoaded ? (
          <button
            disabled={busy}
            onClick={removeDemo}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-rose-300 hover:border-rose-500/50 font-bold text-sm transition-all cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            <span>Remove demo data</span>
          </button>
        ) : (
          <button
            disabled={busy}
            onClick={loadDemo}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl bg-slate-900 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-950/50 font-bold text-sm transition-all cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            <span>Load demo bank data</span>
          </button>
        )}
      </div>
    </div>
  );
}
