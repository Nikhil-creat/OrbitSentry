module.exports = (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ status: 'ok', version: '3.0.0', llm: !!(process.env.GROQ_API_KEY || process.env.GEMINI_API_KEY) });
};
