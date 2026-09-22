import React from 'react';

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen w-full bg-[#0D0B14] text-white flex items-center justify-center p-4 relative overflow-hidden font-sans selection:bg-[#7C3AED] selection:text-white">
      
      {/* Dark Grid Background Overlay (Matching Screenshot) */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.08) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.08) 1px, transparent 1px)
          `,
          backgroundSize: '36px 36px'
        }}
      ></div>

      {/* Radial Purple Ambient Lighting */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#6D28D9] opacity-20 blur-[150px] pointer-events-none rounded-full"></div>
      <div className="absolute bottom-10 left-10 w-[350px] h-[350px] bg-[#4C1D95] opacity-15 blur-[120px] pointer-events-none rounded-full"></div>

      {/* Main Container */}
      <div className="relative z-10 w-full max-w-[420px] my-6">
        {children}
      </div>

    </div>
  );
}
