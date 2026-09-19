#!/usr/bin/env python3
"""Verify headline REGR values against the released final tables."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reproducibility" / "verified_tables" / "final"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def close(actual: str, expected: float, *, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance)


def main() -> int:
    comparison = read_csv(TABLES / "main_comparison.csv")
    paired = read_csv(TABLES / "paired_idf1.csv")
    final_rows = {
        (row["panel"], row["tracker"]): row
        for row in comparison
        if row["method"] == "regr_final"
    }
    expected = {
        ("mmot_oracle", "bytetrack"): (51.87209858498237, 0.0721241129428094),
        ("mmot_oracle", "ocsort"): (46.24956208335191, -0.00012992590615823474),
        ("mmot_oracle", "deepocsort"): (83.99717469521244, -0.004334189806954214),
        ("mmot_detector", "bytetrack"): (41.112227061657705, 0.008167290309060604),
        ("mmot_detector", "ocsort"): (38.75215456704899, -0.012205252837489411),
        ("mmot_detector", "deepocsort"): (64.15066121938067, -0.021163169036682916),
        ("m3ot_oracle", "bytetrack"): (95.47200616427683, 0.016622309122993784),
        ("m3ot_oracle", "ocsort"): (95.41822505851617, 0.39730585673927976),
    }

    checks: list[bool] = [set(final_rows) == set(expected)]
    for key, (idf1, delta) in expected.items():
        row = final_rows[key]
        checks.extend(
            (
                close(row["IDF1"], idf1),
                close(row["delta_vs_strong_IDF1_pp"], delta),
            )
        )

    paired_lookup = {
        (row["panel"], row["tracker"], row["comparison"]): row
        for row in paired
    }
    motion_deltas = {
        tracker: float(
            paired_lookup[
                ("m3ot_oracle", tracker, "regr_final-minus-regr_final_no_motion")
            ]["mean_delta_IDF1_pp"]
        )
        for tracker in ("bytetrack", "ocsort")
    }
    checks.extend(
        (
            close(str(motion_deltas["bytetrack"]), 0.6564885700006126),
            close(str(motion_deltas["ocsort"]), 1.3909881665033907),
            len(paired) == 32,
        )
    )

    report = {
        "final_rows_verified": len(final_rows),
        "m3ot_motion_delta_idf1_pp": motion_deltas,
        "paired_rows_verified": len(paired),
        "status": "PASS" if all(checks) else "FAIL",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
