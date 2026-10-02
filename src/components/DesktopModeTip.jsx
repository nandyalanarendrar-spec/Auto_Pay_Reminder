import React, { useState } from 'react';
import { Smartphone, X } from 'lucide-react';

const STORAGE_KEY = 'autopay_dismiss_desktop_tip';

const isPhoneInDesktopMode = () => {
  try {
    return (
      window.matchMedia('(pointer: coarse)').matches &&
      window.innerWidth >= 900 &&
      Math.min(window.screen.width, window.screen.height) <= 600
    );
  } catch (e) {
    return false;
  }
};

export default function DesktopModeTip() {
  const [visible, setVisible] = useState(() => {
    try {
      return isPhoneInDesktopMode() && localStorage.getItem(STORAGE_KEY) !== 'true';
    } catch (e) {
      return false;
    }
  });

  if (!visible) return null;

  const dismiss = () => {
    try { localStorage.setItem(STORAGE_KEY, 'true'); } catch (e) {}
    setVisible(false);
  };

  return (
    <div className="mb-4 flex items-start justify-between gap-3 rounded-2xl border border-indigo-500/40 bg-indigo-950/70 p-3 text-xs text-indigo-100">
      <div className="flex items-start gap-2">
        <Smartphone className="w-5 h-5 text-indigo-300 flex-shrink-0" />
        <p>
          You are viewing the desktop version. For the best phone experience, open the browser menu (⋮) and turn off
          <strong> Desktop site</strong>.
        </p>
      </div>
      <button onClick={dismiss} className="p-1 rounded-lg hover:bg-white/10 cursor-pointer" aria-label="Dismiss">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
