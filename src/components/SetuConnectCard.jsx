import React, { useState } from 'react';
import { Link2, Loader2, RefreshCw, Unplug, FlaskConical, ExternalLink, X, ShieldCheck } from 'lucide-react';
import { apiRequest } from '../utils/api';

const formatWhen = (iso) => {
  if (!iso) return 'not synced yet';
  const d = new Date(iso);
  return isNaN(d) ? 'recently' : d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
};

export default function SetuConnectCard({ status, onChanged, showToast }) {
  const [busy, setBusy] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [mobile, setMobile] = useState('');
  const [error, setError] = useState('');

  if (!status || !status.configured) return null;

  const state = status.state;
  const isActive = state === 'active';
  const isPending = state === 'pending';
  const isBroken = ['rejected', 'revoked', 'expired', 'paused'].includes(state);

  const run = async (key, fn, success) => {
    setBusy(key);
    try {
      const result = await fn();
      if (success) showToast && showToast(typeof success === 'function' ? success(result) : success);
      onChanged && (await onChanged());
      return result;
    } catch (err) {
      showToast && showToast(`❌ ${err.message}`);
    } finally {
      setBusy('');
    }
    return null;
  };

  const startConnect = async (e) => {
    e.preventDefault();
    setError('');
    setBusy('connect');
    try {
      const { url } = await apiRequest('/bank/setu/connect', { method: 'POST', body: { mobile } });
      window.location.assign(url);
    } catch (err) {
      setError(err.message);
      setBusy('');
    }
  };

  const sync = () =>
    run('sync', () => apiRequest('/bank/setu/sync', { method: 'POST' }), (r) =>
      r?.pending ? `⏳ ${r.message}` : `🏦 Synced: ${r.fetched} debits read, ${r.added} new. ${r.pending_review} to review.`);

  const disconnect = () => {
    if (!window.confirm('Disconnect this bank? Transactions imported from it will be deleted.')) return;
    run('disconnect', () => apiRequest('/bank/setu', { method: 'DELETE' }), '🔌 Bank disconnected and imported data removed.');
  };

  return (
    <div className="glass-card-dark rounded-3xl p-5 border border-white/10 shadow-xl space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 p-0.5 flex-shrink-0">
            <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center">
              <Link2 className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">
              {isActive ? 'Bank connected' : isPending ? 'Waiting for your approval' : 'Connect your bank'}
            </h3>
            <p className="text-xs text-slate-400">
              {isActive
                ? `${(status.accounts || []).map((a) => a.masked).filter(Boolean).join(', ') || 'Account linked'} · last synced ${formatWhen(status.last_synced_at)}`
                : isPending
                ? 'Finish the approval on the Setu page, then come back here.'
                : isBroken
                ? `Your previous connection is ${state}. Connect again to continue.`
                : 'Link a bank account through Setu Account Aggregator and let the app find your subscriptions and EMIs.'}
            </p>
          </div>
        </div>
        <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/40 text-[0.625rem] font-bold text-amber-300 flex-shrink-0">
          <FlaskConical className="w-3 h-3" />
          <span>SANDBOX</span>
        </span>
      </div>

      {isActive ? (
        <div className="grid grid-cols-2 gap-3">
          <button
            disabled={!!busy}
            onClick={sync}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl text-white font-bold text-sm shadow-lg cursor-pointer disabled:opacity-50"
            style={{ background: 'linear-gradient(90deg, #6366f1 0%, #a855f7 100%)' }}
          >
            {busy === 'sync' ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            <span>Sync now</span>
          </button>
          <button
            disabled={!!busy}
            onClick={disconnect}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-rose-300 hover:border-rose-500/50 font-bold text-sm cursor-pointer disabled:opacity-50"
          >
            {busy === 'disconnect' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Unplug className="w-4 h-4" />}
            <span>Disconnect</span>
          </button>
        </div>
      ) : isPending ? (
        <div className="grid grid-cols-2 gap-3">
          <a
            href={status.consent_url}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl text-white font-bold text-sm shadow-lg cursor-pointer"
            style={{ background: 'linear-gradient(90deg, #6366f1 0%, #a855f7 100%)' }}
          >
            <ExternalLink className="w-4 h-4" />
            <span>Open approval page</span>
          </a>
          <button
            disabled={!!busy}
            onClick={disconnect}
            className="flex items-center justify-center space-x-2 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-rose-300 font-bold text-sm cursor-pointer disabled:opacity-50"
          >
            <X className="w-4 h-4" />
            <span>Cancel</span>
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowForm(true)}
          className="w-full flex items-center justify-center space-x-2 py-3 rounded-2xl text-white font-bold text-sm shadow-lg cursor-pointer"
          style={{ background: 'linear-gradient(90deg, #6366f1 0%, #a855f7 100%)' }}
        >
          <Link2 className="w-4 h-4" />
          <span>Connect bank (Sandbox)</span>
        </button>
      )}

      {showForm && (
        <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <form onSubmit={startConnect} className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-700 p-6 space-y-4 shadow-2xl">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Connect a bank (Sandbox)</h3>
              </div>
              <button type="button" onClick={() => setShowForm(false)} className="p-1 rounded-lg text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs text-slate-300 leading-relaxed space-y-1.5">
              <p>You will be sent to Setu's approval page, where you can choose the account to share.</p>
              <p className="text-amber-200/90">
                This is a test environment: you get a real OTP on this number, but the bank accounts shown are
                Setu's test banks (pick <strong>Setu FIP</strong> savings) with test transactions.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Your mobile number</label>
              <input
                type="tel"
                inputMode="numeric"
                autoFocus
                required
                value={mobile}
                onChange={(e) => setMobile(e.target.value)}
                placeholder="10-digit mobile number"
                className="w-full px-3.5 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-base focus:outline-none focus:border-indigo-500"
              />
              <p className="text-[0.6875rem] text-slate-500 mt-1.5">Only the last 4 digits are stored.</p>
              {error && <p className="text-xs text-rose-300 mt-2">{error}</p>}
            </div>

            <button
              type="submit"
              disabled={busy === 'connect'}
              className="w-full flex items-center justify-center space-x-2 py-3 rounded-2xl text-white font-bold text-sm cursor-pointer disabled:opacity-60"
              style={{ background: 'linear-gradient(90deg, #6366f1 0%, #a855f7 100%)' }}
            >
              {busy === 'connect' ? <Loader2 className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />}
              <span>Continue to Setu</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
