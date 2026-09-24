import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  X, 
  CheckCircle2, 
  Calendar, 
  FileText, 
  Trash2, 
  Edit, 
  Bell, 
  Check, 
  Tag, 
  Sparkles,
  ExternalLink,
  Smartphone,
  MessageSquare,
  Power,
  Info,
  CreditCard
} from 'lucide-react';
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const parseLocalDate = (dateStr) => {
  if (!dateStr) return new Date();
  const str = String(dateStr);
  if (str.endsWith('Z') || str.includes('+00:00') || str.includes('+0000')) {
    const parsedUtc = new Date(str);
    if (!isNaN(parsedUtc.getTime())) return parsedUtc;
  }
  const cleanStr = str.replace('Z', '').split('+')[0];
  const parts = cleanStr.split(/[-T:\s]/);
  if (parts.length >= 5) {
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    const hour = parseInt(parts[3], 10);
    const minute = parseInt(parts[4], 10);
    const second = parts[5] ? parseInt(parts[5], 10) : 0;
    return new Date(year, month, day, hour, minute, second);
  }
  return new Date(dateStr);
};

export default function PersonalReminderCountdownModal({
  isOpen,
  onClose,
  reminder,
  onDeleteReminder,
  onEditReminder,
  onToggleComplete,
  showToast
}) {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [isEditing, setIsEditing] = useState(false);

  // Edit Form State
  const [editTitle, setEditTitle] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [editDueDatetime, setEditDueDatetime] = useState('');
  const [editOffsets, setEditOffsets] = useState([10, 30, 60]);
  const [editSyncCalendar, setEditSyncCalendar] = useState(true);
  const [editSyncWhatsapp, setEditSyncWhatsapp] = useState(true);
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  useEffect(() => {
    if (!reminder || !reminder.due_datetime) return;

    // Reset edit state when modal opens
    setIsEditing(false);
    setEditTitle(reminder.title || '');
    setEditNotes(reminder.notes || '');
    setEditDueDatetime(reminder.due_datetime ? String(reminder.due_datetime).replace(' ', 'T').slice(0, 16) : '');
    setEditOffsets(reminder.reminder_offsets || [10, 30, 60]);
    setEditSyncCalendar(reminder.sync_calendar !== false);
    setEditSyncWhatsapp(reminder.sync_whatsapp !== false);

    const calculateTimeLeft = () => {
      const target = parseLocalDate(reminder.due_datetime);
      const now = new Date();
      const diff = target - now;

      if (diff <= 0) {
        setTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / 1000 / 60) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      setTimeLeft({ days, hours, minutes, seconds });
    };

    calculateTimeLeft();
    const interval = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(interval);
  }, [reminder, isOpen]);

  if (!isOpen || !reminder) return null;

  const handleTriggerWhatsAppMessage = async () => {
    const taskTitle = reminder.title || 'Task Reminder';
    const dueFormatted = reminder.due_datetime
      ? new Date(reminder.due_datetime).toLocaleString('en-IN', {
          weekday: 'short',
          day: 'numeric',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      : 'Not Specified';

    const msgText = `⚡ *Autopay Guard Task Alert!*\n\nReminder: *${taskTitle}*\nDue Date & Time: *${dueFormatted}*\n\nNotes: ${reminder.notes || 'None'}\n\n🛡️ *Autopay Guard Automated Assistant*`;

    const encodedText = encodeURIComponent(msgText);
    window.open(`https://wa.me/?text=${encodedText}`, '_blank', 'noopener,noreferrer');

    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${API_BASE_URL}/whatsapp/send-reminder`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          merchant_name: taskTitle,
          amount: 0,
          due_date: dueFormatted,
          days_left: 0
        })
      });
      if (showToast) showToast(`📱 WhatsApp alert triggered for '${taskTitle}'!`);
    } catch (e) {
      console.warn("WhatsApp API trigger note:", e);
    }
  };

  const padZero = (num) => String(num).padStart(2, '0');

  // Radial 3D Circular Progress Ring Gauge Component (Matching Reference Image)
  const renderRadialGauge = (value, maxValue, label) => {
    const percentage = Math.min(100, Math.max(0, (value / maxValue) * 100));
    const radius = 38;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="flex flex-col items-center">
        <div className="relative w-28 h-28 sm:w-32 sm:h-32 flex items-center justify-center">
          
          {/* Radial Ticks SVG Background */}
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="46"
              stroke="#1e293b"
              strokeWidth="2"
              strokeDasharray="1 3"
              fill="none"
            />
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="#0f172a"
              strokeWidth="6"
              fill="none"
            />
            <circle
              cx="50"
              cy="50"
              r={radius}
              stroke="#00F2FE"
              strokeWidth="6"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="none"
              className="transition-all duration-1000 ease-linear"
              style={{
                filter: 'drop-shadow(0px 0px 8px #00F2FE)'
              }}
            />
          </svg>

          {/* 7-Segment Digital Clock Value */}
          <div className="absolute flex items-center justify-center">
            <span className="text-2xl sm:text-3xl font-black tracking-tighter text-white drop-shadow-[0_0_12px_rgba(0,242,254,0.8)] font-mono">
              {padZero(value)}
            </span>
          </div>
        </div>

        <span className="text-[10px] sm:text-[11px] font-black tracking-widest text-cyan-400 uppercase mt-2">
          {label}
        </span>
      </div>
    );
  };

  // Format Added Date (IST Standard)
  const addedDateFormatted = reminder.created_at
    ? parseLocalDate(reminder.created_at).toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    : 'Recently Added';

  // Format Due Date (ISO/IST Format e.g. 2026-10-18)
  const dueObj = reminder.due_datetime ? parseLocalDate(reminder.due_datetime) : null;
  const dueDateFormattedIso = dueObj
    ? dueObj.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' }) // YYYY-MM-DD
    : 'Not Specified';
  
  const dueDateFormattedFull = dueObj
    ? dueObj.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    : 'Not Specified';

  // Format Offsets
  const formatOffsetLabel = (mins) => {
    if (mins < 60) return `${mins}m before`;
    if (mins === 60) return `1h before`;
    if (mins < 1440 && mins % 60 === 0) return `${mins / 60}h before`;
    if (mins === 1440) return `1d before`;
    if (mins > 1440 && mins % 1440 === 0) return `${mins / 1440}d before`;
    return `${mins}m before`;
  };

  // Submit Edit / Update
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editTitle.trim()) return;

    setIsSubmittingEdit(true);
    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }

      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const formattedDue = editDueDatetime ? String(editDueDatetime).replace(' ', 'T') : reminder.due_datetime;

      const res = await fetch(`${API_BASE_URL}/personal-reminders/${reminder.id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          title: editTitle,
          notes: editNotes,
          due_datetime: formattedDue,
          reminder_offsets: editOffsets,
          sync_calendar: editSyncCalendar,
          sync_whatsapp: editSyncWhatsapp
        })
      });

      if (res.ok) {
        const updated = await res.json();
        if (onEditReminder) onEditReminder(updated);
        if (showToast) showToast("✅ Personal Reminder updated successfully!");
        setIsEditing(false);
      } else {
        if (showToast) showToast("❌ Failed to update reminder.");
      }
    } catch (err) {
      if (showToast) showToast("⚠️ Error updating: " + err.message);
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  const isModalTaskDone = reminder.is_completed || (reminder.due_datetime && (parseLocalDate(reminder.due_datetime) - new Date()) <= 0);

  // Initial letter for Avatar
  const initialLetter = reminder.title ? reminder.title.charAt(0).toUpperCase() : 'P';

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-6 bg-slate-950/90 backdrop-blur-xl animate-in fade-in duration-200 overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-[#0b1120] border-2 border-cyan-500/40 rounded-3xl shadow-[0_0_50px_rgba(0,242,254,0.2)] overflow-hidden flex flex-col max-h-[90vh] sm:max-h-[88vh] my-auto">
        
        {/* HEADER BAR (Matching Reference Image) */}
        <div className="px-6 py-4 sm:py-5 border-b border-slate-800/80 flex items-center justify-between bg-[#070c18] shrink-0">
          <div className="flex items-center space-x-4">
            {/* Avatar Circle */}
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-400 via-blue-600 to-indigo-700 p-[2px] shadow-lg shadow-cyan-400/20 flex-shrink-0">
              <div className="w-full h-full bg-[#070c18] rounded-[14px] flex items-center justify-center font-black text-white text-xl uppercase">
                {initialLetter}
              </div>
            </div>
            
            {/* Title & Badge & Subtitle */}
            <div>
              <div className="flex items-center space-x-3 flex-wrap gap-y-1">
                <h3 className="text-xl font-black text-white tracking-tight">{reminder.title}</h3>
                {isModalTaskDone ? (
                  <span className="px-3 py-1 rounded-full text-[11px] font-extrabold bg-emerald-950/90 text-emerald-400 border border-emerald-500/50 uppercase tracking-wider flex items-center space-x-1.5 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>TASK COMPLETED</span>
                  </span>
                ) : (
                  <span className="px-3 py-1 rounded-full text-[11px] font-extrabold bg-emerald-950/90 text-emerald-400 border border-emerald-500/50 uppercase tracking-wider flex items-center space-x-1.5 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>AUTOPAY ON</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-medium mt-0.5">
                Full Subscription Contract & Live Autopay Renewal Countdown
              </p>
            </div>
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-[#131d31] hover:bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center border border-slate-700/60 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* MODAL BODY */}
        <div className="p-6 sm:p-8 space-y-6 overflow-y-auto flex-1 custom-scrollbar">

          {/* EDIT FORM MODE */}
          {isEditing ? (
            <form onSubmit={handleSaveEdit} className="bg-[#060a14] rounded-2xl p-6 border border-amber-500/40 space-y-5 shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h4 className="text-sm font-bold text-amber-300 uppercase tracking-wider flex items-center space-x-2">
                  <Edit className="w-4 h-4 text-amber-400" />
                  <span>Edit Personal Task Details</span>
                </h4>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Task Title *</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Due Date & Time *</label>
                <input
                  type="datetime-local"
                  value={editDueDatetime}
                  onChange={(e) => setEditDueDatetime(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Notes / Remarks</label>
                <input
                  type="text"
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              {/* TRIGGER CHANNELS CHECKLIST */}
              {(() => {
                const editMinsLeft = editDueDatetime ? (parseLocalDate(editDueDatetime) - new Date()) / (1000 * 60) : 9999;
                const isEditWaAvailable = editMinsLeft >= 60;
                return (
                  <div className="pt-3 border-t border-slate-800 space-y-2">
                    <label className="text-xs font-bold text-amber-300 block">Trigger Channels & Integration Checklist</label>
                    <div className="flex items-center space-x-5 text-xs flex-wrap gap-y-2">
                      <label className="flex items-center space-x-2 text-slate-200 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={editSyncCalendar}
                          onChange={(e) => setEditSyncCalendar(e.target.checked)}
                          className="rounded bg-slate-950 border-slate-800 text-indigo-500 focus:ring-0"
                        />
                        <span className="flex items-center space-x-1.5">
                          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Google Calendar (Highest Alert Time)</span>
                        </span>
                      </label>

                      <label className={`flex items-center space-x-2 text-slate-200 ${isEditWaAvailable ? 'cursor-pointer' : 'opacity-60 cursor-not-allowed'}`}>
                        <input
                          type="checkbox"
                          disabled={!isEditWaAvailable}
                          checked={isEditWaAvailable && editSyncWhatsapp}
                          onChange={(e) => setEditSyncWhatsapp(e.target.checked)}
                          className="rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0"
                        />
                        <span className="flex items-center space-x-1.5">
                          <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                          <span>WhatsApp Alert (1h Before)</span>
                        </span>
                      </label>
                    </div>
                  </div>
                );
              })()}

              {/* NOTIFICATION OFFSETS SELECTION */}
              <div className="pt-3 border-t border-slate-800 space-y-2">
                <label className="text-xs font-bold text-amber-300 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5">
                    <Bell className="w-3.5 h-3.5 text-amber-400" />
                    <span>App Push Alert Timing Offsets</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-normal">{editOffsets.length} Alert Times</span>
                </label>

                <div className="flex flex-wrap gap-2">
                  {[
                    { mins: 10, label: '⏱️ 10m' },
                    { mins: 30, label: '⏱️ 30m' },
                    { mins: 60, label: '🕒 1h' },
                    { mins: 120, label: '🕒 2h' },
                    { mins: 1440, label: '🌙 1d' },
                    { mins: 2880, label: '📅 2d' },
                  ].map((preset) => {
                    const isActive = editOffsets.includes(preset.mins);
                    return (
                      <button
                        key={preset.mins}
                        type="button"
                        onClick={() => {
                          if (isActive) {
                            if (editOffsets.length > 1) {
                              setEditOffsets(editOffsets.filter(m => m !== preset.mins));
                            }
                          } else {
                            setEditOffsets([...editOffsets, preset.mins].sort((a, b) => a - b));
                          }
                        }}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                          isActive
                            ? 'bg-amber-500/20 border-amber-500 text-amber-200'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {preset.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-5 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingEdit}
                  className="px-6 py-2.5 rounded-xl text-white font-bold text-xs bg-gradient-to-r from-amber-500 to-indigo-600 hover:scale-105 transition-all shadow-md cursor-pointer"
                >
                  {isSubmittingEdit ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          ) : (
            <>
              {/* LIVE COUNTDOWN PANEL (Matching Reference Image) */}
              <div className="bg-[#060a14] border border-slate-800/80 rounded-2xl p-6 sm:p-8 text-center space-y-6 shadow-inner relative overflow-hidden">
                
                {/* Centered Pill Badge */}
                <div className="inline-flex items-center space-x-2 px-5 py-1.5 rounded-full bg-[#081b29] border border-cyan-500/40 text-cyan-400 text-[11px] font-extrabold uppercase tracking-widest shadow-[0_0_12px_rgba(0,242,254,0.2)]">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                  <span className="w-2 h-2 rounded-full bg-cyan-400 absolute" />
                  <span className="pl-2">TIME REMAINING UNTIL NEXT AUTOPAY DEBIT</span>
                </div>

                {/* 4 Radial Gauges Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-2 max-w-2xl mx-auto">
                  {renderRadialGauge(timeLeft.days, 30, 'DAYS')}
                  {renderRadialGauge(timeLeft.hours, 24, 'HOURS')}
                  {renderRadialGauge(timeLeft.minutes, 60, 'MINUTES')}
                  {renderRadialGauge(timeLeft.seconds, 60, 'SECONDS')}
                </div>
              </div>

              {/* SUBSCRIPTION VAULT & MANDATE BREAKDOWN SECTION (Matching Reference Image) */}
              <div className="space-y-4">
                
                {/* Header Row */}
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-extrabold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    <span>SUBSCRIPTION VAULT & MANDATE BREAKDOWN</span>
                  </h4>
                  <span className="text-xs text-slate-400 font-medium">
                    All amounts in Indian Rupees (INR ₹)
                  </span>
                </div>

                {/* 4 Grid Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  
                  {/* Card 1: Monthly Outflow */}
                  <div className="p-4 rounded-2xl bg-[#060a14] border border-slate-800/80 space-y-1.5 shadow-md">
                    <span className="text-[11px] font-semibold text-slate-400 block">Monthly Outflow</span>
                    <div className="flex items-baseline space-x-1">
                      <span className="text-xl sm:text-2xl font-black text-white">₹649.00</span>
                      <span className="text-xs text-slate-400 font-semibold">/monthly</span>
                    </div>
                  </div>

                  {/* Card 2: Next Renewal Date */}
                  <div className="p-4 rounded-2xl bg-[#060a14] border border-slate-800/80 space-y-1.5 shadow-md">
                    <span className="text-[11px] font-semibold text-slate-400 block">Next Renewal Date</span>
                    <span className="text-lg font-extrabold text-[#00f2fe] block tracking-wide drop-shadow-[0_0_8px_rgba(0,242,254,0.4)]">
                      {dueDateFormattedIso}
                    </span>
                  </div>

                  {/* Card 3: Category & Plan */}
                  <div className="p-4 rounded-2xl bg-[#060a14] border border-slate-800/80 space-y-1.5 shadow-md">
                    <span className="text-[11px] font-semibold text-slate-400 block">Category & Plan</span>
                    <span className="text-sm font-bold text-white block truncate">
                      {reminder.notes?.includes('Category:') ? reminder.notes.split(']')[0].replace('[Category:', '').trim() : 'Entertainment'}
                    </span>
                  </div>

                  {/* Card 4: Payment Method */}
                  <div className="p-4 rounded-2xl bg-[#060a14] border border-slate-800/80 space-y-1.5 shadow-md">
                    <span className="text-[11px] font-semibold text-slate-400 block">Payment Method</span>
                    <div className="flex items-center space-x-2 text-white">
                      <CreditCard className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span className="text-sm font-bold truncate">UPI Autopay</span>
                    </div>
                  </div>

                </div>

                {/* Info Guidance Banner (Matching Reference Image) */}
                <div className="p-4 rounded-2xl bg-[#060a14]/90 border border-slate-800/80 flex items-start space-x-3 text-xs shadow-md">
                  <Info className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                  <div className="space-y-1">
                    <span className="font-bold text-slate-200 block">Autopay Protection & E-Mandate Guidance:</span>
                    <p className="text-slate-400 leading-relaxed">
                      Web Push alerts trigger automatically at configured lead times (10m, 30m, 1h). Multi-time triggers auto-synced with Google Calendar & WhatsApp. Target due: <strong className="text-slate-200">{dueDateFormattedFull}</strong>.
                    </p>
                  </div>
                </div>

              </div>
            </>
          )}

        </div>

        {/* BOTTOM ACTION TOOLBAR (Matching Reference Image) */}
        {!isEditing && (
          <div className="px-6 py-4 border-t border-slate-800/80 flex items-center justify-between flex-wrap gap-3 bg-[#070c18] shrink-0">
            
            {/* Left Button: Pause Autopay (Set OFF) / Toggle Complete */}
            <button
              onClick={(e) => onToggleComplete && onToggleComplete(reminder.id, e)}
              className="px-5 py-2.5 rounded-full border border-emerald-500/60 bg-emerald-950/30 hover:bg-emerald-500/20 text-emerald-400 font-bold text-xs uppercase tracking-wider flex items-center space-x-2 transition-all shadow-[0_0_15px_rgba(16,185,129,0.15)] cursor-pointer"
            >
              <Power className="w-4 h-4 text-emerald-400" />
              <span>{isModalTaskDone ? 'Reactivate Autopay (Set ON)' : 'Pause Autopay (Set OFF)'}</span>
            </button>

            {/* Right Buttons: Edit, WhatsApp, Delete */}
            <div className="flex items-center space-x-3">
              
              {/* Edit / Receipt Vault Button */}
              <button
                onClick={() => setIsEditing(true)}
                className="px-5 py-2.5 rounded-full bg-[#131d31] hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 font-bold text-xs flex items-center space-x-2 transition-all cursor-pointer"
              >
                <FileText className="w-4 h-4 text-cyan-400" />
                <span>Receipt Vault</span>
              </button>

              {/* WhatsApp Alert Button */}
              <button
                onClick={handleTriggerWhatsAppMessage}
                className="px-5 py-2.5 rounded-full bg-emerald-950/70 hover:bg-emerald-900 text-emerald-300 border border-emerald-600/50 font-bold text-xs flex items-center space-x-2 transition-all cursor-pointer"
              >
                <MessageSquare className="w-4 h-4 text-emerald-400" />
                <span>WhatsApp Alert</span>
              </button>

              {/* Delete Button */}
              <button
                onClick={() => {
                  if (onDeleteReminder) onDeleteReminder(reminder.id);
                  onClose();
                }}
                className="px-5 py-2.5 rounded-full bg-[#131d31] hover:bg-rose-950 text-slate-400 hover:text-rose-300 border border-slate-700/60 hover:border-rose-500/50 font-bold text-xs flex items-center space-x-2 transition-all cursor-pointer"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete</span>
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

