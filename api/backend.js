const allow = require('../lib/limit.js');
module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  if (!allow('be:' + allow.ip(req), 20)) return res.status(429).json({ error: 'rate limit' });
  const base = process.env.BACKEND_URL, key = process.env.BACKEND_API_KEY;
  if (!base || !key) return res.status(503).json({ error: 'backend_not_configured' });
  const b = req.body || {}, w = b.window;
  const num = (x) => typeof x === 'number' && isFinite(x);
  if (typeof b.channel !== 'string' || !/^[A-Za-z0-9_-]{1,32}$/.test(b.channel) || !Array.isArray(w) || w.length < 2 || w.length > 250 || !num(b.observed) ||
    !w.every((r) => Array.isArray(r) && r.length >= 1 && r.length <= 64 && r.every(num))) return res.status(400).json({ error: 'bad request' });
  let u;
  try { u = new URL('/api/v1/detect', base); } catch (e) { return res.status(500).json({ error: 'bad BACKEND_URL' }); }
  if (u.protocol !== 'https:') return res.status(500).json({ error: 'BACKEND_URL must be https' });
  const c = new AbortController(), t = setTimeout(() => c.abort(), 9000);
  try {
    const r = await fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-api-key': key }, body: JSON.stringify({ channel: b.channel, window: w, observed: b.observed }), signal: c.signal });
    const j = await r.json().catch(() => null);
    if (!r.ok || !j) return res.status(502).json({ error: 'upstream ' + r.status });
    return res.status(200).json(j);
  } catch (e) { return res.status(502).json({ error: 'backend_unreachable' }); } finally { clearTimeout(t); }
};
