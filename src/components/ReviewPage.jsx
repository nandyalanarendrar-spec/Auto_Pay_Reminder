import React, { useEffect, useState, useCallback } from 'react';
import { ArrowLeft, Check, X, Repeat, Landmark, Sparkles, TrendingUp, Hourglass, Loader2 } from 'lucide-react';
import { apiRequest } from '../utils/api';
import { formatINR, getDaysUntil } from '../utils/finance';

const FLAG_STYLE = {
  trial_converted: { icon: Hourglass, cls: 'bg-rose-500/15 text-rose-300 border-rose-500/40' },
  price_hike: { icon: TrendingUp, cls: 'bg-amber-500/15 text-amber-300 border-amber-500/40' }
};

function ReviewCard({ item, busy, onConfirm, onIgnore }) {
  const isEmi = item.kind === 'emi';
  const details = item.details || {};
  const [total, setTotal] = useState(details.total_installments ? String(details.total_installments) : '');
  const needsTotal = isEmi && !details.total_installments;
  const days = getDaysUntil(item.next_date);
  const Icon = isEmi ? Landmark : Repeat;
  const accent = isEmi ? 'from-purple-500 to-pink-500' : 'from-indigo-500 to-cyan-500';

  return (
    <div className="glass-card-dark rounded-3xl p-4 sm:p-5 border border-white/10 shadow-xl space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-3 min-w-0">
          <div className={`w-11 h-11 rounded-2xl bg-gradient-to-br ${accent} p-0.5 flex-shrink-0`}>
            <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
              <Icon className="w-5 h-5 text-white" />
            </div>
          </div>
          <div className="min-w-0">
            <h3 className="text-base font-extrabold text-white truncate">{item.merchant_name}</h3>
            <p className="text-xs text-slate-400">
              {isEmi ? 'EMI / loan' : 'Subscription'} · {item.billing_frequency}
            </p>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-xl font-black text-white">{formatINR(Number(item.amount))}</p>
          <p className="text-[0.6875rem] text-slate-400">
            Next {days === 0 ? 'today' : days === 1 ? 'tomorrow' : `in ${days} days`}
          </p>
        </div>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed">{details.reason}</p>

      {(item.flags || []).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {(details.tags || []).map((tag, i) => {
            const style = FLAG_STYLE[(item.flags || [])[i]] || FLAG_STYLE.price_hike;
            const FlagIcon = style.icon;
            return (
              <span key={tag} className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border text-[0.6875rem] font-bold ${style.cls}`}>
                <FlagIcon className="w-3.5 h-3.5" />
                <span>{tag}</span>
              </span>
            );
          })}
        </div>
      )}

      <div>
        <div className="flex justify-between text-[0.6875rem] text-slate-400 mb-1">
          <span>Detection confidence</span>
          <span className="font-bold text-slate-200">{item.confidence}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-slate-800 overflow-hidden">
          <div className={`h-full bg-gradient-to-r ${accent}`} style={{ width: `${item.confidence}%` }} />
        </div>
      </div>

      {needsTotal && (
        <div className="rounded-2xl border border-amber-500/40 bg-amber-950/30 p-3">
          <label className="block text-xs font-semibold text-amber-200 mb-1.5">
            How many installments in total? (the bank text does not say)
          </label>
          <input
            type="number"
            min="1"
            inputMode="numeric"
            value={total}
            onChange={(e) => setTotal(e.target.value)}
            placeholder="e.g. 36"
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-base focus:outline-none focus:border-amber-500"
          />
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 pt-1">
        <button
          disabled={busy}
          onClick={() => onIgnore(item)}
          className="flex items-center justify-center space-x-2 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 font-bold text-sm transition-all cursor-pointer disabled:opacity-50"
        >
          <X className="w-4 h-4" />
          <span>Ignore</span>
        </button>
        <button
          disabled={busy || (needsTotal && !total)}
          onClick={() => onConfirm(item, needsTotal ? { total_installments: parseInt(total, 10) } : null)}
          className="flex items-center justify-center space-x-2 py-3 rounded-2xl text-white font-bold text-sm shadow-lg transition-all cursor-pointer disabled:opacity-50"
          style={{ background: 'linear-gradient(90deg, #10b981 0%, #06b6d4 100%)' }}
        >
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          <span>Confirm</span>
        </button>
      </div>
    </div>
  );
}

export default function ReviewPage({ onBack, onChanged, showToast }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await apiRequest('/bank/detected?status=pending');
      setItems(data.items || []);
    } catch (err) {
      showToast && showToast(`⚠️ ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => { load(); }, [load]);

  const handle = async (item, path, body, doneMessage) => {
    setBusyId(item.id);
    try {
      await apiRequest(path, { method: 'POST', body });
      setItems((prev) => prev.filter((i) => i.id !== item.id));
      showToast && showToast(doneMessage);
      onChanged && onChanged();
    } catch (err) {
      showToast && showToast(`❌ ${err.message}`);
    } finally {
      setBusyId(null);
    }
  };

  const confirm = (item, overrides) =>
    handle(item, `/bank/detected/${item.id}/confirm`, overrides || undefined, `✅ Added ${item.merchant_name} to your ${item.kind === 'emi' ? 'EMIs' : 'subscriptions'}`);
  const ignore = (item) =>
    handle(item, `/bank/detected/${item.id}/ignore`, undefined, `Ignored ${item.merchant_name}`);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center space-x-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/60 text-slate-300 hover:text-white transition-all cursor-pointer"
          title="Back to Home"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 p-0.5">
          <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
        </div>
        <div>
          <h2 className="text-lg sm:text-xl font-black text-white tracking-tight">Review detected payments</h2>
          <p className="text-[0.6875rem] text-slate-400">Found in your bank transactions. Nothing is added until you confirm.</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-8 h-8 text-slate-500 animate-spin" /></div>
      ) : items.length === 0 ? (
        <div className="glass-card-dark rounded-3xl p-8 text-center border border-white/10">
          <Check className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">Nothing to review</h3>
          <p className="text-xs text-slate-400 mt-1">
            New subscriptions and EMIs found in your bank data will show up here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <ReviewCard key={item.id} item={item} busy={busyId === item.id} onConfirm={confirm} onIgnore={ignore} />
          ))}
        </div>
      )}
    </div>
  );
}
