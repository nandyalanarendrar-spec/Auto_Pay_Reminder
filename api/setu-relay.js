// Forwards the backend's Setu calls from a Mumbai (bom1) function.
// Setu's login endpoint rejects the backend host's (Render) addresses with an AWS load balancer 403,
// but accepts Indian addresses, so the backend sends its Setu requests through this function.
//
// Locked down on purpose: it needs the shared key, only talks to Setu hosts, and passes only a few headers.
import { timingSafeEqual } from 'node:crypto';

const ALLOWED_HOSTS = new Set(['orgservice-prod.setu.co', 'fiu-sandbox.setu.co']);
const FORWARDED_HEADERS = ['authorization', 'x-product-instance-id', 'content-type', 'accept', 'user-agent'];
const ALLOWED_METHODS = new Set(['GET', 'POST']);

const safeEqual = (a, b) => {
  const left = Buffer.from(String(a || ''));
  const right = Buffer.from(String(b || ''));
  return left.length === right.length && left.length > 0 && timingSafeEqual(left, right);
};

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const expectedKey = process.env.SETU_RELAY_KEY;
  if (!expectedKey) return res.status(503).json({ error: 'Relay is not configured' });
  if (!safeEqual(req.headers['x-relay-key'], expectedKey)) return res.status(401).json({ error: 'Unauthorized' });

  const { method = 'GET', url, headers = {}, body } = req.body || {};
  let target;
  try {
    target = new URL(url);
  } catch {
    return res.status(400).json({ error: 'Invalid url' });
  }
  if (target.protocol !== 'https:' || !ALLOWED_HOSTS.has(target.hostname)) {
    return res.status(403).json({ error: 'Host not allowed' });
  }
  const upperMethod = String(method).toUpperCase();
  if (!ALLOWED_METHODS.has(upperMethod)) return res.status(400).json({ error: 'Method not allowed' });

  const outgoing = {};
  for (const [name, value] of Object.entries(headers)) {
    if (FORWARDED_HEADERS.includes(name.toLowerCase())) outgoing[name] = String(value);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 25000);
  try {
    const upstream = await fetch(target.toString(), {
      method: upperMethod,
      headers: outgoing,
      body: upperMethod === 'GET' || body === undefined || body === null ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await upstream.text();
    return res.status(200).json({
      status: upstream.status,
      content_type: upstream.headers.get('content-type'),
      server: upstream.headers.get('server'),
      body: text,
    });
  } catch (err) {
    return res.status(502).json({ error: `Could not reach Setu (${err.name})` });
  } finally {
    clearTimeout(timer);
  }
}
