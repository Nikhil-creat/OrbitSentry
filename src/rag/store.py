"""Incident vector store: Qdrant (cosine) with in-memory fallback. Zero-cost hashed embeddings."""
from __future__ import annotations

import hashlib
import math
import re
from typing import Dict, List

DIM = 256
SEED: List[Dict[str, str]] = [
    {"id": "SMAP-P1", "text": "Gradual thermal sensor drift: slow monotonic offset, no command correlation. Recalibrate, cross-check redundant sensor."},
    {"id": "MSL-M6", "text": "Power rail transient: abrupt voltage dip on bus after payload command. Isolate load, check battery state of charge."},
    {"id": "SMAP-A4", "text": "Gyro noise burst: high variance spikes, attitude jitter. Reaction wheel desaturation and filter reset."},
    {"id": "MSL-T2", "text": "Radio link dropout: telemetry gaps and stale values. Switch antenna, retry downlink window."},
]


def embed(text: str) -> List[float]:
    v = [0.0] * DIM
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class IncidentStore:
    def __init__(self, url: str = "") -> None:
        self.client = None
        self.docs = list(SEED)
        if url:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, PointStruct, VectorParams
                c = QdrantClient(url=url, timeout=3)
                c.recreate_collection("incidents", vectors_config=VectorParams(size=DIM, distance=Distance.COSINE))
                c.upsert("incidents", [PointStruct(id=i, vector=embed(d["text"]), payload=d)
                                       for i, d in enumerate(self.docs)])
                self.client = c
            except Exception:  # noqa: BLE001 - fall back to memory if Qdrant is down
                self.client = None

    def search(self, query: str, k: int = 2) -> List[Dict[str, object]]:
        q = embed(query)
        if self.client is not None:
            hits = self.client.search("incidents", query_vector=q, limit=k)
            return [{**h.payload, "score": float(h.score)} for h in hits]
        scored = [{**d, "score": sum(a * b for a, b in zip(q, embed(d["text"])))} for d in self.docs]
        return sorted(scored, key=lambda d: d["score"], reverse=True)[:k]
