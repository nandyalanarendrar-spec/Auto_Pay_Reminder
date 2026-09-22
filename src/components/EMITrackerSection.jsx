import React, { useState } from 'react';
import { Landmark, Calendar, Percent, CheckCircle, Plus, DollarSign, RefreshCw, Trash2 } from 'lucide-react';
import EMICountdownModal from './EMICountdownModal';

export default function EMITrackerSection({ userEmis, onPayInstallment, onAddEmi, onRetrySync, onDeleteEmi }) {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedEmiForModal, setSelectedEmiForModal] = useState(null);
  const [newEmi, setNewEmi] = useState({
    loan_name: '',
    installment_amount: '',
    total_installments: '',
    installments_paid: '0',
    next_due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });

  const handleCreate = (e) => {
    e.preventDefault();
    if (!newEmi.loan_name || !newEmi.installment_amount) return;

    const totalInst = parseInt(newEmi.total_installments) || 12;
    const paidInst = parseInt(newEmi.installments_paid) || 0;
    const instAmt = parseFloat(newEmi.installment_amount) || 0;

    const emiObj = {
      id: `emi-${Date.now()}`,
      loan_name: newEmi.loan_name,
      total_installments: totalInst,
      installments_paid: paidInst,
      installment_amount: instAmt,
      remaining_amount: (totalInst - paidInst) * instAmt,
      next_due_date: newEmi.next_due_date,
      status: paidInst >= totalInst ? 'completed' : 'active',
      completion_percentage: Math.round((paidInst / totalInst) * 100)
    };

    onAddEmi(emiObj);
    setIsAddModalOpen(false);
    setNewEmi({ loan_name: '', installment_amount: '', total_installments: '', installments_paid: '0', next_due_date: '' });
  };

  return (
    <div className="glass-panel rounded-3xl p-6 mb-8 shadow-xl border border-indigo-500/20">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Landmark className="w-5 h-5 text-purple-400" />
            <span>EMI Loan Payoff Tracker</span>
            <span className="text-xs bg-purple-500/20 text-purple-300 px-2.5 py-0.5 rounded-full border border-purple-500/30">
              {userEmis.length} active loans
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">Track monthly loan installments, payoff completion bars, and due dates</p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-purple-600/30 border border-purple-500/40 text-purple-200 hover:text-white transition-all text-xs font-semibold hover:bg-purple-600/50"
        >
          <Plus className="w-4 h-4" />
          <span>Add EMI Loan</span>
        </button>
      </div>

      {/* EMI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {userEmis.map((emi) => {
          const completionPct = Math.round((emi.installments_paid / emi.total_installments) * 100) || 0;
          const isCompleted = emi.installments_paid >= emi.total_installments;
          const isSynced = isCompleted || emi.calendar_sync_status?.toUpperCase() === 'SYNCED' || (emi.calendar_event_id && !String(emi.calendar_event_id).startsWith('sim-'));

          return (
            <div 
              key={emi.id} 
              onClick={() => setSelectedEmiForModal(emi)}
              className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 hover:border-purple-500/50 hover:shadow-lg hover:shadow-purple-500/10 cursor-pointer transition-all group/card relative"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-white text-sm group-hover/card:text-purple-300 transition-colors flex items-center space-x-2">
                    <span>{emi.loan_name}</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Installment: <span className="text-indigo-300 font-semibold">₹{parseFloat(emi.installment_amount || 0).toLocaleString()}/mo</span>
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  {emi.calendar_sync_status?.toUpperCase() === 'FAILED' ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRetrySync && onRetrySync(emi.id, 'emi');
                      }}
                      className="flex items-center space-x-1 px-2 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-[10px] font-semibold transition-all group/btn"
                      title={emi.calendar_sync_error ? `Calendar Sync Failed: ${emi.calendar_sync_error}. Click to retry.` : "Calendar sync failed. Click to retry."}
                    >
                      <RefreshCw className="w-3 h-3 text-rose-400 group-hover/btn:rotate-180 transition-transform duration-500" />
                      <span>Retry</span>
                    </button>
                  ) : isSynced ? (
                    <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20" title="Synced to Google Calendar">
                      <CheckCircle className="w-3 h-3 text-emerald-400" />
                      <span>Synced</span>
                    </span>
                  ) : (
                    <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 text-[10px] font-medium border border-amber-500/20" title="Awaiting Google Calendar Connection">
                      <Calendar className="w-3 h-3 text-amber-400" />
                      <span>Awaiting Google Connection</span>
                    </span>
                  )}
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    isCompleted ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30' : 'bg-purple-950 text-purple-300 border border-purple-500/30'
                  }`}>
                    {isCompleted ? 'Completed' : `Due: ${emi.next_due_date}`}
                  </span>

                  {/* EMI Delete Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteEmi && onDeleteEmi(emi.id);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/80 border border-slate-800 hover:border-rose-500/60 text-slate-400 hover:text-rose-400 transition-all ml-1"
                    title="Delete EMI Loan Permanently from Vault"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Payoff Progress Bar */}
              <div className="mt-4">
                <div className="flex justify-between text-xs mb-1.5 font-medium">
                  <span className="text-slate-400">Payoff Progress ({emi.installments_paid}/{emi.total_installments} Paid)</span>
                  <span className="text-purple-300 font-bold">{completionPct}%</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-[#ff007f] transition-all duration-500"
                    style={{ width: `${completionPct}%` }}
                  />
                </div>
              </div>

              {/* Action Button */}
              {!isCompleted && (
                <div className="mt-4 pt-3 border-t border-slate-800 flex justify-end">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onPayInstallment(emi.id);
                    }}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-600/40 text-xs font-semibold transition-all"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Pay Installment (₹{parseFloat(emi.installment_amount || 0).toLocaleString()})</span>
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add EMI Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md rounded-3xl p-6 shadow-2xl border border-slate-700/80">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
              <Landmark className="w-5 h-5 text-purple-400" />
              <span>Add EMI Loan Tracker</span>
            </h3>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-300 mb-1">Loan Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. iPhone 15 EMI, HDFC Home Loan"
                  value={newEmi.loan_name}
                  onChange={(e) => setNewEmi({ ...newEmi, loan_name: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Monthly Installment (₹) *</label>
                  <input
                    type="number"
                    required
                    placeholder="4500"
                    value={newEmi.installment_amount}
                    onChange={(e) => setNewEmi({ ...newEmi, installment_amount: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Total Installments *</label>
                  <input
                    type="number"
                    required
                    placeholder="12"
                    value={newEmi.total_installments}
                    onChange={(e) => setNewEmi({ ...newEmi, total_installments: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">Installments Paid So Far</label>
                <input
                  type="number"
                  placeholder="0"
                  value={newEmi.installments_paid}
                  onChange={(e) => setNewEmi({ ...newEmi, installments_paid: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-semibold"
                >
                  Save EMI
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EMI Countdown Modal */}
      {selectedEmiForModal && (
        <EMICountdownModal
          isOpen={!!selectedEmiForModal}
          onClose={() => setSelectedEmiForModal(null)}
          emi={selectedEmiForModal}
          onPayInstallment={onPayInstallment}
          onRetrySync={onRetrySync}
        />
      )}
    </div>
  );
}
