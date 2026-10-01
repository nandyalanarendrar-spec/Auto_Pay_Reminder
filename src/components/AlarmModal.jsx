import React, { useEffect, useRef } from 'react';
import { AlarmClock, BellOff, Clock3 } from 'lucide-react';
import { startAlarmSound } from '../utils/browserNotifications';

export default function AlarmModal({ reminder, onDismiss, onSnooze }) {
  const stopFnRef = useRef(null);

  useEffect(() => {
    stopFnRef.current = startAlarmSound();

    let vibrateInterval = null;
    if ('vibrate' in navigator) {
      navigator.vibrate([500, 200, 500]);
      vibrateInterval = setInterval(() => navigator.vibrate([500, 200, 500]), 1400);
    }

    return () => {
      if (stopFnRef.current) stopFnRef.current();
      if (vibrateInterval) clearInterval(vibrateInterval);
    };
  }, []);

  const handleDismiss = () => {
    if (stopFnRef.current) stopFnRef.current();
    onDismiss();
  };

  const handleSnooze = () => {
    if (stopFnRef.current) stopFnRef.current();
    onSnooze();
  };

  if (!reminder) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-rose-950/90 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-sm mx-4 rounded-3xl bg-slate-950 border-2 border-rose-500 shadow-[0_0_80px_rgba(244,63,94,0.5)] p-8 text-center">
        <div className="mx-auto mb-5 w-20 h-20 rounded-full bg-rose-500/20 border-2 border-rose-500 flex items-center justify-center animate-pulse">
          <AlarmClock className="w-10 h-10 text-rose-400" />
        </div>

        <div className="text-[11px] font-bold text-rose-400 uppercase tracking-widest mb-2">
          Most Important Task Due
        </div>
        <h2 className="text-2xl font-extrabold text-white mb-2 break-words">
          {reminder.title}
        </h2>
        {reminder.notes && (
          <p className="text-sm text-slate-400 mb-6">{reminder.notes}</p>
        )}

        <div className="flex flex-col gap-3 mt-6">
          <button
            onClick={handleDismiss}
            className="w-full flex items-center justify-center gap-2 px-4 py-3.5 rounded-2xl bg-rose-500 hover:bg-rose-400 text-white font-bold text-base transition-colors"
          >
            <BellOff className="w-5 h-5" />
            Stop Alarm
          </button>
          <button
            onClick={handleSnooze}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-slate-900 border border-slate-700 hover:border-slate-500 text-slate-200 font-semibold text-sm transition-colors"
          >
            <Clock3 className="w-4 h-4" />
            Snooze 5 Minutes
          </button>
        </div>
      </div>
    </div>
  );
}
