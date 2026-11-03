const TH = require('../lib/threshold.js');
const hits = new Map();
module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  const ip = String(req.headers['x-forwarded-for'] || 'anon').split(',')[0];
  const now = Date.now(), h = (hits.get(ip) || []).filter((t) => now - t < 60000);
  if (h.length >= 30) return res.status(429).json({ error: 'rate limit' });
  h.push(now); hits.set(ip, h);
  const v = req.body && req.body.values;
  if (!Array.isArray(v) || v.length < 60 || v.length > 20000 || !v.every((x) => typeof x === 'number' && isFinite(x)))
    return res.status(400).json({ error: 'values must be 60-20000 finite numbers' });
  const d = TH.detect(v);
  res.status(200).json({ threshold: d.threshold, events: d.events, points: v.length, detector: 'ewma-baseline' });
};
