"""Create a tiny Telemanom-layout dataset so the train/evaluate pipeline can be smoke-tested offline."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


def series(n: int, seed: int, anomaly: tuple[int, int] | None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    x = np.sin(t / 25.0) + 0.05 * rng.standard_normal(n)
    if anomaly:
        x[anomaly[0]:anomaly[1]] += 2.0
    cmd = (rng.random((n, 2)) > 0.97).astype(float)
    return np.column_stack([x, cmd])


def main() -> None:
    for d in ("data/train", "data/test"):
        Path(d).mkdir(parents=True, exist_ok=True)
    np.save("data/train/S-1.npy", series(2500, 1, None))
    np.save("data/test/S-1.npy", series(1500, 2, (900, 960)))
    with open("data/labeled_anomalies.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chan_id", "spacecraft", "anomaly_sequences", "class", "num_values"])
        w.writerow(["S-1", "SMAP", "[[900, 960]]", "[point]", 1500])
    print("synthetic channel S-1 written to data/")


if __name__ == "__main__":
    main()
