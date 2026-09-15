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
PAPER_ROOT = Path(
    "/home/oem/projects/deepfake/Ourmethod/_checkpoint/meme_comparison/"
    "workspace/com3d_ace_ivc_overleaf_sync"
)


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
    review = ACE_ROOT / "results_raw/review_response_20260916"
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
        "reference_audit_summary.md": final / "reference_audit_summary.md",
        "RESULTS_DECISION.md": final / "RESULTS_DECISION.md",
        "review_manifest.json": review / "manifest.json",
        "experiment_status.csv": review / "experiment_status.csv",
        "experiment_status.md": review / "experiment_status.md",
        "requested_contrasts_per_sequence.csv": review / "requested_contrasts_per_sequence.csv",
        "requested_contrasts_summary.csv": review / "requested_contrasts_summary.csv",
        "component_comparison_summary.md": review / "component_comparison_summary.md",
        "paper_table_ace_v_strong_linker.tex": review / "paper_table_ace_v_strong_linker.tex",
        "base_off_equivalence.csv": review / "base_off_equivalence.csv",
        "m3ot_preprocessing_control.csv": review / "m3ot_preprocessing_control.csv",
        "reproduction_commands.md": review / "reproduction_commands.md",
        "professor_review_resolution.md": review / "professor_review_resolution.md",
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
    decisions = {
        name: sum(row["decision"] == name for row in reference_rows)
        for name in ("keep", "restore", "add", "remove")
    }
    compiled_count = sum(row["final_pdf"] == "yes" for row in reference_rows)
    source_count = sum(row["final_source_tree"] == "yes" for row in reference_rows)
    checks.append({
        "check": "reference_scope_audit",
        "passed": (
            len(reference_rows) == 49
            and decisions == {"keep": 22, "restore": 1, "add": 11, "remove": 15}
            and compiled_count == 34
            and source_count == 37
        ),
        "observed": {
            "rows": len(reference_rows), "compiled": compiled_count,
            "source_tree": source_count, **decisions,
        },
        "expected": {
            "rows": 49, "compiled": 34, "source_tree": 37,
            "keep": 22, "restore": 1, "add": 11, "remove": 15,
        },
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

    review_manifest = json.loads((review / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in review_manifest["output_sha256"].items():
        path = review / name
        observed = digest(path) if path.is_file() else None
        checks.append({
            "check": f"review_sha256:{name}",
            "passed": observed == expected,
            "observed": observed,
            "expected": expected,
        })
    statuses = list(csv.DictReader((review / "experiment_status.csv").open()))
    checks.append({
        "check": "five_requested_items_complete",
        "passed": (
            len(statuses) == 5
            and all(row["status"] == "완료" for row in statuses)
            and all(row["currently_running"] == "False" for row in statuses)
            and all(row["historical_job_id"] == "not_persisted" for row in statuses)
        ),
        "observed": {
            "rows": len(statuses),
            "complete": sum(row["status"] == "완료" for row in statuses),
            "running": sum(row["currently_running"] == "True" for row in statuses),
        },
        "expected": {"rows": 5, "complete": 5, "running": 0},
    })
    requested_rows = list(csv.DictReader((review / "requested_contrasts_per_sequence.csv").open()))
    requested_summary = list(csv.DictReader((review / "requested_contrasts_summary.csv").open()))
    equivalence = list(csv.DictReader((review / "base_off_equivalence.csv").open()))
    controls = list(csv.DictReader((review / "m3ot_preprocessing_control.csv").open()))
    checks.extend([
        {
            "check": "requested_contrast_row_counts",
            "passed": len(requested_rows) == 2212 and len(requested_summary) == 98,
            "observed": {"per_sequence": len(requested_rows), "summary": len(requested_summary)},
            "expected": {"per_sequence": 2212, "summary": 98},
        },
        {
            "check": "V_off_cached_equivalence",
            "passed": (
                len(equivalence) == 1630
                and all(row["selected_pairs_identical"] == "True" for row in equivalence)
            ),
            "observed": {
                "instances": len(equivalence),
                "identical": sum(row["selected_pairs_identical"] == "True" for row in equivalence),
            },
            "expected": {"instances": 1630, "identical": 1630},
        },
        {
            "check": "m3ot_crop_control_scope",
            "passed": (
                len(controls) == 3
                and all(row["crop_admission_uses_gt"] == "False" for row in controls)
                and all(row["upstream_tracker_input"] == "oracle_box" for row in controls)
            ),
            "observed": {
                "rows": len(controls),
                "gt_free_crop_rows": sum(row["crop_admission_uses_gt"] == "False" for row in controls),
                "oracle_upstream_rows": sum(row["upstream_tracker_input"] == "oracle_box" for row in controls),
            },
            "expected": {"rows": 3, "gt_free_crop_rows": 3, "oracle_upstream_rows": 3},
        },
    ])
    primary_expected = {
        ("M3OT", "development", "hungarian_full_verifier"): 0.06709455808979925,
        ("M3OT", "development", "greedy_full_verifier"): 0.15228881125145577,
        ("M3OT", "held_out", "hungarian_full_verifier"): 0.9954699040613821,
        ("M3OT", "held_out", "greedy_full_verifier"): 0.0,
        ("MMOT", "oracle_aabb", "hungarian_full_verifier"): -0.20957878125533963,
        ("MMOT", "oracle_aabb", "greedy_full_verifier"): -0.15992642351573802,
        ("MMOT", "official_detector", "hungarian_full_verifier"): -0.06644832059660011,
        ("MMOT", "official_detector", "greedy_full_verifier"): -0.020323526493398324,
    }
    summary_lookup = {
        (row["dataset"], row["protocol"], row["contrast"]): float(row["mean_delta_IDF1_pp"])
        for row in requested_summary if row["tracker"] == "all_trackers_sequence_mean"
    }
    checks.append({
        "check": "primary_strong_linker_deltas",
        "passed": all(
            key in summary_lookup and abs(summary_lookup[key] - expected) <= 1e-12
            for key, expected in primary_expected.items()
        ),
        "observed": {"|".join(key): summary_lookup.get(key) for key in primary_expected},
        "expected": {"|".join(key): value for key, value in primary_expected.items()},
    })
    generated_table = review / "paper_table_ace_v_strong_linker.tex"
    manuscript_table = PAPER_ROOT / "ivc_tables/temporal/ace_v_strong_linker.tex"
    checks.append({
        "check": "generated_table_matches_manuscript",
        "passed": (
            manuscript_table.is_file()
            and digest(generated_table) == digest(manuscript_table)
        ),
        "observed": digest(manuscript_table) if manuscript_table.is_file() else None,
        "expected": digest(generated_table),
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
