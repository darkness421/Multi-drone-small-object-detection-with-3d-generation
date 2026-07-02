"""Aggregate experiment metrics.

TODO:
- Read outputs/results/*.json.
- Produce summary tables.
- Export Markdown experiment notes.
"""

from __future__ import annotations

import json
from pathlib import Path


def collect_metrics(result_dir: Path = Path("outputs/results")) -> list[dict]:
    """Collect metrics from result JSON files."""
    if not result_dir.exists():
        return []
    metrics = []
    for path in sorted(result_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "experiment_id" in payload and "metrics" in payload:
            metrics.append(payload)
    return metrics


if __name__ == "__main__":
    print(json.dumps(collect_metrics(), indent=2))
