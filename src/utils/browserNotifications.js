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

    if (!granted) {
      console.warn("🔔 Desktop Notification Permission not granted:", Notification.permission);
      return false;
    }

    const notifOptions = {
      body: options.body || '',
      tag: options.tag || `notif-${Date.now()}`,
      requireInteraction: true,
      silent: false
    };

    console.log("🔔 [Autopay Guard Web Notification Fired]:", title, notifOptions);

    // Play subtle notification chime sound
    try {
      const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
      audio.volume = 0.5;
      audio.play().catch(() => {});
    } catch (aErr) {}

    // Direct HTML5 Standard Notification API (Instant, Non-blocking)
    try {
      const notification = new Notification(title, notifOptions);
      notification.onclick = () => {
        try { window.focus(); } catch (e) {}
        if (options.onClick) options.onClick();
        notification.close();
      };
      return true;
    } catch (directErr) {
      console.warn("Direct HTML5 Notification fallback to ServiceWorker:", directErr);
    }

    // Fallback: ServiceWorker showNotification if direct HTML5 constructor failed
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      try {
        const registration = await Promise.race([
          navigator.serviceWorker.ready,
          new Promise((_, reject) => setTimeout(() => reject(new Error("SW timeout")), 500))
        ]);
        if (registration && registration.showNotification) {
          await registration.showNotification(title, notifOptions);
          return true;
        }
      } catch (swErr) {
        console.warn("ServiceWorker showNotification error:", swErr);
      }
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


