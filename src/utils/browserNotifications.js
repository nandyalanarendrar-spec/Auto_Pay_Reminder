/**
 * Browser Web Notification Manager
 * Enables native OS Desktop Web Notifications via HTML5 Notification API
 */

let _sharedAudioCtx = null;
const getAudioCtx = () => {
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    if (!_sharedAudioCtx || _sharedAudioCtx.state === 'closed') {
      _sharedAudioCtx = new Ctx();
    }
    if (_sharedAudioCtx.state === 'suspended') {
      _sharedAudioCtx.resume().catch(() => {});
    }
    return _sharedAudioCtx;
  } catch (e) {
    return null;
  }
};

// Synthesized "bubble drop" pop — a quick downward pitch sweep with a soft
// decay, mimicking a water droplet/bubble sound. No external audio file
// dependency, so it always loads instantly and never breaks on a dead CDN link.
export const playBubbleDropSound = () => {
  try {
    const ctx = getAudioCtx();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(900, now);
    osc.frequency.exponentialRampToValueAtTime(220, now + 0.18);

    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.45, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.22);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.24);
  } catch (e) {}
};

// Loud, looping alarm-clock tone for "most important" reminders. Returns a
// stop() function the caller must invoke to silence it.
export const startAlarmSound = () => {
  const ctx = getAudioCtx();
  if (!ctx) return () => {};

  let stopped = false;
  let timeoutId = null;

  const beepPair = () => {
    if (stopped) return;
    const now = ctx.currentTime;
    [0, 0.3].forEach((offset) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'square';
      osc.frequency.setValueAtTime(880, now + offset);
      gain.gain.setValueAtTime(0.0001, now + offset);
      gain.gain.exponentialRampToValueAtTime(0.35, now + offset + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.25);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + offset);
      osc.stop(now + offset + 0.27);
    });
    timeoutId = setTimeout(beepPair, 900);
  };

  beepPair();

  return () => {
    stopped = true;
    if (timeoutId) clearTimeout(timeoutId);
  };
};

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

    // Play bubble-drop notification sound
    playBubbleDropSound();

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

