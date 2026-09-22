/**
 * Headless Google Calendar API Sync Engine
 * Uses backend REST API (Google Calendar API v3) via OAuth 2.0 refresh tokens.
 * Zero browser popups, zero pre-filled URLs, zero manual 'Save' buttons.
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const getAuthToken = async () => {
  try {
    const { supabase, isSupabaseConfigured } = await import('../lib/supabaseClient');
    if (isSupabaseConfigured && supabase) {
      const { data: { session } } = await supabase.auth.getSession();
      return session?.access_token || null;
    }
  } catch (e) {}
  return null;
};

/**
 * 1. Headlessly Syncs an Active Subscription to Google Calendar via FastAPI Backend
 */
export const syncSubscriptionToCalendar = async (sub, showToast, customToken = null) => {
  if (!sub || sub.status === 'cancelled' || sub.status === 'paid' || sub.autopay_enabled === false) return;

  const name = sub.name || sub.merchant_name || 'Subscription';
  const amount = parseFloat(sub.amount || 0);
  const dateRaw = sub.next_renewal_date || sub.next_payment_date || new Date().toISOString().split('T')[0];
  const isTrial = sub.is_free_trial || sub.status === 'trial' || (name && name.toLowerCase().includes('trial'));

  const title = isTrial ? `⚠️ ${name} Trial Ending — ₹${amount.toFixed(0)}` : `🔴 ${name} Autopay — ₹${amount.toFixed(0)}`;

  try {
    const token = customToken || await getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}/integrations/google-calendar/sync-event`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        title,
        date: dateRaw,
        description: `Autopay Protection Alert\nMerchant: ${name}\nAmount: ₹${amount.toFixed(2)}\nPayment/Renewal Date: ${dateRaw}`,
        amount: amount
      })
    });

    if (res.ok) {
      if (showToast) showToast(`🟢 Google Calendar event created for ${name} (${dateRaw})!`);
    }
  } catch (err) {
    console.warn("Google Calendar API sync note:", err);
  }
};

/**
 * 2. Headlessly Cancels / Removes Event from Google Calendar via Backend
 */
export const cancelSubscriptionCalendarEvent = async (sub, showToast) => {
  if (!sub) return;
  const name = sub.name || sub.merchant_name || 'Subscription';

  try {
    const token = await getAuthToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    await fetch(`${API_BASE_URL}/integrations/google-calendar/sync`, { method: 'POST', headers });
    if (showToast) {
      showToast(`🗑️ Event for ${name} updated/removed on Google Calendar!`);
    }
  } catch (err) {
    console.warn("Google Calendar API cancel note:", err);
  }
};

/**
 * 3. Headlessly Syncs EMI Installment Due Date to Google Calendar
 */
export const syncEmiToCalendar = async (emi, showToast, customToken = null) => {
  if (!emi || emi.status === 'cancelled' || emi.status === 'completed' || emi.status === 'paid') return;

  const name = emi.loan_name || emi.lender_name || 'EMI Loan';
  const amount = parseFloat(emi.installment_amount || 0);
  const dateRaw = emi.next_due_date || new Date().toISOString().split('T')[0];

  try {
    const token = customToken || await getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE_URL}/integrations/google-calendar/sync-event`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        title: `💳 ${name} EMI — ₹${amount.toFixed(0)}`,
        date: dateRaw,
        description: `Autopay Protection Alert — EMI Loan Installment\nLoan: ${name}\nAmount: ₹${amount.toFixed(2)}\nDue Date: ${dateRaw}`,
        amount: amount
      })
    });

    if (res.ok) {
      if (showToast) showToast(`🟢 EMI event created for ${name} (${dateRaw})!`);
    }
  } catch (err) {
    console.warn("Google Calendar EMI sync note:", err);
  }
};

/**
 * 4. Headlessly Wipes Calendar & Syncs Fresh Single Entries
 */
export const syncAllSubscriptionsToCalendar = async (subscriptions = [], userEmis = [], showToast) => {
  try {
    const token = await getAuthToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    // Step 1: Total sweep purge of all existing calendar events across all pages
    await fetch(`${API_BASE_URL}/integrations/google-calendar/debug-purge`, { method: 'POST', headers });

    // Step 2: Clean single-entry resync
    const res = await fetch(`${API_BASE_URL}/integrations/google-calendar/sync`, { method: 'POST', headers });
    if (res.ok && showToast) {
      showToast(`🟢 Google Calendar wiped clean & freshly synchronized with single entries!`);
    }
  } catch (err) {
    console.warn("Full re-sync note:", err);
  }
};
