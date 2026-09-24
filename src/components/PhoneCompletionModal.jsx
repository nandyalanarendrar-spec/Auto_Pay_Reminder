import React, { useState } from 'react';
import { Phone, Shield, Check, X, Sparkles, MessageSquare } from 'lucide-react';
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
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    const cleanPhone = phoneNumber.replace(/\s+/g, '');
    if (!cleanPhone) {
      setErrorMsg('Please enter a valid mobile number.');
      return;
    }
    if (countryCode === '+91' && !/^[6-9]\d{9}$/.test(cleanPhone)) {
      setErrorMsg('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    const formattedPhone = `${countryCode}${cleanPhone}`;
    setIsLoading(true);

    try {
      // 1. Update Supabase Auth user metadata
      if (isSupabaseConfigured && supabase) {
        const { data, error } = await supabase.auth.updateUser({
          data: {
            phone_number: formattedPhone,
            country_code: countryCode
          }
        });
        if (error) throw error;

        // 2. Also send backend API update
        try {
          const sessionRes = await supabase.auth.getSession();
          const token = sessionRes.data?.session?.access_token;
          const headers = { 'Content-Type': 'application/json' };
          if (token) headers['Authorization'] = `Bearer ${token}`;

          await fetch('http://127.0.0.1:8000/api/v1/auth/complete-phone', {
            method: 'POST',
            headers,
            body: JSON.stringify({ phone_number: formattedPhone })
          });
        } catch (apiErr) {
          console.warn("Backend phone update note:", apiErr);
        }

        if (onPhoneUpdated && data?.user) {
          onPhoneUpdated(data.user);
        }
      } else {
        // Local Demo fallback
        if (onPhoneUpdated) {
          onPhoneUpdated({
            ...currentUser,
            phone_number: formattedPhone,
            user_metadata: {
              ...(currentUser?.user_metadata || {}),
              phone_number: formattedPhone
            }
          });
        }
      }

      onClose();
    } catch (err) {
      console.error("Phone completion error:", err);
      setErrorMsg(err.message || 'Failed to save phone number. Please try again.');
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
          className="absolute top-4 right-4 p-1.5 rounded-full bg-slate-800/80 text-slate-400 hover:text-white transition-colors"
          title="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header Icon & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 p-0.5 shadow-lg shadow-emerald-950/50">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-emerald-400">
              <MessageSquare className="w-6 h-6" />
            </div>
          </div>

          <div>
            <h3 className="text-lg font-extrabold text-white tracking-tight flex items-center space-x-1.5">
              <span>Enable WhatsApp Alerts</span>
              <Sparkles className="w-4 h-4 text-emerald-400" />
            </h3>
            <p className="text-xs text-slate-400">Complete your profile to receive payment reminders</p>
          </div>
        </div>

        {/* Explanation Message */}
        <div className="p-3.5 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl text-xs text-emerald-200/90 leading-relaxed">
          📱 <b>Instant WhatsApp Reminders</b>: Enter your mobile number so AutoPay Guard can send direct WhatsApp alerts before your subscriptions & EMIs are auto-debited!
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-500/50 text-rose-300 text-xs font-semibold">
            {errorMsg}
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <PhoneInput
            label="YOUR WHATSAPP MOBILE NUMBER"
            countryCode={countryCode}
            onCountryCodeChange={setCountryCode}
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            required
          />

          <div className="pt-2 space-y-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 transition-all cursor-pointer shadow-lg shadow-emerald-950/50 flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{isLoading ? 'Saving Phone Number...' : 'Save & Enable WhatsApp Reminders'}</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              className="w-full py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            >
              Remind Me Later
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
