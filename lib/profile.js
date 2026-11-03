(function (root) {
  var R = (typeof require !== 'undefined' && typeof module !== 'undefined') ? require('./rag.js') : root.RAG;
  var KB = [
    { id: 'who', kw: 'education college degree study background about who where studied', text: 'Nikhil Chary Sriramoju is a final-year B.Tech Computer Science and Engineering student at Vaagdevi College of Engineering (2023 to 2027), based in Thorrur, Telangana, India.' },
    { id: 'experience', kw: 'experience internships work jobs', text: 'Machine Learning Engineer Intern at Yuva Intern (NSDC), Aug to Sep 2026, and Data Analytics Intern at Thiranex, Jul to Aug 2026.' },
    { id: 'certifications', kw: 'certifications certificates courses', text: 'NASSCOM / Skill India Digital Hub (AI-Data Engineering and Cloud Infrastructure Analyst), IBM SkillsBuild (AI Fundamentals), Reliance Foundation (AI/ML Engineer Foundation).' },
    { id: 'projects', kw: 'projects built portfolio repositories work', text: 'OrbitSentry (spacecraft telemetry anomaly detection), AssignmentWriter (exam answer generator using Groq), Voyagr (AI trip planner PWA), KV Freight (scroll-hero site with AI copilot), Resume Reviewer Pro, Voice Assistant and Semanticache.' },
    { id: 'orbitsentry', kw: 'orbitsentry orbit project telemetry', text: 'OrbitSentry detects anomalies in NASA SMAP and MSL style telemetry with a CNN-BiLSTM, explains them with Integrated Gradients, recalls similar incidents with RAG, and runs a LangGraph triage loop where risky actions need human approval. Stack: PyTorch, FastAPI, Qdrant, Docker, Vercel.' },
    { id: 'skills', kw: 'skills technologies stack tools know', text: 'Python, PyTorch, LangGraph, RAG with Qdrant, FastAPI, Docker, JavaScript, Node, Vercel serverless, data analytics and machine learning.' },
    { id: 'contact', kw: 'contact hire reach email linkedin github', text: 'Email: sriramojunikhil66@gmail.com. GitHub: github.com/Nikhil-creat. LinkedIn: in.linkedin.com/in/nikhil-chary-sriramoju-95041b38a. Open to machine learning, data and AI engineering roles and internships.' }
  ];
  var api = { KB: KB, retrieve: function (q, k) { return R.search(KB, q, k || 2); } };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PROFILE = api;
})(this);
