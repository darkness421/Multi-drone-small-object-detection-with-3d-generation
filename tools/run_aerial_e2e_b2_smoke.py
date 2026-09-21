#!/usr/bin/env python3
"""Run one real-MMOT, two-frame optimization/evaluation smoke for B2."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from aerial_e2e_v2 import B2Scaffold, compute_b2_loss
from aerial_e2e_v2.mmot_smoke import build_dense_targets, load_sequence_pair
from aerial_e2e_v2.registry import append_fixed_row, append_result


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=False, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_per_sequence(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = REPOSITORY_ROOT
    config_path = args.config.resolve()
    output_dir = args.output_dir.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    sequence = Path(config["data"]["sequence_dir"])
    seed = int(config["seed"])
    torch.manual_seed(seed)
    device = torch.device(config["runtime"]["device"])
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")

    frames, labels, frame_names = load_sequence_pair(sequence, int(config["data"]["image_size"]))
    frames = frames.to(device)
    model = B2Scaffold(
        num_classes=int(config["model"]["num_classes"]),
        embedding_dim=int(config["model"]["embedding_dim"]),
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config["optimizer"]["lr"]))

    started = time.perf_counter()
    model.train()
    outputs = model(frames)
    targets = build_dense_targets(
        labels,
        tuple(config["data"]["original_size"]),
        tuple(outputs.objectness_logits.shape[-2:]),
        model.num_classes,
    )
    targets = type(targets)(*(value.to(device) for value in vars(targets).values()))
    losses = compute_b2_loss(outputs, targets)
    before = float(losses["total"].detach())
    optimizer.zero_grad(set_to_none=True)
    losses["total"].backward()
    optimizer.step()

    model.eval()
    with torch.no_grad():
        after_outputs = model(frames)
        after_losses = compute_b2_loss(after_outputs, targets)
    elapsed = time.perf_counter() - started
    after = float(after_losses["total"])
    parameters = sum(parameter.numel() for parameter in model.parameters())
    positive_cells = int(targets.objectness.sum().item())
    peak_memory = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "status": "PASS" if torch.isfinite(after_losses["total"]) else "FAIL",
        "scope": "infrastructure smoke only; not a scientific baseline result",
        "dataset": "MMOT",
        "split": "official test sequence used only for pipeline smoke; no model selection",
        "sequence": sequence.name,
        "frames": frame_names,
        "frame_tensor_shape": list(frames.shape),
        "feature_grid": list(after_outputs.objectness_logits.shape[-2:]),
        "positive_grid_cells": positive_cells,
        "loss_before": before,
        "loss_after_one_step": after,
        "loss_components_after": {
            name: float(value.detach()) for name, value in after_losses.items()
        },
        "parameters": parameters,
        "elapsed_seconds": elapsed,
        "latency_ms_per_frame_including_train_step": elapsed / frames.shape[1] * 1000.0,
        "device": str(device),
        "cuda_available": torch.cuda.is_available(),
        "peak_gpu_memory_bytes": peak_memory,
        "config": str(config_path.relative_to(root)),
        "config_sha256": sha256(config_path),
        "git_commit": git_head(root),
        "torch": torch.__version__,
    }
    (output_dir / "smoke_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    per_sequence = {
        "experiment_id": config["experiment_id"],
        "dataset": "MMOT",
        "split": "test_pipeline_smoke_only",
        "sequence": sequence.name,
        "frames": ";".join(frame_names),
        "loss_before": before,
        "loss_after_one_step": after,
        "positive_grid_cells": positive_cells,
        "latency_ms_per_frame_including_train_step": metrics["latency_ms_per_frame_including_train_step"],
        "status": metrics["status"],
    }
    write_per_sequence(output_dir / "per_sequence_metrics.csv", per_sequence)
    append_fixed_row(
        root / config["registry"]["per_sequence_csv"],
        list(per_sequence),
        per_sequence,
    )
    append_result(
        root / config["registry"]["results_csv"],
        {
            "experiment_id": config["experiment_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": "MMOT",
            "split": "test_pipeline_smoke_only",
            "detector": "B2 minimal shared encoder",
            "tracker": "B2 embedding interface (no benchmark tracker)",
            "modules": "shared_encoder+deterministic_obb_head+identity_head",
            "seed": seed,
            "image_size": config["data"]["image_size"],
            "FPS": frames.shape[1] / elapsed,
            "latency_ms": metrics["latency_ms_per_frame_including_train_step"],
            "gpu_memory": peak_memory,
            "Params": parameters,
            "config_path": str(config_path.relative_to(root)),
            "checkpoint_path": "",
            "git_commit": metrics["git_commit"],
            "status": "smoke_pass" if metrics["status"] == "PASS" else "smoke_fail",
            "notes": metrics["scope"],
        },
    )
    print(json.dumps(metrics, indent=2, sort_keys=True), flush=True)
    return 0 if metrics["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
