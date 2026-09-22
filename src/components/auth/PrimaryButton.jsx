import React from 'react';
import { Loader2 } from 'lucide-react';

export default function PrimaryButton({
  children,
  type = "submit",
  onClick,
  isLoading = false,
  loadingText = "Processing...",
  disabled = false,
  className = ""
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isLoading || disabled}
      className={`w-full py-3.5 px-6 rounded-xl font-bold text-sm text-white transition-all duration-200 flex items-center justify-center space-x-2 btn-gradient-primary active:scale-[0.98] ${
        isLoading || disabled
          ? 'opacity-60 cursor-not-allowed'
          : ''
      } ${className}`}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-white" />
          <span>{loadingText}</span>
        </>
      ) : (
        <span>{children}</span>
      )}
    </button>
  );
}
