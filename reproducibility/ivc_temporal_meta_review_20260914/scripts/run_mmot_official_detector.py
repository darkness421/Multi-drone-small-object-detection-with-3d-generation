#!/usr/bin/env python3
"""Cache official MMOT YOLO11L-3ch detections for frozen temporal evaluation."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import ultralytics
from ultralytics import YOLO


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def git_head(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def frame_number(path: Path, fallback: int) -> int:
    digits = "".join(character for character in path.stem if character.isdigit())
    return int(digits) if digits else fallback


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True)
    parser.add_argument("--device", default="0")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--confidence", type=float, default=0.1)
    parser.add_argument("--nms-iou", type=float, default=0.6)
    parser.add_argument("--max-sequences-per-family", type=int)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(0)
    np.random.seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)
        torch.backends.cudnn.benchmark = False
    model = YOLO(str(args.checkpoint))
    rows = []
    sequence_rows = []
    output_hashes = {}
    started_all = time.perf_counter()

    for family, raw_root in args.family_root:
        root = Path(raw_root)
        sequences = sorted(path for path in root.iterdir() if path.is_dir())
        if args.max_sequences_per_family is not None:
            sequences = sequences[:args.max_sequences_per_family]
        for sequence in sequences:
            images = sorted(sequence.glob("*.npy"))
            destination = args.output_dir / "detections" / family / f"{sequence.name}.jsonl.gz"
            destination.parent.mkdir(parents=True, exist_ok=True)
            detection_count = zero_frames = 0
            sequence_started = time.perf_counter()
            with gzip.open(destination, "wt", encoding="utf-8", newline="") as handle:
                for index, image_path in enumerate(images, start=1):
                    frame = frame_number(image_path, index)
                    array = np.load(image_path, mmap_mode="r")
                    if array.ndim != 3 or array.shape[2] < 5 or array.dtype != np.uint8:
                        raise RuntimeError(f"unsupported MMOT frame: {image_path} {array.shape} {array.dtype}")
                    # The official predictor supplies BGR bands [2,3,5] to
                    # Ultralytics, which converts NumPy BGR input to RGB.
                    bgr = np.ascontiguousarray(array[:, :, [1, 2, 4]])
                    started = time.perf_counter()
                    result = model.predict(
                        source=bgr, imgsz=args.imgsz, conf=args.confidence,
                        iou=args.nms_iou, device=args.device, verbose=False,
                    )[0]
                    if torch.cuda.is_available():
                        torch.cuda.synchronize()
                    elapsed = time.perf_counter() - started
                    count = len(result.obb)
                    detection_count += count
                    zero_frames += int(count == 0)
                    rows.append({
                        "family": family, "sequence": sequence.name, "frame": frame,
                        "image_path": str(image_path), "height": int(array.shape[0]),
                        "width": int(array.shape[1]), "detections": count,
                        "zero_detection_frame": count == 0,
                        "inference_seconds": elapsed,
                    })
                    if count:
                        polygons = result.obb.xyxyxyxy.detach().float().cpu().numpy()
                        classes = result.obb.cls.detach().cpu().numpy()
                        confidences = result.obb.conf.detach().float().cpu().numpy()
                        for polygon, class_id, confidence in zip(polygons, classes, confidences):
                            points = np.asarray(polygon, dtype=float).reshape(4, 2)
                            x1, y1 = points.min(axis=0)
                            x2, y2 = points.max(axis=0)
                            record = {
                                "family": family, "sequence": sequence.name,
                                "frame": frame, "class_id": int(class_id),
                                "confidence": float(confidence),
                                "x": float(x1), "y": float(y1),
                                "w": float(x2 - x1), "h": float(y2 - y1),
                                "obb_xy": points.reshape(-1).tolist(),
                            }
                            handle.write(json.dumps(record, sort_keys=True) + "\n")
            digest = sha256(destination)
            output_hashes[f"{family}/{sequence.name}"] = {
                "path": str(destination), "sha256": digest,
            }
            sequence_rows.append({
                "family": family, "sequence": sequence.name,
                "frame_count": len(images), "detection_count": detection_count,
                "zero_detection_frames": zero_frames,
                "runtime_seconds": time.perf_counter() - sequence_started,
                "output_path": str(destination), "output_sha256": digest,
            })
            print(
                f"{family}/{sequence.name}: frames={len(images)} detections={detection_count} "
                f"zero={zero_frames}",
                flush=True,
            )

    write_csv(args.output_dir / "real_detection_frame_manifest.csv", rows)
    write_csv(args.output_dir / "real_detection_sequence_manifest.csv", sequence_rows)
    package_root = Path(ultralytics.__file__).resolve().parents[1]
    manifest = {
        "status": "COMPLETE",
        "dataset": "MMOT official test subset",
        "detector": "official MMOT YOLO11L-3ch",
        "checkpoint": {
            "path": str(args.checkpoint), "sha256": sha256(args.checkpoint),
            "source": "MMOT official Google Drive pretrained-model folder",
            "google_drive_file_id": "15gmA4-Yclvh5EZvTJYhcyV1CVdNRGIkR",
        },
        "implementation": {
            "ultralytics_version": ultralytics.__version__,
            "package_root": str(package_root),
            "repository_commit": git_head(package_root),
        },
        "settings": {
            "input": "raw HWC uint8 bands zero-based [1,2,4] as BGR; Ultralytics internally converts to RGB",
            "spectral_rgb_equivalent": "bands 5,3,2",
            "imgsz": args.imgsz, "confidence": args.confidence,
            "nms_iou": args.nms_iou, "task": "oriented detection",
            "aabb_adapter": "axis-aligned min/max envelope of the predicted OBB, without clipping or GT filtering",
        },
        "training_split_provenance": "Checkpoint is supplied by the MMOT authors for their train/test benchmark protocol; no target-test adaptation was performed here.",
        "families": [{"name": name, "root": path} for name, path in args.family_root],
        "frames": len(rows),
        "detections": sum(row["detection_count"] for row in sequence_rows),
        "zero_detection_frames": sum(row["zero_detection_frames"] for row in sequence_rows),
        "runtime_seconds": time.perf_counter() - started_all,
        "device": {
            "requested": args.device,
            "cuda_available": torch.cuda.is_available(),
            "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "torch": torch.__version__,
        },
        "outputs": output_hashes,
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
    }
    write_json(args.output_dir / "detector_checkpoint_manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"], "frames": manifest["frames"],
        "detections": manifest["detections"],
        "zero_detection_frames": manifest["zero_detection_frames"],
        "runtime_seconds": manifest["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
