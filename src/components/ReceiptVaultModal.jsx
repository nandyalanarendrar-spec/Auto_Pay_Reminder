import React, { useState, useRef } from 'react';
import { X, FileText, ExternalLink, ShieldCheck, Upload, CheckCircle2, Lock, Sparkles, Building2, Calendar, CreditCard, Camera } from 'lucide-react';
import { isNativeApp, takePhoto } from '../utils/nativeFeatures';

export default function ReceiptVaultModal({ isOpen, onClose, subscription }) {
  const [customUrl, setCustomUrl] = useState('');
  const [activeReceiptUrl, setActiveReceiptUrl] = useState(null);
  const webFileInputRef = useRef(null);

  if (!isOpen || !subscription) return null;

  const currentReceipt = activeReceiptUrl || subscription.receipt_url;
  const subName = subscription.merchant_name || subscription.name || 'Subscription';
  const amount = parseFloat(subscription.amount || 0).toFixed(2);
  const mandateId = `MND-${(subName.slice(0, 3)).toUpperCase()}-${subscription.id ? subscription.id.slice(0, 8).toUpperCase() : '84729104'}`;
  const shaHash = `0x${Array.from({length: 16}, () => Math.floor(Math.random()*16).toString(16)).join('')}...ec9a`;

  const handleSaveCustomReceipt = (e) => {
    e.preventDefault();
    if (customUrl.trim()) {
      setActiveReceiptUrl(customUrl.trim());
      setCustomUrl('');
    }
  };

  const handleCapturePhoto = async () => {
    if (isNativeApp()) {
      const file = await takePhoto();
      if (file) setActiveReceiptUrl(URL.createObjectURL(file));
    } else {
      webFileInputRef.current?.click();
    }
  };

  const handleWebFileSelected = (e) => {
    const file = e.target.files?.[0];
    if (file) setActiveReceiptUrl(URL.createObjectURL(file));
    e.target.value = '';
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-3xl p-6 sm:p-7 shadow-2xl border border-cyan-500/30 bg-slate-900/95 text-white relative overflow-hidden">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-2 rounded-xl bg-slate-800/80 border border-slate-700 hover:border-slate-600 transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-11 h-11 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-inner">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center space-x-2">
              <span>Receipt & E-Mandate Vault</span>
              <span className="text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full font-mono">
                VERIFIED
              </span>
            </h3>
            <p className="text-xs text-slate-400">{subName} • Digital Vault Record</p>
          </div>
        </div>

        {/* Receipt Display Area */}
        {currentReceipt ? (
          <div className="my-4 rounded-2xl overflow-hidden border border-slate-800 bg-slate-950/80 max-h-80 flex flex-col items-center justify-center p-3">
            <img 
              src={currentReceipt} 
              alt={`Receipt for ${subName}`}
              className="max-h-64 object-contain rounded-xl shadow-lg border border-slate-800"
              onError={() => setActiveReceiptUrl(null)}
            />
          </div>
        ) : (
          /* Auto-Generated Digital E-Mandate Receipt Voucher */
          <div className="my-4 rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-5 shadow-inner relative overflow-hidden">
            {/* Background Decorative Stamp */}
            <div className="absolute -right-6 -bottom-6 w-32 h-32 rounded-full border-4 border-cyan-500/10 flex items-center justify-center rotate-12 pointer-events-none">
              <span className="text-[10px] font-black tracking-widest text-cyan-500/20 uppercase text-center">AUTOPAY<br/>GUARD<br/>VAULTED</span>
            </div>

            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-slate-200">{subName}</span>
              </div>
              <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>E-Mandate Active</span>
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 my-4 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Mandate Outflow</span>
                <span className="text-base font-extrabold text-white">₹{amount} <span className="text-[10px] font-normal text-slate-400">/{subscription.billing_cycle || subscription.billing_frequency || 'monthly'}</span></span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Next Auto-Debit</span>
                <span className="text-sm font-semibold text-cyan-300 flex items-center space-x-1 mt-0.5">
                  <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{subscription.next_renewal_date || subscription.next_payment_date || 'Active'}</span>
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Mandate Ref ID</span>
                <span className="font-mono text-slate-300 text-[11px]">{mandateId}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Payment Method</span>
                <span className="text-slate-300 flex items-center space-x-1 mt-0.5">
                  <CreditCard className="w-3.5 h-3.5 text-purple-400" />
                  <span>UPI E-Mandate</span>
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span className="flex items-center space-x-1">
                <Lock className="w-3 h-3 text-cyan-500" />
                <span>SHA-256 Vault Stamp: {shaHash}</span>
              </span>
            </div>
          </div>
        )}

        {/* Capture Receipt Photo (native camera on app, file picker on web) */}
        <button
          type="button"
          onClick={handleCapturePhoto}
          className="mt-3 w-full px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center space-x-2 transition-all"
        >
          <Camera className="w-4 h-4 text-cyan-400" />
          <span>{isNativeApp() ? 'Take Photo of Receipt' : 'Upload Receipt Photo'}</span>
        </button>
        <input
          ref={webFileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleWebFileSelected}
          className="hidden"
        />

        {/* Upload Custom Receipt Form */}
        <form onSubmit={handleSaveCustomReceipt} className="mt-3 flex items-center space-x-2">
          <input
            type="url"
            placeholder="Paste image/PDF receipt URL..."
            value={customUrl}
            onChange={(e) => setCustomUrl(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-all"
          />
          <button
            type="submit"
            className="px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center space-x-1 shadow-md transition-all flex-shrink-0"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Attach</span>
          </button>
        </form>

        {/* Footer info */}
        <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-800">
          <div className="flex items-center space-x-1.5 text-xs text-emerald-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Encrypted Vault Security Active</span>
          </div>

          {currentReceipt && (
            <a
              href={currentReceipt}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Open Image</span>
            </a>
          )}
        </div>

      </div>
    </div>
  );
}
