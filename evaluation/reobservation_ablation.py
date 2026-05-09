"""Generate re-observation policy ablation table templates."""

from __future__ import annotations

import argparse
from pathlib import Path

from .policy_compare import REOBSERVATION_COLUMNS, empty_reobservation_table
from .stats import write_metrics_csv


def write_reobservation_template(out_path: str | Path) -> None:
    write_metrics_csv(empty_reobservation_table(), out_path, fieldnames=REOBSERVATION_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create re-observation ablation CSV template.")
    parser.add_argument("--out", default="paper/tables/reobservation_policy_ablation.csv")
    args = parser.parse_args()
    write_reobservation_template(args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
