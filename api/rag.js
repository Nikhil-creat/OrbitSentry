const RAG = require('../lib/rag.js');
const allow = require('../lib/limit.js');
module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'GET') return res.status(405).json({ error: 'GET only' });
  if (!allow('rag:' + allow.ip(req), 60)) return res.status(429).json({ error: 'rate limit' });
  const q = String((req.query && req.query.q) || '').slice(0, 200);
  if (!q.trim()) return res.status(400).json({ error: 'q required' });
  res.status(200).json({ matches: RAG.retrieve(q, 3) });
};
