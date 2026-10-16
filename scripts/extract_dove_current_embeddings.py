#!/usr/bin/env python3
"""Extract frozen-detector embeddings from the current DOVE observation only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ultralytics import YOLO  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialised = list(rows)
    fields = list(dict.fromkeys(key for row in materialised for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(materialised)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--current-uav-id", default="uav_01")
    parser.add_argument("--device", default="0")
    parser.add_argument("--imgsz", type=int, default=1280)
    args = parser.parse_args()

    capture_dir = Path(args.capture_dir).resolve()
    checkpoint = Path(args.checkpoint).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    capture = json.loads(
        (capture_dir / "proxy_capture_summary.json").read_text(encoding="utf-8")
    )
    records = sorted(
        (
            row
            for row in capture["direct_capture"]["records"]
            if row["uav_id"] == args.current_uav_id
        ),
        key=lambda row: int(row["frame_index"]),
    )
    if not records:
        raise RuntimeError(f"no capture rows for {args.current_uav_id}")

    model = YOLO(str(checkpoint))
    rows = []
    started = time.perf_counter()
    for index, record in enumerate(records, start=1):
        image_path = capture_dir / record["rgb_path"]
        values = model.embed(
            source=str(image_path),
            imgsz=args.imgsz,
            device=args.device,
            verbose=False,
        )
        if len(values) != 1:
            raise RuntimeError(f"expected one embedding for {image_path}, got {len(values)}")
        vector = values[0].detach().float().cpu().numpy().reshape(-1)
        row: dict[str, Any] = {
            "scene_variant": int(record["frame_index"]),
            "current_uav_id": args.current_uav_id,
            "current_rgb_path": str(image_path),
            "current_rgb_sha256": _sha256(image_path),
        }
        for feature_index, value in enumerate(vector):
            row[f"embedding_{feature_index:04d}"] = float(value)
        rows.append(row)
        print(
            json.dumps(
                {
                    "stage": "frozen_current_rgb_embedding",
                    "scene": record["frame_index"],
                    "progress": f"{index}/{len(records)}",
                    "dimensions": len(vector),
                }
            ),
            flush=True,
        )
    csv_path = output_dir / "current_visual_embeddings.csv"
    _write_csv(csv_path, rows)
    summary = {
        "status": "COMPLETE",
        "capture_dir": str(capture_dir),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "current_uav_id": args.current_uav_id,
        "scene_variant_count": len(rows),
        "embedding_dimensions": len(rows[0]) - 4,
        "candidate_outcome_rgb_used": False,
        "ground_truth_used": False,
        "device": args.device,
        "imgsz": args.imgsz,
        "elapsed_seconds": time.perf_counter() - started,
        "output_csv": str(csv_path),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
