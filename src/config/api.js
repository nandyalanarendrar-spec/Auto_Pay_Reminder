/**
 * Single source of truth for the backend base URL.
 *
 * Web dev: defaults to http://127.0.0.1:8000, which is correct because the
 * browser and the FastAPI server run on the same machine.
 *
 * Native app (Android/iOS): "127.0.0.1" on the PHONE is the phone itself, not
 * your dev machine, so the app can never reach a backend running on your PC
 * at that address. Set VITE_API_BASE_URL in .env to your PC's LAN IP (e.g.
 * http://192.168.0.194:8000) before running `npm run android:build`, and
 * start the backend with `uvicorn backend.main:app --reload --host 0.0.0.0
 * --port 8000` so it accepts connections from other devices on the network.
 */
const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const API_ROOT_URL = BASE;
export const API_BASE_URL = `${BASE}/api/v1`;
