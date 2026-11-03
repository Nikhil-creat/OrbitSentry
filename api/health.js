module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ status: 'ok', version: '4.0.0', llm: !!(process.env.GROQ_API_KEY || process.env.GEMINI_API_KEY), backend: !!(process.env.BACKEND_URL && process.env.BACKEND_API_KEY) });
};
