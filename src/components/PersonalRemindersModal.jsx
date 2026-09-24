import React, { useState, useEffect } from 'react';
import { 
  X, 
  Bell, 
  Calendar, 
  Clock, 
  Plus, 
  Trash2, 
  CheckCircle2, 
  Sparkles, 
  ShieldAlert, 
  Check, 
  CheckSquare, 
  Smartphone,
  MessageSquare
} from 'lucide-react';
import { isSupabaseConfigured, supabase } from '../lib/supabaseClient';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export default function PersonalRemindersModal({ isOpen, onClose, showToast }) {
  const [reminders, setReminders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form State
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');
  
  // Default datetime: tomorrow at 10:00 AM
  const getTomorrowDefault = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(10, 0, 0, 0);
    return d.toISOString().slice(0, 16);
  };
  
  const [dueDatetime, setDueDatetime] = useState(getTomorrowDefault);
  
  // Custom Reminder Offsets (minutes before due time)
  // Default preset offsets: 10 mins, 30 mins, 60 mins (1 hr), 1440 mins (1 day)
  const [selectedOffsets, setSelectedOffsets] = useState([10, 30, 60]);
  const [customOffsetInput, setCustomOffsetInput] = useState('');
  const [customUnit, setCustomUnit] = useState('minutes'); // 'minutes' | 'hours' | 'days'

  const [syncCalendar, setSyncCalendar] = useState(true);
  const [syncWhatsapp, setSyncWhatsapp] = useState(true);

  // Fetch reminders from backend
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
    if (isOpen) {
      fetchReminders();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Toggle Preset Offset
  const togglePresetOffset = (minutes) => {
    if (selectedOffsets.includes(minutes)) {
      if (selectedOffsets.length === 1) {
        if (showToast) showToast("⚠️ Please keep at least one reminder offset.");
        return;
      }
      setSelectedOffsets(selectedOffsets.filter(m => m !== minutes));
    } else {
      setSelectedOffsets([...selectedOffsets, minutes].sort((a, b) => a - b));
    }
  };

  // Add Custom Offset
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
      if (showToast) showToast(`✅ Added custom reminder: ${val} ${customUnit} before!`);
    }
    setCustomOffsetInput('');
  };

  // Remove offset tag
  const removeOffset = (minutes) => {
    if (selectedOffsets.length === 1) {
      if (showToast) showToast("⚠️ Minimum 1 reminder time required.");
      return;
    }
    setSelectedOffsets(selectedOffsets.filter(m => m !== minutes));
  };

  // Format minutes into human friendly label
  const formatOffsetLabel = (mins) => {
    if (mins < 60) return `${mins} mins before`;
    if (mins === 60) return `1 hr before`;
    if (mins < 1440 && mins % 60 === 0) return `${mins / 60} hrs before`;
    if (mins === 1440) return `1 day before`;
    if (mins > 1440 && mins % 1440 === 0) return `${mins / 1440} days before`;
    return `${mins} mins before`;
  };

  // Submit New Custom Personal Reminder
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
          notes,
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
        
        // Reset form
        setTitle('');
        setNotes('');
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

  // Delete Reminder
  const handleDelete = async (id) => {
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
    } catch (err) {
      console.warn("Delete reminder note:", err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden glass-container my-8">
        
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-amber-500 to-indigo-600 p-0.5 shadow-lg shadow-amber-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
                <Bell className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <span>Personal Reminders & Alerts Vault</span>
              </h3>
              <p className="text-xs text-slate-400">Set custom task reminders with multi-time notifications</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-800/60 text-slate-400 hover:text-white transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto custom-scrollbar">
          
          {/* Section 1: Create New Custom Personal Reminder Form */}
          <form onSubmit={handleSubmit} className="glass-card-dark rounded-2xl p-5 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>Add Custom Personal Reminder</span>
              </h4>
              <span className="text-[10px] text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 rounded-full font-semibold">
                Multi-Time Trigger Ready
              </span>
            </div>

            {/* Task Title & Notes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">What to Remind? *</label>
                <input
                  type="text"
                  placeholder="e.g. Electricity Bill, Passport Renewal"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Due Date & Time *</label>
                <input
                  type="datetime-local"
                  value={dueDatetime}
                  onChange={(e) => setDueDatetime(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Notes / Remarks (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Account number, payment link or details"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>

            {/* CUSTOM MULTI-TIME REMINDER OFFSET SELECTOR */}
            <div className="pt-2 border-t border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-amber-300 flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-amber-400" />
                  <span>How long before should we remind you? (Select Multiple)</span>
                </label>
                <span className="text-[11px] text-slate-400 font-semibold">{selectedOffsets.length} active alerts</span>
              </div>

              {/* Quick Preset Toggle Chips */}
              <div className="flex flex-wrap gap-2">
                {[
                  { mins: 10, label: '⏱️ 10 Mins Before' },
                  { mins: 30, label: '⏱️ 30 Mins Before' },
                  { mins: 60, label: '🕒 1 Hour Before' },
                  { mins: 120, label: '🕒 2 Hours Before' },
                  { mins: 1440, label: '🌙 1 Day Before' },
                  { mins: 2880, label: '📅 2 Days Before' },
                ].map((preset) => {
                  const isActive = selectedOffsets.includes(preset.mins);
                  return (
                    <button
                      key={preset.mins}
                      type="button"
                      onClick={() => togglePresetOffset(preset.mins)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                        isActive
                          ? 'bg-gradient-to-r from-amber-500/20 to-indigo-600/20 border-amber-500 text-amber-200 shadow-md shadow-amber-500/10'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {preset.label}
                    </button>
                  );
                })}
              </div>

              {/* Custom Time Adder Row */}
              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="number"
                  placeholder="e.g. 45"
                  min="1"
                  value={customOffsetInput}
                  onChange={(e) => setCustomOffsetInput(e.target.value)}
                  className="w-24 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500"
                />
                <select
                  value={customUnit}
                  onChange={(e) => setCustomUnit(e.target.value)}
                  className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none"
                >
                  <option value="minutes">Minutes before</option>
                  <option value="hours">Hours before</option>
                  <option value="days">Days before</option>
                </select>
                <button
                  type="button"
                  onClick={handleAddCustomOffset}
                  className="px-3 py-1.5 rounded-xl bg-indigo-900/60 hover:bg-indigo-800 border border-indigo-500/40 text-indigo-200 text-xs font-semibold transition-all cursor-pointer"
                >
                  + Add Offset
                </button>
              </div>

              {/* Active Selected Offsets Tags */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {selectedOffsets.map((mins) => (
                  <span 
                    key={mins}
                    className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-amber-950/60 border border-amber-500/40 text-amber-300 text-[11px] font-semibold"
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

            {/* Sync Channel Options */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
              <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={syncCalendar}
                  onChange={(e) => setSyncCalendar(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-indigo-500 focus:ring-0"
                />
                <span className="flex items-center space-x-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Google Calendar Sync</span>
                </span>
              </label>

              <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={syncWhatsapp}
                  onChange={(e) => setSyncWhatsapp(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0"
                />
                <span className="flex items-center space-x-1">
                  <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                  <span>WhatsApp & Web Push</span>
                </span>
              </label>

              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl text-white font-semibold text-xs transition-all cursor-pointer shadow-md"
                style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
              >
                {isSubmitting ? 'Saving...' : 'Set Reminder'}
              </button>
            </div>
          </form>

          {/* Section 2: Vault List of Active Personal Reminders */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>Your Active Personal Reminders ({reminders.length})</span>
            </h4>

            {isLoading ? (
              <div className="p-6 text-center text-xs text-slate-400">Loading your personal reminders...</div>
            ) : reminders.length === 0 ? (
              <div className="glass-card-dark rounded-2xl p-6 text-center space-y-2 border border-slate-800/80">
                <Bell className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400">No custom personal reminders set yet.</p>
                <p className="text-[11px] text-slate-500">Create one above for passport renewals, bills, meetings, or custom tasks!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {reminders.map((rem) => {
                  const offsets = rem.reminder_offsets || [10, 30, 60];
                  const dueObj = new Date(rem.due_datetime);
                  const formattedDue = dueObj.toLocaleString('en-IN', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  });

                  return (
                    <div 
                      key={rem.id}
                      className="glass-card-dark rounded-2xl p-4 border border-slate-800 flex items-center justify-between hover:border-amber-500/40 transition-all"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-white">{rem.title}</span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-950/80 border border-amber-500/40 text-amber-300">
                            {offsets.length} Alerts Set
                          </span>
                        </div>

                        {rem.notes && (
                          <p className="text-[11px] text-slate-400">{rem.notes}</p>
                        )}

                        <div className="flex items-center space-x-2 text-[11px] text-slate-400">
                          <span className="flex items-center space-x-1 text-slate-300">
                            <Clock className="w-3 h-3 text-amber-400" />
                            <span>Due: {formattedDue}</span>
                          </span>
                        </div>

                        {/* Offsets List Badges */}
                        <div className="flex flex-wrap gap-1 pt-1">
                          {offsets.map((m) => (
                            <span key={m} className="px-2 py-0.5 rounded-md bg-slate-950 text-slate-300 text-[10px] border border-slate-800">
                              🔔 {formatOffsetLabel(m)}
                            </span>
                          ))}
                        </div>
                      </div>

                      <button
                        onClick={() => handleDelete(rem.id)}
                        className="p-2 rounded-xl bg-slate-950 text-slate-500 hover:text-rose-400 hover:border-rose-500/30 border border-slate-800 transition-colors"
                        title="Delete Reminder"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
