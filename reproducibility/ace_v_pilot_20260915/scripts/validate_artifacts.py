#!/usr/bin/env python3
"""Validate ACE-V manifests, required outputs, and frozen decision invariants."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


ACE_ROOT = Path(__file__).resolve().parents[1]


def digest_stream(handle) -> str:
    value = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        value.update(block)
    return value.hexdigest()


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return digest_stream(handle)


def csv_rows(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def check_manifest(directory: Path) -> list[dict]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    checks = []
    for name, expected in manifest["outputs"].items():
        path = directory / name
        observed = digest(path) if path.is_file() else None
        checks.append({
            "check": f"sha256:{directory.name}/{name}",
            "passed": observed == expected["sha256"],
            "observed": observed,
            "expected": expected["sha256"],
        })
        if path.suffix == ".gz" and "uncompressed_sha256" in expected:
            with gzip.open(path, "rb") as handle:
                uncompressed = digest_stream(handle)
            checks.append({
                "check": f"uncompressed_sha256:{directory.name}/{name}",
                "passed": uncompressed == expected["uncompressed_sha256"],
                "observed": uncompressed,
                "expected": expected["uncompressed_sha256"],
            })
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=ACE_ROOT / "results_raw/final/validation_report.json",
    )
    args = parser.parse_args()
    final = ACE_ROOT / "results_raw/final"
    checks = []
    for directory in (
        ACE_ROOT / "results_raw/m3ot_direct_crop_v1",
        ACE_ROOT / "results_raw/mmot_full50_v1",
    ):
        checks.extend(check_manifest(directory))

    required = {
        "artifact_inventory.json": ACE_ROOT / "artifact_inventory.json",
        "protocol_freeze.yaml": ACE_ROOT / "protocol_freeze.yaml",
        "baseline_reproduction.csv": final / "baseline_reproduction.csv",
        "complementarity_by_condition.csv": ACE_ROOT / "results_raw/complementarity/complementarity_by_condition.csv",
        "disagreement_edges.csv": ACE_ROOT / "results_raw/complementarity/disagreement_edges.csv",
        "verification_features.csv": ACE_ROOT / "results_raw/mmot_full50_v1/verification_features.csv",
        "development_selection.csv": ACE_ROOT / "results_raw/m3ot_direct_crop_v1/development_selection.csv",
        "hybrid_results_per_sequence.csv": ACE_ROOT / "results_raw/mmot_full50_v1/hybrid_results_per_sequence.csv",
        "paired_comparisons.csv": final / "paired_comparisons.csv",
        "link_audit_label_quality.csv": ACE_ROOT / "results_raw/mmot_full50_v1/link_audit_label_quality.csv",
        "candidate_recall.csv": ACE_ROOT / "results_raw/m3ot_direct_crop_v1/candidate_recall.csv",
        "m3ot_direct_crop_diagnostic.csv": ACE_ROOT / "results_raw/m3ot_direct_crop_v1/m3ot_direct_crop_diagnostic.csv",
        "runtime_breakdown.csv": ACE_ROOT / "results_raw/mmot_full50_v1/runtime_breakdown.csv",
        "reference_audit.csv": final / "reference_audit.csv",
        "RESULTS_DECISION.md": final / "RESULTS_DECISION.md",
    }
    for name, path in required.items():
        checks.append({
            "check": f"required:{name}", "passed": path.is_file(),
            "observed": str(path), "expected": "regular file",
        })

    reproduction = list(csv.DictReader((final / "baseline_reproduction.csv").open()))
    checks.append({
        "check": "baseline_reproduction_420_of_420",
        "passed": len(reproduction) == 420 and all(row["passed"] == "True" for row in reproduction),
        "observed": f"rows={len(reproduction)}, passed={sum(row['passed'] == 'True' for row in reproduction)}",
        "expected": "rows=420, passed=420",
    })
    decision = json.loads((final / "results_decision.json").read_text(encoding="utf-8"))
    checks.extend([
        {
            "check": "no_unsupported_success_claim", "passed": decision["success"] is False,
            "observed": decision["success"], "expected": False,
        },
        {
            "check": "no_figure_replacement", "passed": decision["replace_figure"] is False,
            "observed": decision["replace_figure"], "expected": False,
        },
    ])
    reference_rows = list(csv.DictReader((final / "reference_audit.csv").open()))
    decisions = {name: sum(row["decision"] == name for row in reference_rows) for name in ("keep", "add", "remove")}
    checks.append({
        "check": "reference_scope_audit",
        "passed": len(reference_rows) == 42 and decisions == {"keep": 26, "add": 4, "remove": 12},
        "observed": {"rows": len(reference_rows), **decisions},
        "expected": {"rows": 42, "keep": 26, "add": 4, "remove": 12},
    })
    row_counts = {
        "mmot_hybrid_per_sequence": csv_rows(ACE_ROOT / "results_raw/mmot_full50_v1/hybrid_results_per_sequence.csv"),
        "mmot_verification_features": csv_rows(ACE_ROOT / "results_raw/mmot_full50_v1/verification_features.csv"),
        "mmot_accepted_link_audit": csv_rows(ACE_ROOT / "results_raw/mmot_full50_v1/accepted_link_audit.csv.gz"),
        "m3ot_hybrid_per_sequence": csv_rows(ACE_ROOT / "results_raw/m3ot_direct_crop_v1/hybrid_results_per_sequence.csv"),
    }
    checks.append({
        "check": "nonempty_primary_outputs",
        "passed": all(value > 0 for value in row_counts.values()),
        "observed": row_counts, "expected": "all counts > 0",
    })

    payload = {
        "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
        "checks_passed": sum(item["passed"] for item in checks),
        "checks_total": len(checks),
        "checks": checks,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("status", "checks_passed", "checks_total")}, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
