/**
 * Single source of truth for the backend base URL.
 *
 * Defaults to http://127.0.0.1:8000 for local dev (browser and FastAPI server
 * on the same machine). Set VITE_API_BASE_URL in the environment to point at
 * a deployed backend instead — e.g. the Render URL — for a production build.
 */
const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const API_ROOT_URL = BASE;
export const API_BASE_URL = `${BASE}/api/v1`;
