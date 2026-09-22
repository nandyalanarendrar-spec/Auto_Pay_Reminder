/**
 * Browser Web Notification Manager
 * Enables native OS Desktop Web Notifications via HTML5 Notification API
 */

export const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.warn("This browser does not support desktop web notifications.");
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  return false;
};

export const sendWebNotification = async (title, options = {}) => {
  try {
    if (!('Notification' in window)) return false;

    let granted = Notification.permission === 'granted';
    if (!granted && Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      granted = permission === 'granted';
    }

    if (granted) {
      const notifOptions = {
        body: options.body || '',
        tag: options.tag || `notif-${Date.now()}`,
        requireInteraction: true,
        silent: false
      };

      console.log("🔔 [Autopay Guard Web Notification Fired]:", title, notifOptions);

      // Attempt 1: ServiceWorker Persistent Notification if registered
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        try {
          const registration = await navigator.serviceWorker.ready;
          if (registration && registration.showNotification) {
            await registration.showNotification(title, notifOptions);
            return true;
          }
        } catch (swErr) {
          console.warn("ServiceWorker showNotification fallback to HTML5 Notification API:", swErr);
        }
      }

      // Attempt 2: HTML5 Standard Notification API
      const notification = new Notification(title, notifOptions);

      notification.onclick = () => {
        try { window.focus(); } catch (e) {}
        if (options.onClick) options.onClick();
        notification.close();
      };

      return true;
    }
  } catch (err) {
    console.warn("Web Notification trigger error:", err);
  }
  return false;
};

export const fireDueReminderNotification = async (alertItem) => {
  if (!alertItem) return false;

  const title = alertItem.title || `⚡ Autopay Guard Alert: ${alertItem.name}`;
  const body = alertItem.body || `Payment of ₹${alertItem.amount} is due!`;
  const tag = `alert-${alertItem.type}-${alertItem.id}-${alertItem.next_due_date}`;

  return await sendWebNotification(title, { body, tag });
};

export const notifyUpcomingRenewals = (dueAlerts = []) => {
  if (!Array.isArray(dueAlerts) || dueAlerts.length === 0) return;

  dueAlerts.forEach(item => {
    fireDueReminderNotification(item);
  });
};


