import React, { useState } from 'react';
import { X, PlusCircle, Upload, ShieldAlert, CreditCard, Calendar, CheckCircle, FileText } from 'lucide-react';
import { CATEGORIES } from '../constants/categories';


export default function AddSubscriptionModal({ isOpen, onClose, onAddSubscription }) {
  const [formData, setFormData] = useState({
    name: '',
    provider: '',
    category: 'Software & AI',
    amount: '',
    currency: 'USD',
    billing_cycle: 'monthly',
    next_renewal_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    autopay_enabled: true,
    payment_method: 'Credit Card',
    is_free_trial: false,
    receipt_url: '',
    notes: ''
  });

  const [receiptFile, setReceiptFile] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name || !formData.amount) return;

    // Estimate risk score based on trial and amount
    let estimatedRisk = 10;
    if (formData.is_free_trial) estimatedRisk += 65;
    if (parseFloat(formData.amount) > 30) estimatedRisk += 20;

    const newSub = {
      ...formData,
      id: `sub-${Date.now()}`,
      amount: parseFloat(formData.amount),
      status: formData.is_free_trial ? 'trial' : 'active',
      risk_score: Math.min(estimatedRisk, 100),
      receipt_url: receiptFile ? URL.createObjectURL(receiptFile) : (formData.receipt_url || null)
    };

    onAddSubscription(newSub);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-xl rounded-3xl p-6 shadow-2xl border border-slate-700/80 relative max-h-[90vh] overflow-y-auto">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-xl bg-slate-900 border border-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <PlusCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Add New Subscription</h3>
            <p className="text-xs text-slate-400">Set renewal dates, autopay controls, and receipt vaulting</p>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* Subscription Name & Provider */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Subscription Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Netflix, ChatGPT, Gym"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Provider Company</label>
              <input
                type="text"
                placeholder="e.g. OpenAI, Google, Apple"
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Amount, Currency & Billing Cycle */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Cost / Price *</label>
              <input
                type="number"
                step="0.01"
                required
                placeholder="e.g. 19.99"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none cursor-pointer"
              >
                {CATEGORIES.filter(c => c !== 'All').map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Billing Cycle</label>
              <select
                value={formData.billing_cycle}
                onChange={(e) => setFormData({ ...formData, billing_cycle: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none cursor-pointer"
              >
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          </div>

          {/* Renewal Date & Payment Method */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Next Renewal / Debit Date *</label>
              <input
                type="date"
                required
                value={formData.next_renewal_date}
                onChange={(e) => setFormData({ ...formData, next_renewal_date: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Payment Method</label>
              <select
                value={formData.payment_method}
                onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none cursor-pointer"
              >
                <option value="Credit Card">Credit Card</option>
                <option value="UPI Autopay">UPI Autopay</option>
                <option value="NetBanking">NetBanking</option>
                <option value="PayPal">PayPal</option>
              </select>
            </div>
          </div>

          {/* Free Trial & Autopay Checkboxes */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl">
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_free_trial}
                onChange={(e) => setFormData({ ...formData, is_free_trial: e.target.checked })}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
              />
              <span className="text-xs text-slate-300 font-medium">Is this a Free Trial?</span>
            </label>

            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.autopay_enabled}
                onChange={(e) => setFormData({ ...formData, autopay_enabled: e.target.checked })}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
              />
              <span className="text-xs text-slate-300 font-medium">Autopay Active on Bank</span>
            </label>
          </div>

          {/* Receipt File Upload */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Upload Receipt / Invoice (PDF / Image)</label>
            <div className="border-2 border-dashed border-slate-800 hover:border-indigo-500/50 rounded-2xl p-4 text-center cursor-pointer transition-colors bg-slate-900/50">
              <input
                type="file"
                accept="image/*,.pdf"
                onChange={(e) => setReceiptFile(e.target.files[0])}
                className="hidden"
                id="receipt-upload"
              />
              <label htmlFor="receipt-upload" className="cursor-pointer flex flex-col items-center justify-center space-y-1">
                <Upload className="w-5 h-5 text-indigo-400" />
                <span className="text-xs text-slate-300 font-medium">
                  {receiptFile ? receiptFile.name : 'Click to select receipt image or PDF'}
                </span>
                <span className="text-[10px] text-slate-500">Vaulted in Supabase Storage</span>
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.01]"
            >
              Save Subscription to Vault
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
