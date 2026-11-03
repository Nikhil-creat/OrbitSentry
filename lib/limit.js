const hits = new Map();
module.exports = function allow(key, max, windowMs) {
  const now = Date.now(), w = windowMs || 60000;
  const h = (hits.get(key) || []).filter((t) => now - t < w);
  if (h.length >= max) { hits.set(key, h); return false; }
  h.push(now); hits.set(key, h);
  if (hits.size > 5000) hits.delete(hits.keys().next().value);
  return true;
};
module.exports.ip = (req) => String((req.headers && req.headers['x-forwarded-for']) || 'anon').split(',')[0].trim();
