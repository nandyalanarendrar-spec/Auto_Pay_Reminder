import React, { useState, useRef, useEffect } from 'react';
import { 
  ShieldCheck, 
  Sparkles, 
  PlusCircle, 
  LogOut, 
  User, 
  FileText, 
  Download, 
  Calculator, 
  Power, 
  Bell, 
  MessageSquare, 
  Sun, 
  Moon, 
  Smartphone,
  ChevronDown,
  Wrench,
  Clock
} from 'lucide-react';

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
  onEnableNotifications,
  onOpenWhatsAppModal,
  onOpenPersonalReminders,
  activeTab = 'dashboard',
  onSelectTab,
  theme = 'dark',
  onToggleTheme,
  canInstallPwa,
  onInstallPwa
}) {
  const [isToolsDropdownOpen, setIsToolsDropdownOpen] = useState(false);
  const toolsDropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (toolsDropdownRef.current && !toolsDropdownRef.current.contains(event.target)) {
        setIsToolsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format) => {
    setIsToolsDropdownOpen(false);
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
    <header className="sticky top-0 z-30 glass-panel border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
        
        {/* GROUP 1: Brand Logo & Title */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-600 to-indigo-500 p-0.5 shadow-lg shadow-[#ff007f]/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-[#ff007f]" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-200 tracking-tight">
                Autopay Guard
              </h1>
              <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider text-indigo-300 bg-indigo-950/80 border border-indigo-500/30 rounded-full uppercase">
                PRO V1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden lg:block">Smart Subscription & Autopay Renewal Vault</p>
          </div>
        </div>

        {/* PAGE NAVIGATION TABS */}
        <div className="hidden md:flex items-center space-x-1 bg-slate-900/90 p-1 rounded-2xl border border-slate-800">
          <button
            onClick={() => onSelectTab && onSelectTab('dashboard')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'dashboard'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Dashboard
          </button>
          
          <button
            onClick={() => onSelectTab && onSelectTab('reminders')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'reminders'
                ? 'bg-gradient-to-r from-amber-500 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Reminders Hub</span>
          </button>
        </div>

        {/* GROUP 2: Primary Actions & Tools Dropdown */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          
          {/* Tools & Reports Dropdown Menu */}
          <div className="relative" ref={toolsDropdownRef}>
            <button
              onClick={() => setIsToolsDropdownOpen(!isToolsDropdownOpen)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 text-slate-300 hover:text-white text-xs font-semibold transition-all cursor-pointer shadow-sm"
              title="Tools & Export Reports"
            >
              <Wrench className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Tools & Reports</span>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isToolsDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu Overlay */}
            {isToolsDropdownOpen && (
              <div className="absolute right-0 sm:left-0 mt-2 w-56 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="text-[10px] font-bold text-slate-500 uppercase px-3 py-1 tracking-wider">
                  Emergency Control
                </div>
                <button
                  onClick={() => { setIsToolsDropdownOpen(false); onToggleKillSwitch(); }}
                  className={`w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-bold transition-all text-left ${
                    killSwitchActive 
                      ? 'bg-rose-950/90 text-rose-200 border border-rose-500/50' 
                      : 'hover:bg-slate-800 text-slate-300 hover:text-white'
                  }`}
                >
                  <Power className={`w-4 h-4 ${killSwitchActive ? 'text-rose-400 animate-pulse' : 'text-slate-400'}`} />
                  <span>{killSwitchActive ? 'Kill-Switch: ACTIVE' : 'Autopay Status: ON'}</span>
                </button>

                <div className="text-[10px] font-bold text-slate-500 uppercase px-3 py-1 mt-2 tracking-wider">
                  Analytics & Reports
                </div>
                <button
                  onClick={() => { setIsToolsDropdownOpen(false); onOpenWhatIf(); }}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium hover:bg-slate-800 text-slate-300 hover:text-white transition-all text-left"
                >
                  <Calculator className="w-4 h-4 text-indigo-400" />
                  <span>Savings Simulator</span>
                </button>
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium hover:bg-slate-800 text-slate-300 hover:text-white transition-all text-left"
                >
                  <FileText className="w-4 h-4 text-rose-400" />
                  <span>Download PDF Report</span>
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium hover:bg-slate-800 text-slate-300 hover:text-white transition-all text-left"
                >
                  <Download className="w-4 h-4 text-emerald-400" />
                  <span>Export CSV Spreadsheet</span>
                </button>
              </div>
            )}
          </div>

          {/* Personal Task Reminders Vault Button */}
          <button
            onClick={onOpenPersonalReminders}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-600/30 to-indigo-600/30 border border-amber-500/40 text-amber-200 hover:text-white transition-all text-xs font-semibold cursor-pointer shadow-sm"
            title="Personal Reminders & Multi-Time Alerts"
          >
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Reminders</span>
          </button>

          {/* AI Chat Button */}
          <button
            onClick={onToggleAiChat}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-600/30 to-indigo-600/30 border border-purple-500/40 text-purple-200 hover:text-white transition-all text-xs font-semibold cursor-pointer shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400 animate-pulse" />
            <span className="hidden sm:inline">AI Chat</span>
          </button>

          {/* Add Subscription Button */}
          <button
            onClick={onOpenAddModal}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-white font-semibold text-xs sm:text-sm shadow-md transition-all hover:scale-[1.02] cursor-pointer"
            style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Sub</span>
          </button>
        </div>

        {/* GROUP 3: Alerts, Theme, PWA & Profile */}
        <div className="flex items-center space-x-1.5 sm:space-x-2">
          
          {/* WhatsApp Alert Button */}
          <button
            onClick={onOpenWhatsAppModal}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/60 text-emerald-400 hover:text-emerald-300 transition-all cursor-pointer relative group"
            title="Activate WhatsApp Alerts"
          >
            <MessageSquare className="w-4 h-4 group-hover:scale-110 transition-transform text-emerald-400" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full" />
          </button>

          {/* Desktop Web Notification Bell */}
          <button
            onClick={onEnableNotifications}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-amber-500/60 text-amber-400 hover:text-amber-300 transition-all cursor-pointer relative group"
            title="Enable Web Notifications"
          >
            <Bell className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full" />
          </button>

          {/* Theme Switcher Toggle */}
          <button
            onClick={onToggleTheme}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 transition-all cursor-pointer relative group"
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400 group-hover:rotate-45 transition-transform" />
            ) : (
              <Moon className="w-4 h-4 text-indigo-500 group-hover:-rotate-12 transition-transform" />
            )}
          </button>

          {/* PWA Mobile App Install Button */}
          <button
            onClick={onInstallPwa}
            className={`p-2 rounded-xl border transition-all cursor-pointer relative group ${
              canInstallPwa
                ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 shadow-md animate-pulse'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
            title="Install Mobile/Desktop App"
          >
            <Smartphone className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
          </button>

          {/* User Account & Profile Avatar Capsule */}
          {currentUser && (
            <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800">
              <button
                onClick={onOpenProfileModal}
                className="flex items-center space-x-2 p-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 transition-all cursor-pointer group"
                title="View Profile Details"
              >
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-sm group-hover:scale-105 transition-transform">
                  {currentUser.email ? currentUser.email.charAt(0).toUpperCase() : <User className="w-3.5 h-3.5" />}
                </div>
                <span className="text-xs font-medium text-slate-300 hidden lg:inline group-hover:text-white max-w-[100px] truncate">
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
