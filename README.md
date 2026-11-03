# OrbitSentry
Spacecraft telemetry anomaly detection (NASA SMAP + MSL), explainable attribution, RAG incident recall and an agentic triage loop with human-in-the-loop approval.

```
telemetry -> CNN(3/5/7)+BiLSTM(2x80) -> error -> EWMA(30) -> dynamic threshold -> pruning
                                   \-> Integrated Gradients -> LangGraph: ingest -> RAG(Qdrant) -> hypothesis -> router
```

## Run the site
Open `index.html` / `workspace.html`, or `python -m http.server 8080`.

## Run the backend
```
cp .env.example .env   # set API_KEYS
docker compose up --build
pytest -q
curl -H "x-api-key: change-me-1" -H "content-type: application/json" -d '{"channel":"SMAP-P1","window":[[0.1,0],[0.2,0]],"observed":0.9}' localhost:8000/api/v1/detect
```
Endpoints: `GET /healthz`, `POST /api/v1/detect`, `WS /ws/telemetry?api_key=...`.

## Security
API-key auth, token-bucket rate limit (per IP, in-memory), CORS allow-list, pydantic validation, payload dedupe, env-based secrets, non-root container. Risky actions (throttle, isolation) require human approval.

## Limitations
- Model ships untrained: download SMAP/MSL data into `data/` and train before trusting scores.
- Web demo is a JavaScript simulation. LLM hypotheses are hints, not verdicts.
- Rate limiter and dedupe cache are single-instance. Not flight-qualified.
- Do not publish benchmark numbers until you have measured them on your own runs.

## Author
Nikhil Chary Sriramoju - https://github.com/Nikhil-creat

## Deploy free on Vercel
Push to GitHub, import the repo at vercel.com (Framework: Other, no build command). Add env vars `GROQ_API_KEY` and/or `GEMINI_API_KEY` in Project Settings. Serverless routes: `/api/chat` (Groq→Gemini failover), `/api/detect` (EWMA baseline), `/api/health`. Security headers + CSP are in `vercel.json`.

## Train on real data
Place Telemanom-layout arrays in `data/train/<CHAN>.npy` and `data/test/<CHAN>.npy`, then `python -m src.train --chan P-1 --epochs 5`. Set `WEIGHTS_PATH=weights/P-1.pt` in `.env`. Note: the API builds the model by input width, so use weights trained with the same channel count.

## Benchmarks (fill in after you measure)
| Method | Event precision | Event recall | F1 |
|---|---|---|---|
| Z-score baseline | TBD | TBD | TBD |
| LSTM + dynamic threshold (Telemanom-style) | TBD | TBD | TBD |
| CNN-BiLSTM + pruning (this repo) | TBD | TBD | TBD |

## Resume bullets (replace brackets with your measured results)
- Built a CNN-BiLSTM telemetry anomaly detector with label-free EWMA dynamic thresholding; reached [F1] on [channels] of NASA SMAP/MSL.
- Added Integrated Gradients attribution and a LangGraph triage agent with Qdrant RAG and human-approval gating for risky actions.
- Shipped FastAPI + Docker (multi-stage, compose) and a Vercel serverless demo with rate limiting, CSP and Groq/Gemini failover.

## One-command Termux push
`bash scripts/termux_push.sh orbitsentry`

**Live demo:** https://YOUR-DOMAIN.vercel.app/workspace
