#!/usr/bin/env python3
"""Text dashboard for GPU health and the append-only experiment registry."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


def gpu_snapshot() -> dict:
    command = [
        "nvidia-smi",
        "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip() or result.stdout.strip()}
    rows = []
    for line in result.stdout.splitlines():
        values = [value.strip() for value in line.split(",")]
        rows.append(
            dict(zip(("index", "name", "util_pct", "memory_used_mb", "memory_total_mb", "temp_c", "power_w"), values))
        )
    return {"status": "available", "gpus": rows}


def latest_result(path: Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {"status": "empty", "path": str(path)}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {"status": "available", "count": len(rows), "latest": rows[-1]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("experiments/results.csv"))
    parser.add_argument("--snapshot", type=Path, default=Path("outputs/monitor/live_status.json"))
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--iterations", type=int, default=0, help="0 keeps monitoring until interrupted")
    args = parser.parse_args()
    iteration = 0
    while args.iterations == 0 or iteration < args.iterations:
        payload = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "gpu": gpu_snapshot(),
            "experiments": latest_result(args.results),
        }
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, sort_keys=True), flush=True)
        iteration += 1
        if args.iterations == 0 or iteration < args.iterations:
            time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
