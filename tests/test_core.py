import numpy as np
import torch

from src.engine.threshold import detect, event_metrics, ewma
from src.model.network import CNNBiLSTM, integrated_gradients


def test_model_shape():
    assert CNNBiLSTM(in_channels=5)(torch.randn(4, 250, 5)).shape == (4, 1)


def test_ig_shape():
    m = CNNBiLSTM(in_channels=3)
    assert integrated_gradients(m, torch.randn(2, 50, 3), steps=4).shape == (2, 3)


def test_ewma_len():
    assert ewma(np.ones(10)).shape == (10,)


def test_detects_spike():
    rng = np.random.default_rng(0)
    e = np.abs(rng.normal(0, .05, 800))
    e[400:430] += 2.0
    seqs, _ = detect(e)
    assert event_metrics(seqs, [(400, 430)])["recall"] == 1.0
