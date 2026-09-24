import React, { useState } from 'react';
import { Phone, Shield, Check, X, Sparkles, MessageSquare, Mail, ShieldCheck } from 'lucide-react';
import PhoneInput from './auth/PhoneInput';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';

export default function PhoneCompletionModal({
  isOpen,
  onClose,
  currentUser,
  onPhoneUpdated
}) {
  const [countryCode, setCountryCode] = useState('+91');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpStep, setOtpStep] = useState('input'); // 'input' | 'otp'
  const [otpCode, setOtpCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  if (!isOpen) return null;

  const userEmail = currentUser?.email || 'user@autopayguard.com';

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setStatusMsg('');

    const cleanPhone = phoneNumber.replace(/\s+/g, '');
    if (!cleanPhone) {
      setErrorMsg('Please enter a valid mobile number.');
      return;
    }
    if (countryCode === '+91' && !/^[6-9]\d{9}$/.test(cleanPhone)) {
      setErrorMsg('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    setIsLoading(true);

    try {
      // Use Supabase's built-in OTP email — same system as registration
      if (isSupabaseConfigured && supabase) {
        const { error } = await supabase.auth.signInWithOtp({
          email: userEmail,
          options: { shouldCreateUser: false }
        });
        if (error) {
          setErrorMsg(error.message || 'Failed to send OTP email.');
          setIsLoading(false);
          return;
        }
      }

      setOtpStep('otp');
      setOtpCode(''); // User must check Gmail manually
      setStatusMsg(`📩 6-digit OTP sent to ${userEmail}. Check your Gmail inbox!`);
    } catch (err) {
      console.error("OTP request error:", err);
      setErrorMsg('Failed to send OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setStatusMsg('');

    if (!otpCode || otpCode.trim().length < 6) {
      setErrorMsg('Please enter the 6-digit OTP code sent to your email.');
      return;
    }

    const cleanPhone = phoneNumber.replace(/\s+/g, '');
    const formattedPhone = `${countryCode}${cleanPhone}`;
    setIsLoading(true);

    try {
      // Verify OTP using Supabase's built-in system — same as registration verification
      if (isSupabaseConfigured && supabase) {
        const { data: verifyData, error: verifyError } = await supabase.auth.verifyOtp({
          email: userEmail,
          token: otpCode.trim(),
          type: 'email'
        });

        if (verifyError) {
          setErrorMsg(verifyError.message || 'Invalid or expired OTP code.');
          setIsLoading(false);
          return;
        }

        // OTP verified! Now update the phone number
        let updatedUserObj = currentUser;
        try {
          const { data: supaData } = await supabase.auth.updateUser({
            data: { phone_number: formattedPhone, country_code: countryCode }
          });
          if (supaData?.user) updatedUserObj = supaData.user;
        } catch (e) {}

        // Also update in backend database
        try {
          const { data: { session } } = await supabase.auth.getSession();
          const token = session?.access_token;
          const headers = { 'Content-Type': 'application/json' };
          if (token) headers['Authorization'] = `Bearer ${token}`;

          await fetch('http://127.0.0.1:8000/api/v1/auth/complete-phone', {
            method: 'POST',
            headers,
            body: JSON.stringify({ phone_number: formattedPhone })
          });
        } catch (e) {}

        if (onPhoneUpdated) {
          onPhoneUpdated(updatedUserObj);
        }
        onClose();
      }
    } catch (err) {
      console.error("OTP verification error:", err);
      setErrorMsg('Failed to verify OTP code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden p-6 text-white space-y-5">
        
        {/* Top Dismiss Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full bg-slate-800/80 text-slate-400 hover:text-white transition-colors cursor-pointer"
          title="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header Icon & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 p-0.5 shadow-lg shadow-emerald-950/50">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
          </div>

          <div>
            <h3 className="text-lg font-extrabold text-white tracking-tight flex items-center space-x-1.5">
              <span>Security WhatsApp Setup</span>
              <Sparkles className="w-4 h-4 text-emerald-400" />
            </h3>
            <p className="text-xs text-slate-400">Verify your identity via Email OTP</p>
          </div>
        </div>

        {/* Status or Error Messages */}
        {errorMsg && (
          <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-500/50 text-rose-300 text-xs font-semibold">
            {errorMsg}
          </div>
        )}

        {statusMsg && (
          <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-xs font-semibold">
            {statusMsg}
          </div>
        )}

        {/* Form Steps */}
        {otpStep === 'input' ? (
          <form onSubmit={handleRequestOtp} className="space-y-4">
            <PhoneInput
              label="YOUR WHATSAPP MOBILE NUMBER"
              countryCode={countryCode}
              onCountryCodeChange={setCountryCode}
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              required
            />

            <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs text-indigo-200 leading-relaxed flex items-start space-x-2">
              <Mail className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <span>Identity Verification: A 6-digit OTP code will be sent to <b>{userEmail}</b> to confirm ownership.</span>
            </div>

            <div className="pt-2 space-y-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 transition-all cursor-pointer shadow-lg shadow-indigo-950/50 flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <Mail className="w-4 h-4" />
                <span>{isLoading ? 'Sending OTP to Email...' : '📩 Send Verification OTP to Email'}</span>
              </button>

              <button
                type="button"
                onClick={onClose}
                className="w-full py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
              >
                Remind Me Later
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-4 animate-fadeIn">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Target Mobile Number:</span>
                <button
                  type="button"
                  onClick={() => setOtpStep('input')}
                  className="text-[11px] font-bold text-amber-400 hover:underline cursor-pointer"
                >
                  Edit
                </button>
              </div>
              <p className="text-sm font-bold text-emerald-300 font-mono">{countryCode} {phoneNumber}</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Enter 6-Digit Verification OTP</label>
              <input
                type="text"
                required
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="e.g. 749204"
                className="w-full px-3.5 py-2.5 text-base font-bold tracking-widest text-center bg-slate-950 border border-emerald-500/60 rounded-xl text-emerald-300 placeholder-slate-600 focus:outline-none focus:border-emerald-400 font-mono"
              />
            </div>

            <div className="flex items-center space-x-2 pt-1">
              <button
                type="button"
                onClick={() => setOtpStep('input')}
                className="w-1/3 py-2.5 px-3 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 cursor-pointer"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="w-2/3 py-2.5 px-4 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 shadow-lg shadow-emerald-950/60 cursor-pointer flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                <span>{isLoading ? 'Verifying...' : 'Verify OTP & Enable'}</span>
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}
