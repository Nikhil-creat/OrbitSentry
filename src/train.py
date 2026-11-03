"""Train CNN-BiLSTM on one Telemanom-layout channel and run dynamic thresholding.

Expects data/train/<CHAN>.npy and data/test/<CHAN>.npy, shape (T, C): col 0 = telemetry, cols 1+ = commands.
Usage: python -m src.train --chan P-1 --epochs 5
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import yaml

from src.engine.threshold import detect
from src.model.network import CNNBiLSTM


def windows(arr: np.ndarray, length: int) -> tuple[torch.Tensor, torch.Tensor]:
    if arr.shape[0] <= length:
        raise ValueError(f"series shorter than window ({arr.shape[0]} <= {length})")
    idx = np.arange(arr.shape[0] - length)
    x = np.stack([arr[i:i + length] for i in idx])
    y = arr[length:, 0:1]
    return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chan", required=True)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--config", default="config/default.yaml")
    a = ap.parse_args()
    cfg = yaml.safe_load(Path(a.config).read_text())
    train = np.load(f"data/train/{a.chan}.npy")
    test = np.load(f"data/test/{a.chan}.npy")
    length = int(cfg["window"])
    xtr, ytr = windows(train, length)
    xte, yte = windows(test, length)
    model = CNNBiLSTM(train.shape[1], **cfg["model"])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    for ep in range(a.epochs):
        model.train()
        perm = torch.randperm(len(xtr))
        total = 0.0
        for i in range(0, len(perm), 64):
            b = perm[i:i + 64]
            opt.zero_grad()
            loss = loss_fn(model(xtr[b]), ytr[b])
            loss.backward()
            opt.step()
            total += float(loss) * len(b)
        print(f"epoch {ep + 1}/{a.epochs} loss {total / len(xtr):.5f}")
    model.eval()
    with torch.no_grad():
        pred = torch.cat([model(xte[i:i + 256]) for i in range(0, len(xte), 256)])
    err = (pred - yte).abs().squeeze(1).numpy()
    t = cfg["threshold"]
    events, thr = detect(err, t["ewma_span"], t["z_min"], t["z_max"], t["prune_p"])
    Path("weights").mkdir(exist_ok=True)
    torch.save(model.state_dict(), f"weights/{a.chan}.pt")
    print(f"threshold {thr:.5f}; events (window-offset indices): {events}")
    print(f"weights saved: weights/{a.chan}.pt  (set WEIGHTS_PATH to use in the API)")


if __name__ == "__main__":
    main()
