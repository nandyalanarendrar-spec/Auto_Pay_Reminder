import { isSupabaseConfigured, supabase } from '../lib/supabaseClient';
import { API_BASE_URL } from '../config/api';

export const getAuthToken = async () => {
  try {
    if (isSupabaseConfigured && supabase) {
      const { data: { session } } = await supabase.auth.getSession();
      return session?.access_token || null;
    }
  } catch (e) {}
  return null;
};

// fetch() against the backend /api/v1 with the signed-in user's token; throws Error(detail) on failure.
export const apiRequest = async (path, { method = 'GET', body } = {}) => {
  const token = await getAuthToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined
  });

  let data = null;
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${res.status})`);
  }
  return data;
};
