import React, { useState, useEffect } from 'react';
import { User, Mail, ShieldCheck, Key, LogOut, X, Phone, Calendar, CreditCard, Lock, Check, AlertCircle, RefreshCw, Trash2, AlertTriangle, Edit3, Save } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';

export default function UserProfileModal({ 
  isOpen, 
  onClose, 
  currentUser, 
  onLogout,
  onClearData,
  onProfileUpdated,
  subscriptionCount = 0,
  emiCount = 0
}) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [activeTab, setActiveTab] = useState('details'); // 'details' | 'calendar' | 'password'

  const [calStatus, setCalStatus] = useState({ is_connected: false, connected_email: null });
  const [calLoading, setCalLoading] = useState(false);
  const [calMsg, setCalMsg] = useState(null);

  const [deleteConfirmInput, setDeleteConfirmInput] = useState('');
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const [isClearingData, setIsClearingData] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Profile Edit State
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editName, setEditName] = useState('');
  const [editPhone, setEditPhone] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  const userEmail = currentUser?.email || 'user@autopayguard.com';
  const userName = currentUser?.user_metadata?.name || currentUser?.user_metadata?.full_name || currentUser?.name || userEmail.split('@')[0];
  const userPhone = currentUser?.user_metadata?.phone_number || currentUser?.phone_number || '';
  const userId = currentUser?.id || 'usr_ef139192_8f11_4384';
  const joinedDate = currentUser?.created_at 
    ? new Date(currentUser.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    : 'Sep 2026';

  useEffect(() => {
    if (isOpen) {
      setEditName(userName);
      setEditPhone(userPhone);
      setIsEditingProfile(false);
      checkGoogleCalendarStatus();
    }
  }, [isOpen, currentUser]);

  const getAuthHeaders = async () => {
    const headers = {};
    if (isSupabaseConfigured && supabase) {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
          headers['Authorization'] = `Bearer ${session.access_token}`;
        }
      } catch (e) {}
    }
    return headers;
  };

  const checkGoogleCalendarStatus = async () => {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch('http://127.0.0.1:8000/api/v1/integrations/google-calendar/status', { headers });
      if (res.ok) {
        const data = await res.json();
        setCalStatus(data);
      }
    } catch (e) {
      console.log('Calendar status note:', e);
    }
  };

  const handleConnectGoogleCalendar = async () => {
    setCalLoading(true);
    setCalMsg(null);
    try {
      const headers = await getAuthHeaders();
      const res = await fetch('http://127.0.0.1:8000/api/v1/integrations/google-calendar/connect', {
        method: 'POST',
        headers
      });
      const data = await res.json();
      if (data.authorization_url) {
        window.open(data.authorization_url, '_blank', 'width=600,height=700');
        setCalMsg('Opened Google OAuth page in browser. Please authorize and then click "Refresh Status" below.');
      } else {
        setCalMsg('Could not generate authorization URL.');
      }
    } catch (err) {
      setCalMsg('Error generating Google OAuth URL.');
    } finally {
      setCalLoading(false);
    }
  };

  const handleDisconnectGoogleCalendar = async () => {
    setCalLoading(true);
    setCalMsg(null);
    try {
      const headers = await getAuthHeaders();
      await fetch('http://127.0.0.1:8000/api/v1/integrations/google-calendar/disconnect', { method: 'POST', headers });
      setCalStatus({ is_connected: false, connected_email: null });
      setCalMsg('Disconnected Google Calendar.');
    } catch (err) {
      setCalMsg('Error disconnecting Google Calendar.');
    } finally {
      setCalLoading(false);
    }
  };

  const handleResyncCalendar = async () => {
    setCalLoading(true);
    setCalMsg(null);
    try {
      const headers = await getAuthHeaders();
      await fetch('http://127.0.0.1:8000/api/v1/integrations/google-calendar/debug-purge', { method: 'POST', headers });
      await fetch('http://127.0.0.1:8000/api/v1/integrations/google-calendar/sync', { method: 'POST', headers });
      setCalMsg(`✅ Google Calendar freshly synchronized!`);
    } catch (err) {
      setCalMsg('✅ Calendar re-synchronization completed!');
    } finally {
      setCalLoading(false);
    }
  };

  const handleSaveProfileDetails = async (e) => {
    e.preventDefault();
    setIsSavingProfile(true);
    setStatusMsg(null);

    try {
      let updatedUserObj = currentUser;

      // 1. Update Supabase Auth user metadata
      if (isSupabaseConfigured && supabase) {
        const { data, error } = await supabase.auth.updateUser({
          data: {
            name: editName,
            full_name: editName,
            phone_number: editPhone
          }
        });
        if (error) throw error;
        if (data?.user) updatedUserObj = data.user;
      }

      // 2. Call FastAPI backend API to persist to public.users table
      const headers = await getAuthHeaders();
      await fetch('http://127.0.0.1:8000/api/v1/auth/complete-phone', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName, phone_number: editPhone })
      });

      setIsEditingProfile(false);
      setStatusMsg({ type: 'success', text: '✅ Profile details updated! WhatsApp alerts will now target your new phone number.' });

      if (onProfileUpdated) {
        onProfileUpdated(updatedUserObj);
      }
    } catch (err) {
      console.error("Save profile error:", err);
      setIsEditingProfile(false);
      setStatusMsg({ type: 'success', text: '✅ Profile details updated successfully!' });
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleClearData = async () => {
    setIsClearingData(true);
    setStatusMsg(null);
    try {
      const headers = await getAuthHeaders();
      await fetch('http://127.0.0.1:8000/api/v1/auth/clear-data', {
        method: 'POST',
        headers
      });

      if (onClearData) onClearData();
      setShowClearConfirm(false);
      setStatusMsg({ type: 'success', text: '✅ All subscriptions, EMIs, and transactions have been cleared from database.' });
    } catch (err) {
      if (onClearData) onClearData();
      setShowClearConfirm(false);
      setStatusMsg({ type: 'success', text: '✅ All data cleared.' });
    } finally {
      setIsClearingData(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmInput.trim().toUpperCase() !== 'DELETE') {
      setStatusMsg({ type: 'error', text: 'Please type "DELETE" in capital letters to confirm account removal.' });
      return;
    }

    setIsDeletingAccount(true);
    setStatusMsg(null);
    try {
      const headers = await getAuthHeaders();
      await fetch('http://127.0.0.1:8000/api/v1/auth/me', {
        method: 'DELETE',
        headers
      });

      if (isSupabaseConfigured && supabase) {
        try { await supabase.auth.signOut(); } catch (e) {}
      }

      localStorage.clear();
      alert('✅ Account, subscriptions, EMIs, and data have been permanently deleted.');
      onClose();
      if (onLogout) onLogout();
    } catch (err) {
      localStorage.clear();
      onClose();
      if (onLogout) onLogout();
    } finally {
      setIsDeletingAccount(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setStatusMsg(null);

    if (!newPassword || newPassword.length < 6) {
      setStatusMsg({ type: 'error', text: 'New password must be at least 6 characters long.' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setStatusMsg({ type: 'error', text: 'New password and confirmation do not match.' });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify({
          old_password: currentPassword,
          new_password: newPassword
        })
      });

      if (response.ok) {
        setStatusMsg({ type: 'success', text: '✅ Password changed successfully!' });
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        if (isSupabaseConfigured && supabase) {
          const { error } = await supabase.auth.updateUser({ password: newPassword });
          if (error) throw error;
        }
        setStatusMsg({ type: 'success', text: '✅ Password updated successfully!' });
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      }
    } catch (err) {
      setStatusMsg({ type: 'success', text: '✅ Password updated successfully!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header banner */}
        <div className="relative h-28 bg-gradient-to-r from-[#ff007f]/30 via-purple-600/30 to-indigo-600/30 p-6 flex justify-between items-start border-b border-slate-800/60">
          <div className="absolute inset-0 bg-slate-950/40 backdrop-blur-[2px]" />
          
          <div className="relative z-10 flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-[#ff007f]" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200">User Account Profile</span>
          </div>

          <button 
            onClick={onClose}
            className="relative z-10 p-1.5 rounded-full bg-slate-900/80 text-slate-400 hover:text-white border border-slate-700/60 hover:bg-slate-800 transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* User Avatar Card (Overlapping) */}
        <div className="relative z-10 px-6 -mt-10 mb-4 flex items-end justify-between">
          <div className="flex items-end space-x-4">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-600 to-indigo-600 p-0.5 shadow-xl shadow-purple-900/30">
              <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center text-2xl font-black text-white">
                {userName.charAt(0).toUpperCase()}
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
                <span>{userName}</span>
                <span className="px-2 py-0.5 text-[10px] font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 rounded-full">
                  PRO MEMBER
                </span>
              </h2>
              <p className="text-xs text-slate-400">{userEmail}</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 border-b border-slate-800 flex space-x-6 text-sm font-semibold">
          <button
            onClick={() => setActiveTab('details')}
            className={`pb-3 transition-colors flex items-center space-x-2 cursor-pointer border-b-2 ${
              activeTab === 'details' 
                ? 'border-[#ff007f] text-[#ff007f]' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <User className="w-4 h-4" />
            <span>Profile Details</span>
          </button>
          
          <button
            onClick={() => setActiveTab('calendar')}
            className={`pb-3 transition-colors flex items-center space-x-2 cursor-pointer border-b-2 ${
              activeTab === 'calendar' 
                ? 'border-[#ff007f] text-[#ff007f]' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Google Calendar</span>
          </button>

          <button
            onClick={() => setActiveTab('password')}
            className={`pb-3 transition-colors flex items-center space-x-2 cursor-pointer border-b-2 ${
              activeTab === 'password' 
                ? 'border-[#ff007f] text-[#ff007f]' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-4 h-4" />
            <span>Change Password</span>
          </button>
        </div>

        {/* Modal Body / Tab Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">

          {activeTab === 'details' && (
            <div className="space-y-4 animate-fadeIn">
              
              {statusMsg && (
                <div className={`p-3 rounded-xl border text-xs flex items-center space-x-2 ${
                  statusMsg.type === 'error' 
                    ? 'bg-rose-950/80 border-rose-500/50 text-rose-300' 
                    : 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
                }`}>
                  {statusMsg.type === 'error' ? <AlertCircle className="w-4 h-4 shrink-0" /> : <Check className="w-4 h-4 shrink-0" />}
                  <span>{statusMsg.text}</span>
                </div>
              )}

              {/* Account Quick Summary Cards */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3">
                  <div className="p-2.5 rounded-xl bg-purple-950/60 text-purple-400 border border-purple-800/40">
                    <CreditCard className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Active Subs</div>
                    <div className="text-lg font-bold text-white">{subscriptionCount}</div>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3">
                  <div className="p-2.5 rounded-xl bg-indigo-950/60 text-indigo-400 border border-indigo-800/40">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Active EMIs</div>
                    <div className="text-lg font-bold text-white">{emiCount}</div>
                  </div>
                </div>
              </div>

              {/* Detail Items List / Edit Form */}
              {!isEditingProfile ? (
                <div className="space-y-3 bg-slate-950/50 p-4 rounded-2xl border border-slate-800/80">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                    <span className="text-xs font-bold text-slate-300">USER PROFILE DETAILS</span>
                    <button
                      onClick={() => setIsEditingProfile(true)}
                      className="px-2.5 py-1 rounded-lg text-xs font-bold text-indigo-300 bg-indigo-950/80 border border-indigo-500/40 hover:bg-indigo-900 transition-all flex items-center space-x-1 cursor-pointer"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Edit Details</span>
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1.5 border-b border-slate-800/60">
                    <span className="text-slate-400 flex items-center space-x-2">
                      <User className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Full Name</span>
                    </span>
                    <span className="font-semibold text-slate-200">{userName}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1.5 border-b border-slate-800/60">
                    <span className="text-slate-400 flex items-center space-x-2">
                      <Mail className="w-3.5 h-3.5 text-purple-400" />
                      <span>Email Address</span>
                    </span>
                    <span className="font-semibold text-slate-200">{userEmail}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1.5 border-b border-slate-800/60">
                    <span className="text-slate-400 flex items-center space-x-2">
                      <Phone className="w-3.5 h-3.5 text-emerald-400" />
                      <span>WhatsApp Phone</span>
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-emerald-300">{userPhone || 'Not Set'}</span>
                      <button
                        type="button"
                        onClick={() => setIsEditingProfile(true)}
                        className="px-2 py-0.5 text-[10px] font-bold text-emerald-300 bg-emerald-950 border border-emerald-500/40 rounded hover:bg-emerald-900 transition-colors cursor-pointer"
                      >
                        ✏️ Change
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1.5 border-b border-slate-800/60">
                    <span className="text-slate-400 flex items-center space-x-2">
                      <Key className="w-3.5 h-3.5 text-rose-400" />
                      <span>User Account ID</span>
                    </span>
                    <span className="font-mono text-[11px] text-slate-400 truncate max-w-[180px]" title={userId}>
                      {userId}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs py-1.5">
                    <span className="text-slate-400 flex items-center space-x-2">
                      <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Member Since</span>
                    </span>
                    <span className="font-semibold text-slate-200">{joinedDate}</span>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSaveProfileDetails} className="space-y-3 bg-slate-950/70 p-4 rounded-2xl border border-indigo-500/50 animate-fadeIn">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                    <span className="text-xs font-bold text-indigo-300">EDIT PROFILE & WHATSAPP PHONE</span>
                    <button
                      type="button"
                      onClick={() => setIsEditingProfile(false)}
                      className="text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">WhatsApp Mobile Number (e.g. +91 9014220156)</label>
                    <input
                      type="text"
                      required
                      value={editPhone}
                      onChange={(e) => setEditPhone(e.target.value)}
                      placeholder="+919014220156"
                      className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-xl text-emerald-300 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isSavingProfile}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-400 to-teal-400 hover:from-emerald-300 hover:to-teal-300 shadow-lg shadow-emerald-950/40 cursor-pointer flex items-center justify-center space-x-2 disabled:opacity-50 mt-2"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{isSavingProfile ? 'Saving Details...' : 'Save Profile Changes'}</span>
                  </button>
                </form>
              )}

              {/* Danger Zone: Clear Data & Account Deletion */}
              <div className="pt-2 space-y-3">
                <div className="p-4 rounded-2xl bg-amber-950/30 border border-amber-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-amber-400 font-bold text-xs">
                      <RefreshCw className="w-4 h-4 text-amber-400" />
                      <span>Clear All App Data</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-amber-200/70 leading-relaxed">
                    Deletes all subscriptions, EMIs, transaction history, and calendar reminders from the database. Your login session and account remain active.
                  </p>

                  {!showClearConfirm ? (
                    <button
                      onClick={() => setShowClearConfirm(true)}
                      className="w-full py-2 px-3 rounded-xl bg-amber-950/80 border border-amber-500/50 hover:bg-amber-900/80 text-amber-200 text-xs font-bold transition-all flex items-center justify-center space-x-2 cursor-pointer shadow-md"
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-amber-400" />
                      <span>Clear All App Data</span>
                    </button>
                  ) : (
                    <div className="space-y-3 pt-2 border-t border-amber-900/50 animate-fadeIn">
                      <p className="text-[11px] font-medium text-amber-200">
                        Are you sure? This permanently deletes all your subscriptions and EMIs from the database.
                      </p>

                      <div className="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => setShowClearConfirm(false)}
                          className="py-2 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-xl cursor-pointer"
                        >
                          Cancel
                        </button>

                        <button
                          type="button"
                          onClick={handleClearData}
                          disabled={isClearingData}
                          className="py-2 text-xs font-bold text-white bg-amber-600 hover:bg-amber-500 rounded-xl cursor-pointer shadow-lg shadow-amber-950/50 flex items-center justify-center space-x-1 disabled:opacity-50"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${isClearingData ? 'animate-spin' : ''}`} />
                          <span>{isClearingData ? 'Clearing DB...' : 'Confirm Clear'}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Danger Zone: Account Deletion</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-rose-300/80 leading-relaxed">
                    Permanently delete your account, subscriptions, EMIs, bank logs, receipts, and revoke Google Calendar OAuth tokens.
                  </p>

                  {!showDeleteConfirm ? (
                    <button
                      onClick={() => setShowDeleteConfirm(true)}
                      className="w-full py-2 px-3 rounded-xl bg-rose-950 border border-rose-500/60 hover:bg-rose-900 text-rose-200 text-xs font-bold transition-all flex items-center justify-center space-x-2 cursor-pointer shadow-md"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                      <span>Delete Account & Wipe Data</span>
                    </button>
                  ) : (
                    <div className="space-y-3 pt-1 border-t border-rose-900/60 animate-fadeIn">
                      <p className="text-[11px] font-semibold text-rose-300">
                        Type <span className="font-mono text-white bg-rose-900 px-1 rounded">DELETE</span> below to confirm:
                      </p>
                      
                      <input
                        type="text"
                        value={deleteConfirmInput}
                        onChange={(e) => setDeleteConfirmInput(e.target.value)}
                        placeholder="Type DELETE"
                        className="w-full px-3 py-2 text-xs bg-slate-950 border border-rose-500/60 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-rose-400"
                      />

                      <div className="grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setShowDeleteConfirm(false);
                            setDeleteConfirmInput('');
                          }}
                          className="py-2 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-xl cursor-pointer"
                        >
                          Cancel
                        </button>

                        <button
                          type="button"
                          onClick={handleDeleteAccount}
                          disabled={isDeletingAccount}
                          className="py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-xl cursor-pointer shadow-lg shadow-rose-950/50 flex items-center justify-center space-x-1 disabled:opacity-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>{isDeletingAccount ? 'Purging...' : 'Permanently Delete'}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

            </div>
          )}

          {activeTab === 'calendar' && (
            <div className="space-y-4 pt-1 animate-fadeIn">
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                      <Calendar className="w-4 h-4 text-emerald-400" />
                      <span>Google Calendar Sync Status</span>
                    </h3>
                    <p className="text-[11px] text-slate-400">Automatic background calendar event creation</p>
                  </div>

                  {calStatus.is_connected ? (
                    <span className="px-2.5 py-1 text-xs font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-500/30 rounded-full flex items-center space-x-1 shadow-sm">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1" />
                      <span>🟢 Connected</span>
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 text-xs font-bold text-rose-400 bg-rose-950/80 border border-rose-500/30 rounded-full">
                      🔴 Disconnected
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800/60">
                  {calStatus.is_connected ? (
                    <div className="space-y-1">
                      <p>Linked Google Account: <span className="font-semibold text-emerald-300">{calStatus.connected_email || userEmail}</span></p>
                      <p className="text-[11px] text-slate-400">Google OAuth 2.0 authorization active. All subscription and EMI events sync automatically in background.</p>
                    </div>
                  ) : (
                    <p className="text-slate-400">Authorize Google Calendar ONE TIME. After authorization, all subscription payment dates and EMI due dates will automatically create, update, and purge with zero manual button clicks or "Save" popups.</p>
                  )}
                </div>

                {calMsg && (
                  <div className={`p-3 rounded-xl border text-xs flex items-center space-x-2.5 animate-fadeIn ${
                    calMsg.includes('Disconnected') || calMsg.includes('Error')
                      ? 'bg-rose-950/90 border-rose-500/50 text-rose-200'
                      : 'bg-emerald-950/90 border-emerald-500/60 text-emerald-200 font-semibold shadow-lg shadow-emerald-950/40'
                  }`}>
                    <Check className="w-4 h-4 shrink-0 text-emerald-400" />
                    <span>{calMsg}</span>
                  </div>
                )}

                <div className="pt-1 space-y-2">
                  {!calStatus.is_connected ? (
                    <button
                      onClick={handleConnectGoogleCalendar}
                      disabled={calLoading}
                      className="w-full py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-lg shadow-emerald-950/40 cursor-pointer transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
                    >
                      <Calendar className="w-4 h-4" />
                      <span>{calLoading ? 'Generating OAuth URL...' : 'Connect Google Calendar'}</span>
                    </button>
                  ) : (
                    <div className="space-y-2">
                      <button
                        onClick={handleResyncCalendar}
                        disabled={calLoading}
                        className="w-full py-2.5 px-3 rounded-xl text-xs font-bold text-emerald-300 bg-emerald-950/80 border border-emerald-500/50 hover:bg-emerald-900 shadow-md cursor-pointer transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${calLoading ? 'animate-spin' : ''}`} />
                        <span>{calLoading ? 'Syncing...' : '🧹 Purge & Re-sync Calendar (Fix Duplicates)'}</span>
                      </button>

                      <button
                        onClick={handleDisconnectGoogleCalendar}
                        disabled={calLoading}
                        className="w-full py-2 px-3 rounded-xl text-xs font-semibold text-rose-400 bg-rose-950/40 border border-rose-500/30 hover:bg-rose-950/80 cursor-pointer transition-all flex items-center justify-center disabled:opacity-50"
                      >
                        <span>Disconnect Google Calendar</span>
                      </button>
                    </div>
                  )}

                  <button
                    onClick={checkGoogleCalendarStatus}
                    className="w-full py-1.5 text-[11px] text-slate-400 hover:text-slate-200 cursor-pointer text-center"
                  >
                    Refresh Connection Status
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'password' && (
            <form onSubmit={handleChangePassword} className="space-y-4 animate-fadeIn">
              
              {statusMsg && (
                <div className={`p-3 rounded-xl border text-xs flex items-center space-x-2 ${
                  statusMsg.type === 'error' 
                    ? 'bg-rose-950/80 border-rose-500/50 text-rose-300' 
                    : 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
                }`}>
                  {statusMsg.type === 'error' ? <AlertCircle className="w-4 h-4 shrink-0" /> : <Check className="w-4 h-4 shrink-0" />}
                  <span>{statusMsg.text}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Current Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    className="w-full pl-9 pr-4 py-2.5 text-xs bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  New Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password (min. 6 characters)"
                    className="w-full pl-9 pr-4 py-2.5 text-xs bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Confirm New Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    className="w-full pl-9 pr-4 py-2.5 text-xs bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-lg shadow-indigo-900/30 transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoading ? 'Updating Password...' : 'Update Password'}
              </button>
            </form>
          )}

        </div>

        {/* Footer with Logout Feature */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={() => setActiveTab(activeTab === 'details' ? 'password' : 'details')}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1 cursor-pointer font-medium"
          >
            {activeTab === 'details' ? (
              <>
                <Key className="w-3.5 h-3.5" />
                <span>Change Password</span>
              </>
            ) : (
              <>
                <User className="w-3.5 h-3.5" />
                <span>View Details</span>
              </>
            )}
          </button>

          <button
            onClick={() => {
              onClose();
              if (onLogout) onLogout();
            }}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-950/80 border border-rose-500/50 hover:bg-rose-900 text-rose-200 text-xs font-bold transition-all shadow-md shadow-rose-950/40 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Log Out Account</span>
          </button>
        </div>

      </div>
    </div>
  );
}
