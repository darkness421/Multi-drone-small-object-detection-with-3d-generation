"""Generate selective VLM verification ablation table templates."""

from __future__ import annotations

import argparse
from pathlib import Path

from .stats import write_metrics_csv
from .vlm_compare import empty_vlm_table


VLM_COLUMNS = [
    "Method",
    "Ambiguous Acc ↑",
    "Correction Rate ↑",
    "Over-correction ↓",
    "VLM Calls ↓",
    "Avg Tokens ↓",
    "Latency ↓",
    "Explanation Usefulness ↑",
    "JSON Parse Success ↑",
]


def write_vlm_template(out_path: str | Path) -> None:
    write_metrics_csv(empty_vlm_table(), out_path, fieldnames=VLM_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create selective VLM ablation CSV template.")
    parser.add_argument("--out", default="paper/tables/selective_vlm_ablation.csv")
    args = parser.parse_args()
    write_vlm_template(args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

