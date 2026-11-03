const RAG = require('../lib/rag.js');
const allow = require('../lib/limit.js');
const SYS = {
  triage: 'You are a spacecraft telemetry triage agent. Classify each action AUTONOMOUS_READ or HUMAN_APPROVAL_REQUIRED. Be concise.',
  rag: 'Answer using only the supplied illustrative incident notes. Cite incident IDs. Be concise.',
  sec: 'You are a security reviewer for an API gateway: auth, rate limits, secrets, CORS, human approval gating. Be concise.'
};
async function post(url, headers, body, pick) {
  const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 9000);
  try {
    const r = await fetch(url, { method: 'POST', headers: Object.assign({ 'Content-Type': 'application/json' }, headers), body: JSON.stringify(body), signal: ctl.signal });
    if (!r.ok) throw new Error('upstream ' + r.status);
    return pick(await r.json());
  } finally { clearTimeout(t); }
}
const groq = (sys, msg) => post('https://api.groq.com/openai/v1/chat/completions', { Authorization: 'Bearer ' + process.env.GROQ_API_KEY },
  { model: 'llama-3.3-70b-versatile', messages: [{ role: 'system', content: sys }, { role: 'user', content: msg }] }, (j) => j.choices[0].message.content);
const gemini = (sys, msg) => post('https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent', { 'x-goog-api-key': process.env.GEMINI_API_KEY },
  { contents: [{ parts: [{ text: sys + '\n\n' + msg }] }] }, (j) => j.candidates[0].content.parts[0].text);
module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  if (!allow('chat:' + allow.ip(req), 20)) return res.status(429).json({ error: 'rate limit' });
  const b = req.body || {};
  if (!SYS[b.assistant] || typeof b.message !== 'string' || !b.message.trim() || b.message.length > 1500)
    return res.status(400).json({ error: 'bad request' });
  const ctx = RAG.retrieve(b.message, 3).map((d) => d.id + ': ' + d.text).join('\n');
  const msg = 'Incident notes:\n' + ctx + '\n\nQuestion: ' + b.message;
  const order = [];
  if (process.env.GROQ_API_KEY) order.push(['groq', groq]);
  if (process.env.GEMINI_API_KEY) order.push(['gemini', gemini]);
  if (!order.length) return res.status(503).json({ error: 'no_key' });
  for (const [name, fn] of order) {
    try { return res.status(200).json({ reply: await fn(SYS[b.assistant], msg), provider: name }); } catch (e) { /* failover */ }
  }
  res.status(502).json({ error: 'providers_failed' });
};
