import React, { useState } from 'react';
import { MessageSquare, ExternalLink, Send, CheckCircle2, AlertCircle, X, ShieldCheck, Sparkles, Smartphone, Edit3 } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';

export default function WhatsAppActivationModal({
  isOpen,
  onClose,
  currentUser,
  onOpenProfile
}) {
  const [waBusinessNumber, setWaBusinessNumber] = useState('15551911379'); // Meta Business Account Phone Number (+1 555 191 1379)
  const [testSending, setTestSending] = useState(false);
  const [testResult, setTestResult] = useState(null);

  if (!isOpen) return null;

  const metadata = currentUser?.user_metadata || {};
  const userPhone = metadata.phone_number || metadata.phone || currentUser?.phone || 'Not registered';
  const userName = metadata.name || metadata.full_name || 'User';

  // Construct direct WhatsApp link
  const cleanBusinessNumber = waBusinessNumber.replace(/[^0-9]/g, '');
  const waDirectUrl = `https://wa.me/${cleanBusinessNumber}?text=Hi%20AutoPay%20Guard%20activate%20alerts`;

  const handleOpenWhatsAppLink = () => {
    window.open(waDirectUrl, '_blank', 'noopener,noreferrer');
  };

  const handleSendTestAlert = async () => {
    setTestSending(true);
    setTestResult(null);

    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('http://127.0.0.1:8000/api/v1/whatsapp/send-test', {
        method: 'POST',
        headers,
        body: JSON.stringify({ phone_number: userPhone !== 'Not registered' ? userPhone : null })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setTestResult({
          type: 'success',
          message: `✅ Test alert delivered! Meta Message ID: ${data.whatsapp_message_id}`
        });
      } else {
        setTestResult({
          type: 'error',
          message: `⚠️ Meta delivery error: ${data.detail || data.error || 'Recipient window inactive. Please send "Hi" to WhatsApp number first!'}`
        });
      }
    } catch (err) {
      setTestResult({
        type: 'error',
        message: `❌ API Request Failed: ${err.message}`
      });
    } finally {
      setTestSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-emerald-950/60 via-teal-950/40 to-slate-900 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-950/50">
              <MessageSquare className="w-6 h-6 animate-bounce" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
                <span>Activate WhatsApp Alerts</span>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 rounded-full flex items-center space-x-1">
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  <span>Meta Verified</span>
                </span>
              </h3>
              <p className="text-xs text-slate-400">Enable instant 24-hour payment & trial notifications</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-slate-800/80 text-slate-400 hover:text-white border border-slate-700/60 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">

          {/* Meta Policy Explanation Banner */}
          <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 space-y-2">
            <div className="flex items-center space-x-2 font-bold text-sm text-emerald-300">
              <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
              <span>WhatsApp 24-Hour Delivery Policy</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Under Meta WhatsApp Business rules, your phone must send a quick <strong className="text-emerald-300 font-bold">'Hi'</strong> message to our business number once to open your 24-hour alert window.
            </p>
          </div>

          {/* User Registered Target Phone Box */}
          <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-semibold flex items-center space-x-1.5">
                <Smartphone className="w-4 h-4 text-amber-400" />
                <span>Alert Target Phone Number:</span>
              </span>
              <button
                onClick={() => {
                  onClose();
                  if (onOpenProfile) onOpenProfile();
                }}
                className="text-[11px] font-bold text-amber-400 hover:text-amber-300 flex items-center space-x-1 cursor-pointer"
              >
                <Edit3 className="w-3 h-3" />
                <span>Edit Details</span>
              </button>
            </div>
            <div className="flex items-center space-x-2">
              <p className="text-base font-bold text-white tracking-wide">
                {userPhone !== 'Not registered' ? userPhone : '⚠️ No Mobile Number Linked'}
              </p>
              <span className="text-xs text-slate-400">({userName})</span>
            </div>
            {userPhone === 'Not registered' && (
              <p className="text-xs text-rose-400">
                Please click "Edit Details" to add your mobile number before activating WhatsApp.
              </p>
            )}
          </div>

          {/* Business WhatsApp Number Input / Display */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 block">
              Business WhatsApp Number (Target for 'Hi' message):
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={waBusinessNumber}
                onChange={(e) => setWaBusinessNumber(e.target.value)}
                placeholder="e.g. 15551380349"
                className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
              />
              <span className="text-[10px] text-slate-500 font-semibold">Meta Cloud API</span>
            </div>
          </div>

          {/* Action Step 1: Send Hi Button */}
          <div className="pt-2 space-y-3">
            <label className="text-xs font-bold text-slate-200 block">
              Step 1: Open WhatsApp & Send 'Hi'
            </label>
            
            <button
              onClick={handleOpenWhatsAppLink}
              className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-sm shadow-xl shadow-emerald-950/60 flex items-center justify-center space-x-2 cursor-pointer transition-all hover:scale-[1.02]"
            >
              <Send className="w-4 h-4 fill-white" />
              <span>📲 Send 'Hi' to WhatsApp Number</span>
              <ExternalLink className="w-4 h-4 ml-1 opacity-80" />
            </button>
            <p className="text-[11px] text-center text-slate-400">
              Clicking will open WhatsApp chat with pre-filled message: <em className="text-emerald-400">"Hi AutoPay Guard activate alerts"</em>
            </p>
          </div>

          {/* Action Step 2: Test Alert Button */}
          <div className="pt-3 border-t border-slate-800 space-y-3">
            <label className="text-xs font-bold text-slate-200 block">
              Step 2: Verify Instant Delivery
            </label>

            <button
              onClick={handleSendTestAlert}
              disabled={testSending}
              className="w-full py-3 px-4 rounded-2xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-emerald-400 hover:text-emerald-300 font-bold text-xs shadow-lg flex items-center justify-center space-x-2 cursor-pointer transition-all disabled:opacity-50"
            >
              <Sparkles className={`w-4 h-4 ${testSending ? 'animate-spin' : ''}`} />
              <span>{testSending ? 'Dispatching Meta Alert...' : '🧪 Send Test WhatsApp Alert Now'}</span>
            </button>

            {testResult && (
              <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
                testResult.type === 'success'
                  ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
                  : 'bg-rose-950/80 border-rose-500/50 text-rose-200'
              }`}>
                {testResult.message}
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center space-x-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>AutoPay Guard Meta Integration</span>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 text-slate-200 hover:text-white font-bold cursor-pointer transition-colors"
          >
            Got it
          </button>
        </div>

      </div>
    </div>
  );
}
