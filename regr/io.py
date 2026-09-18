"""Portable readers and writers for frozen REGR cache inputs."""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def _open_text(path: Path, mode: str):
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8")
    return path.open(mode, encoding="utf-8")


def load_predictions(path: Path) -> dict[int, list[dict]]:
    """Load one JSON object per observation from JSONL or JSONL.GZ."""
    output: dict[int, list[dict]] = defaultdict(list)
    with _open_text(path, "rt") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "frame" not in row or "id" not in row:
                raise ValueError(f"{path}:{line_number} requires frame and id")
            frame = int(row.pop("frame"))
            output[frame].append(row)
    return dict(output)


def write_predictions(path: Path, predictions: dict[int, list[dict]]) -> None:
    """Write frame-indexed observations as deterministic JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with _open_text(path, "wt") as handle:
        for frame in sorted(predictions):
            for row in sorted(predictions[frame], key=lambda item: int(item["id"])):
                handle.write(json.dumps({"frame": frame, **row}, sort_keys=True) + "\n")


def load_descriptors(path: Path) -> dict[int, np.ndarray]:
    """Load tracklet descriptors from JSON or NPZ."""
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {int(key): np.asarray(value, dtype=float) for key, value in payload.items()}
    if path.suffix == ".npz":
        with np.load(path) as payload:
            return {int(key): np.asarray(payload[key], dtype=float) for key in payload.files}
    raise ValueError(f"unsupported descriptor format: {path}")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
