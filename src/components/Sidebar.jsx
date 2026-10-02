import React, { useState, useRef, useEffect } from 'react';
import {
  Wrench,
  MessageSquare,
  Bell,
  Sun,
  Moon,
  Smartphone,
  Power,
  Calculator,
  FileText,
  Download,
  ChevronRight
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';

export default function Sidebar({
  currentUser,
  onOpenWhatsAppModal,
  onEnableNotifications,
  theme = 'dark',
  onToggleTheme,
  canInstallPwa,
  onInstallPwa,
  onToggleKillSwitch,
  killSwitchActive,
  onOpenWhatIf
}) {
  const [isToolsOpen, setIsToolsOpen] = useState(false);
  const toolsRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (toolsRef.current && !toolsRef.current.contains(event.target)) {
        setIsToolsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format) => {
    setIsToolsOpen(false);
    const uid = currentUser?.id || 'default_user';
    const reportUrl = `${API_BASE_URL}/reports/export?format=${format}&user_id=${uid}`;
    try {
      const response = await fetch(reportUrl);
      if (!response.ok) {
        window.open(reportUrl, '_blank');
        return;
      }
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

  const iconBtnClass = "p-3 sm:p-3.5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 text-slate-300 hover:text-white transition-all cursor-pointer relative group";

  return (
    <aside className="flex sticky top-0 self-start h-screen w-16 sm:w-20 flex-shrink-0 flex-col items-center py-4 gap-3 sm:gap-4 bg-slate-950/95 border-r border-slate-800/80 backdrop-blur-xl z-20">

      {/* Tools & Reports (flyout) */}
      <div className="relative" ref={toolsRef}>
        <button
          onClick={() => setIsToolsOpen(!isToolsOpen)}
          className={iconBtnClass}
          title="Tools & Reports"
        >
          <Wrench className="w-6 h-6 sm:w-7 sm:h-7 text-indigo-400 group-hover:scale-110 transition-transform" />
        </button>

        {isToolsOpen && (
          <div className="absolute left-full top-0 ml-2 w-56 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-left-2 duration-150">
            <div className="text-[10px] font-bold text-slate-500 uppercase px-3 py-1 tracking-wider">
              Emergency Control
            </div>
            <button
              onClick={() => { setIsToolsOpen(false); onToggleKillSwitch(); }}
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
              onClick={() => { setIsToolsOpen(false); onOpenWhatIf(); }}
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

      <div className="w-8 border-t border-slate-800 my-1" />

      {/* WhatsApp Alert */}
      <button onClick={onOpenWhatsAppModal} className={iconBtnClass} title="Activate WhatsApp Alerts">
        <MessageSquare className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-400 group-hover:scale-110 transition-transform" />
        <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-ping" />
        <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full" />
      </button>

      {/* Notifications Bell */}
      <button onClick={onEnableNotifications} className={iconBtnClass} title="Enable Web Notifications">
        <Bell className="w-6 h-6 sm:w-7 sm:h-7 text-amber-400 group-hover:scale-110 transition-transform" />
        <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full animate-ping" />
        <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full" />
      </button>

      <div className="w-8 border-t border-slate-800 my-1" />

      {/* Theme Toggle */}
      <button onClick={onToggleTheme} className={iconBtnClass} title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}>
        {theme === 'dark' ? (
          <Sun className="w-6 h-6 sm:w-7 sm:h-7 text-amber-400 group-hover:rotate-45 transition-transform" />
        ) : (
          <Moon className="w-6 h-6 sm:w-7 sm:h-7 text-indigo-500 group-hover:-rotate-12 transition-transform" />
        )}
      </button>

      {/* PWA Install */}
      <button
        onClick={onInstallPwa}
        className={`p-3 sm:p-3.5 rounded-2xl border transition-all cursor-pointer relative group ${
          canInstallPwa
            ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 shadow-md animate-pulse'
            : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
        }`}
        title="Install Mobile/Desktop App"
      >
        <Smartphone className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-400 group-hover:scale-110 transition-transform" />
      </button>

    </aside>
  );
}
