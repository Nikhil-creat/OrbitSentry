const TH = require('../lib/threshold.js');
const allow = require('../lib/limit.js');
module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  if (!allow('detect:' + allow.ip(req), 30)) return res.status(429).json({ error: 'rate limit' });
  const v = req.body && req.body.values;
  if (!Array.isArray(v) || v.length < 60 || v.length > 20000 || !v.every((x) => typeof x === 'number' && isFinite(x)))
    return res.status(400).json({ error: 'values must be 60-20000 finite numbers' });
  const d = TH.detect(v);
  res.status(200).json({ threshold: d.threshold, events: d.events, points: v.length, detector: 'ewma-baseline' });
};
