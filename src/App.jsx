import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import ToolsRow from './components/ToolsRow';
import DashboardStats from './components/DashboardStats';
import HomeNavTiles from './components/HomeNavTiles';
import MonthlySummaryCard from './components/MonthlySummaryCard';
import BankDataCard from './components/BankDataCard';
import ReviewPage from './components/ReviewPage';
import SetuConnectCard from './components/SetuConnectCard';
import TrialAlertBanner from './components/TrialAlertBanner';
import SubscriptionsPage from './components/SubscriptionsPage';
import EmisPage from './components/EmisPage';
import CalendarPage from './components/CalendarPage';
import BottomNav from './components/BottomNav';
import ChatFab from './components/ChatFab';
import DesktopModeTip from './components/DesktopModeTip';
import AddSubscriptionModal from './components/AddSubscriptionModal';
import ReceiptVaultModal from './components/ReceiptVaultModal';
import AIChatDrawer from './components/AIChatDrawer';
import AuthContainer from './components/auth/AuthContainer';
import WhatIfSimulatorModal from './components/WhatIfSimulatorModal';
import UserProfileModal from './components/UserProfileModal';
import NotificationsCenterModal from './components/NotificationsCenterModal';
import AutopayCountdownModal from './components/AutopayCountdownModal';
import NotificationPermissionBanner from './components/NotificationPermissionBanner';
import PhoneCompletionModal from './components/PhoneCompletionModal';
import WhatsAppActivationModal from './components/WhatsAppActivationModal';
import PersonalRemindersPage from './components/PersonalRemindersPage';
import { isSupabaseConfigured, supabase } from './lib/supabaseClient';
import { requestNotificationPermission, sendWebNotification, fireDueReminderNotification } from './utils/browserNotifications';
import { syncSubscriptionToCalendar, cancelSubscriptionCalendarEvent, syncEmiToCalendar, syncAllSubscriptionsToCalendar } from './utils/calendarSync';
import { Check, ShieldAlert, Calendar } from 'lucide-react';
import { API_BASE_URL } from './config/api';
import { getDaysUntil, addBillingCycle, subRenewalDate, notifTypeForDays } from './utils/finance';
import { apiRequest } from './utils/api';

// Helper: get Supabase auth token for backend API calls
const getAuthTokenForSync = async () => {
  try {
    if (isSupabaseConfigured && supabase) {
      const { data: { session } } = await supabase.auth.getSession();
      return session?.access_token || null;
    }
  } catch (e) {}
  return null;
};

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [pendingPasswordReset, setPendingPasswordReset] = useState(false);

  // Subscriptions state fetched fresh from backend API
  const [subscriptions, setSubscriptions] = useState([]);

  // EMIs state fetched fresh from backend API
  const [userEmis, setUserEmis] = useState([]);

  // Kill Switch state
  const [killSwitchActive, setKillSwitchActive] = useState(false);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState(false);
  const [selectedReceiptSub, setSelectedReceiptSub] = useState(null);
  const [isAiChatOpen, setIsAiChatOpen] = useState(false);
  const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false);
  const [isWhatsAppModalOpen, setIsWhatsAppModalOpen] = useState(false);
  const [selectedCountdownSub, setSelectedCountdownSub] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [isPhoneModalOpen, setIsPhoneModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Theme State (Dark / Light)
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('autopay_theme') || 'dark';
  });

  // PWA Deferred Prompt State
  const [deferredInstallPrompt, setDeferredInstallPrompt] = useState(null);

  // Apply Light Theme Class to Body
  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
    localStorage.setItem('autopay_theme', theme);
  }, [theme]);

  // Listen to PWA beforeinstallprompt Event
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredInstallPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleToggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    showToast(nextTheme === 'light' ? '☀️ Switched to Light Mode' : '🌙 Switched to Dark Mode');
  };

  const handleInstallPwa = async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const choiceResult = await deferredInstallPrompt.userChoice;
      if (choiceResult.outcome === 'accepted') {
        showToast('🎉 Autopay Guard app installation accepted!');
      }
      setDeferredInstallPrompt(null);
    } else {
      showToast('📲 To install: Open Browser Menu → Tap "Add to Home Screen"');
    }
  };

  // Check Supabase session on mount & clean URL hash fragment safely
  useEffect(() => {
    async function checkAuthSession() {
      // Clean hash from URL bar if present (e.g. #access_token=...) immediately
      if (window.location.hash && (window.location.hash.includes('access_token') || window.location.hash.includes('error'))) {
        window.history.replaceState(null, '', window.location.pathname);
      }

      // Local development only: when there is no login session, use a demo user so the UI can be
      // previewed. In production, no session always means "show the login page" - never someone's account.
      const demoUser = import.meta.env.DEV
        ? { id: 'demo-user-1', email: 'demo@example.com', user_metadata: { name: 'Demo' } }
        : null;

      if (isSupabaseConfigured && supabase) {
        try {
          const { data } = await supabase.auth.getSession();
          setCurrentUser(data?.session?.user || demoUser);
        } catch (err) {
          console.warn("Supabase Auth check error:", err);
          setCurrentUser(demoUser);
        }
      } else {
        setCurrentUser(demoUser);
      }
      setIsAuthLoading(false);
    }

    checkAuthSession();

    if (isSupabaseConfigured && supabase) {
      const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
        if (session?.user) {
          if (!pendingPasswordReset) {
            setCurrentUser(session.user);
          }
        } else if (event === 'SIGNED_OUT') {
          setCurrentUser(null);
        }
      });

      return () => {
        authListener.subscription.unsubscribe();
      };
    } else {
      setIsAuthLoading(false);
    }
  }, []);

  // Prompt missing phone number for Google login / new users
  useEffect(() => {
    if (currentUser) {
      const hasPhone = currentUser.user_metadata?.phone_number || currentUser.phone_number;
      const isDismissed = sessionStorage.getItem('autopay_dismiss_phone_modal') === 'true';
      if (!hasPhone && !isDismissed) {
        setIsPhoneModalOpen(true);
      }
    }
  }, [currentUser]);

  const [googleCalConnected, setGoogleCalConnected] = useState(true);

  // Check Google Calendar connection status on user load
  useEffect(() => {
    async function checkCalStatus() {
      if (!currentUser) return;
      try {
        const token = await getAuthTokenForSync();
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const res = await fetch(`${API_BASE_URL}/integrations/google-calendar/status`, { headers });
        if (res.ok) {
          const data = await res.json();
          setGoogleCalConnected(data.is_connected);
        }
      } catch (e) {}
    }
    checkCalStatus();
  }, [currentUser]);

  // ── FETCH SUBSCRIPTIONS & EMIs FROM BACKEND (SINGLE SOURCE OF TRUTH) ──
  const [isDataLoading, setIsDataLoading] = useState(false);

  const fetchFromBackend = async () => {
    setIsDataLoading(true);
    try {
      const token = await getAuthTokenForSync();
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      // Fetch subscriptions AND EMIs in PARALLEL (not sequentially)
      const [subRes, emiRes] = await Promise.all([
        fetch(`${API_BASE_URL}/subscriptions/`, { headers }),
        fetch(`${API_BASE_URL}/emis/`, { headers })
      ]);

      // Process subscriptions
      if (subRes.ok) {
        const subData = await subRes.json();
        const items = subData.subscriptions || subData.data || subData;
        if (Array.isArray(items)) {
          const mapped = [];
          const seen = new Set();
          for (const s of items) {
            const key = (s.merchant_name || s.name || '').trim().toLowerCase();
            if (key && seen.has(key)) continue;
            if (key) seen.add(key);
            mapped.push({
              ...s,
              id: s.id || `sub-${Date.now()}-${Math.random()}`,
              name: s.merchant_name || s.name || 'Subscription',
              next_renewal_date: s.next_payment_date || s.next_renewal_date || s.start_date,
              billing_cycle: s.billing_frequency || s.billing_cycle || 'monthly',
              payment_method: s.payment_method || 'UPI Autopay',
              autopay_enabled: s.autopay_enabled ?? true,
            });
          }
          setSubscriptions(mapped);
          console.log(`✅ Loaded ${mapped.length} subscriptions from backend DB`);
        }
      }

      // Process EMIs
      if (emiRes.ok) {
        const emiData = await emiRes.json();
        const emiItems = emiData.emis || emiData.data || emiData;
        if (Array.isArray(emiItems)) {
          setUserEmis(emiItems);
          console.log(`✅ Loaded ${emiItems.length} EMIs from backend DB`);
        }
      }
    } catch (err) {
      console.log('Backend fetch error:', err);
    } finally {
      setIsDataLoading(false);
    }
  };

  // Bank data: demo status and how many detected payments wait for review
  const [bankStatus, setBankStatus] = useState(null);

  const refreshBankStatus = async () => {
    try {
      setBankStatus(await apiRequest('/bank/status'));
    } catch (err) {
      console.warn('Bank status unavailable:', err.message);
    }
  };

  // Setu (sandbox) bank connection state
  const [setuStatus, setSetuStatus] = useState(null);
  const autoSyncStartedRef = useRef(false);

  const refreshSetuStatus = async () => {
    try {
      setSetuStatus(await apiRequest('/bank/setu/status'));
    } catch (err) {
      console.warn('Setu status unavailable:', err.message);
    }
  };

  const handleBankDataChanged = async () => {
    await Promise.all([fetchFromBackend(), refreshBankStatus(), refreshSetuStatus()]);
  };

  // Right after the user approves on Setu's page and returns, import their transactions once.
  useEffect(() => {
    if (setuStatus?.state === 'active' && !setuStatus.last_synced_at && !autoSyncStartedRef.current) {
      autoSyncStartedRef.current = true;
      apiRequest('/bank/setu/sync', { method: 'POST' })
        .then((r) => showToast(r?.pending ? `⏳ ${r.message}` : `🏦 Bank connected. ${r.fetched} debits read, ${r.pending_review} payments to review.`))
        .catch((err) => showToast(`⚠️ ${err.message}`))
        .finally(handleBankDataChanged);
    }
  }, [setuStatus]);

  const fetchedUserRef = useRef(null);

  useEffect(() => {
    if (currentUser && fetchedUserRef.current !== currentUser.id) {
      fetchedUserRef.current = currentUser.id;
      fetchFromBackend();
      refreshBankStatus();
      refreshSetuStatus();
    }
  }, [currentUser]);



  // Auto-check upcoming renewals against backend DB deduplication engine
  const checkAndFireBackendDueReminders = async () => {
    if (!currentUser) return;
    try {
      const token = await getAuthTokenForSync();
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/notifications/due-reminders`, { headers });
      if (res.ok) {
        const data = await res.json();
        const dueAlerts = data.due_alerts || [];

        for (const alertItem of dueAlerts) {
          const fired = await fireDueReminderNotification(alertItem);
          if (fired) {
            // Mark as logged in backend DB so no other device re-fires this notification today
            await fetch(`${API_BASE_URL}/notifications/mark-notified`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
              },
              body: JSON.stringify({
                entity_type: alertItem.type,
                entity_id: alertItem.id,
                notification_type: alertItem.notification_type
              })
            });
          }
        }
      }
    } catch (err) {
      console.error("Backend due reminders check error:", err);
    }
  };

  useEffect(() => {
    if (currentUser) {
      checkAndFireBackendDueReminders();

      // Periodically poll backend every 2 hours while tab is open
      const intervalId = setInterval(() => {
        checkAndFireBackendDueReminders();
      }, 2 * 60 * 60 * 1000);

      return () => clearInterval(intervalId);
    }
  }, [currentUser, subscriptions, userEmis]);

  // Helper toast notification
  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Open Notification Center Modal & handle Push Notifications
  const handleEnableNotifications = async () => {
    setIsNotificationModalOpen(true);
    const granted = await requestNotificationPermission();
    if (granted) {
      checkAndFireBackendDueReminders();
    }
  };

  // Logout handler
  const handleLogout = async () => {
    if (isSupabaseConfigured && supabase) {
      await supabase.auth.signOut();
    }
    setCurrentUser(null);
    showToast("Signed out successfully.");
  };

  // Add subscription handler (Confirmed DB round-trip update)
  const handleAddSubscription = async (newSub) => {
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/subscriptions/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          merchant_name: newSub.name,
          category: newSub.category || 'General',
          amount: parseFloat(newSub.amount) || 0,
          billing_frequency: newSub.billing_cycle || 'monthly',
          next_payment_date: newSub.next_renewal_date || '2026-10-01',
          status: newSub.status || 'active',
          is_recurring: true,
          is_free_trial: !!newSub.is_free_trial,
          trial_end_date: newSub.is_free_trial ? (newSub.next_renewal_date || null) : null,
          autopay_enabled: killSwitchActive ? false : (newSub.autopay_enabled ?? true)
        })
      });

      if (res.ok) {
        const resData = await res.json();
        const savedSub = resData.subscription || resData;
        const formattedSub = {
          ...savedSub,
          id: savedSub.id,
          name: savedSub.merchant_name || savedSub.name || newSub.name,
          next_renewal_date: savedSub.next_payment_date || newSub.next_renewal_date,
          billing_cycle: savedSub.billing_frequency || newSub.billing_cycle || 'monthly',
          payment_method: 'UPI Autopay',
          autopay_enabled: savedSub.autopay_enabled ?? true
        };

        setSubscriptions(prev => [formattedSub, ...prev]);
        showToast(`Added "${formattedSub.name}" to vault (DB Synced)!`);
      } else {
        showToast(`Failed to save subscription to database.`);
      }
    } catch (err) {
      console.error("Backend API sync error:", err);
      showToast("Error adding subscription to database.");
    }
  };

  // Delete subscription handler with Automatic Calendar Cancellation (Confirmed DB round-trip)
  const handleDeleteSubscription = async (id) => {
    const subToDelete = subscriptions.find(s => s.id === id || s.merchant_name?.toLowerCase() === id.toLowerCase() || s.name?.toLowerCase() === id.toLowerCase());

    // 1. Immediate UI update for instant feedback
    setSubscriptions(prev => prev.filter(s => s.id !== id && s.name !== subToDelete?.name && s.merchant_name !== subToDelete?.merchant_name));
    showToast(`Deleted "${subToDelete?.name || 'subscription'}" (DB Synced)`);

    // 2. Perform backend DB deletion and calendar sync
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const res = await fetch(`${API_BASE_URL}/subscriptions/${id}`, {
        method: 'DELETE',
        headers
      });

      if (!res.ok) {
        console.error("Backend deletion returned status:", res.status);
      }
    } catch (err) {
      console.error('Backend delete sync error:', err);
    }
  };


  // Toggle Autopay state (Confirmed DB round-trip update)
  const handleToggleAutopay = async (id) => {
    const currentSub = subscriptions.find(s => s.id === id);
    if (!currentSub) return;
    const newState = !currentSub.autopay_enabled;

    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      const res = await fetch(`${API_BASE_URL}/subscriptions/${id}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ autopay_enabled: newState })
      });

      if (res.ok) {
        const resData = await res.json();
        const updatedFromDb = resData.subscription || resData;

        setSubscriptions(prev => prev.map(s => {
          if (s.id === id) {
            return {
              ...s,
              ...updatedFromDb,
              autopay_enabled: newState
            };
          }
          return s;
        }));

        if (!newState) {
          showToast(`⚠️ Autopay set to OFF for ${currentSub.name}. Excluded from monthly spend!`);
          sendWebNotification(`⚪ Autopay Disabled: ${currentSub.name}`, {
            body: `Autopay auto-debit has been PAUSED (OFF) for ${currentSub.name}. Excluded from monthly spend outflow.`,
            tag: `autopay-toggle-${id}`
          });
        } else {
          showToast(`✅ Autopay set to ON for ${currentSub.name}. Included in spending & alerts.`);
          sendWebNotification(`🟢 Autopay Enabled: ${currentSub.name}`, {
            body: `Autopay auto-debit is ACTIVE (ON) for ${currentSub.name}. Linked to your primary bank e-mandate.`,
            tag: `autopay-toggle-${id}`
          });
        }
      }
    } catch (err) {
      console.error('Backend autopay toggle sync error:', err);
    }
  };

  // View Receipt handler
  const handleViewReceipt = (sub) => {
    setSelectedReceiptSub(sub);
    setIsReceiptModalOpen(true);
  };

  // Pay EMI installment handler (Confirmed DB round-trip)
  const handlePayInstallment = async (emiId) => {
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/emis/${emiId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ pay_installment: true })
      });

      if (res.ok) {
        const resData = await res.json();
        const updatedEmi = resData.emi || resData;
        
        setUserEmis(prev => prev.map(emi => (emi.id === emiId ? { ...emi, ...updatedEmi } : emi)));
        showToast(`Logged installment payment for ${updatedEmi.loan_name}! (${updatedEmi.installments_paid}/${updatedEmi.total_installments} paid)`);
      }
    } catch (err) {
      console.error('Backend pay installment error:', err);
    }
  };

  // Add new EMI loan (Confirmed DB round-trip)
  const handleAddEmi = async (emiObj) => {
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/emis/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          loan_name: emiObj.loan_name,
          total_installments: parseInt(emiObj.total_installments) || 12,
          installments_paid: parseInt(emiObj.installments_paid) || 0,
          installment_amount: parseFloat(emiObj.installment_amount) || 0,
          next_due_date: emiObj.next_due_date || '2026-10-15',
          status: 'active'
        })
      });

      if (res.ok) {
        const resData = await res.json();
        const savedEmi = resData.emi || resData;
        setUserEmis(prev => [savedEmi, ...prev]);
        showToast(`Added EMI Tracker for "${savedEmi.loan_name}" (DB Synced)!`);
      }
    } catch (err) {
      console.error("Backend API EMI sync error:", err);
    }
  };

  // Delete EMI loan (Confirmed DB round-trip)
  const handleDeleteEmi = async (emiId) => {
    const currentEmi = userEmis.find(e => e.id === emiId);
    const loanName = currentEmi?.loan_name || 'EMI Loan';

    setUserEmis(prev => prev.filter(e => e.id !== emiId));
    showToast(`Deleted EMI Tracker for "${loanName}" from Vault!`);

    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      await fetch(`${API_BASE_URL}/emis/${emiId}`, {
        method: 'DELETE',
        headers
      });
    } catch (err) {
      console.error('Backend delete EMI error:', err);
    }
  };

  // Mark a subscription as paid: advance its renewal date by one billing cycle
  const handleMarkSubPaid = async (sub) => {
    const currentDate = subRenewalDate(sub);
    const nextDate = addBillingCycle(currentDate, sub.billing_cycle);
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/subscriptions/${sub.id}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ next_payment_date: nextDate })
      });

      if (res.ok) {
        setSubscriptions(prev => prev.map(s => s.id === sub.id
          ? { ...s, next_renewal_date: nextDate, next_payment_date: nextDate }
          : s));
        showToast(`✅ ${sub.name} marked paid. Next renewal: ${nextDate}`);
      } else {
        showToast(`❌ Could not update ${sub.name}. Please try again.`);
      }
    } catch (err) {
      console.error('Mark paid error:', err);
      showToast(`⚠️ Error updating ${sub.name}.`);
    }
  };

  // Snooze: log today's alert as already sent so every channel (web, push, WhatsApp) stays quiet today
  const snoozeEntityAlerts = async (entityType, entityId, name, dateString, isTrial = false) => {
    const baseType = notifTypeForDays(getDaysUntil(dateString));
    const types = isTrial ? [baseType, `trial_${baseType}`] : [baseType];
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      await Promise.all(types.map(notification_type =>
        fetch(`${API_BASE_URL}/notifications/mark-notified`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ entity_type: entityType, entity_id: entityId, notification_type })
        })
      ));
      showToast(`🔕 Alerts for ${name} muted for today. You'll be reminded again tomorrow.`);
    } catch (err) {
      console.error('Snooze error:', err);
      showToast(`⚠️ Could not snooze ${name}.`);
    }
  };

  const handleSnoozeSubAlert = (sub) =>
    snoozeEntityAlerts('subscription', sub.id, sub.name, subRenewalDate(sub), !!(sub.is_free_trial || sub.status === 'trial'));

  const handleSnoozeEmiAlert = (emi) =>
    snoozeEntityAlerts('emi', emi.id, emi.loan_name, emi.next_due_date);

  // Toggle Master Emergency Kill Switch
  const handleToggleKillSwitch = async () => {
    const nextState = !killSwitchActive;
    setKillSwitchActive(nextState);

    setSubscriptions(prev => {
      const updated = prev.map(s => ({
        ...s,
        autopay_enabled: !nextState
      }));

      return updated;
    });

    showToast(nextState ? "🚨 EMERGENCY KILL-SWITCH ACTIVATED! All Autopay debits set to OFF." : "Autopay Normal Operation Resumed. All debits set to ON.");

    if (nextState) {
      sendWebNotification("🚨 EMERGENCY KILL-SWITCH ACTIVATED!", {
        body: "All recurring bank auto-debit permissions have been set to Autopay OFF across linked bank accounts and cards.",
        tag: "kill-switch-active"
      });
    } else {
      sendWebNotification("✅ Emergency Kill-Switch Deactivated", {
        body: "Autopay Guard normal operation resumed. Recurring debits restored.",
        tag: "kill-switch-inactive"
      });
    }

    try {
      await fetch(`${API_BASE_URL}/autopay/kill-switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: nextState })
      });
    } catch (e) {
      console.warn("Kill-switch backend persist failed:", e);
    }

    // ★ Auto-resync calendar: kill switch ON = purge all events, OFF = recreate all events
    try {
      const token = await getAuthTokenForSync();
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      await fetch(`${API_BASE_URL}/integrations/google-calendar/sync`, { method: 'POST', headers });
      console.log(`🚨 Kill switch ${nextState ? 'ON' : 'OFF'} → calendar auto-resynced`);
    } catch (e) {
      console.warn("Kill-switch calendar auto-resync failed:", e);
    }
  };


  // Google Calendar & Direct Device Calendar Sync Handler
  const handleCalendarSync = (sub) => {
    syncSubscriptionToCalendar(sub, showToast);
  };

  // Retry Google Calendar Sync for Failed Subscription / EMI
  const handleRetrySync = async (id, type = 'subscription') => {
    try {
      const token = await getAuthTokenForSync();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const endpoint = type === 'subscription' 
        ? `${API_BASE_URL}/subscriptions/${id}/retry-sync`
        : `${API_BASE_URL}/emis/${id}/retry-sync`;

      showToast(`🔄 Retrying Google Calendar sync for ${type}...`);
      const res = await fetch(endpoint, { method: 'POST', headers });

      if (res.ok) {
        const data = await res.json();
        const syncRes = data.result || {};
        const isSuccess = syncRes.status === 'SUCCESS' || syncRes.calendar_sync_status === 'SYNCED';

        if (type === 'subscription') {
          setSubscriptions(prev => prev.map(s => {
            if (s.id === id) {
              return {
                ...s,
                calendar_sync_status: syncRes.calendar_sync_status || (isSuccess ? 'SYNCED' : 'FAILED'),
                calendar_sync_error: syncRes.calendar_sync_error || null,
                calendar_event_id: syncRes.calendar_event_id || s.calendar_event_id
              };
            }
            return s;
          }));
        } else {
          setUserEmis(prev => prev.map(e => {
            if (e.id === id) {
              return {
                ...e,
                calendar_sync_status: syncRes.calendar_sync_status || (isSuccess ? 'SYNCED' : 'FAILED'),
                calendar_sync_error: syncRes.calendar_sync_error || null,
                calendar_event_id: syncRes.calendar_event_id || e.calendar_event_id
              };
            }
            return e;
          }));
        }

        if (isSuccess) {
          showToast(`✅ Google Calendar event synced successfully for ${type}!`);
        } else {
          showToast(`⚠️ Sync failed: ${syncRes.calendar_sync_error || 'Please verify Google Calendar connection.'}`);
        }
      } else {
        showToast(`⚠️ Sync retry request failed.`);
      }
    } catch (err) {
      console.error('Retry sync error:', err);
      showToast(`❌ Error triggering calendar retry: ${err.message}`);
    }
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-[#080F1F] flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 rounded-full border-4 border-t-[#ff007f] border-r-[#9b1cff] border-b-transparent border-l-transparent animate-spin mb-4"></div>
        <p className="text-xs text-[#B8BECC] tracking-widest uppercase font-semibold">Authenticating Vault...</p>
      </div>
    );
  }

  if (!currentUser || pendingPasswordReset) {
    return <AuthContainer
      onAuthenticated={(user) => { setPendingPasswordReset(false); setCurrentUser(user); }}
      onPasswordResetStarted={() => setPendingPasswordReset(true)}
      onPasswordResetComplete={() => { setPendingPasswordReset(false); setCurrentUser(null); }}
    />;
  }

  return (
    <div className="min-h-screen flex bg-[#080F1F] text-slate-100">

      <div className="flex-1 flex flex-col min-w-0">

      {/* Soft Notification Permission Request Banner */}
      <NotificationPermissionBanner onPermissionGranted={() => checkAndFireBackendDueReminders()} />

      {/* Toast Banner */}
      {toastMessage && (
        <div className="fixed bottom-24 inset-x-0 z-50 flex justify-center px-4 pointer-events-none">
          <div className="glass-panel border border-[#ff007f]/40 text-white px-4 py-3 rounded-2xl shadow-2xl flex items-center space-x-2 animate-bounce text-xs font-semibold bg-slate-900/90 pointer-events-auto">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>{toastMessage}</span>
          </div>
        </div>
      )}

      {/* Navigation Header */}
      <Navbar currentUser={currentUser} killSwitchActive={killSwitchActive}>
        <ToolsRow
          currentUser={currentUser}
          onOpenWhatsAppModal={() => setIsWhatsAppModalOpen(true)}
          onEnableNotifications={handleEnableNotifications}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          canInstallPwa={!!deferredInstallPrompt}
          onInstallPwa={handleInstallPwa}
          onToggleKillSwitch={handleToggleKillSwitch}
          killSwitchActive={killSwitchActive}
          onOpenWhatIf={() => setIsWhatIfOpen(true)}
        />
      </Navbar>

      {/* Main Content Area (extra bottom padding for the fixed bottom nav) */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-36">
        
        <DesktopModeTip />

        {/* Emergency Kill-Switch Active Warning Banner */}
        {killSwitchActive && (
          <div className="mb-6 bg-rose-950/90 border-2 border-rose-500 rounded-2xl p-4 text-rose-200 flex items-center space-x-3 shadow-2xl animate-pulse">
            <ShieldAlert className="w-6 h-6 text-rose-400 flex-shrink-0" />
            <div>
              <p className="font-bold text-sm text-white">EMERGENCY KILL-SWITCH IS ACTIVE</p>
              <p className="text-xs text-rose-300">All recurring bank debit permissions have been set to Autopay OFF across linked UPI/cards.</p>
            </div>
          </div>
        )}

        {/* Google Calendar 1-Time Authorization Onboarding Banner */}
        {!googleCalConnected && (
          <div className="mb-6 bg-gradient-to-r from-emerald-950/90 via-slate-900 to-indigo-950/90 border border-emerald-500/40 rounded-2xl p-4 text-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <p className="font-bold text-sm text-white flex items-center space-x-2">
                  <span>Connect Google Calendar for Automatic Payment Date Sync</span>
                  <span className="px-2 py-0.5 text-[0.625rem] font-bold text-emerald-300 bg-emerald-950 rounded-full border border-emerald-500/40">1-Time Authorization</span>
                </p>
                <p className="text-xs text-slate-400 mt-0.5">Authorize once so all subscription renewal dates and EMI due dates automatically sync to Google Calendar with zero manual "Save" buttons.</p>
              </div>
            </div>
            <button
              onClick={() => setIsProfileModalOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-md cursor-pointer transition-all whitespace-nowrap"
            >
              Connect Google Calendar
            </button>
          </div>
        )}

        {/* ── Loading Skeleton (shows instantly while backend data loads) ── */}
        {isDataLoading && subscriptions.length === 0 && (
          <div className="space-y-6 mb-8 max-w-2xl mx-auto animate-pulse">
            {/* Estimated Spend skeleton */}
            <div className="rounded-3xl p-6 border border-white/10 bg-slate-900/60">
              <div className="h-3 w-32 bg-slate-700 rounded mb-3"></div>
              <div className="h-10 w-40 bg-slate-700 rounded mb-4"></div>
              <div className="h-1 w-full bg-slate-800 rounded mt-4"></div>
              <div className="flex justify-between mt-4">
                <div className="h-3 w-24 bg-slate-700 rounded"></div>
                <div className="h-3 w-20 bg-slate-700 rounded"></div>
              </div>
            </div>
            {/* AI Banner skeleton */}
            <div className="rounded-3xl p-5 border border-white/10 bg-slate-900/60 flex items-center space-x-4">
              <div className="w-12 h-12 rounded-2xl bg-slate-700"></div>
              <div className="flex-1">
                <div className="h-3 w-40 bg-slate-700 rounded mb-2"></div>
                <div className="h-2 w-64 bg-slate-800 rounded"></div>
              </div>
            </div>
            {/* Subscription cards skeleton */}
            {[1,2,3].map(i => (
              <div key={i} className="rounded-3xl p-5 border border-white/10 bg-slate-900/60 flex items-center space-x-4">
                <div className="w-10 h-10 rounded-full bg-slate-700"></div>
                <div className="flex-1">
                  <div className="h-3 w-32 bg-slate-700 rounded mb-2"></div>
                  <div className="h-2 w-20 bg-slate-800 rounded"></div>
                </div>
                <div className="h-6 w-16 bg-slate-700 rounded-full"></div>
              </div>
            ))}
          </div>
        )}

        {/* FULL PAGE CONDITIONAL RENDERING */}
        {activeTab === 'reminders' ? (
          <PersonalRemindersPage showToast={showToast} />
        ) : activeTab === 'subscriptions' ? (
          <SubscriptionsPage
            subscriptions={subscriptions}
            onBack={() => setActiveTab('dashboard')}
            onOpenAddModal={() => setIsAddModalOpen(true)}
            onDeleteSubscription={handleDeleteSubscription}
            onToggleAutopay={handleToggleAutopay}
            onViewReceipt={handleViewReceipt}
            onSelectSubscription={(sub) => setSelectedCountdownSub(sub)}
            onRetrySync={handleRetrySync}
            onMarkPaid={handleMarkSubPaid}
            onSnoozeAlert={handleSnoozeSubAlert}
          />
        ) : activeTab === 'emis' ? (
          <EmisPage
            userEmis={userEmis}
            onBack={() => setActiveTab('dashboard')}
            onPayInstallment={handlePayInstallment}
            onAddEmi={handleAddEmi}
            onRetrySync={handleRetrySync}
            onDeleteEmi={handleDeleteEmi}
            onSnoozeEmi={handleSnoozeEmiAlert}
          />
        ) : activeTab === 'review' ? (
          <ReviewPage
            onBack={() => setActiveTab('dashboard')}
            onChanged={handleBankDataChanged}
            showToast={showToast}
          />
        ) : activeTab === 'calendar' ? (
          <CalendarPage
            subscriptions={subscriptions}
            userEmis={userEmis}
            onBack={() => setActiveTab('dashboard')}
          />
        ) : (
          <div className="w-full lg:max-w-4xl lg:mx-auto space-y-6">
            <DashboardStats
              subscriptions={subscriptions}
              onToggleAiChat={() => setIsAiChatOpen(true)}
              onOpenSubscriptions={() => setActiveTab('subscriptions')}
            />

            <TrialAlertBanner subscriptions={subscriptions} onNavigate={setActiveTab} />

            <HomeNavTiles
              subscriptions={subscriptions}
              userEmis={userEmis}
              onNavigate={setActiveTab}
            />

            <BankDataCard
              status={bankStatus}
              isEmpty={!isDataLoading && subscriptions.length === 0 && userEmis.length === 0}
              onAddManually={() => setIsAddModalOpen(true)}
              onOpenReview={() => setActiveTab('review')}
              onChanged={handleBankDataChanged}
              showToast={showToast}
            />

            <SetuConnectCard
              status={setuStatus}
              onChanged={handleBankDataChanged}
              showToast={showToast}
            />

            <MonthlySummaryCard subscriptions={subscriptions} userEmis={userEmis} />
          </div>
        )}

      </main>

      {/* Modals & AI Chat Drawer */}
      <AddSubscriptionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAddSubscription={handleAddSubscription}
      />

      <ReceiptVaultModal
        isOpen={isReceiptModalOpen}
        onClose={() => setIsReceiptModalOpen(false)}
        subscription={selectedReceiptSub}
      />

      <WhatIfSimulatorModal
        isOpen={isWhatIfOpen}
        onClose={() => setIsWhatIfOpen(false)}
        subscriptions={subscriptions}
      />

      <AIChatDrawer
        isOpen={isAiChatOpen}
        onClose={() => setIsAiChatOpen(false)}
        subscriptions={subscriptions}
      />

      <UserProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        currentUser={currentUser}
        onLogout={handleLogout}
        onProfileUpdated={(updatedUser) => {
          if (updatedUser) setCurrentUser(updatedUser);
          showToast("✅ Profile updated! WhatsApp alerts will target your new mobile number.");
        }}
        onClearData={() => {
          setSubscriptions([]);
          setUserEmis([]);
          showToast("🧹 All subscriptions, EMIs, and transactions have been cleared from database!");
        }}
        subscriptionCount={subscriptions.length}
        emiCount={userEmis.length}
      />

      <NotificationsCenterModal
        isOpen={isNotificationModalOpen}
        onClose={() => setIsNotificationModalOpen(false)}
        subscriptions={subscriptions}
        killSwitchActive={killSwitchActive}
        userEmis={userEmis}
        onOpenWhatsAppModal={() => setIsWhatsAppModalOpen(true)}
      />

      <AutopayCountdownModal
        isOpen={Boolean(selectedCountdownSub)}
        onClose={() => setSelectedCountdownSub(null)}
        subscription={selectedCountdownSub}
        onToggleAutopay={handleToggleAutopay}
        onViewReceipt={handleViewReceipt}
        onDeleteSubscription={handleDeleteSubscription}
      />

      <PhoneCompletionModal
        isOpen={isPhoneModalOpen}
        onClose={() => {
          sessionStorage.setItem('autopay_dismiss_phone_modal', 'true');
          setIsPhoneModalOpen(false);
        }}
        currentUser={currentUser}
        onPhoneUpdated={(updatedUser) => {
          setCurrentUser(updatedUser);
          showToast("📱 Mobile number saved! Instant WhatsApp alerts enabled.");
        }}
      />

      <WhatsAppActivationModal
        isOpen={isWhatsAppModalOpen}
        onClose={() => setIsWhatsAppModalOpen(false)}
        currentUser={currentUser}
        onOpenProfile={() => setIsProfileModalOpen(true)}
      />

      {/* Floating Bottom-Right WhatsApp Quick Activation Pill */}
      <button
        onClick={() => setIsWhatsAppModalOpen(true)}
        className="hidden lg:flex fixed bottom-24 left-6 z-40 px-4 py-2.5 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-2xl border border-emerald-400/40 items-center space-x-2 transition-all hover:scale-105 cursor-pointer animate-pulse"
        title="Activate WhatsApp Alerts (Meta 24h Rule)"
      >
        <span className="text-base">💬</span>
        <span>Send 'Hi' on WhatsApp</span>
      </button>

      <BottomNav
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        currentUser={currentUser}
        onOpenProfile={() => setIsProfileModalOpen(true)}
      />

      {!isAiChatOpen && <ChatFab onClick={() => setIsAiChatOpen(true)} />}

      </div>
    </div>
  );
}
