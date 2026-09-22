import React from 'react';

export default function SocialLoginButton({ onGoogleClick }) {
  return (
    <div className="w-full space-y-4 pt-3">
      
      {/* Clean Divider Line */}
      <div className="relative flex items-center justify-center my-3">
        <div className="w-full border-t border-white/10"></div>
        <span className="bg-[#151221] px-3 text-[10px] font-extrabold text-[#7F7990] tracking-widest uppercase absolute rounded-md">
          OR
        </span>
      </div>

      {/* Continue with Google Button */}
      <button
        type="button"
        onClick={onGoogleClick}
        className="w-full py-3 px-4 rounded-xl bg-[#1A1626] border border-white/15 hover:border-[#7C3AED]/60 hover:bg-[#221D33] text-white text-xs font-bold flex items-center justify-center space-x-2.5 transition-all duration-200 shadow-md active:scale-[0.99]"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24">
          <path
            fill="#EA4335"
            d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
          />
          <path
            fill="#4285F4"
            d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
          />
          <path
            fill="#FBBC05"
            d="M5.6 14.8c-.3-.8-.4-1.8-.4-2.8s.1-2 .4-2.8L1.9 6.3C.7 8.7 0 10.3 0 12s.7 3.3 1.9 5.7l3.7-2.9z"
          />
          <path
            fill="#34A853"
            d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"
          />
        </svg>
        <span>Continue with Google</span>
      </button>

    </div>
  );
}
