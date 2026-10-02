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
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient';

// Literal class strings per tool so Tailwind can generate them.
const T = {
  tools: { ring: 'from-indigo-400 to-blue-500', glow: 'shadow-indigo-500/40', icon: 'text-[#a5b4fc]' },
  whatsapp: { ring: 'from-emerald-400 to-teal-500', glow: 'shadow-emerald-500/40', icon: 'text-[#6ee7b7]' },
  alerts: { ring: 'from-amber-400 to-orange-500', glow: 'shadow-amber-500/40', icon: 'text-[#fcd34d]' },
  theme: { ring: 'from-yellow-300 via-orange-400 to-pink-500', glow: 'shadow-orange-500/40', icon: 'text-[#fde68a]' },
  install: { ring: 'from-cyan-400 to-emerald-400', glow: 'shadow-cyan-500/40', icon: 'text-[#67e8f9]' }
};

const Tile = ({ tone, pulse, children }) => (
  <span className={`relative block w-14 h-14 rounded-2xl bg-gradient-to-br ${T[tone].ring} p-[1.5px] shadow-lg ${T[tone].glow} group-hover:-translate-y-1 transition-transform duration-300`}>
    <span className="flex w-full h-full items-center justify-center rounded-[0.9rem] bg-[#0a0d24]/90 backdrop-blur">
      {children}
    </span>
    {pulse && (
      <span className="absolute -top-1 -right-1 flex w-3 h-3">
        <span className={`absolute inline-flex w-full h-full rounded-full opacity-75 animate-ping ${pulse}`} />
        <span className={`relative inline-flex w-3 h-3 rounded-full border-2 border-[#0a0d24] ${pulse}`} />
      </span>
    )}
  </span>
);

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
    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token || null;
      }
      const response = await fetch(`${API_BASE_URL}/reports/export?format=${format}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!response.ok) {
        alert('Could not download the report. Please sign in again and retry.');
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
      alert('Could not download the report. Please check your connection and retry.');
    }
  };

  const cellClass = 'group flex flex-col items-center justify-center gap-1.5 py-1 cursor-pointer active:scale-95 transition-transform';
  const labelClass = 'text-[0.65rem] font-bold tracking-wide text-[#c7d2fe] group-hover:text-[#ffffff] transition-colors';
  const iconSize = 'w-7 h-7 transition-transform duration-300 group-hover:scale-110';

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.06] backdrop-blur-xl shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_10px_30px_rgba(0,0,0,0.35)] px-2 py-3">
      <div className="grid grid-cols-5">

        {/* Tools & Reports (dropdown) */}
        <div className="relative flex justify-center" ref={toolsRef}>
          <button onClick={() => setIsToolsOpen(!isToolsOpen)} className={cellClass} title="Tools & Reports">
            <Tile tone="tools">
              <Wrench className={`${iconSize} ${T.tools.icon}`} />
            </Tile>
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
          <Tile tone="whatsapp" pulse="bg-emerald-400">
            <MessageSquare className={`${iconSize} ${T.whatsapp.icon}`} />
          </Tile>
          <span className={labelClass}>WhatsApp</span>
        </button>

        {/* Notifications */}
        <button onClick={onEnableNotifications} className={cellClass} title="Enable Web Notifications">
          <Tile tone="alerts" pulse="bg-amber-400">
            <Bell className={`${iconSize} ${T.alerts.icon}`} />
          </Tile>
          <span className={labelClass}>Alerts</span>
        </button>

        {/* Theme Toggle */}
        <button onClick={onToggleTheme} className={cellClass} title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}>
          <Tile tone="theme">
            {theme === 'dark' ? (
              <Sun className={`${iconSize} ${T.theme.icon} group-hover:rotate-45`} />
            ) : (
              <Moon className={`${iconSize} text-[#a5b4fc] group-hover:-rotate-12`} />
            )}
          </Tile>
          <span className={labelClass}>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>

        {/* PWA Install */}
        <button onClick={onInstallPwa} className={cellClass} title="Install Mobile/Desktop App">
          <Tile tone="install" pulse={canInstallPwa ? 'bg-emerald-400' : null}>
            <Smartphone className={`${iconSize} ${T.install.icon}`} />
          </Tile>
          <span className={labelClass}>Install</span>
        </button>
      </div>
    </div>
  );
}
