import React, { useState, useEffect } from 'react';
import { Clock, X, CheckCircle2, AlertTriangle, Calendar, FileText, Trash2, CreditCard, ShieldCheck, Power, Info, ExternalLink } from 'lucide-react';

export default function AutopayCountdownModal({
  isOpen,
  onClose,
  subscription,
  onToggleAutopay,
  onViewReceipt,
  onDeleteSubscription
}) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  useEffect(() => {
    if (!subscription || !subscription.next_renewal_date) return;

    const calculateTimeLeft = () => {
      const targetStr = subscription.next_renewal_date.includes('T')
        ? subscription.next_renewal_date
        : `${subscription.next_renewal_date}T00:00:00`;
      
      const target = new Date(targetStr);
      const now = new Date();
      const diff = target - now;

      if (diff <= 0) {
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / 1000 / 60) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      setTimeLeft({ days, hours, minutes, seconds });
    };

    calculateTimeLeft();
    const interval = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(interval);
  }, [subscription]);

  if (!isOpen || !subscription) return null;

  const padZero = (num) => String(num).padStart(2, '0');

  // Radial tick ring generator for SVG gauges (Clean, spacious, zero overlapping)
  const renderRadialGauge = (value, maxValue, label) => {
    const percentage = Math.min(100, Math.max(0, (value / maxValue) * 100));
    const radius = 38;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32 flex items-center justify-center">
          
          {/* Radial Ticks SVG Background */}
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            {/* Outer Tick Marks Circle */}
            <circle
              cx="50"
              cy="50"
              r="46"
              stroke="#1e293b"
              strokeWidth="2"
              strokeDasharray="1 3"
              fill="none"
            />
            
            {/* Background Track Circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="#0f172a"
              strokeWidth="6"
              fill="none"
            />
            
            {/* Neon Glowing Active Progress Ring */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="#00F2FE"
              strokeWidth="6"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="none"
              className="transition-all duration-1000 ease-linear"
              style={{
                filter: 'drop-shadow(0px 0px 8px #00F2FE)'
              }}
            />
          </svg>

          {/* Digital 7-Segment Style Number */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span 
              className="text-3xl font-black text-cyan-300 tracking-wider drop-shadow-[0_0_12px_#00F2FE]"
              style={{ fontFamily: 'Courier New, monospace, sans-serif' }}
            >
              {padZero(value)}
            </span>
          </div>

        </div>

        {/* Label Below Gauge */}
        <span className="mt-3 text-xs font-black tracking-widest text-cyan-400 uppercase drop-shadow-[0_0_6px_#00F2FE]">
          {label}
        </span>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/90 backdrop-blur-lg animate-fadeIn overflow-y-auto">
      <div className="relative w-full max-w-5xl bg-slate-950 border-2 border-cyan-500/40 rounded-3xl shadow-[0_0_60px_rgba(0,242,254,0.2)] overflow-hidden flex flex-col max-h-[95vh]">
        
        {/* Header Bar */}
        <div className="p-5 sm:p-6 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 p-0.5 shadow-lg shadow-cyan-950/50">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-xl font-black text-cyan-300">
                {(subscription.name || subscription.merchant_name || 'A').charAt(0).toUpperCase()}
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h3 className="text-xl font-extrabold text-white tracking-tight">
                  {subscription.name || subscription.merchant_name}
                </h3>
                {subscription.autopay_enabled ? (
                  <span className="px-3 py-1 text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 rounded-full flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>AUTOPAY ON</span>
                  </span>
                ) : (
                  <span className="px-3 py-1 text-xs font-bold bg-rose-950 text-rose-300 border border-rose-500/40 rounded-full flex items-center space-x-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    <span>AUTOPAY OFF</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">Full Subscription Contract & Live Autopay Renewal Countdown</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2.5 rounded-full bg-slate-800/80 text-slate-400 hover:text-white border border-slate-700/60 hover:bg-slate-700 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Main Content Wrapper */}
        <div className="overflow-y-auto flex-1 divide-y divide-slate-800/80">
          
          {/* TOP SECTION: NEON RADIAL COUNTDOWN DISPLAY */}
          <div className="py-8 px-6 bg-slate-950 relative overflow-hidden flex flex-col items-center justify-center">
            
            {/* Ambient Glowing Background Orb */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-48 bg-cyan-500/10 blur-3xl pointer-events-none rounded-full" />
            
            <div className="text-center mb-8 relative z-10">
              <span className="px-3 py-1 text-xs font-bold tracking-widest text-cyan-300 bg-cyan-950/80 border border-cyan-500/30 rounded-full uppercase inline-flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                <span>TIME REMAINING UNTIL NEXT AUTOPAY DEBIT</span>
              </span>
            </div>

            {/* 4 Neon Radial Progress Gauges in Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-12 w-full max-w-3xl justify-items-center relative z-10 py-2">
              {renderRadialGauge(timeLeft.days, 30, 'DAYS')}
              {renderRadialGauge(timeLeft.hours, 24, 'HOURS')}
              {renderRadialGauge(timeLeft.minutes, 60, 'MINUTES')}
              {renderRadialGauge(timeLeft.seconds, 60, 'SECONDS')}
            </div>

          </div>

          {/* BOTTOM SECTION: ALL CONTRACT & VAULT DETAILS (No merging) */}
          <div className="p-6 sm:p-8 bg-slate-900/60 space-y-6">
            
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-extrabold tracking-wider text-slate-200 uppercase flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <span>Subscription Vault & Mandate Breakdown</span>
              </h4>
              <span className="text-xs text-slate-400 font-medium">All amounts in Indian Rupees (INR ₹)</span>
            </div>

            {/* Detailed 4-Column Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* Card 1: Monthly Cost */}
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 shadow-md">
                <span className="text-slate-400 text-xs font-medium block">Monthly Outflow</span>
                <span className="text-xl font-black text-white mt-1 block">
                  ₹{parseFloat(subscription.amount || 0).toFixed(2)}
                  <span className="text-xs font-normal text-slate-400"> / {subscription.billing_cycle || 'monthly'}</span>
                </span>
              </div>

              {/* Card 2: Next Renewal Date */}
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 shadow-md">
                <span className="text-slate-400 text-xs font-medium block">Next Renewal Date</span>
                <span className="text-sm font-extrabold text-cyan-300 mt-1.5 block">
                  {subscription.next_renewal_date || subscription.next_payment_date || 'N/A'}
                </span>
              </div>

              {/* Card 3: Category */}
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 shadow-md">
                <span className="text-slate-400 text-xs font-medium block">Category & Plan</span>
                <span className="text-sm font-bold text-slate-200 mt-1.5 block">
                  {subscription.category || 'General'}
                </span>
              </div>

              {/* Card 4: Linked Payment Method */}
              <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 shadow-md">
                <span className="text-slate-400 text-xs font-medium block">Payment Method</span>
                <span className="text-sm font-bold text-slate-200 mt-1.5 flex items-center space-x-1.5">
                  <CreditCard className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span className="truncate">{subscription.payment_method || 'UPI Autopay / Card'}</span>
                </span>
              </div>

            </div>

            {/* Information Alert Banner */}
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-start space-x-3 text-xs text-slate-300">
              <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-slate-200 block">Autopay Protection & E-Mandate Guidance:</span>
                <p className="text-slate-400 leading-relaxed">
                  {subscription.autopay_enabled 
                    ? 'Autopay is currently ACTIVE for this merchant. On the next renewal date, your linked bank account will be automatically debited. You can pause Autopay anytime using the toggle below.' 
                    : 'Autopay is currently PAUSED (OFF). Auto-debit permissions are disabled and excluded from your monthly spend projections. Remember to update your bank app if necessary.'}
                </p>
              </div>
            </div>

          </div>

        </div>

        {/* Footer Action Bar */}
        <div className="p-5 bg-slate-950 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
          
          <button
            onClick={() => onToggleAutopay(subscription.id)}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer shadow-md ${
              subscription.autopay_enabled
                ? 'bg-emerald-950 border-emerald-500/50 text-emerald-300 hover:bg-emerald-900'
                : 'bg-rose-950 border-rose-500/50 text-rose-300 hover:bg-rose-900'
            }`}
          >
            <Power className="w-4 h-4" />
            <span>{subscription.autopay_enabled ? 'Pause Autopay (Set OFF)' : 'Enable Autopay (Set ON)'}</span>
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => onViewReceipt(subscription)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-cyan-300 text-xs font-semibold transition-all cursor-pointer"
              title="View Receipt Vault"
            >
              <FileText className="w-4 h-4 text-cyan-400" />
              <span className="hidden sm:inline">Receipt Vault</span>
            </button>

            <button
              onClick={() => {
                onClose();
                onDeleteSubscription(subscription.id);
              }}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-rose-500/50 text-rose-300 text-xs font-semibold transition-all cursor-pointer"
              title="Delete Subscription"
            >
              <Trash2 className="w-4 h-4 text-rose-400" />
              <span className="hidden sm:inline">Delete</span>
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}
