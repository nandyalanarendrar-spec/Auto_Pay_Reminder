export const toLocalISODate = (d) => {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

export const parseDateOnly = (dateString) => {
  if (!dateString) return null;
  const [y, m, d] = String(dateString).slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
};

export const getDaysUntil = (dateString) => {
  const target = parseDateOnly(dateString);
  if (!target) return 999;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
};

export const toMonthlyAmount = (sub) => {
  let amount = parseFloat(sub.amount) || 0;
  if (sub.billing_cycle === 'yearly') amount = amount / 12;
  if (sub.billing_cycle === 'weekly') amount = amount * 4;
  return amount;
};

export const subRenewalDate = (sub) => sub.next_renewal_date || sub.next_payment_date;

export const isSubCounted = (sub) =>
  sub.status !== 'cancelled' && sub.status !== 'paused' && sub.autopay_enabled !== false;

export const addBillingCycle = (dateString, cycle) => {
  const base = parseDateOnly(dateString) || new Date();
  const next = new Date(base);
  if (cycle === 'weekly') {
    next.setDate(next.getDate() + 7);
  } else if (cycle === 'yearly') {
    next.setFullYear(next.getFullYear() + 1);
  } else {
    const day = base.getDate();
    next.setDate(1);
    next.setMonth(next.getMonth() + 1);
    const lastDay = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
    next.setDate(Math.min(day, lastDay));
  }
  return toLocalISODate(next);
};

// Mirrors the backend get_notif_type() bucketing so snoozes match the alerts it would send.
export const notifTypeForDays = (days) => {
  if (days <= 0) return '0d';
  if (days === 1) return '1d';
  if (days <= 3) return '3d';
  return '7d';
};

export const formatINR = (n) => `₹${Math.round(n).toLocaleString('en-IN')}`;
