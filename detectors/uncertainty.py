"""Compatibility wrappers for detector uncertainty utilities."""

from __future__ import annotations

import math
from typing import Sequence

from evidence.uncertainty import (
    brier_score,
    class_entropy,
    expected_calibration_error,
    margin_confidence,
    max_softmax_confidence,
    softmax,
    summarize_mc_dropout,
    uncertainty_score,
)


def entropy(probabilities: Sequence[float]) -> float:
    """Compute Shannon entropy from probabilities without normalization."""

    return -sum(prob * math.log(max(prob, 1e-12)) for prob in probabilities)


__all__ = [
    "softmax",
    "class_entropy",
    "max_softmax_confidence",
    "margin_confidence",
    "uncertainty_score",
    "brier_score",
    "expected_calibration_error",
    "summarize_mc_dropout",
    "entropy",
]
