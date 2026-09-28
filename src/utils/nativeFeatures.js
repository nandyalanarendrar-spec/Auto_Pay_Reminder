/**
 * Native feature bridge for the Capacitor-wrapped mobile app.
 * Every export is safe to call from web builds too — it checks
 * Capacitor.isNativePlatform() and falls back to existing web behavior,
 * so the same React code path works in the browser and inside the app.
 */
import { Capacitor } from '@capacitor/core';
import { API_BASE_URL } from '../config/api';

// PushNotifications.register() calls into Firebase Messaging natively, which throws
// an uncaught exception (crashing the whole app, not just rejecting a JS promise) if
// google-services.json hasn't been added to the Android project yet. Flip this to
// true only after that file is in place and the app has been rebuilt with it —
// otherwise every native app install will crash on login.
const FIREBASE_CONFIGURED = false;

export const isNativeApp = () => Capacitor.isNativePlatform();
export const nativePlatform = () => Capacitor.getPlatform(); // 'android' | 'ios' | 'web'

/**
 * Opens the native camera (or falls back to the browser's file input with
 * capture="environment" on web) and returns a File-like object the rest of
 * the app can upload exactly like a normal <input type="file"> selection.
 */
export const takePhoto = async () => {
  if (isNativeApp()) {
    const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera');
    const photo = await Camera.getPhoto({
      quality: 85,
      resultType: CameraResultType.Uri,
      source: CameraSource.Prompt, // lets the user pick Camera or Photo Library
    });
    const response = await fetch(photo.webPath);
    const blob = await response.blob();
    const ext = (photo.format || 'jpeg').replace('jpg', 'jpeg');
    return new File([blob], `receipt-${Date.now()}.${ext}`, { type: `image/${ext}` });
  }
  // Web fallback: caller should render a normal <input type="file" accept="image/*" capture="environment" />
  return null;
};

/**
 * Saves a Blob to the device's Downloads-equivalent directory on native,
 * or triggers a normal browser download on web. Used by report export /
 * receipt saving.
 */
export const saveFileToDevice = async (blob, filename) => {
  if (isNativeApp()) {
    const { Filesystem, Directory } = await import('@capacitor/filesystem');
    const base64Data = await blobToBase64(blob);
    await Filesystem.writeFile({
      path: filename,
      data: base64Data,
      directory: Directory.Documents,
      recursive: true,
    });
    return { savedNative: true, path: filename };
  }
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
  return { savedNative: false };
};

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Registers this device for push notifications. On native it wires up the
 * Capacitor PushNotifications plugin (FCM under the hood) and forwards the
 * token to the existing /notifications/register-device endpoint. On web it
 * defers to the existing browser Notification permission flow.
 */
export const initNativePushNotifications = async (getAuthToken) => {
  if (!isNativeApp() || !FIREBASE_CONFIGURED) return false;

  const { PushNotifications } = await import('@capacitor/push-notifications');

  let permStatus = await PushNotifications.checkPermissions();
  if (permStatus.receive !== 'granted') {
    permStatus = await PushNotifications.requestPermissions();
  }
  if (permStatus.receive !== 'granted') return false;

  await PushNotifications.register();

  PushNotifications.addListener('registration', async (token) => {
    try {
      const authToken = getAuthToken ? await getAuthToken() : null;
      const headers = { 'Content-Type': 'application/json' };
      if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
      await fetch(`${API_BASE_URL}/notifications/register-device`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ device_token: token.value, platform: nativePlatform() }),
      });
    } catch (err) {
      console.warn('Native push token registration failed:', err);
    }
  });

  PushNotifications.addListener('registrationError', (err) => {
    console.warn('Native push registration error:', err);
  });

  return true;
};
