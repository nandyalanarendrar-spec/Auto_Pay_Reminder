import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  Calendar, 
  Clock, 
  Plus, 
  Trash2, 
  CheckCircle2, 
  Sparkles, 
  Check, 
  Smartphone,
  MessageSquare,
  FileText,
  Briefcase,
  Plane,
  HeartPulse,
  Tag,
  Search,
  Filter,
  AlertCircle,
  Edit,
  Eye
} from 'lucide-react';
import PersonalReminderCountdownModal from './PersonalReminderCountdownModal';
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient';
import { sendWebNotification, requestNotificationPermission } from '../utils/browserNotifications';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const parseLocalDate = (dateStr) => {
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

export default function PersonalRemindersPage({ showToast }) {
  const [reminders, setReminders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [statusFilter, setStatusFilter] = useState('Active'); // 'Active' | 'Completed' | 'All'
  const [searchQuery, setSearchQuery] = useState('');

  // 3D Countdown Ring Modal State
  const [selectedReminderForModal, setSelectedReminderForModal] = useState(null);
  const [isCountdownModalOpen, setIsCountdownModalOpen] = useState(false);

  // Form State
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('General');
  const [notes, setNotes] = useState('');
  
  // Default datetime: tomorrow at 10:00 AM
  const getTomorrowDefault = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(10, 0, 0, 0);
    return d.toISOString().slice(0, 16);
  };
  
  const [dueDatetime, setDueDatetime] = useState(getTomorrowDefault);
  const [selectedOffsets, setSelectedOffsets] = useState([10, 30, 60]);
  const [customOffsetInput, setCustomOffsetInput] = useState('');
  const [customUnit, setCustomUnit] = useState('minutes');

  const [syncCalendar, setSyncCalendar] = useState(true);
  const [syncWhatsapp, setSyncWhatsapp] = useState(true);

  const minutesUntilDue = dueDatetime ? (parseLocalDate(dueDatetime) - new Date()) / (1000 * 60) : 9999;
  const isWhatsappAvailable = minutesUntilDue >= 60;

  const fetchReminders = async () => {
    setIsLoading(true);
    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }
      
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const res = await fetch(`${API_BASE_URL}/personal-reminders`, { headers });
      if (res.ok) {
        const data = await res.json();
        setReminders(data);
      }
    } catch (err) {
      console.warn("Fetch personal reminders note:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
  }, []);

  const handleToggleComplete = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/personal-reminders/${id}/toggle-complete`, {
        method: 'PATCH',
        headers
      });

      if (res.ok) {
        const data = await res.json();
        setReminders(prev => prev.map(r => r.id === id ? { ...r, is_completed: data.is_completed } : r));
        if (selectedReminderForModal?.id === id) {
          setSelectedReminderForModal(prev => ({ ...prev, is_completed: data.is_completed }));
        }
        if (showToast) showToast(data.is_completed ? "✅ Task marked as Completed!" : "⏳ Task reactivated as Active!");
      }
    } catch (err) {
      console.warn("Toggle completion note:", err);
    }
  };

  // Real-time notification offset scanner (runs every 10 seconds)
  useEffect(() => {
    if (reminders.length === 0) return;

    const firedMapKey = 'autopay_fired_reminder_offsets';
    const firedMap = JSON.parse(sessionStorage.getItem(firedMapKey) || '{}');

    const checkOffsets = () => {
      const now = new Date();
      reminders.forEach(rem => {
        if (!rem.due_datetime || rem.is_completed) return;
        const dueObj = parseLocalDate(rem.due_datetime);
        const diffMs = dueObj - now;

        // User selected offsets + Guaranteed 0m (exact target due time)
        const userOffsets = rem.reminder_offsets || [10, 30, 60];
        const allPushOffsets = Array.from(new Set([...userOffsets, 0])).sort((a, b) => b - a);

        allPushOffsets.forEach(offset => {
          const targetOffsetMs = offset * 60 * 1000;
          let inWindow = false;
          if (offset === 0) {
            // Trigger 0m alert when within 30s around target due time
            inWindow = (diffMs <= 5000 && diffMs >= -30000);
          } else {
            // Trigger lead-time alert within 25s window at exact target offset time
            inWindow = (diffMs <= targetOffsetMs + 5000 && diffMs >= targetOffsetMs - 20000);
          }

          if (inWindow) {
            const key = `${rem.id}_offset_${offset}`;
            if (!firedMap[key]) {
              firedMap[key] = true;
              sessionStorage.setItem(firedMapKey, JSON.stringify(firedMap));

              const actualRemainingMins = Math.max(0, Math.round(diffMs / (1000 * 60)));
              const dueTimeStr = dueObj.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: true });

              let titleMsg = `⏰ Task Reminder: ${rem.title}`;
              let bodyMsg = `Your task "${rem.title}" is due in ${actualRemainingMins > 0 ? `${actualRemainingMins} minutes` : 'a few moments'}! (${dueTimeStr})`;

              if (offset === 0 || actualRemainingMins === 0) {
                titleMsg = `🚨 Task Due NOW: ${rem.title}`;
                bodyMsg = `Your personal task "${rem.title}" is DUE RIGHT NOW! (${dueTimeStr})`;
              } else if (offset >= 60 && actualRemainingMins >= 60) {
                const hrs = Math.round(actualRemainingMins / 60);
                bodyMsg = `Your task "${rem.title}" is due in ${hrs} hour(s)! (${dueTimeStr})`;
              }

              sendWebNotification(titleMsg, { body: bodyMsg });
              if (showToast) showToast(`⚡ ${titleMsg}: ${offset === 0 ? 'DUE NOW!' : `Due in ${offset}m`}`);
            }
          }
        });
      });
    };

    checkOffsets();
    const interval = setInterval(checkOffsets, 10000);
    return () => clearInterval(interval);
  }, [reminders, showToast]);

  const togglePresetOffset = (minutes) => {
    if (selectedOffsets.includes(minutes)) {
      if (selectedOffsets.length === 1) {
        if (showToast) showToast("⚠️ Keep at least one reminder offset.");
        return;
      }
      setSelectedOffsets(selectedOffsets.filter(m => m !== minutes));
    } else {
      setSelectedOffsets([...selectedOffsets, minutes].sort((a, b) => a - b));
    }
  };

  const handleAddCustomOffset = (e) => {
    e.preventDefault();
    const val = parseInt(customOffsetInput, 10);
    if (isNaN(val) || val <= 0) return;

    let multiplier = 1;
    if (customUnit === 'hours') multiplier = 60;
    if (customUnit === 'days') multiplier = 1440;

    const totalMinutes = val * multiplier;
    if (!selectedOffsets.includes(totalMinutes)) {
      setSelectedOffsets([...selectedOffsets, totalMinutes].sort((a, b) => a - b));
      if (showToast) showToast(`✅ Added custom alert: ${val} ${customUnit} before!`);
    }
    setCustomOffsetInput('');
  };

  const removeOffset = (minutes) => {
    if (selectedOffsets.length === 1) {
      if (showToast) showToast("⚠️ Minimum 1 reminder time required.");
      return;
    }
    setSelectedOffsets(selectedOffsets.filter(m => m !== minutes));
  };

  const formatOffsetLabel = (mins) => {
    if (mins < 60) return `${mins}m before`;
    if (mins === 60) return `1h before`;
    if (mins < 1440 && mins % 60 === 0) return `${mins / 60}h before`;
    if (mins === 1440) return `1d before`;
    if (mins > 1440 && mins % 1440 === 0) return `${mins / 1440}d before`;
    return `${mins}m before`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) {
      if (showToast) showToast("⚠️ Please enter a reminder title.");
      return;
    }

    setIsSubmitting(true);
    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }

      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/personal-reminders`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          title,
          notes: notes ? `[Category: ${category}] ${notes}` : `[Category: ${category}]`,
          due_datetime: dueDatetime,
          reminder_offsets: selectedOffsets,
          sync_calendar: syncCalendar,
          sync_whatsapp: syncWhatsapp
        })
      });

      if (res.ok) {
        const newRecord = await res.json();
        setReminders([newRecord, ...reminders]);
        if (showToast) showToast(`⏰ Personal Reminder set for '${title}' with ${selectedOffsets.length} alert times!`);
        
        setTitle('');
        setNotes('');
        setCategory('General');
        setDueDatetime(getTomorrowDefault());
      } else {
        if (showToast) showToast("❌ Failed to create custom reminder.");
      }
    } catch (err) {
      if (showToast) showToast("⚠️ Error creating reminder: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id, e) => {
    if (e) e.stopPropagation();
    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }

      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${API_BASE_URL}/personal-reminders/${id}`, { method: 'DELETE', headers });
      setReminders(reminders.filter(r => r.id !== id));
      if (showToast) showToast("🗑️ Personal reminder removed.");
      if (selectedReminderForModal?.id === id) {
        setIsCountdownModalOpen(false);
      }
    } catch (err) {
      console.warn("Delete reminder note:", err);
    }
  };

  const handleOpenModal = (reminder, e) => {
    if (e) e.stopPropagation();
    setSelectedReminderForModal(reminder);
    setIsCountdownModalOpen(true);
  };

  const handleUpdateLocalReminder = (updatedReminder) => {
    setReminders(prev => prev.map(r => r.id === updatedReminder.id ? updatedReminder : r));
    setSelectedReminderForModal(updatedReminder);
  };

  // Notification permission state
  const [notifPermission, setNotifPermission] = useState(() => {
    return typeof window !== 'undefined' && 'Notification' in window ? Notification.permission : 'unsupported';
  });

  const handleEnableNotifications = async () => {
    const granted = await requestNotificationPermission();
    setNotifPermission(granted ? 'granted' : Notification.permission);
    if (showToast) {
      showToast(granted ? "🔔 Desktop notifications enabled!" : "⚠️ Notification permission denied in browser.");
    }
  };

  const handleTestNotification = async () => {
    const granted = await requestNotificationPermission();
    setNotifPermission(granted ? 'granted' : Notification.permission);
    if (!granted) {
      if (showToast) showToast("⚠️ Desktop notifications blocked. Enable permissions in browser header.");
      return;
    }
    const fired = await sendWebNotification("⚡ Test Personal Reminder Alert", {
      body: "Desktop notifications are working perfectly! You will receive task reminders right on time."
    });
    if (showToast) {
      showToast(fired ? "✅ Sent test desktop notification!" : "⚠️ Browser blocked notification.");
    }
  };

  // Category Icon Resolver
  const getCategoryIcon = (cat) => {
    switch ((cat || '').toLowerCase()) {
      case 'bills': return <FileText className="w-4 h-4 text-emerald-400" />;
      case 'travel': return <Plane className="w-4 h-4 text-cyan-400" />;
      case 'work': return <Briefcase className="w-4 h-4 text-indigo-400" />;
      case 'health': return <HeartPulse className="w-4 h-4 text-rose-400" />;
      default: return <Tag className="w-4 h-4 text-amber-400" />;
    }
  };

  // Task is Completed if user manually completed it (r.is_completed) OR target due_datetime has passed
  const isTaskCompleted = (r) => {
    if (r.is_completed) return true;
    if (!r.due_datetime) return false;
    const dueObj = parseLocalDate(r.due_datetime);
    return (dueObj - new Date()) <= 0;
  };

  const activeCount = reminders.filter(r => !isTaskCompleted(r)).length;
  const completedCount = reminders.filter(r => isTaskCompleted(r)).length;

  // Filtered Reminders
  const filteredReminders = reminders.filter(r => {
    const matchesSearch = r.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (r.notes || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || 
                            (r.notes || '').toLowerCase().includes(selectedCategory.toLowerCase());
    
    let matchesStatus = true;
    const isDone = isTaskCompleted(r);
    if (statusFilter === 'Active') matchesStatus = !isDone;
    if (statusFilter === 'Completed') matchesStatus = isDone;

    return matchesSearch && matchesCategory && matchesStatus;
  });

  const totalActiveTriggers = reminders.reduce((acc, r) => acc + (r.reminder_offsets?.length || 1), 0);

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-in fade-in duration-300">
      
      {/* PAGE HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-card-dark rounded-3xl p-6 border border-slate-800 shadow-2xl">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-500 via-indigo-600 to-purple-600 p-0.5 shadow-xl shadow-amber-500/20 flex-shrink-0">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Clock className="w-7 h-7 text-amber-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-2xl font-black text-white tracking-tight">Personal Reminders & Tasks Vault</h2>
              <span className="px-2.5 py-0.5 text-xs font-bold text-amber-300 bg-amber-950/80 border border-amber-500/40 rounded-full">
                Multi-Alert Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Never forget anything — set custom task alerts for passport renewals, bills, meetings, health, or personal tasks with multi-time notification triggers (10m, 30m, 1h, 1d).
            </p>
          </div>
        </div>

        {/* TOP METRICS BADGES */}
        <div className="flex items-center space-x-3 self-start md:self-auto">
          <div className="px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-800 text-center">
            <span className="block text-xl font-black text-amber-400 leading-none">{reminders.length}</span>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Tasks</span>
          </div>
          <div className="px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-800 text-center">
            <span className="block text-xl font-black text-indigo-400 leading-none">{totalActiveTriggers}</span>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Alert Triggers</span>
          </div>
        </div>
      </div>

      {/* DESKTOP NOTIFICATION CONTROLS BANNER */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-md">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-xl border ${notifPermission === 'granted' ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400' : 'bg-amber-950/80 border-amber-500/40 text-amber-400'}`}>
            <Bell className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white">Desktop Web Notifications:</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${notifPermission === 'granted' ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40' : 'bg-amber-950 text-amber-300 border-amber-500/40'}`}>
                {notifPermission === 'granted' ? 'Active & Allowed' : notifPermission === 'denied' ? 'Blocked by Browser' : 'Permission Required'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {notifPermission === 'granted' 
                ? 'Desktop popups will trigger on exact offset times (10m, 30m, 1h, Due NOW).' 
                : 'Enable desktop notifications so popups trigger on your screen.'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {notifPermission !== 'granted' && (
            <button
              onClick={handleEnableNotifications}
              className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition-all cursor-pointer"
            >
              🔔 Enable Notifications
            </button>
          )}
          <button
            onClick={handleTestNotification}
            className="px-3 py-1.5 rounded-xl bg-indigo-900/60 hover:bg-indigo-800 border border-indigo-500/40 text-indigo-200 font-bold text-xs transition-all cursor-pointer flex items-center space-x-1"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Test Notification</span>
          </button>
        </div>
      </div>

      {/* CREATE REMINDER FORM + LIST GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN: CREATE TASK FORM (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <form onSubmit={handleSubmit} className="glass-card-dark rounded-3xl p-6 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Plus className="w-4 h-4 text-amber-400" />
                <span>Create New Personal Reminder</span>
              </h3>
              <span className="text-[10px] font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded-full border border-amber-500/30">
                Any Task
              </span>
            </div>

            {/* Title */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Task / Event Title *</label>
              <input
                type="text"
                placeholder="e.g. Passport Renewal, Electricity Bill, Meeting"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
                required
              />
            </div>

            {/* Category Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Task Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none"
              >
                <option value="General">🏷️ General Task</option>
                <option value="Bills">📄 Bills & Documents</option>
                <option value="Travel">✈️ Travel & Passport</option>
                <option value="Work">💼 Work & Meetings</option>
                <option value="Health">🏥 Health & Appointments</option>
              </select>
            </div>

            {/* Due Date & Time */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Due Date & Time *</label>
              <input
                type="datetime-local"
                value={dueDatetime}
                onChange={(e) => setDueDatetime(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
                required
              />
            </div>

            {/* Notes */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Notes / Link (Optional)</label>
              <textarea
                placeholder="e.g. Reference number, location or payment link"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>

            {/* MULTI-TIME REMINDER OFFSET SELECTOR */}
            <div className="pt-3 border-t border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-amber-300 flex items-center space-x-1.5">
                  <Bell className="w-3.5 h-3.5 text-amber-400" />
                  <span>Notification Offsets (Select Multiple)</span>
                </label>
                <span className="text-[10px] text-slate-400 font-semibold">{selectedOffsets.length} Alert Times</span>
              </div>

              {/* Chips */}
              <div className="flex flex-wrap gap-2">
                {[
                  { mins: 10, label: '⏱️ 10m' },
                  { mins: 30, label: '⏱️ 30m' },
                  { mins: 60, label: '🕒 1h' },
                  { mins: 120, label: '🕒 2h' },
                  { mins: 1440, label: '🌙 1d' },
                  { mins: 2880, label: '📅 2d' },
                ].map((preset) => {
                  const isActive = selectedOffsets.includes(preset.mins);
                  return (
                    <button
                      key={preset.mins}
                      type="button"
                      onClick={() => togglePresetOffset(preset.mins)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                        isActive
                          ? 'bg-amber-500/20 border-amber-500 text-amber-200 shadow-md shadow-amber-500/10'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {preset.label}
                    </button>
                  );
                })}
              </div>

              {/* Custom Offset Input */}
              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="number"
                  placeholder="e.g. 45"
                  min="1"
                  value={customOffsetInput}
                  onChange={(e) => setCustomOffsetInput(e.target.value)}
                  className="w-20 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500"
                />
                <select
                  value={customUnit}
                  onChange={(e) => setCustomUnit(e.target.value)}
                  className="px-2.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none"
                >
                  <option value="minutes">Mins before</option>
                  <option value="hours">Hours before</option>
                  <option value="days">Days before</option>
                </select>
                <button
                  type="button"
                  onClick={handleAddCustomOffset}
                  className="px-3 py-1.5 rounded-xl bg-indigo-900/60 hover:bg-indigo-800 border border-indigo-500/40 text-indigo-200 text-xs font-semibold transition-all cursor-pointer"
                >
                  + Add
                </button>
              </div>

              {/* Active Tags */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {selectedOffsets.map((mins) => (
                  <span 
                    key={mins}
                    className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-amber-950/80 border border-amber-500/40 text-amber-300 text-[11px] font-semibold"
                  >
                    <span>🔔 {formatOffsetLabel(mins)}</span>
                    <button
                      type="button"
                      onClick={() => removeOffset(mins)}
                      className="hover:text-rose-400 text-amber-500 transition-colors ml-1"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Sync Toggles & Submit */}
            <div className="pt-3 border-t border-slate-800 space-y-3">
              <div className="flex flex-col space-y-2 text-xs">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={syncCalendar}
                      onChange={(e) => setSyncCalendar(e.target.checked)}
                      className="rounded bg-slate-950 border-slate-800 text-indigo-500 focus:ring-0"
                    />
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Google Calendar (Highest Alert Time)</span>
                    </span>
                  </label>

                  <label className={`flex items-center space-x-2 text-slate-300 ${isWhatsappAvailable ? 'cursor-pointer' : 'opacity-60 cursor-not-allowed'}`}>
                    <input
                      type="checkbox"
                      disabled={!isWhatsappAvailable}
                      checked={isWhatsappAvailable && syncWhatsapp}
                      onChange={(e) => setSyncWhatsapp(e.target.checked)}
                      className="rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0"
                    />
                    <span className="flex items-center space-x-1">
                      <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                      <span>WhatsApp Alert (1h Before)</span>
                    </span>
                  </label>
                </div>

                {!isWhatsappAvailable && (
                  <div className="p-2 rounded-xl bg-amber-950/40 border border-amber-500/30 text-[11px] text-amber-300 flex items-center space-x-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span>WhatsApp alert not available (Due time is less than 1 hour away).</span>
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 rounded-2xl text-white font-bold text-xs shadow-lg transition-all hover:scale-[1.01] cursor-pointer flex items-center justify-center space-x-2"
                style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
              >
                <Sparkles className="w-4 h-4" />
                <span>{isSubmitting ? 'Saving Task...' : 'Set Personal Reminder'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* RIGHT COLUMN: REMINDERS VAULT LIST & SEARCH (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* SEARCH, STATUS TABS & CATEGORY FILTER BAR */}
          <div className="glass-card-dark rounded-3xl p-4 border border-slate-800 space-y-3 shadow-lg">
            
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              {/* Search Input */}
              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search personal reminders..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
                />
              </div>

              {/* Status Filter Tabs (Incompleted, Completed, All) */}
              <div className="flex items-center space-x-1 p-1 bg-slate-950 rounded-2xl border border-slate-800 w-full sm:w-auto justify-center">
                {[
                  { id: 'Active', label: `Incompleted (${activeCount})` },
                  { id: 'Completed', label: `Completed (${completedCount})` },
                  { id: 'All', label: `All Tasks (${reminders.length})` }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setStatusFilter(tab.id)}
                    className={`px-3.5 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                      statusFilter === tab.id
                        ? tab.id === 'Completed'
                          ? 'bg-emerald-600 text-white shadow-md'
                          : 'bg-amber-500 text-slate-950 shadow-md'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Category Pills */}
            <div className="flex items-center space-x-1 overflow-x-auto custom-scrollbar pt-2 border-t border-slate-800/80">
              <span className="text-[10px] font-bold text-slate-500 uppercase mr-1.5 shrink-0">Category:</span>
              {['All', 'Bills', 'Travel', 'Work', 'Health'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap border ${
                    selectedCategory === cat
                      ? 'bg-amber-500/20 border-amber-500 text-amber-200'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* VAULT TASK CARDS */}
          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-400 glass-card-dark rounded-3xl border border-slate-800">
              Loading your personal reminders vault...
            </div>
          ) : filteredReminders.length === 0 ? (
            <div className="glass-card-dark rounded-3xl p-10 text-center space-y-3 border border-slate-800 shadow-xl">
              <div className="w-12 h-12 rounded-2xl bg-amber-950/60 border border-amber-500/30 flex items-center justify-center mx-auto text-amber-400">
                <Bell className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-white">No Reminders Found</h4>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                {statusFilter === 'Completed' 
                  ? 'No completed tasks yet. Mark tasks as completed when finished!' 
                  : searchQuery || selectedCategory !== 'All' 
                  ? 'No tasks match your current filter or search criteria.' 
                  : 'Add your first personal reminder above for passport renewals, bills, meetings, or custom tasks!'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredReminders.map((rem) => {
                const offsets = rem.reminder_offsets || [10, 30, 60];
                const dueObj = parseLocalDate(rem.due_datetime);
                const formattedDue = dueObj.toLocaleString('en-IN', {
                  timeZone: 'Asia/Kolkata',
                  weekday: 'short',
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true
                });

                const addedObj = rem.created_at ? parseLocalDate(rem.created_at) : new Date();
                const formattedAdded = addedObj.toLocaleString('en-IN', {
                  timeZone: 'Asia/Kolkata',
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true
                });

                // Calculate countdown
                const now = new Date();
                const diffMs = dueObj - now;
                const diffMins = (dueObj - now) / (1000 * 60);
                const diffHours = Math.round(diffMs / (1000 * 60 * 60));
                const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

                let countdownLabel = `${diffHours}h left`;
                if (diffDays >= 2) countdownLabel = `${diffDays} days left`;
                if (diffMs <= 0) countdownLabel = 'Due / Passed';

                const isWaActive = rem.sync_whatsapp !== false && diffMins >= 60;
                const isDone = isTaskCompleted(rem);

                return (
                  <div 
                    key={rem.id}
                    onClick={(e) => handleOpenModal(rem, e)}
                    className={`glass-card-dark rounded-3xl p-5 border flex items-start justify-between hover:border-cyan-500/60 shadow-xl transition-all group cursor-pointer hover:bg-slate-900/40 relative ${
                      isDone ? 'border-emerald-500/30 bg-emerald-950/10 opacity-85' : 'border-slate-800'
                    }`}
                  >
                    <div className="space-y-2.5 max-w-md">
                      
                      {/* Title & Category Badge & Countdown Badge */}
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        <span className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                          {getCategoryIcon(rem.notes)}
                        </span>
                        <h4 className={`text-sm font-bold transition-colors ${
                          isDone ? 'line-through text-slate-400' : 'text-white group-hover:text-cyan-300'
                        }`}>
                          {rem.title}
                        </h4>
                        
                        {/* Status Badge */}
                        {isDone ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 border border-emerald-500/60 text-emerald-300 flex items-center space-x-1 shadow-sm">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>Completed</span>
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border bg-amber-950 border-amber-500/40 text-amber-300">
                            {countdownLabel}
                          </span>
                        )}

                        {/* 3D Gauge Hint Badge */}
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-500/40 flex items-center space-x-1 opacity-90 group-hover:opacity-100">
                          <Eye className="w-3 h-3 text-cyan-400" />
                          <span>3D Gauge</span>
                        </span>
                      </div>

                      {/* Notes / Details */}
                      {rem.notes && (
                        <p className="text-xs text-slate-400 pl-7">{rem.notes}</p>
                      )}

                      {/* Due Datetime & Added Date Row */}
                      <div className="flex items-center flex-wrap gap-3 text-xs text-slate-300 pl-7">
                        <span className="flex items-center space-x-1">
                          <Clock className="w-3.5 h-3.5 text-amber-400" />
                          <span>Due: <strong>{formattedDue}</strong></span>
                        </span>

                        <span className="flex items-center space-x-1 text-slate-400">
                          <Calendar className="w-3 h-3 text-slate-500" />
                          <span>Added: <strong>{formattedAdded}</strong></span>
                        </span>
                      </div>

                      {/* Calendar Sync Status & WhatsApp Status & Notification Offsets Badges */}
                      <div className="flex items-center flex-wrap gap-1.5 pl-7 pt-1">
                        {/* Calendar Status */}
                        <span className="px-2 py-0.5 rounded-md bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-[10px] font-bold flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          <span>Google Cal Synced</span>
                        </span>

                        {/* WhatsApp Status Badge */}
                        {isWaActive ? (
                          <span className="px-2 py-0.5 rounded-md bg-teal-950/80 border border-teal-500/40 text-teal-300 text-[10px] font-bold flex items-center space-x-1">
                            <MessageSquare className="w-3 h-3 text-teal-400" />
                            <span>WhatsApp Active (1h Before)</span>
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-md bg-amber-950/60 border border-amber-500/30 text-amber-300 text-[10px] font-medium flex items-center space-x-1">
                            <AlertCircle className="w-3 h-3 text-amber-400" />
                            <span>WhatsApp N/A (&lt; 1h)</span>
                          </span>
                        )}

                        {/* Multi-Time Alerts */}
                        {offsets.map((m) => (
                          <span key={m} className="px-2 py-0.5 rounded-md bg-slate-950 text-slate-300 text-[10px] border border-slate-800 flex items-center space-x-1">
                            <Bell className="w-2.5 h-2.5 text-amber-400" />
                            <span>{formatOffsetLabel(m)}</span>
                          </span>
                        ))}
                      </div>

                    </div>

                    {/* Action Buttons: Mark Complete, Edit & Delete */}
                    <div className="flex items-center space-x-1.5">
                      <button
                        onClick={(e) => handleToggleComplete(rem.id, e)}
                        className={`p-2 rounded-xl border transition-all cursor-pointer ${
                          isDone
                            ? 'bg-emerald-950/80 border-emerald-500/60 text-emerald-400 hover:bg-emerald-900'
                            : 'bg-slate-950 border-slate-800 text-slate-500 hover:text-emerald-400 hover:border-emerald-500/40'
                        }`}
                        title={isDone ? "Reactivate Task as Pending" : "Mark Task as Completed"}
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>

                      <button
                        onClick={(e) => handleOpenModal(rem, e)}
                        className="p-2 rounded-xl bg-slate-950 text-slate-400 hover:text-amber-300 hover:border-amber-500/40 border border-slate-800 transition-colors cursor-pointer"
                        title="Edit & View 3D Live Countdown"
                      >
                        <Edit className="w-4 h-4" />
                      </button>

                      <button
                        onClick={(e) => handleDelete(rem.id, e)}
                        className="p-2 rounded-xl bg-slate-950 text-slate-500 hover:text-rose-400 hover:border-rose-500/30 border border-slate-800 transition-colors cursor-pointer"
                        title="Delete Reminder"
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

      </div>

      {/* 3D LIVE CIRCULAR COUNTDOWN GAUGES MODAL */}
      <PersonalReminderCountdownModal
        isOpen={isCountdownModalOpen}
        onClose={() => setIsCountdownModalOpen(false)}
        reminder={selectedReminderForModal}
        onDeleteReminder={(id) => handleDelete(id)}
        onEditReminder={handleUpdateLocalReminder}
        onToggleComplete={(id, e) => handleToggleComplete(id, e)}
        showToast={showToast}
      />

    </div>
  );
}
