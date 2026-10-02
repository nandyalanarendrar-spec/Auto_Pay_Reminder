import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function Navbar({ currentUser }) {
  const name =
    currentUser?.user_metadata?.name ||
    currentUser?.name ||
    (currentUser?.email ? currentUser.email.split('@')[0] : '');

  return (
    <header className="sticky top-0 z-30 glass-panel border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-center">
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-600 to-indigo-500 p-0.5 shadow-lg shadow-[#ff007f]/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-[#ff007f]" />
            </div>
          </div>
          <div className="text-center sm:text-left">
            <h1 className="text-xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-200 tracking-tight leading-tight">
              Autopay Guard
            </h1>
            {name && (
              <p className="text-xs font-semibold text-indigo-300 leading-tight">Hi, {name}</p>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
