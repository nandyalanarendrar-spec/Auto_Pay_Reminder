import React, { useState } from 'react';
import GlassCard from './GlassCard';
import PrimaryButton from './PrimaryButton';
import { MailCheck, ArrowLeft, RefreshCw, KeyRound, CheckCircle } from 'lucide-react';

export default function EmailVerificationView({ email, onVerifyOtp, onResendEmail, onNavigateLogin }) {
  const [otpCode, setOtpCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [resendMessage, setResendMessage] = useState('');

  const handleVerifySubmit = async (e) => {
    if (e) e.preventDefault();
    if (!otpCode || otpCode.trim().length < 6) {
      setErrorMessage('Please enter the full 6-digit verification code.');
      return;
    }

    setIsVerifying(true);
    setErrorMessage('');
    setResendMessage('');

    try {
      if (onVerifyOtp) {
        await onVerifyOtp(email, otpCode.trim());
      }
    } catch (err) {
      setErrorMessage(err.message || 'Invalid or expired OTP code. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    setResendMessage('');
    setErrorMessage('');
    try {
      if (onResendEmail) await onResendEmail(email);
      setResendMessage('Verification code resent to your email!');
    } catch (err) {
      setErrorMessage(err.message || 'Failed to resend verification email.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <GlassCard className="animate-fadeIn text-center">
      
      {/* Icon */}
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#10B981] to-[#3B82F6] p-0.5 shadow-lg shadow-[#10B981]/20 mx-auto mb-4">
        <div className="w-full h-full bg-[#080F1F] rounded-[14px] flex items-center justify-center">
          <MailCheck className="w-7 h-7 text-[#10B981]" />
        </div>
      </div>

      <h2 className="text-2xl font-extrabold text-white tracking-tight">
        Enter 6-Digit Email OTP
      </h2>

      <p className="text-xs text-[#B8BECC] mt-2 leading-relaxed">
        We sent a 6-digit verification code via Brevo SMTP to <br/>
        <span className="font-semibold text-white">{email || 'your email address'}</span>.
      </p>

      {/* OTP Code Form */}
      <form onSubmit={handleVerifySubmit} className="mt-5 space-y-4">
        <div className="relative">
          <input
            type="text"
            maxLength={6}
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
            placeholder="0 0 0 0 0 0"
            className="w-full py-3 px-4 text-center tracking-[0.5em] text-2xl font-extrabold font-mono text-white bg-slate-900/80 border border-white/15 rounded-xl focus:outline-none focus:border-[#10B981] focus:ring-1 focus:ring-[#10B981]"
            autoFocus
          />
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium">
            {errorMessage}
          </div>
        )}

        {resendMessage && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
            {resendMessage}
          </div>
        )}

        <PrimaryButton type="submit" disabled={isVerifying || otpCode.length < 6}>
          {isVerifying ? 'Verifying OTP...' : 'Verify & Log In'}
        </PrimaryButton>
      </form>

      <div className="mt-5 pt-4 border-t border-white/10 space-y-2">
        <button
          type="button"
          onClick={handleResend}
          disabled={isResending}
          className="w-full py-2.5 px-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 text-xs font-semibold text-slate-300 flex items-center justify-center space-x-2 transition-all hover:bg-white/10"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isResending ? 'animate-spin' : ''}`} />
          <span>{isResending ? 'Resending Code...' : 'Resend Email OTP Code'}</span>
        </button>

        <button
          type="button"
          onClick={onNavigateLogin}
          className="w-full text-xs text-slate-400 hover:text-white py-1 flex items-center justify-center space-x-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Sign In</span>
        </button>
      </div>

    </GlassCard>
  );
}
