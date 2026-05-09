"""Generate paper table templates for detector and system comparisons."""

from __future__ import annotations

import argparse
from pathlib import Path

from .detector_compare import DETECTOR_COLUMNS, empty_detector_table
from .stats import write_metrics_csv
from .system_compare import SYSTEM_COLUMNS, empty_system_table


def write_paper_table_templates(out_dir: str | Path = "paper/tables") -> None:
    out_dir = Path(out_dir)
    write_metrics_csv(empty_detector_table(), out_dir / "detector_frontend_comparison.csv", fieldnames=DETECTOR_COLUMNS)
    write_metrics_csv(empty_system_table(), out_dir / "system_level_comparison.csv", fieldnames=SYSTEM_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create detector and system-level paper table templates.")
    parser.add_argument("--out-dir", default="paper/tables")
    args = parser.parse_args()
    write_paper_table_templates(args.out_dir)
    print(f"Wrote paper table templates to {args.out_dir}")


if __name__ == "__main__":
    main()

