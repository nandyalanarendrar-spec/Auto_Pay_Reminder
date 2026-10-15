import React, { useEffect, useState } from 'react';
import { TrendingUp, Hourglass, ChevronRight, X } from 'lucide-react';

const STORAGE_KEY = 'autopay_dismissed_insight_alerts';
const NOTIFIED_KEY = 'autopay_notified_insight_alerts';

const readIds = (key) => {
  try {
    return JSON.parse(localStorage.getItem(key) || '[]');
  } catch (e) {
    return [];
  }
};

const writeIds = (key, ids) => {
  try {
    localStorage.setItem(key, JSON.stringify(ids.slice(-100)));
  } catch (e) {}
};

const alertKey = (a) => `${a.item_id}:${a.kind}`;

export default function InsightAlertsBanner({ alerts, onOpenReview }) {
  const [dismissed, setDismissed] = useState(() => readIds(STORAGE_KEY));

  // Browser notification, once per alert on this device, only when the user already allowed notifications.
  useEffect(() => {
    if (!alerts || alerts.length === 0) return;
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return;
    const done = readIds(NOTIFIED_KEY);
    const fresh = alerts.filter((a) => !done.includes(alertKey(a)));
    fresh.forEach((a) => {
      try {
        new Notification(a.title, { body: a.message });
      } catch (e) {}
    });
    if (fresh.length) writeIds(NOTIFIED_KEY, [...done, ...fresh.map(alertKey)]);
  }, [alerts]);

  const visible = (alerts || []).filter((a) => !dismissed.includes(alertKey(a)));
  if (visible.length === 0) return null;

  const dismiss = (a) => {
    const next = [...dismissed, alertKey(a)];
    setDismissed(next);
    writeIds(STORAGE_KEY, next);
  };

  return (
    <div className="space-y-2">
      {visible.map((a) => {
        const isHike = a.kind === 'price_hike';
        const Icon = isHike ? TrendingUp : Hourglass;
        const tone = isHike
          ? 'border-amber-500/50 from-amber-950/70 text-amber-200/90 bg-amber-500/20 border-amber-500/40'
          : 'border-rose-500/50 from-rose-950/70 text-rose-200/90 bg-rose-500/20 border-rose-500/40';
        const [border, from, sub, iconBg, iconBorder] = tone.split(' ');
        return (
          <div
            key={alertKey(a)}
            className={`w-full rounded-2xl p-4 border ${border} bg-gradient-to-r ${from} via-slate-900 to-slate-900 flex items-center justify-between gap-3 shadow-lg`}
          >
            <button onClick={onOpenReview} className="flex items-center space-x-3 min-w-0 text-left cursor-pointer flex-1">
              <div className={`w-10 h-10 rounded-xl ${iconBg} border ${iconBorder} flex items-center justify-center flex-shrink-0`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-white truncate">{a.title}</p>
                <p className={`text-xs ${sub}`}>{a.message}</p>
              </div>
              <ChevronRight className="w-5 h-5 text-white/70 flex-shrink-0" />
            </button>
            <button
              onClick={() => dismiss(a)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white cursor-pointer flex-shrink-0"
              aria-label="Dismiss alert"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
