"""Nonparametric dynamic thresholding, EWMA smoothing, pruning, event metrics."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

Seq = Tuple[int, int]


def ewma(err: np.ndarray, span: int = 30) -> np.ndarray:
    if err.size == 0:
        raise ValueError("empty error array")
    alpha = 2.0 / (span + 1)
    out = np.empty(err.shape, dtype=float)
    out[0] = err[0]
    for i in range(1, err.size):
        out[i] = alpha * err[i] + (1 - alpha) * out[i - 1]
    return out


def sequences(mask: np.ndarray) -> List[Seq]:
    seqs: List[Seq] = []
    start = None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            seqs.append((start, i - 1))
            start = None
    if start is not None:
        seqs.append((start, len(mask) - 1))
    return seqs


def select_threshold(es: np.ndarray, z_min: float = 2.5, z_max: float = 10.0) -> float:
    """Label-free search maximising relative mean/std drop per flagged point."""
    mu, sd = float(es.mean()), float(es.std())
    best_t, best = mu + z_min * sd, -np.inf
    if sd == 0 or mu == 0:
        return best_t
    for z in np.arange(z_min, z_max + 1e-9, 0.5):
        t = mu + z * sd
        below, above = es[es <= t], es > t
        if below.size < 2 or not above.any():
            continue
        score = ((mu - below.mean()) / mu + (sd - below.std()) / sd) / (
            above.sum() + len(sequences(above)) ** 2)
        if score > best:
            best, best_t = score, t
    return float(best_t)


def prune(es: np.ndarray, seqs: List[Seq], p: float = 0.13) -> List[Seq]:
    """Drop candidate sequences whose peak drop-off to the next is below p."""
    if not seqs:
        return []
    mask = np.ones(es.size, dtype=bool)
    for s, e in seqs:
        mask[s:e + 1] = False
    floor = float(es[mask].max()) if mask.any() else 0.0
    ranked = sorted(((float(es[s:e + 1].max()), (s, e)) for s, e in seqs), reverse=True)
    vals = [v for v, _ in ranked] + [floor]
    cut = -1
    for i in range(len(vals) - 1):
        if vals[i] > 0 and (vals[i] - vals[i + 1]) / vals[i] >= p:
            cut = i
    return sorted(s for _, s in ranked[:cut + 1])


def detect(err: np.ndarray, span: int = 30, z_min: float = 2.5,
           z_max: float = 10.0, p: float = 0.13) -> Tuple[List[Seq], float]:
    es = ewma(np.asarray(err, dtype=float), span)
    t = select_threshold(es, z_min, z_max)
    return prune(es, sequences(es > t), p), t


def event_metrics(pred: List[Seq], truth: List[Seq]) -> dict:
    def hit(a: Seq, b: Seq) -> bool:
        return a[0] <= b[1] and b[0] <= a[1]
    tp = sum(any(hit(t, p_) for p_ in pred) for t in truth)
    fp = sum(not any(hit(p_, t) for t in truth) for p_ in pred)
    fn = len(truth) - tp
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1}
