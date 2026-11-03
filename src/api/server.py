"""FastAPI gateway: API-key auth, token-bucket rate limit, CORS, idempotency, 200ms fallback."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Deque, Dict, List, Optional, Tuple

import numpy as np
import torch
from fastapi import Depends, FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.agent.triage_graph import run_triage
from src.engine.threshold import detect
from src.model.network import CNNBiLSTM, integrated_gradients


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    api_keys: str = "dev-key"
    cors_origins: str = "http://localhost:8080"
    rate_capacity: int = 20
    rate_refill_per_sec: float = 5.0
    latency_budget_ms: int = 200
    weights_path: str = ""


cfg = Settings()
KEYS = {k.strip() for k in cfg.api_keys.split(",") if k.strip()}
app = FastAPI(title="OrbitSentry", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=cfg.cors_origins.split(","),
                   allow_methods=["GET", "POST"], allow_headers=["x-api-key", "content-type"])
POOL = ThreadPoolExecutor(max_workers=2)
MODELS: Dict[int, CNNBiLSTM] = {}
HIST: Dict[str, Deque[float]] = {}
SEEN: Dict[str, dict] = {}
BUCKETS: Dict[str, List[float]] = {}


@app.middleware("http")
async def token_bucket(request: Request, call_next):
    who = request.client.host if request.client else "anon"
    now = time.monotonic()
    tokens, last = BUCKETS.get(who, [float(cfg.rate_capacity), now])
    tokens = min(cfg.rate_capacity, tokens + (now - last) * cfg.rate_refill_per_sec)
    if tokens < 1:
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429, headers={"Retry-After": "1"})
    BUCKETS[who] = [tokens - 1, now]
    return await call_next(request)


def require_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    if not x_api_key or x_api_key not in KEYS:
        raise HTTPException(status_code=401, detail="invalid API key")
    return x_api_key


class DetectRequest(BaseModel):
    channel: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    window: List[List[float]] = Field(min_length=2, max_length=250)
    observed: float

    @field_validator("window")
    @classmethod
    def rectangular(cls, w: List[List[float]]) -> List[List[float]]:
        if len({len(r) for r in w}) != 1 or not w[0]:
            raise ValueError("window must be rectangular (L x C)")
        return w


def _model(c: int) -> CNNBiLSTM:
    if c not in MODELS:
        m = CNNBiLSTM(c)
        if cfg.weights_path:
            m.load_state_dict(torch.load(cfg.weights_path, map_location="cpu"))
        MODELS[c] = m.eval()
    return MODELS[c]


def _infer(x: np.ndarray, observed: float) -> Tuple[float, dict]:
    t = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
    m = _model(t.shape[2])
    with torch.no_grad():
        pred = float(m(t)[0, 0])
    attr = integrated_gradients(m, t, steps=8)[0].tolist()
    return abs(observed - pred), {("telemetry" if i == 0 else f"cmd_{i}"): round(a, 4) for i, a in enumerate(attr)}


def _zscore(x: np.ndarray, observed: float) -> Tuple[float, dict]:
    col = x[:, 0]
    return abs(observed - float(col.mean())) / (float(col.std()) or 1.0), {"telemetry": 1.0}


@app.get("/healthz")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/detect")
async def detect_endpoint(req: DetectRequest, _: str = Depends(require_key)) -> dict:
    fp = hashlib.sha256(json.dumps(req.model_dump(), sort_keys=True).encode()).hexdigest()
    if fp in SEEN:
        return {**SEEN[fp], "deduplicated": True}
    x = np.asarray(req.window, dtype=float)
    detector = "cnn-bilstm"
    fut = asyncio.wrap_future(POOL.submit(_infer, x, req.observed))
    try:
        err, attr = await asyncio.wait_for(fut, cfg.latency_budget_ms / 1000)
    except asyncio.TimeoutError:
        err, attr = _zscore(x, req.observed)
        detector = "zscore-fallback"
    h = HIST.setdefault(req.channel, deque(maxlen=2000))
    h.append(err)
    anomalous = False
    if len(h) >= 60:
        seqs, _t = detect(np.array(h))
        anomalous = bool(seqs) and seqs[-1][1] >= len(h) - 2
    elif detector == "zscore-fallback" and err > 3.0:
        anomalous = True
    out: dict = {"channel": req.channel, "error": round(err, 5), "anomaly": anomalous,
                 "detector": detector, "attribution": attr, "deduplicated": False}
    if anomalous:
        t = run_triage(req.channel, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), err, attr)
        out["triage"] = {"hypothesis": t["hypothesis"], "actions": t["actions"], "matches": t["matches"]}
    SEEN[fp] = out
    if len(SEEN) > 5000:
        SEEN.pop(next(iter(SEEN)))
    return out


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket) -> None:
    if ws.query_params.get("api_key", "") not in KEYS:
        await ws.close(code=4401)
        return
    await ws.accept()
    try:
        while True:
            try:
                req = DetectRequest(**json.loads(await ws.receive_text()))
                err, attr = _zscore(np.asarray(req.window, dtype=float), req.observed)
                await ws.send_json({"channel": req.channel, "error": round(err, 5), "attribution": attr})
            except (ValueError, TypeError) as exc:
                await ws.send_json({"error": f"bad payload: {exc}"})
    except WebSocketDisconnect:
        return
