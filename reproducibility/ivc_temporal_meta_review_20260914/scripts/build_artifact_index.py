#!/usr/bin/env python3
"""Build a compact SHA-256 index for the meta-review delivery artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


EXPLICIT_PATHS = [
    "README.md",
    "requirements-audit.txt",
    "experiment_inventory.md",
    "experiment_report.md",
    "paper_verification.json",
    "results_raw/e0/e0_execution_manifest.json",
    "results_raw/e0/channel_audit.json",
    "results_raw/e0/evaluator_sanity_tests.json",
    "results_raw/e0/tracker_runtime_configs.json",
    "results_raw/e0/input_manifest.csv",
    "results_raw/e0/stage_counts.csv",
    "results_raw/e1_direct_12_v1/manifest.json",
    "results_raw/e1_direct_full50_v2_equal/manifest.json",
    "results_raw/derived/e1_direct_full50_v2_equal/legacy12_exact_equivalence.json",
    "results_raw/e1_direct_full50_v2_equal/results/linker_comparison_aggregate.csv",
    "results_raw/e1_direct_full50_v2_equal/results/temporal_ablation.csv",
    "results_raw/e1_full50_download/manifest.json",
    "results_raw/e1_full50_split/manifest.json",
    "results_raw/e1_giao_availability/manifest.json",
    "results_raw/e3_detector_full50_v1/detector_checkpoint_manifest.json",
    "results_raw/e3_temporal_full50_v2_equal/manifest.json",
    "results_raw/derived/e3_temporal_full50_v2_equal/legacy12_exact_equivalence.json",
    "results_raw/e3_temporal_full50_v2_equal/results/detector_input_temporal_results.csv",
    "results_raw/derived/e1_direct_full50_v2_equal/paired_sequence_summary.csv",
    "results_raw/derived/e3_temporal_full50_v2_equal/paired_sequence_summary.csv",
    "results_raw/e2_error_coverage_direct_full50_v1/manifest.json",
    "results_raw/e2_error_coverage_direct_full50_v1/link_error_coverage.csv",
    "results_raw/e2_error_coverage_direct_full50_v1/trajectory_error_coverage_aggregate.csv",
    "results_raw/e2_m3ot_failure_attempt2/manifest.json",
    "results_raw/e2_m3ot_failure_attempt2/m3ot_sequence_diagnostics.csv",
    "results_raw/e2_m3ot_failure_attempt2/m3ot_failure_links.csv",
    "results_raw/derived/e1_direct_full50_v2_equal_sizes/native_box_size_distribution.csv",
    "results_raw/derived/e1_direct_full50_v2_equal_sizes/size_stratified_link_audit.csv",
    "results_raw/e2_runtime_reid_full50_v1/manifest.json",
    "results_raw/e2_runtime_reid_full50_v1/reid_runtime_summary.csv",
    "results_raw/e2_runtime_graph_full50_v1/manifest.json",
    "results_raw/e2_runtime_graph_full50_v1/graph_runtime_summary.csv",
    "results_raw/paper_ready/manifest.json",
    "results_raw/paper_ready/key_numbers.json",
    "evidence/temporal_pipeline/manifest.json",
    "evidence/temporal_pipeline/temporal_refinement_pipeline.pdf",
    "evidence/error_coverage_full50/manifest.json",
    "evidence/error_coverage_full50/mmot_error_coverage.pdf",
    "evidence/temporal_link_examples_full50/manifest.json",
    "evidence/temporal_link_examples_full50/temporal_link_success_failure.pdf",
    "evidence/paper_after_A/main_A_20260914.pdf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("artifact_index.json"))
    args = parser.parse_args()
    root = args.root.resolve()

    paths = list(EXPLICIT_PATHS)
    paths.extend(
        str(path.relative_to(root))
        for path in sorted((root / "results_raw/paper_ready").glob("table_*.*"))
    )
    paths.extend(
        str(path.relative_to(root)) for path in sorted((root / "scripts").glob("*.py"))
        if path.is_file()
    )
    paths.extend(
        str(path.relative_to(root)) for path in sorted((root / "logs").glob("*"))
        if path.is_file()
    )

    files = {}
    missing = []
    for relative in sorted(set(paths)):
        path = root / relative
        if not path.is_file():
            missing.append(relative)
            continue
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256(path)}

    payload = {
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "root_policy": "Paths are repository-relative; raw datasets and model weights are not duplicated.",
        "file_count": len(files),
        "files": files,
        "missing": missing,
    }
    output = args.output if args.output.is_absolute() else root / args.output
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "files": len(files), "missing": missing}, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
