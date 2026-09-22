import React, { useState } from 'react';
import { Bell, ShieldAlert, CheckCircle2, Clock, X, Volume2, Power, AlertTriangle, Sparkles } from 'lucide-react';
import { requestNotificationPermission, sendWebNotification } from '../utils/browserNotifications';

export default function NotificationsCenterModal({
  isOpen,
  onClose,
  subscriptions = [],
  killSwitchActive = false,
  userEmis = []
}) {
  const [browserPermission, setBrowserPermission] = useState(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      return Notification.permission;
    }
    return 'default';
  });
  const [testSent, setTestSent] = useState(false);

  if (!isOpen) return null;

  const handleEnableWebPush = async () => {
    const granted = await requestNotificationPermission();
    if ('Notification' in window) {
      setBrowserPermission(Notification.permission);
    }
    
    setTestSent(true);
    setTimeout(() => setTestSent(false), 4000);

    sendWebNotification("⚡ Autopay Guard Notifications Active!", {
      body: "Instant desktop alerts enabled for upcoming renewals and autopay debits.",
      tag: `test-notif-${Date.now()}`
    });
  };

  // Generate real dynamic notification items from subscriptions & EMIs
  const today = new Date();
  const alerts = [];

  if (killSwitchActive) {
    alerts.push({
      id: 'alert-ks',
      type: 'critical',
      title: '🚨 Emergency Kill-Switch Active',
      message: 'All bank auto-debit permissions are paused across linked UPI accounts & cards.',
      time: 'Just now'
    });
  }

  (subscriptions || []).forEach(sub => {
    if (!sub || sub.status === 'cancelled') return;

    const renewalStr = sub.next_payment_date || sub.next_renewal_date;
    if (renewalStr) {
      const renewalDate = new Date(renewalStr);
      const diffDays = Math.ceil((renewalDate - today) / (1000 * 60 * 60 * 24));

      if (diffDays >= 0 && diffDays <= 7) {
        alerts.push({
          id: `alert-sub-${sub.id || sub.name}`,
          type: sub.autopay_enabled === false ? 'warning' : 'info',
          title: `Upcoming Renewal: ${sub.name || sub.merchant_name}`,
          message: `₹${parseFloat(sub.amount || 0).toFixed(2)} due in ${diffDays === 0 ? 'TODAY' : `${diffDays} days`} (${renewalStr}). Autopay is ${sub.autopay_enabled === false ? 'OFF (Paused)' : 'ON (Active)'}.`,
          time: diffDays === 0 ? 'Due Today' : `In ${diffDays}d`
        });
      }
    }
  });

  (userEmis || []).forEach(emi => {
    if (emi && emi.status === 'active' && emi.next_due_date) {
      alerts.push({
        id: `alert-emi-${emi.id}`,
        type: 'info',
        title: `EMI Installment Due: ${emi.loan_name}`,
        message: `Installment of ₹${parseFloat(emi.installment_amount || 0).toFixed(2)} due on ${emi.next_due_date}.`,
        time: 'Upcoming'
      });
    }
  });

  if (alerts.length === 0) {
    alerts.push({
      id: 'alert-clean',
      type: 'success',
      title: '✅ All Subscriptions Verified',
      message: 'No urgent renewal debits or spending leaks detected for the next 7 days.',
      time: 'Updated just now'
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-amber-950/40 via-purple-950/40 to-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <Bell className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
                <span>Notification Center</span>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-500/40 rounded-full">
                  {alerts.length} ALERTS
                </span>
              </h3>
              <p className="text-xs text-slate-400">Live renewal alerts & browser push controls</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-slate-800/80 text-slate-400 hover:text-white border border-slate-700/60 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Browser Push Permission Banner */}
        <div className="p-4 bg-slate-950/90 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2.5 text-xs text-slate-300">
            <Volume2 className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <div>
              <span className="font-semibold block text-slate-200">Desktop Web Push</span>
              <span className="text-[11px] text-slate-400">
                Status: {browserPermission === 'granted' ? '🟢 Allowed' : browserPermission === 'denied' ? '🔴 Blocked in Browser' : '🟡 Not Enabled'}
              </span>
            </div>
          </div>

          <button
            onClick={handleEnableWebPush}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-md ${
              testSent
                ? 'bg-amber-500 text-slate-950 scale-105'
                : browserPermission === 'granted'
                ? 'bg-emerald-950 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900'
                : 'bg-gradient-to-r from-amber-500 to-purple-600 text-white hover:opacity-90'
            }`}
          >
            {testSent ? '🔔 Test Fired!' : browserPermission === 'granted' ? 'Test Notification' : 'Enable Web Push'}
          </button>
        </div>

        {/* Alerts List */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          {alerts.map(item => (
            <div 
              key={item.id}
              className={`p-4 rounded-2xl border flex items-start space-x-3 transition-all ${
                item.type === 'critical'
                  ? 'bg-rose-950/60 border-rose-500/60 text-rose-200 shadow-lg shadow-rose-950/40'
                  : item.type === 'warning'
                  ? 'bg-amber-950/60 border-amber-500/50 text-amber-200'
                  : item.type === 'success'
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                  : 'bg-slate-950/60 border-slate-800 text-slate-200'
              }`}
            >
              {item.type === 'critical' ? (
                <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              ) : item.type === 'warning' ? (
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              ) : item.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <Clock className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
              )}

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold truncate pr-2">{item.title}</h4>
                  <span className="text-[10px] opacity-75 shrink-0 font-semibold">{item.time}</span>
                </div>
                <p className="text-xs opacity-90 mt-1 leading-relaxed">{item.message}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-500">
            Autopay Guard automatically scans for upcoming renewals every 24 hours.
          </p>
        </div>

      </div>
    </div>
  );
}
