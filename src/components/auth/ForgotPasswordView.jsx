import React, { useState } from 'react';
import GlassCard from './GlassCard';
import InputField from './InputField';
import PrimaryButton from './PrimaryButton';
import { Mail, KeyRound, ArrowLeft, CheckCircle2 } from 'lucide-react';

export default function ForgotPasswordView({ onResetRequested, onNavigateLogin, onOtpSent }) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }

    setIsLoading(true);
    try {
      await onResetRequested(email);
      if (onOtpSent) {
        onOtpSent(email);
      } else {
        setIsSuccess(true);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Unable to send password reset email.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassCard className="animate-fadeIn">
      
      {/* Icon Header */}
      <div className="flex justify-center mb-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#ff007f] to-[#9b1cff] p-0.5 shadow-lg shadow-[#ff007f]/20">
          <div className="w-full h-full bg-[#080F1F] rounded-[14px] flex items-center justify-center">
            <KeyRound className="w-6 h-6 text-[#ff007f]" />
          </div>
        </div>
      </div>

      {/* Heading */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-extrabold tracking-tight text-white">
          Reset Password
        </h2>
        <p className="text-xs text-[#B8BECC] mt-1">
          Enter your email and we'll send you a password reset link.
        </p>
      </div>

      {/* Success State Notification */}
      {isSuccess ? (
        <div className="text-center space-y-4 py-2">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <p className="text-xs text-emerald-300 font-medium">
            Password reset link sent! Please check your inbox.
          </p>
          <button
            type="button"
            onClick={onNavigateLogin}
            className="text-xs font-bold text-[#ff007f] hover:underline flex items-center justify-center space-x-1.5 mx-auto pt-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Sign In</span>
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium text-center">
              {errorMessage}
            </div>
          )}

          <InputField
            label="EMAIL ADDRESS"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="hello@design.com"
            icon={Mail}
            required
          />

          <div className="pt-2">
            <PrimaryButton isLoading={isLoading} loadingText="Sending Link...">
              Send Reset Link
            </PrimaryButton>
          </div>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={onNavigateLogin}
              className="text-xs font-semibold text-[#B8BECC] hover:text-white transition-colors inline-flex items-center space-x-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>
          </div>

        </form>
      )}

    </GlassCard>
  );
}
