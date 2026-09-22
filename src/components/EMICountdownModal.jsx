import React, { useState, useEffect } from 'react';
import { Clock, X, CheckCircle2, Landmark, DollarSign, Calendar, RefreshCw, Percent } from 'lucide-react';

export default function EMICountdownModal({
  isOpen,
  onClose,
  emi,
  onPayInstallment,
  onRetrySync
}) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  useEffect(() => {
    if (!emi || !emi.next_due_date) return;

    const calculateTimeLeft = () => {
      const targetStr = emi.next_due_date.includes('T')
        ? emi.next_due_date
        : `${emi.next_due_date}T00:00:00`;
      
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
  }, [emi]);

  if (!isOpen || !emi) return null;

  const padZero = (num) => String(num).padStart(2, '0');

  // Radial tick ring generator for SVG gauges
  const renderRadialGauge = (value, maxValue, label) => {
    const percentage = Math.min(100, Math.max(0, (value / maxValue) * 100));
    const radius = 38;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="flex flex-col items-center">
        <div className="relative w-28 h-28 sm:w-32 sm:h-32 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="46"
              stroke="#1e293b"
              strokeWidth="2"
              strokeDasharray="1 3"
              fill="none"
            />
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="#0f172a"
              strokeWidth="6"
              fill="none"
            />
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="#A855F7"
              strokeWidth="6"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="none"
              className="transition-all duration-1000 ease-linear"
              style={{
                filter: 'drop-shadow(0px 0px 8px #A855F7)'
              }}
            />
          </svg>

          <div className="absolute flex flex-col items-center justify-center text-center">
            <span className="text-2xl sm:text-3xl font-black font-mono text-purple-300 tracking-wider">
              {padZero(value)}
            </span>
          </div>
        </div>

        <span className="mt-2 text-[10px] font-bold tracking-widest text-purple-400 uppercase">
          {label}
        </span>
      </div>
    );
  };

  const totalInst = emi.total_installments || 12;
  const paidInst = emi.installments_paid || 0;
  const instAmt = parseFloat(emi.installment_amount || 0);
  const remAmt = emi.remaining_amount !== undefined ? parseFloat(emi.remaining_amount) : (totalInst - paidInst) * instAmt;
  const completionPct = Math.round((paidInst / totalInst) * 100) || 0;
  const isCompleted = paidInst >= totalInst;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn">
      <div 
        className="glass-panel w-full max-w-2xl rounded-3xl p-6 sm:p-8 shadow-2xl border border-purple-500/30 bg-slate-900/90 text-white relative overflow-hidden"
        style={{
          boxShadow: '0 0 50px rgba(168, 85, 247, 0.15)'
        }}
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between pb-6 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center">
              <Landmark className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white">{emi.loan_name}</h3>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  isCompleted ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30' : 'bg-purple-950 text-purple-300 border border-purple-500/30'
                }`}>
                  {isCompleted ? 'Completed' : 'Active EMI Loan'}
                </span>
              </div>
              <p className="text-xs text-slate-400">Full EMI Payoff Contract & Live Auto-Debit Countdown</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Live Countdown Section */}
        <div className="my-6">
          <div className="flex items-center justify-center mb-6">
            <span className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping"></span>
              <span>TIME REMAINING UNTIL NEXT EMI DEBIT</span>
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 sm:gap-4 justify-items-center">
            {renderRadialGauge(timeLeft.days, 30, 'DAYS')}
            {renderRadialGauge(timeLeft.hours, 24, 'HOURS')}
            {renderRadialGauge(timeLeft.minutes, 60, 'MINUTES')}
            {renderRadialGauge(timeLeft.seconds, 60, 'SECONDS')}
          </div>
        </div>

        {/* EMI Mandate & Progress Breakdown */}
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Landmark className="w-4 h-4" />
            <span>EMI Loan Payoff Breakdown</span>
          </h4>

          {/* Progress Bar */}
          <div className="bg-slate-950/60 rounded-2xl p-4 border border-slate-800">
            <div className="flex justify-between text-xs mb-2">
              <span className="text-slate-400">Installments Progress ({paidInst}/{totalInst} Paid)</span>
              <span className="text-purple-300 font-bold">{completionPct}% Complete</span>
            </div>
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-[#ff007f] transition-all duration-500"
                style={{ width: `${completionPct}%` }}
              />
            </div>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-950/60 rounded-2xl p-4 border border-slate-800">
              <span className="text-[11px] text-slate-400">Monthly Outflow</span>
              <p className="text-lg font-bold text-white mt-1">₹{instAmt.toLocaleString()}<span className="text-xs text-slate-400 font-normal">/mo</span></p>
            </div>

            <div className="bg-slate-950/60 rounded-2xl p-4 border border-slate-800">
              <span className="text-[11px] text-slate-400">Next Due Date</span>
              <p className="text-lg font-bold text-purple-300 mt-1">{emi.next_due_date || 'N/A'}</p>
            </div>

            <div className="bg-slate-950/60 rounded-2xl p-4 border border-slate-800">
              <span className="text-[11px] text-slate-400">Remaining Loan Balance</span>
              <p className="text-lg font-bold text-amber-300 mt-1">₹{remAmt.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
          {emi.calendar_sync_status?.toUpperCase() === 'FAILED' ? (
            <button
              onClick={() => onRetrySync && onRetrySync(emi.id, 'emi')}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-xs font-semibold transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Calendar Sync</span>
            </button>
          ) : (
            <span className="text-xs text-slate-500 flex items-center space-x-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Calendar Auto-Sync Active</span>
            </span>
          )}

          {!isCompleted && onPayInstallment && (
            <button
              onClick={() => {
                onPayInstallment(emi.id);
                onClose();
              }}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-purple-600/30 transition-all transform hover:scale-[1.02]"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Pay Installment (₹{instAmt.toLocaleString()})</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
