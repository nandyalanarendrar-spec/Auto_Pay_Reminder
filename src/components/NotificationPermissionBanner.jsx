import React, { useState, useEffect } from 'react';
import { Bell, X, ShieldAlert, Lock, RefreshCw, CheckCircle2, ArrowRight } from 'lucide-react';
import { requestNotificationPermission } from '../utils/browserNotifications';

export const NotificationPermissionBanner = ({ onPermissionGranted }) => {
  const [showBanner, setShowBanner] = useState(false);
  const [permissionState, setPermissionState] = useState('default'); // 'default', 'granted', 'denied'
  const [showGuideModal, setShowGuideModal] = useState(false);

  const checkPermission = () => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      const current = Notification.permission;
      setPermissionState(current);

      const isDismissed = sessionStorage.getItem('autopay_dismiss_notif_banner') === 'true';

      if (current === 'granted') {
        setShowBanner(false);
        if (onPermissionGranted) onPermissionGranted();
      } else if (!isDismissed) {
        setShowBanner(true);
      }
    }
  };

  useEffect(() => {
    checkPermission();
  }, []);

  const handleEnable = async () => {
    if (Notification.permission === 'denied') {
      // Permission already blocked by browser -> show guide modal
      setShowGuideModal(true);
      return;
    }

    const granted = await requestNotificationPermission();
    if (granted) {
      setPermissionState('granted');
      setShowBanner(false);
      if (onPermissionGranted) onPermissionGranted();
    } else {
      setPermissionState(Notification.permission);
      if (Notification.permission === 'denied') {
        setShowGuideModal(true);
      }
    }
  };

  const handleDismiss = () => {
    sessionStorage.setItem('autopay_dismiss_notif_banner', 'true');
    setShowBanner(false);
  };

  const handleRecheckPermission = () => {
    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        setPermissionState('granted');
        setShowBanner(false);
        setShowGuideModal(false);
        if (onPermissionGranted) onPermissionGranted();
      } else if (Notification.permission === 'denied') {
        alert("Notifications are still blocked in Chrome. Please follow the 3 steps below to allow permissions.");
      } else {
        handleEnable();
      }
    }
  };

  if (!showBanner && !showGuideModal) return null;

  return (
    <>
      {/* Top Notification Permission Banner */}
      {showBanner && (
        <div className={`border-b px-4 py-3 text-sm flex items-center justify-between shadow-lg relative z-40 backdrop-blur-md transition-all ${
          permissionState === 'denied' 
            ? 'bg-gradient-to-r from-red-500/15 via-red-500/25 to-red-500/15 border-red-500/40 text-red-200' 
            : 'bg-gradient-to-r from-amber-500/10 via-amber-500/20 to-amber-500/10 border-amber-500/30 text-amber-200'
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${permissionState === 'denied' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
              {permissionState === 'denied' ? (
                <ShieldAlert className="w-5 h-5 animate-pulse" />
              ) : (
                <Bell className="w-5 h-5 animate-pulse" />
              )}
            </div>
            <div>
              <span className="font-semibold text-white">
                {permissionState === 'denied' ? 'Browser Notifications Blocked:' : 'Enable Payment Reminders:'}
              </span>{' '}
              {permissionState === 'denied'
                ? 'Chrome is currently blocking desktop alerts. Turn on permissions to receive auto-debit reminders.'
                : 'Get automatic desktop alerts when subscriptions or EMIs are due in 7, 3, or 1 day(s).'}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleEnable}
              className={`px-4 py-1.5 font-bold text-xs rounded-lg transition-all shadow-md flex items-center space-x-1.5 ${
                permissionState === 'denied'
                  ? 'bg-red-500 hover:bg-red-400 text-white shadow-red-500/20'
                  : 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
              }`}
            >
              {permissionState === 'denied' ? <Lock className="w-3.5 h-3.5" /> : <Bell className="w-3.5 h-3.5" />}
              <span>{permissionState === 'denied' ? 'How to Unblock' : 'Enable Reminders'}</span>
            </button>
            <button
              onClick={handleDismiss}
              className="p-1.5 hover:bg-white/10 rounded-lg text-amber-400/70 hover:text-amber-200 transition-colors"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Guide Modal: How to Unblock Notifications in Chrome */}
      {showGuideModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-md w-full p-6 shadow-2xl relative text-white space-y-5">
            
            {/* Close Button */}
            <button 
              onClick={() => setShowGuideModal(false)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Icon & Title */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Unblock Chrome Notifications</h3>
                <p className="text-xs text-slate-400">Follow 3 quick steps to enable payment alerts</p>
              </div>
            </div>

            {/* Step-by-Step Instructions */}
            <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs">
              <div className="flex items-start space-x-3">
                <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 font-bold flex items-center justify-center shrink-0">1</span>
                <div>
                  <span className="font-bold text-white">Click the Lock / Tuning icon 🔒</span>
                  <p className="text-slate-400 text-[11px]">Located on the far left side of your browser address bar (next to <code>http://localhost:5173</code>).</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 font-bold flex items-center justify-center shrink-0">2</span>
                <div>
                  <span className="font-bold text-white">Toggle "Notifications" to ALLOW</span>
                  <p className="text-slate-400 text-[11px]">Find the <b>Notifications</b> permission setting and change it from <i>Block</i> to <b>Allow</b>.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 font-bold flex items-center justify-center shrink-0">3</span>
                <div>
                  <span className="font-bold text-white">Click "Check Permission Again" below</span>
                  <p className="text-slate-400 text-[11px]">Or reload the page to activate your desktop payment notifications.</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3 pt-2">
              <button
                onClick={handleRecheckPermission}
                className="flex-1 py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-lg shadow-purple-600/30"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Check Permission Again</span>
              </button>
              
              <button
                onClick={() => setShowGuideModal(false)}
                className="py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}
    </>
  );
};

export default NotificationPermissionBanner;
