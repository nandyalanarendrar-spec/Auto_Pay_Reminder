import React, { useState } from 'react';
import { Sparkles, X, TrendingDown, DollarSign, CheckCircle, Calculator } from 'lucide-react';

export default function WhatIfSimulatorModal({ isOpen, onClose, subscriptions }) {
  const [selectedSubIds, setSelectedSubIds] = useState([]);

  if (!isOpen) return null;

  const toggleSub = (id) => {
    setSelectedSubIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const selectedSubs = subscriptions.filter(s => selectedSubIds.includes(s.id));
  const monthlySavings = selectedSubs.reduce((acc, s) => acc + (parseFloat(s.amount) || 0), 0);
  const yearlySavings = monthlySavings * 12;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-lg rounded-3xl p-6 shadow-2xl border border-indigo-500/30 relative max-h-[90vh] overflow-y-auto">
        
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-xl bg-slate-900 border border-slate-800"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">What-If Savings Simulator</h3>
            <p className="text-xs text-slate-400">Select subscriptions to simulate potential cancellation savings</p>
          </div>
        </div>

        {/* Savings Results Banner */}
        <div className="bg-gradient-to-r from-indigo-950/80 via-purple-950/80 to-slate-900 border border-indigo-500/40 rounded-2xl p-4 mb-5 flex justify-between items-center">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-indigo-300 font-semibold">Simulated Monthly Savings</p>
            <p className="text-2xl font-extrabold text-white mt-0.5">₹{monthlySavings.toLocaleString('en-IN')}<span className="text-xs text-slate-400 font-normal">/mo</span></p>
          </div>

          <div className="text-right border-l border-slate-800 pl-4">
            <p className="text-[11px] uppercase tracking-wider text-emerald-400 font-semibold">Annual Projected Savings</p>
            <p className="text-lg font-bold text-emerald-300 mt-0.5">₹{yearlySavings.toLocaleString('en-IN')}<span className="text-xs text-slate-400 font-normal">/yr</span></p>
          </div>
        </div>

        {/* Checkbox List of Subscriptions */}
        <div className="space-y-2 mb-6">
          <p className="text-xs font-semibold text-slate-300 mb-2">Select items to simulate cancellation:</p>
          {subscriptions.map(sub => {
            const isSelected = selectedSubIds.includes(sub.id);
            return (
              <div
                key={sub.id}
                onClick={() => toggleSub(sub.id)}
                className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                  isSelected ? 'bg-indigo-950/50 border-indigo-500 text-white' : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-5 h-5 rounded-md border flex items-center justify-center ${isSelected ? 'bg-indigo-600 border-indigo-500 text-white' : 'border-slate-700'}`}>
                    {isSelected && <CheckCircle className="w-3.5 h-3.5" />}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white">{sub.name}</p>
                    <p className="text-[10px] text-slate-400">{sub.category}</p>
                  </div>
                </div>

                <span className="text-xs font-bold text-indigo-300">₹{sub.amount}/mo</span>
              </div>
            );
          })}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold shadow-lg"
        >
          Close Simulator
        </button>
      </div>
    </div>
  );
}
