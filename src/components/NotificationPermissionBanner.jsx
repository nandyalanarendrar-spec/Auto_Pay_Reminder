import React, { useState, useEffect } from 'react';
import { Bell, X } from 'lucide-react';
import { requestNotificationPermission } from '../utils/browserNotifications';

export const NotificationPermissionBanner = ({ onPermissionGranted }) => {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Check if browser supports notifications & permission is still pending ('default')
    if (typeof window !== 'undefined' && 'Notification' in window) {
      const currentPermission = Notification.permission;
      const isDismissed = sessionStorage.getItem('autopay_dismiss_notif_banner') === 'true';

      if (currentPermission === 'default' && !isDismissed) {
        setShowBanner(true);
      }
    }
  }, []);

  const handleEnable = async () => {
    const granted = await requestNotificationPermission();
    if (granted) {
      setShowBanner(false);
      if (onPermissionGranted) onPermissionGranted();
    } else {
      setShowBanner(false);
    }
  };

  const handleDismiss = () => {
    sessionStorage.getItem('autopay_dismiss_notif_banner');
    sessionStorage.setItem('autopay_dismiss_notif_banner', 'true');
    setShowBanner(false);
  };

  if (!showBanner) return null;

  return (
    <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/20 to-amber-500/10 border-b border-amber-500/30 px-4 py-3 text-amber-200 text-sm flex items-center justify-between shadow-lg relative z-40 backdrop-blur-md">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-amber-500/20 rounded-full text-amber-400">
          <Bell className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <span className="font-semibold text-white">Enable Payment Reminders:</span> Get automatic desktop alerts when subscriptions or EMIs are due in 7, 3, or 1 day(s).
        </div>
      </div>
      <div className="flex items-center space-x-3">
        <button
          onClick={handleEnable}
          className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-md hover:shadow-amber-500/20 flex items-center space-x-1.5"
        >
          <Bell className="w-3.5 h-3.5" />
          <span>Enable Reminders</span>
        </button>
        <button
          onClick={handleDismiss}
          className="p-1.5 hover:bg-amber-500/20 rounded-lg text-amber-400/70 hover:text-amber-200 transition-colors"
          title="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default NotificationPermissionBanner;
