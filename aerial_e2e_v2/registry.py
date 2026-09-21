"""Append-only CSV registry for aerial E2E experiments."""

from __future__ import annotations

import csv
import os
from pathlib import Path


RESULT_COLUMNS = [
    "experiment_id", "timestamp", "dataset", "split", "detector", "tracker",
    "modules", "seed", "image_size", "conf_threshold", "nms_threshold",
    "AP50", "AP50_95", "AP_small", "Recall_small", "OBB_mAP", "angle_error",
    "state_NLL", "calibration_error", "HOTA", "DetA", "AssA", "IDF1",
    "MOTA", "IDSW", "Frag", "FPS", "latency_ms", "gpu_memory", "Params",
    "FLOPs", "config_path", "checkpoint_path", "git_commit", "status", "notes",
]


def append_result(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    unknown = sorted(set(row) - set(RESULT_COLUMNS))
    if unknown:
        raise ValueError(f"unknown result columns: {unknown}")
    write_header = not path.exists() or path.stat().st_size == 0
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    descriptor = os.open(path, flags, 0o644)
    try:
        with os.fdopen(descriptor, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS, lineterminator="\n")
            if write_header:
                writer.writeheader()
            writer.writerow({column: row.get(column, "") for column in RESULT_COLUMNS})
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def append_fixed_row(path: Path, fieldnames: list[str], row: dict) -> None:
    """Append one row while enforcing an existing file's schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    if path.exists() and not write_header:
        with path.open(newline="", encoding="utf-8") as handle:
            current = next(csv.reader(handle))
        if current != fieldnames:
            raise ValueError(f"schema mismatch for {path}: {current} != {fieldnames}")
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fieldnames})
        handle.flush()
        os.fsync(handle.fileno())
