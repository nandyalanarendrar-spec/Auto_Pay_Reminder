import React from 'react';
import { MessageCircle } from 'lucide-react';

export default function ChatFab({ onClick }) {
  return (
    <button
      onClick={onClick}
      aria-label="Ask AutopayGuard AI"
      title="Ask AutopayGuard AI"
      className="fixed bottom-24 right-4 sm:right-6 z-40 w-14 h-14 rounded-full bg-gradient-to-tr from-cyan-500 to-indigo-600 text-white shadow-2xl shadow-indigo-500/40 border border-white/20 flex items-center justify-center hover:scale-110 active:scale-95 transition-transform cursor-pointer"
    >
      <span className="absolute inset-0 rounded-full bg-cyan-400/30 animate-ping" />
      <MessageCircle className="relative w-7 h-7" />
    </button>
  );
}
