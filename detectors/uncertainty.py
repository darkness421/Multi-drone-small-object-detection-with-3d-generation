"""Uncertainty utilities for detector outputs.

TODO:
- Convert logits to uncertainty measures.
- Combine confidence, entropy, and multi-view disagreement.
- Trigger ambiguity diagnosis.
"""

from __future__ import annotations

import math


def entropy(probabilities: list[float]) -> float:
    """Compute Shannon entropy from probabilities."""
    return -sum(prob * math.log(max(prob, 1e-12)) for prob in probabilities)


if __name__ == "__main__":
    print(entropy([0.5, 0.5]))

