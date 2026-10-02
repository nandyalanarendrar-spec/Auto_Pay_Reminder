import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 glass-panel border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-600 to-indigo-500 p-0.5 shadow-lg shadow-[#ff007f]/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-[#ff007f]" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-200 tracking-tight">
                Autopay Guard
              </h1>
              <span className="hidden sm:inline px-2 py-0.5 text-[9px] font-bold tracking-wider text-indigo-300 bg-indigo-950/80 border border-indigo-500/30 rounded-full uppercase">
                PRO V1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden lg:block">Smart Subscription & Autopay Renewal Vault</p>
          </div>
        </div>
      </div>
    </header>
  );
}
