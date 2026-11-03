module.exports = (req, res) => res.status(200).json({ status: 'ok', llm: !!(process.env.GROQ_API_KEY || process.env.GEMINI_API_KEY) });
