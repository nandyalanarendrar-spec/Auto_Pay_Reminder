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
  Download
} from 'lucide-react';
import { API_BASE_URL } from '../config/api';

export default function ToolsRow({
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

  const cellClass = 'flex flex-col items-center justify-center gap-1 py-2 cursor-pointer group';
  const iconWrap = 'relative p-3 rounded-2xl bg-slate-900 border border-slate-800 group-hover:border-indigo-500/60 transition-all';
  const iconSize = 'w-7 h-7 group-hover:scale-110 transition-transform';
  const labelClass = 'text-[0.625rem] font-semibold text-slate-400 group-hover:text-white';

  return (
    <div className="sticky top-20 z-20 bg-slate-950/95 backdrop-blur-xl border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-2 sm:px-6 lg:px-8 grid grid-cols-5">

        {/* Tools & Reports (dropdown) */}
        <div className="relative flex justify-center" ref={toolsRef}>
          <button onClick={() => setIsToolsOpen(!isToolsOpen)} className={cellClass} title="Tools & Reports">
            <span className={iconWrap}>
              <Wrench className={`${iconSize} text-indigo-400`} />
            </span>
            <span className={labelClass}>Tools</span>
          </button>

          {isToolsOpen && (
            <div className="absolute left-0 top-full mt-1 w-64 max-w-[90vw] rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="text-[0.625rem] font-bold text-slate-500 uppercase px-3 py-1 tracking-wider">
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

              <div className="text-[0.625rem] font-bold text-slate-500 uppercase px-3 py-1 mt-2 tracking-wider">
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

        {/* WhatsApp Alert */}
        <button onClick={onOpenWhatsAppModal} className={cellClass} title="Activate WhatsApp Alerts">
          <span className={iconWrap}>
            <MessageSquare className={`${iconSize} text-emerald-400`} />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full" />
          </span>
          <span className={labelClass}>WhatsApp</span>
        </button>

        {/* Notifications */}
        <button onClick={onEnableNotifications} className={cellClass} title="Enable Web Notifications">
          <span className={iconWrap}>
            <Bell className={`${iconSize} text-amber-400`} />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-amber-400 rounded-full" />
          </span>
          <span className={labelClass}>Alerts</span>
        </button>

        {/* Theme Toggle */}
        <button onClick={onToggleTheme} className={cellClass} title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}>
          <span className={iconWrap}>
            {theme === 'dark' ? (
              <Sun className={`${iconSize} text-amber-400`} />
            ) : (
              <Moon className={`${iconSize} text-indigo-500`} />
            )}
          </span>
          <span className={labelClass}>Theme</span>
        </button>

        {/* PWA Install */}
        <button onClick={onInstallPwa} className={cellClass} title="Install Mobile/Desktop App">
          <span className={`${iconWrap} ${canInstallPwa ? '!bg-emerald-950/80 !border-emerald-500 animate-pulse' : ''}`}>
            <Smartphone className={`${iconSize} text-emerald-400`} />
          </span>
          <span className={labelClass}>Install</span>
        </button>
      </div>
    </div>
  );
}
