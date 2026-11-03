"""Hybrid multi-scale 1D-CNN + Bi-LSTM forecaster with Integrated Gradients."""
from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn


class CNNBiLSTM(nn.Module):
    """Input (B, L, C) -> next-step prediction (B, horizon)."""

    def __init__(self, in_channels: int, filters: int = 32, hidden: int = 80,
                 layers: int = 2, dropout: float = 0.3, horizon: int = 1) -> None:
        super().__init__()
        self.branches = nn.ModuleList(
            nn.Sequential(nn.Conv1d(in_channels, filters, k, padding=k // 2), nn.ReLU())
            for k in (3, 5, 7)
        )
        self.lstm = nn.LSTM(filters * 3, hidden, layers, batch_first=True,
                            bidirectional=True, dropout=dropout)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden * 2, horizon))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3:
            raise ValueError(f"expected (B, L, C), got {tuple(x.shape)}")
        z = torch.cat([b(x.transpose(1, 2)) for b in self.branches], dim=1).transpose(1, 2)
        out, _ = self.lstm(z)
        return self.head(out[:, -1])


def integrated_gradients(model: nn.Module, x: torch.Tensor,
                         baseline: Optional[torch.Tensor] = None,
                         steps: int = 32, target: int = 0) -> torch.Tensor:
    """Per-channel attribution (B, C): sum over time of |IG|."""
    model.eval()
    base = torch.zeros_like(x) if baseline is None else baseline
    total = torch.zeros_like(x)
    with torch.backends.cudnn.flags(enabled=False):
        for a in torch.linspace(0.0, 1.0, steps):
            p = (base + a * (x - base)).detach().requires_grad_(True)
            (grad,) = torch.autograd.grad(model(p)[:, target].sum(), p)
            total += grad
    return ((x - base) * total / steps).abs().sum(dim=1)
