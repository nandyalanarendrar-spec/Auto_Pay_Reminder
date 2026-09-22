import React from 'react';
import { ShieldCheck, Sparkles, PlusCircle, Database, LogOut, User, FileText, Download, Calculator, Power, Bell } from 'lucide-react';
import { isSupabaseConfigured } from '../lib/supabaseClient';

export default function Navbar({ 
  currentUser, 
  onLogout, 
  onOpenAddModal, 
  onToggleAiChat, 
  averageRiskScore,
  onOpenWhatIf,
  onToggleKillSwitch,
  killSwitchActive,
  onOpenProfileModal,
  onEnableNotifications
}) {
  const handleExport = async (format) => {
    const uid = currentUser?.id || 'default_user';
    const reportUrl = `http://127.0.0.1:8000/api/v1/reports/export?format=${format}&user_id=${uid}`;
    try {
      const response = await fetch(reportUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `autopay_guard_${format === 'csv' ? 'report.csv' : 'summary.pdf'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      window.open(reportUrl, '_blank');
    }
  };

  return (
    <header className="sticky top-0 z-30 glass-panel border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-600 to-indigo-500 p-0.5 shadow-lg shadow-[#ff007f]/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-[#ff007f]" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-200 tracking-tight">
                Autopay Guard
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider text-indigo-300 bg-indigo-950/80 border border-indigo-500/30 rounded-full uppercase">
                PRO V1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Smart Subscription & Autopay Renewal Vault</p>
          </div>
        </div>

        {/* Action Controls & Indicators */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          
          {/* 1. Autopay Emergency Kill Switch Toggle */}
          <button
            onClick={onToggleKillSwitch}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all cursor-pointer ${
              killSwitchActive 
                ? 'bg-rose-950/90 border-rose-500 text-rose-200 shadow-lg shadow-rose-900/40 animate-pulse' 
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
            }`}
            title="Toggle Autopay Emergency Kill-Switch"
          >
            <Power className={`w-3.5 h-3.5 ${killSwitchActive ? 'text-rose-400' : 'text-slate-400'}`} />
            <span className="hidden lg:inline">{killSwitchActive ? 'KILL SWITCH ON' : 'Autopay ON'}</span>
          </button>

          {/* 2. What-If Savings Simulator Button */}
          <button
            onClick={onOpenWhatIf}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-indigo-500/50 text-xs font-semibold transition-all cursor-pointer"
            title="Open What-If Savings Simulator"
          >
            <Calculator className="w-3.5 h-3.5 text-indigo-400" />
            <span>Simulator</span>
          </button>

          {/* 3. Export PDF Report Button */}
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-rose-500/50 text-xs font-semibold transition-all cursor-pointer"
            title="Download PDF Financial Report"
          >
            <FileText className="w-3.5 h-3.5 text-rose-400" />
            <span className="hidden sm:inline">PDF Report</span>
          </button>

          {/* 4. Export CSV Button */}
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-emerald-500/50 text-xs font-semibold transition-all cursor-pointer"
            title="Download CSV Spreadsheet Report"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span className="hidden sm:inline">CSV</span>
          </button>

          {/* 5. AI Assistant Button */}
          <button
            onClick={onToggleAiChat}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-purple-600/30 to-indigo-600/30 border border-purple-500/40 text-purple-200 hover:text-white transition-all text-xs font-semibold cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
            <span className="hidden sm:inline">AI Chat</span>
          </button>

          {/* 6. Add Subscription Button */}
          <button
            onClick={onOpenAddModal}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-white font-semibold text-xs sm:text-sm shadow-md transition-all hover:scale-[1.02] cursor-pointer"
            style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Sub</span>
          </button>

          {/* 7. Browser Web Notification Bell */}
          <button
            onClick={onEnableNotifications}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-amber-500/60 text-amber-400 hover:text-amber-300 transition-all cursor-pointer relative group"
            title="Enable Desktop Web Notifications"
          >
            <Bell className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full" />
          </button>

          {/* User Account & Profile Avatar Button */}
          {currentUser && (
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
              <button
                onClick={onOpenProfileModal}
                className="flex items-center space-x-2 p-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 transition-all cursor-pointer group"
                title="View User Profile Details & Password"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-sm group-hover:scale-105 transition-transform">
                  {currentUser.email ? currentUser.email.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
                </div>
                <span className="text-xs font-medium text-slate-300 hidden md:inline group-hover:text-white">
                  {currentUser.user_metadata?.name || currentUser.name || currentUser.email?.split('@')[0]}
                </span>
              </button>
              <button
                onClick={onLogout}
                className="p-2 rounded-xl bg-slate-900 hover:bg-rose-950/60 border border-slate-800 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 transition-all cursor-pointer"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}

        </div>

      </div>
    </header>
  );
}
