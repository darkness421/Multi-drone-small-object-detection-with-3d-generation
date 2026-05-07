"""Evidence association algorithms."""

from __future__ import annotations

from typing import Callable

import numpy as np

from evidence import EvidenceToken
from .costs import pairwise_evidence_cost


Match = tuple[int, int, float]


def cost_matrix(left: list[EvidenceToken], right: list[EvidenceToken]) -> np.ndarray:
    return np.asarray([[pairwise_evidence_cost(a, b) for b in right] for a in left], dtype=float)


def greedy_matching(left: list[EvidenceToken], right: list[EvidenceToken], threshold: float) -> list[Match]:
    costs = [(i, j, pairwise_evidence_cost(a, b)) for i, a in enumerate(left) for j, b in enumerate(right)]
    matches: list[Match] = []
    used_left: set[int] = set()
    used_right: set[int] = set()
    for i, j, cost in sorted(costs, key=lambda item: item[2]):
        if cost > threshold or i in used_left or j in used_right:
            continue
        matches.append((i, j, float(cost)))
        used_left.add(i)
        used_right.add(j)
    return matches


def threshold_association(tokens: list[EvidenceToken], threshold: float) -> list[tuple[int, int, float]]:
    matches: list[tuple[int, int, float]] = []
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            cost = pairwise_evidence_cost(tokens[i], tokens[j])
            if cost <= threshold:
                matches.append((i, j, float(cost)))
    return matches


def hungarian_matching(left: list[EvidenceToken], right: list[EvidenceToken], threshold: float) -> list[Match]:
    matrix = cost_matrix(left, right)
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        return greedy_matching(left, right, threshold)
    row_ind, col_ind = linear_sum_assignment(matrix)
    return [(int(i), int(j), float(matrix[i, j])) for i, j in zip(row_ind, col_ind) if matrix[i, j] <= threshold]

