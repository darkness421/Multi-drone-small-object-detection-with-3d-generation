"""Utilities for reading Isaac proxy detector ground truth."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Mapping


GT_CANONICAL = {
    "sedan": "car",
    "pickup": "car",
    "police_car": "car",
    "car": "car",
    "van": "van",
    "ambulance": "van",
    "truck": "truck",
    "bus": "bus",
    "pedestrian": "pedestrian",
    "people": "pedestrian",
    "person": "pedestrian",
    "worker": "pedestrian",
    "small_boat": "boat",
    "boat": "boat",
    "debris": "debris",
}


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _canonical(value: Any) -> str:
    label = _normalise(value)
    return GT_CANONICAL.get(label, label)


def _label(info: Mapping[str, Any], semantic_id: Any) -> str:
    mapping = info.get("idToLabels") or info.get("id_to_labels") or {}
    raw = mapping.get(str(semantic_id), mapping.get(semantic_id, "")) if isinstance(mapping, dict) else ""
    if isinstance(raw, dict):
        return str(raw.get("class") or raw.get("label") or raw.get("name") or "")
    if isinstance(raw, str):
        try:
            parsed = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            parsed = None
        if isinstance(parsed, dict):
            return str(parsed.get("class") or parsed.get("label") or parsed.get("name") or "")
        return raw
    return str(raw or "")


def _coord(row: Mapping[str, Any], *names: str) -> float:
    for name in names:
        if name in row:
            return float(row[name])
    raise KeyError(f"missing coordinate {names} in {sorted(row)}")


def load_deduplicated_gt(path: Path) -> list[dict[str, Any]]:
    """Merge proxy mesh and cutout annotations into one visible box per object."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected Isaac annotation mapping: {path}")
    data = payload.get("data", [])
    info = payload.get("info", {})
    prim_paths = info.get("primPaths", []) if isinstance(info, dict) else []
    grouped: dict[str, dict[str, Any]] = {}

    for row_index, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        semantic_id = item.get("semanticId", item.get("semantic_id", item.get("id")))
        label = _label(info, semantic_id) or str(item.get("class") or item.get("label") or "unknown")
        x1 = _coord(item, "x_min", "xMin", "xmin")
        y1 = _coord(item, "y_min", "yMin", "ymin")
        x2 = _coord(item, "x_max", "xMax", "xmax")
        y2 = _coord(item, "y_max", "yMax", "ymax")
        if x2 <= x1 or y2 <= y1:
            continue

        prim_path = str(prim_paths[row_index]) if row_index < len(prim_paths) else ""
        object_match = re.search(r"obj_\d+", prim_path)
        object_id = object_match.group(0) if object_match else f"annotation_{row_index:04d}"
        canonical = _canonical(label)
        key = f"{object_id}:{canonical}"
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = {
                "object_id": object_id,
                "semantic_id": semantic_id,
                "label": _normalise(label),
                "canonical": canonical,
                "xyxy": [x1, y1, x2, y2],
                "component_count": 1,
                "prim_paths": [prim_path] if prim_path else [],
            }
            continue

        existing["xyxy"] = [
            min(existing["xyxy"][0], x1),
            min(existing["xyxy"][1], y1),
            max(existing["xyxy"][2], x2),
            max(existing["xyxy"][3], y2),
        ]
        existing["component_count"] += 1
        if prim_path:
            existing["prim_paths"].append(prim_path)

    return sorted(grouped.values(), key=lambda row: (row["object_id"], row["canonical"]))
