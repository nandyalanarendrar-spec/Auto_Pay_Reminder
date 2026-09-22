import React, { useState } from 'react';
import { Search, Filter, Calendar, FileText, CreditCard, ShieldAlert, CheckCircle2, Clock, Trash2, Edit3, ExternalLink, RefreshCw } from 'lucide-react';
import { CATEGORIES } from '../constants/categories';


export default function SubscriptionList({ 
  subscriptions, 
  onDeleteSubscription, 
  onToggleAutopay, 
  onViewReceipt,
  onSelectSubscription,
  onRetrySync
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedSort, setSelectedSort] = useState('days_asc');

  // Helper for renewal countdown calculation
  const getDaysUntilRenewal = (dateString) => {
    if (!dateString) return 999;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const renewalDate = new Date(dateString);
    renewalDate.setHours(0, 0, 0, 0);
    
    const diffTime = renewalDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const filteredSubscriptions = subscriptions.filter(sub => {
    const subName = sub.name || sub.merchant_name || '';
    const matchesSearch = subName.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (sub.provider && sub.provider.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = selectedCategory === 'All' || sub.category === selectedCategory;
    const matchesStatus = selectedStatus === 'all' || sub.status === selectedStatus;
    
    const daysLeft = getDaysUntilRenewal(sub.next_renewal_date || sub.next_payment_date);
    let matchesHorizon = true;
    if (selectedSort === 'next_7') {
      matchesHorizon = daysLeft >= 0 && daysLeft <= 7;
    } else if (selectedSort === 'next_10') {
      matchesHorizon = daysLeft >= 0 && daysLeft <= 10;
    } else if (selectedSort === 'next_30') {
      matchesHorizon = daysLeft >= 0 && daysLeft <= 30;
    }
    
    return matchesSearch && matchesCategory && matchesStatus && matchesHorizon;
  }).sort((a, b) => {
    const daysA = getDaysUntilRenewal(a.next_renewal_date || a.next_payment_date);
    const daysB = getDaysUntilRenewal(b.next_renewal_date || b.next_payment_date);
    const costA = parseFloat(a.amount || 0);
    const costB = parseFloat(b.amount || 0);
    const nameA = (a.name || a.merchant_name || '').toLowerCase();
    const nameB = (b.name || b.merchant_name || '').toLowerCase();

    if (selectedSort === 'amount_desc') return costB - costA;
    if (selectedSort === 'amount_asc') return costA - costB;
    if (selectedSort === 'name_asc') return nameA.localeCompare(nameB);
    
    // Default (days_asc, next_7, next_10, next_30): Soonest renewal date first!
    return daysA - daysB;
  });

  return (
    <div className="glass-panel rounded-3xl p-6 mb-8 shadow-xl">
      
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <span>Your Subscriptions</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2.5 py-0.5 rounded-full border border-indigo-500/30">
              {filteredSubscriptions.length} total
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">Click any subscription to view live renewal countdown & vault details</p>
        </div>

        {/* Search & Category Filter */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Search Input */}
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search Netflix, Spotify..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all"
            />
          </div>

          {/* Category Dropdown */}
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none transition-all cursor-pointer"
            >
              {CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Status Dropdown */}
          <div className="relative">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none transition-all cursor-pointer"
            >
              <option value="all">All Status</option>
              <option value="active">Active Only</option>
              <option value="trial">Free Trials</option>
              <option value="paused">Paused</option>
            </select>
          </div>

          {/* Days Left & Horizon Filter Dropdown */}
          <div className="relative">
            <select
              value={selectedSort}
              onChange={(e) => setSelectedSort(e.target.value)}
              className="bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none transition-all cursor-pointer font-medium"
            >
              <option value="days_asc">⏳ Days Left: Soonest First</option>
              <option value="next_7">⚡ Next 7 Days Only</option>
              <option value="next_10">📅 Next 10 Days Only</option>
              <option value="next_30">📆 Next 30 Days Only</option>
              <option value="amount_desc">💰 Cost: High to Low</option>
              <option value="amount_asc">💵 Cost: Low to High</option>
              <option value="name_asc">🔤 Name (A-Z)</option>
            </select>
          </div>

        </div>
      </div>

      {/* Subscription Cards List */}
      {filteredSubscriptions.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-800 rounded-2xl">
          <Clock className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-300">No subscriptions found</h3>
          <p className="text-xs text-slate-500 mt-1">Try adjusting your search filters or add a new subscription above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredSubscriptions.map((sub) => {
            const daysLeft = getDaysUntilRenewal(sub.next_renewal_date);
            const isTrial = sub.is_free_trial || sub.status === 'trial';

            return (
              <div 
                key={sub.id} 
                className="glass-panel glass-panel-hover p-4 sm:p-5 rounded-2xl flex flex-col lg:flex-row lg:items-center justify-between gap-4 border border-slate-800/80 cursor-pointer group"
              >
                {/* Left: Provider Details & Name */}
                <div 
                  onClick={() => onSelectSubscription && onSelectSubscription(sub)}
                  className="flex items-start space-x-4 min-w-[240px] flex-1"
                >
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/60 flex items-center justify-center text-indigo-400 font-bold text-lg shadow-inner flex-shrink-0 group-hover:scale-105 group-hover:border-cyan-500/50 transition-all">
                    {sub.name.charAt(0)}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors flex items-center space-x-2">
                        <span>{sub.name}</span>
                        <Clock className="w-3.5 h-3.5 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </h4>
                      {isTrial && (
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 rounded-full">
                          FREE TRIAL
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-slate-400">{sub.category}</span>
                      <span className="text-slate-600">•</span>
                      <span className="text-xs text-slate-400 flex items-center space-x-1">
                        <CreditCard className="w-3 h-3 text-slate-500" />
                        <span>{sub.payment_method}</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Middle: Amount & Billing Cycle */}
                <div 
                  onClick={() => onSelectSubscription && onSelectSubscription(sub)}
                  className="flex items-center space-x-6 sm:space-x-8"
                >
                  <div>
                    <p className="text-xs text-slate-400">Cost</p>
                    <p className="text-lg font-extrabold text-white mt-0.5">
                      ₹{parseFloat(sub.amount).toFixed(2)}
                      <span className="text-xs font-normal text-slate-400">/{sub.billing_cycle === 'yearly' ? 'yr' : 'mo'}</span>
                    </p>
                  </div>

                  {/* Renewal Date & Days Countdown Badge */}
                  <div>
                    <p className="text-xs text-slate-400">Next Autopay Date</p>
                    <div className="flex items-center space-x-1.5 mt-0.5">
                      <span className="text-sm font-semibold text-slate-200">{sub.next_renewal_date}</span>
                      <span className={`px-2 py-0.5 text-[11px] font-bold rounded-lg ${
                        daysLeft <= 2 
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse'
                          : daysLeft <= 7 
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-300'
                      }`}>
                        {daysLeft < 0 ? 'Due for Rollover' : daysLeft === 0 ? 'Today' : daysLeft === 1 ? 'Tomorrow' : `In ${daysLeft} days`}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Right: Autopay Toggle & Action Buttons */}
                <div className="flex items-center justify-between lg:justify-end gap-3 pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                  
                  {/* Calendar Sync Status Indicator / Retry Button */}
                  {sub.calendar_sync_status?.toUpperCase() === 'FAILED' ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRetrySync && onRetrySync(sub.id, 'subscription');
                      }}
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-xs font-semibold transition-all shadow-sm group/btn"
                      title={sub.calendar_sync_error ? `Calendar Sync Failed: ${sub.calendar_sync_error}. Click to retry.` : "Calendar sync failed. Click to retry."}
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-rose-400 group-hover/btn:rotate-180 transition-transform duration-500" />
                      <span>Retry Sync</span>
                    </button>
                  ) : sub.calendar_sync_status?.toUpperCase() === 'SYNCED' && sub.calendar_event_id && !String(sub.calendar_event_id).startsWith('sim-') ? (
                    <span 
                      className="hidden sm:flex items-center space-x-1 px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-[10px] font-medium border border-emerald-500/20"
                      title="Synced to Google Calendar"
                    >
                      <Calendar className="w-3 h-3 text-emerald-400" />
                      <span>Synced</span>
                    </span>
                  ) : (
                    <span 
                      className="hidden sm:flex items-center space-x-1 px-2 py-1 rounded-lg bg-amber-500/10 text-amber-300 text-[10px] font-medium border border-amber-500/20"
                      title="Google Calendar not connected yet. Connect Google Calendar in Settings to enable live sync."
                    >
                      <Calendar className="w-3 h-3 text-amber-400" />
                      <span>Awaiting Google Connection</span>
                    </span>
                  )}

                  {/* Autopay Toggle Switch */}
                  <button
                    onClick={() => onToggleAutopay(sub.id)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                      sub.autopay_enabled
                        ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/60'
                        : 'bg-slate-900 border-rose-500/40 text-rose-300 hover:text-white'
                    }`}
                    title={sub.autopay_enabled ? "Autopay Active (Included in spend)" : "Autopay OFF (Excluded from spend forecast)"}
                  >
                    <CheckCircle2 className={`w-3.5 h-3.5 ${sub.autopay_enabled ? 'text-emerald-400' : 'text-rose-400'}`} />
                    <span>{sub.autopay_enabled ? 'Autopay ON' : 'Autopay OFF'}</span>
                  </button>

                  {/* Receipt Vault */}
                  <button
                    onClick={() => onViewReceipt(sub)}
                    className="p-2 rounded-xl bg-slate-900 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-500/40 text-slate-300 hover:text-indigo-300 transition-all cursor-pointer"
                    title="View Saved Receipt Vault"
                  >
                    <FileText className="w-4 h-4 text-cyan-400" />
                  </button>

                  {/* Separate Delete Subscription Button */}
                  <button
                    onClick={() => onDeleteSubscription(sub.id)}
                    className="p-2 rounded-xl bg-slate-900 hover:bg-rose-950/80 border border-slate-800 hover:border-rose-500/60 text-slate-400 hover:text-rose-400 transition-all"
                    title="Delete Subscription Permanently from Vault"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
