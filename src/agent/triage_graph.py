"""LangGraph triage: ingest -> retrieve -> hypothesis -> action router."""
from __future__ import annotations

import os
from typing import Dict, List, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from src.rag.store import IncidentStore

AUTONOMOUS_READ = "AUTONOMOUS_READ"
HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
RISKY = ("throttle", "isolat", "shutdown", "safe mode")


class TriageState(TypedDict, total=False):
    channel: str
    timestamp: str
    error: float
    attribution: Dict[str, float]
    query: str
    matches: List[dict]
    hypothesis: str
    actions: List[dict]


STORE = IncidentStore(os.getenv("QDRANT_URL", ""))


def ingest(s: TriageState) -> TriageState:
    top = sorted(s.get("attribution", {}).items(), key=lambda kv: kv[1], reverse=True)
    names = " ".join(k for k, _ in top[:3])
    return {"query": f"{s['channel']} anomaly error {s['error']:.3f} drivers {names}"}


def retrieve(s: TriageState) -> TriageState:
    return {"matches": STORE.search(s["query"], k=2)}


def _llm(prompt: str) -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return ""
    try:
        r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                       headers={"Authorization": f"Bearer {key}"}, timeout=8,
                       json={"model": "llama-3.3-70b-versatile",
                             "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError):
        return ""


def hypothesise(s: TriageState) -> TriageState:
    top = s["matches"][0] if s.get("matches") else {"id": "none", "text": "no precedent"}
    text = _llm(f"Telemetry anomaly: {s['query']}. Similar incident: {top['text']}. Give a one-line root-cause hypothesis.")
    return {"hypothesis": text or f"Likely similar to {top['id']}: {top['text']}"}


def route(s: TriageState) -> TriageState:
    steps = [a.strip() for a in s["hypothesis"].replace(";", ".").split(".") if a.strip()]
    acts = [{"action": a, "class": HUMAN_APPROVAL_REQUIRED if any(r in a.lower() for r in RISKY)
             else AUTONOMOUS_READ} for a in steps[1:] or ["log and alert operator"]]
    acts.append({"action": "log, alert, reroute metrics", "class": AUTONOMOUS_READ})
    return {"actions": acts}


def build():
    g = StateGraph(TriageState)
    for n, f in (("ingest", ingest), ("retrieve", retrieve), ("hypothesis", hypothesise), ("router", route)):
        g.add_node(n, f)
    g.set_entry_point("ingest")
    g.add_edge("ingest", "retrieve")
    g.add_edge("retrieve", "hypothesis")
    g.add_edge("hypothesis", "router")
    g.add_edge("router", END)
    return g.compile()


GRAPH = build()


def run_triage(channel: str, timestamp: str, error: float, attribution: Dict[str, float]) -> TriageState:
    return GRAPH.invoke({"channel": channel, "timestamp": timestamp, "error": error, "attribution": attribution})
