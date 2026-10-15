#!/usr/bin/env python3
"""Run the DOVE-WM proxy diagnostics with typed CSV action fields."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import summarize_dove_wm_detector_proxy as diagnostics


NUMERIC_ACTION_FIELDS = (
    "altitude_m", "horizontal_range_m", "range_m", "inverse_range",
    "image_width", "image_height", "processed_pixels", "detector_token_count",
    "target_token_count", "target_max_confidence", "target_confidence_sum",
    "target_bbox_area_ratio", "detector_proxy_utility", "inference_seconds",
)


def typed_read_csv(path: Path):
    rows = original_read_csv(path)
    if path.name == "action_outcomes.csv":
        for row in rows:
            for field in NUMERIC_ACTION_FIELDS:
                row[field] = float(row[field])
    return rows


original_read_csv = diagnostics.read_csv
diagnostics.read_csv = typed_read_csv


if __name__ == "__main__":
    raise SystemExit(diagnostics.main())
