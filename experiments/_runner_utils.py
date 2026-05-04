"""Utilities shared by dummy experiment runners."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_common_args(default_config: str) -> argparse.Namespace:
    """Parse common experiment args."""
    parser = argparse.ArgumentParser(description="CoM3D-ACE experiment runner")
    parser.add_argument("--config", type=Path, default=Path(default_config))
    parser.add_argument("--dummy", action="store_true", help="Run without real model training.")
    return parser.parse_args()


def read_config_text(config_path: Path) -> str:
    """Read YAML config as text using only standard library."""
    if not config_path.exists():
        return ""
    return config_path.read_text(encoding="utf-8")


def save_dummy_metrics(experiment_id: str, config_path: Path, output_dir: Path = Path("outputs/results")) -> Path:
    """Save a dummy metrics JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = {
        "experiment_id": experiment_id,
        "config": str(config_path),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dummy": True,
        "metrics": {
            "mAP": 0.0,
            "AP_small": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "FPS": 0.0,
            "fine_grained_accuracy": 0.0,
            "evidence_completion_success": 0.0
        }
    }
    path = output_dir / f"{experiment_id}.json"
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return path


def run_dummy(experiment_id: str, default_config: str) -> None:
    """Run a dummy experiment."""
    args = parse_common_args(default_config)
    config_text = read_config_text(args.config)
    print(f"experiment: {experiment_id}")
    print(f"config: {args.config}")
    print(f"dummy: {args.dummy}")
    print(f"config_bytes: {len(config_text.encode('utf-8'))}")
    if not args.dummy:
        raise SystemExit("Only --dummy mode is implemented at this stage.")
    output = save_dummy_metrics(experiment_id, args.config)
    print(f"wrote {output}")

