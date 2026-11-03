"""Event-level benchmark: CNN-BiLSTM + dynamic thresholding vs a Z-score baseline.

Usage: python -m src.evaluate --max-chans 20 --epochs 3 [--spacecraft SMAP]
Needs data/train, data/test and data/labeled_anomalies.csv (see scripts/get_nasa_data.sh).
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import yaml

from src.engine.threshold import detect, event_metrics, sequences
from src.model.network import CNNBiLSTM
from src.train import windows

Seq = Tuple[int, int]


def fit_errors(train: np.ndarray, test: np.ndarray, cfg: dict, epochs: int) -> np.ndarray:
    length = int(cfg["window"])
    xtr, ytr = windows(train, length)
    xte, yte = windows(test, length)
    model = CNNBiLSTM(train.shape[1], **cfg["model"])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(len(xtr))
        for i in range(0, len(perm), 64):
            b = perm[i:i + 64]
            opt.zero_grad()
            loss_fn(model(xtr[b]), ytr[b]).backward()
            opt.step()
    model.eval()
    with torch.no_grad():
        pred = torch.cat([model(xte[i:i + 256]) for i in range(0, len(xte), 256)])
    return (pred - yte).abs().squeeze(1).numpy()


def tally(pred: List[Seq], truth: List[Seq], acc: Dict[str, int]) -> None:
    m = event_metrics(pred, truth)
    for k in ("tp", "fp", "fn"):
        acc[k] += m[k]


def summarize(acc: Dict[str, int]) -> Dict[str, float]:
    p = acc["tp"] / (acc["tp"] + acc["fp"]) if acc["tp"] + acc["fp"] else 0.0
    r = acc["tp"] / (acc["tp"] + acc["fn"]) if acc["tp"] + acc["fn"] else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3), **acc}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--labels", default="data/labeled_anomalies.csv")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-chans", type=int, default=10)
    ap.add_argument("--spacecraft", default="")
    a = ap.parse_args()
    cfg = yaml.safe_load(Path(a.config).read_text())
    t = cfg["threshold"]
    length = int(cfg["window"])
    ours = {"tp": 0, "fp": 0, "fn": 0}
    base = {"tp": 0, "fp": 0, "fn": 0}
    done = 0
    with open(a.labels, newline="") as f:
        for row in csv.DictReader(f):
            if a.spacecraft and row["spacecraft"] != a.spacecraft:
                continue
            ctr, cte = Path(f"data/train/{row['chan_id']}.npy"), Path(f"data/test/{row['chan_id']}.npy")
            if not (ctr.exists() and cte.exists()):
                continue
            if done >= a.max_chans:
                break
            train, test = np.load(ctr), np.load(cte)
            truth = [(int(s), int(e)) for s, e in ast.literal_eval(row["anomaly_sequences"])]
            err = fit_errors(train, test, cfg, a.epochs)
            events, _ = detect(err, t["ewma_span"], t["z_min"], t["z_max"], t["prune_p"])
            tally([(s + length, e + length) for s, e in events], truth, ours)
            z = np.abs(test[:, 0] - test[:, 0].mean()) / (test[:, 0].std() or 1.0)
            tally(sequences(z > 3.0), truth, base)
            done += 1
            print(f"{row['chan_id']}: ok ({done}/{a.max_chans})")
    res = {"channels": done, "epochs": a.epochs, "cnn_bilstm": summarize(ours), "zscore": summarize(base)}
    Path("results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print("\n| Method | Precision | Recall | F1 |\n|---|---|---|---|")
    for name, k in (("Z-score baseline", "zscore"), ("CNN-BiLSTM + pruning", "cnn_bilstm")):
        m = res[k]
        print(f"| {name} | {m['precision']} | {m['recall']} | {m['f1']} |")


if __name__ == "__main__":
    main()
