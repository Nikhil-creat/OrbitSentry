const SYS = {
  triage: 'You are a spacecraft telemetry triage agent. Classify each action AUTONOMOUS_READ or HUMAN_APPROVAL_REQUIRED. Be concise.',
  rag: 'Answer using only the supplied historical incidents. Cite incident IDs. Be concise.',
  sec: 'You are a security reviewer for an API gateway: auth, rate limits, secrets, CORS, human approval gating. Be concise.'
};
const hits = new Map();
async function groq(sys, msg) {
  const r = await fetch('https://api.groq.com/openai/v1/chat/completions', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + process.env.GROQ_API_KEY }, body: JSON.stringify({ model: 'llama-3.3-70b-versatile', messages: [{ role: 'system', content: sys }, { role: 'user', content: msg }] }) });
  if (!r.ok) throw new Error('groq ' + r.status); return (await r.json()).choices[0].message.content;
}
async function gemini(sys, msg) {
  const r = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent', { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': process.env.GEMINI_API_KEY }, body: JSON.stringify({ contents: [{ parts: [{ text: sys + '\n\n' + msg }] }] }) });
  if (!r.ok) throw new Error('gemini ' + r.status); return (await r.json()).candidates[0].content.parts[0].text;
}
module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  const ip = String(req.headers['x-forwarded-for'] || 'anon').split(',')[0], now = Date.now();
  const h = (hits.get(ip) || []).filter((t) => now - t < 60000);
  if (h.length >= 20) return res.status(429).json({ error: 'rate limit' });
  h.push(now); hits.set(ip, h);
  const b = req.body || {};
  if (!SYS[b.assistant] || typeof b.message !== 'string' || !b.message.trim() || b.message.length > 1500)
    return res.status(400).json({ error: 'bad request' });
  const msg = (typeof b.context === 'string' ? 'Context:\n' + b.context.slice(0, 1500) + '\n\n' : '') + 'Question: ' + b.message;
  const order = [];
  if (process.env.GROQ_API_KEY) order.push(groq);
  if (process.env.GEMINI_API_KEY) order.push(gemini);
  if (!order.length) return res.status(503).json({ error: 'no_key' });
  for (const fn of order) { try { return res.status(200).json({ reply: await fn(SYS[b.assistant], msg), provider: fn.name }); } catch (e) { /* failover */ } }
  res.status(502).json({ error: 'providers_failed' });
};
