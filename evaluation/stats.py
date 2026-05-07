"""Statistical tests and paper-ready CSV helpers."""

from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np


def bootstrap_ci(values: Sequence[float], *, samples: int = 1000, confidence: float = 0.95, seed: int = 0) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    rng = random.Random(seed)
    means = []
    values = list(values)
    for _ in range(samples):
        draw = [rng.choice(values) for _ in values]
        means.append(float(np.mean(draw)))
    alpha = (1.0 - confidence) / 2.0
    return float(np.quantile(means, alpha)), float(np.quantile(means, 1.0 - alpha))


def paired_t_test(a: Sequence[float], b: Sequence[float]) -> dict[str, float]:
    try:
        from scipy.stats import ttest_rel

        stat, pvalue = ttest_rel(a, b)
        return {"statistic": float(stat), "pvalue": float(pvalue)}
    except ImportError:
        diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
        return {"statistic": float(np.mean(diff)), "pvalue": 1.0}


def wilcoxon_signed_rank(a: Sequence[float], b: Sequence[float]) -> dict[str, float]:
    try:
        from scipy.stats import wilcoxon

        stat, pvalue = wilcoxon(a, b)
        return {"statistic": float(stat), "pvalue": float(pvalue)}
    except ImportError:
        return {"statistic": 0.0, "pvalue": 1.0}


def write_metrics_csv(
    rows: Sequence[Mapping[str, object]],
    path: str | Path,
    fieldnames: Sequence[str] | None = None,
) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
