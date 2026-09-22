import React from 'react';

export default function GlassCard({ children, topError, className = '' }) {
  return (
    <div className="relative w-full">
      
      {/* Floating Top Error Pill */}
      {topError && (
        <div className="flex justify-center mb-4 animate-fadeIn">
          <div className="bg-[#12192B] border border-rose-500/50 text-white text-xs font-semibold px-4 py-2 rounded-full flex items-center space-x-2 shadow-xl">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
            <span>{topError}</span>
          </div>
        </div>
      )}

      {/* Main Glass Container (Matching Photo 1) */}
      <div 
        className={`w-full rounded-3xl p-6 sm:p-8 glass-container relative overflow-hidden ${className}`}
      >
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent pointer-events-none"></div>
        {children}
      </div>

    </div>
  );
}
