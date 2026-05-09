"""Uncertainty and calibration utilities for detection evidence."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


def softmax(logits: Sequence[float]) -> list[float]:
    if not logits:
        return []
    max_logit = max(logits)
    exps = [math.exp(x - max_logit) for x in logits]
    total = sum(exps)
    return [x / total for x in exps]


def class_entropy(logits_or_probs: Sequence[float], *, normalized: bool = True) -> float:
    probs = list(logits_or_probs)
    if not probs:
        return 0.0
    if any(p < 0.0 for p in probs) or abs(sum(probs) - 1.0) > 1e-4:
        probs = softmax(probs)
    entropy = -sum(p * math.log(max(p, 1e-12)) for p in probs)
    if normalized and len(probs) > 1:
        entropy /= math.log(len(probs))
    return float(entropy)


def max_softmax_confidence(logits: Sequence[float]) -> float:
    probs = softmax(logits)
    return max(probs) if probs else 0.0


def margin_confidence(logits: Sequence[float]) -> float:
    probs = sorted(softmax(logits), reverse=True)
    if not probs:
        return 0.0
    if len(probs) == 1:
        return probs[0]
    return probs[0] - probs[1]


def uncertainty_score(logits: Sequence[float]) -> float:
    """Combine entropy and confidence margin into a single uncertainty score."""

    entropy = class_entropy(logits)
    margin = margin_confidence(logits)
    return float(max(0.0, min(1.0, 0.7 * entropy + 0.3 * (1.0 - margin))))


def brier_score(probs: Sequence[float], target_index: int) -> float:
    return float(sum((p - (1.0 if i == target_index else 0.0)) ** 2 for i, p in enumerate(probs)))


def expected_calibration_error(confidences: Sequence[float], correct: Sequence[bool], bins: int = 10) -> float:
    if len(confidences) != len(correct):
        raise ValueError("confidences and correct must have the same length")
    if not confidences:
        return 0.0
    total = len(confidences)
    ece = 0.0
    for bin_idx in range(bins):
        lo = bin_idx / bins
        hi = (bin_idx + 1) / bins
        indices = [i for i, c in enumerate(confidences) if lo <= c <= hi if bin_idx == bins - 1 or c < hi]
        if not indices:
            continue
        acc = sum(1.0 for i in indices if correct[i]) / len(indices)
        conf = sum(confidences[i] for i in indices) / len(indices)
        ece += len(indices) / total * abs(acc - conf)
    return float(ece)


@dataclass(slots=True)
class MCDropoutSummary:
    mean_probs: list[float]
    predictive_entropy: float
    variance: list[float]


def summarize_mc_dropout(prob_samples: Sequence[Sequence[float]]) -> MCDropoutSummary:
    if not prob_samples:
        return MCDropoutSummary([], 0.0, [])
    n = len(prob_samples)
    dim = len(prob_samples[0])
    mean = [sum(sample[i] for sample in prob_samples) / n for i in range(dim)]
    var = [sum((sample[i] - mean[i]) ** 2 for sample in prob_samples) / n for i in range(dim)]
    return MCDropoutSummary(mean, class_entropy(mean), var)
