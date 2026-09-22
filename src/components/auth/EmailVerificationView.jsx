import React, { useState } from 'react';
import GlassCard from './GlassCard';
import PrimaryButton from './PrimaryButton';
import { MailCheck, ArrowLeft, RefreshCw } from 'lucide-react';

export default function EmailVerificationView({ email, onResendEmail, onNavigateLogin }) {
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  const handleResend = async () => {
    setIsResending(true);
    setResendMessage('');
    try {
      if (onResendEmail) await onResendEmail(email);
      setResendMessage('Verification email resent successfully!');
    } catch (err) {
      setResendMessage(err.message || 'Failed to resend verification email.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <GlassCard className="animate-fadeIn text-center">
      
      {/* Icon */}
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#ff007f] to-[#9b1cff] p-0.5 shadow-lg shadow-[#ff007f]/20 mx-auto mb-4">
        <div className="w-full h-full bg-[#080F1F] rounded-[14px] flex items-center justify-center">
          <MailCheck className="w-7 h-7 text-[#ff007f]" />
        </div>
      </div>

      <h2 className="text-2xl font-extrabold text-white tracking-tight">
        Check Your Email
      </h2>

      <p className="text-xs text-[#B8BECC] mt-2 leading-relaxed">
        We sent a verification link to <span className="font-semibold text-white">{email || 'your email'}</span>. Please click the link to activate your Autopay Protection account.
      </p>

      {resendMessage && (
        <div className="mt-4 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium">
          {resendMessage}
        </div>
      )}

      <div className="mt-6 space-y-3">
        <button
          type="button"
          onClick={handleResend}
          disabled={isResending}
          className="w-full py-3 px-4 rounded-xl bg-white/5 border border-white/15 hover:border-white/30 text-xs font-semibold text-white flex items-center justify-center space-x-2 transition-all hover:bg-white/10"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isResending ? 'animate-spin' : ''}`} />
          <span>{isResending ? 'Resending Link...' : 'Resend Verification Email'}</span>
        </button>

        <PrimaryButton onClick={onNavigateLogin}>
          Back to Sign In
        </PrimaryButton>
      </div>

    </GlassCard>
  );
}
