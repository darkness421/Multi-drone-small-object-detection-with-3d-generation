#!/usr/bin/env python3
"""Create a content-addressed inventory without copying frozen artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
ORIGINAL_REPO = Path("/home/oem/projects/multi-uav-marine-city")
FROZEN_SOURCE_COMMIT = "2a033849f1746604db774c95537f0400b5e513a2"
LEGACY_ROOT = Path(
    "/home/oem/projects/multi-uav-marine-city/outputs/experiments/"
    "ivc_temporal_meta_review_20260913"
)
MMOT_WORKSPACE = Path("/mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal")
MMOT_DATA = Path("/mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav")
M3OT_RUN = Path(
    "/mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/"
    "rebuttal_r3/m3ot_ambiguity_aware"
)
PAPER = Path(
    "/home/oem/projects/deepfake/Ourmethod/_checkpoint/meme_comparison/"
    "workspace/com3d_ace_ivc_overleaf_sync"
)
ACE_ROOT = REPO / "reproducibility/ace_v_pilot_20260915"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def file_record(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else None,
        "sha256": digest(path) if path.is_file() else None,
    }


def tree_record(path: Path) -> dict:
    tree_hash = hashlib.sha256()
    files = [] if not path.is_dir() else sorted(
        item for item in path.rglob("*")
        if item.is_file()
        and not (item.suffix == ".csv" and item.with_suffix(item.suffix + ".gz").is_file())
    )
    byte_count = 0
    suffixes: Counter[str] = Counter()
    trackers: Counter[str] = Counter()
    families: Counter[str] = Counter()
    for item in files:
        relative = item.relative_to(path).as_posix()
        item_digest = digest(item)
        item_size = item.stat().st_size
        tree_hash.update(f"{relative}\0{item_size}\0{item_digest}\n".encode("utf-8"))
        byte_count += item_size
        suffixes[item.suffix or "<none>"] += 1
        parts = item.relative_to(path).parts
        if len(parts) >= 2 and parts[0] in {"tracker_outputs", "descriptors"}:
            families[parts[1]] += 1
        if item.stem in {"bytetrack", "ocsort", "deepocsort"}:
            trackers[item.stem] += 1
    return {
        "path": str(path),
        "exists": path.is_dir(),
        "file_count": len(files),
        "bytes": byte_count,
        "sha256_tree": tree_hash.hexdigest() if path.is_dir() else None,
        "suffix_counts": dict(sorted(suffixes.items())),
        "family_file_counts": dict(sorted(families.items())),
        "tracker_file_counts": dict(sorted(trackers.items())),
    }


def command_output(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "reproducibility/ace_v_pilot_20260915/artifact_inventory.json",
    )
    args = parser.parse_args()

    oracle_cache = LEGACY_ROOT / "results_raw/e1_direct_full50_v1"
    detector_cache = LEGACY_ROOT / "results_raw/e3_temporal_full50_v1"
    oracle_results = LEGACY_ROOT / "results_raw/e1_direct_full50_v2_equal"
    detector_results = LEGACY_ROOT / "results_raw/e3_temporal_full50_v2_equal"
    solver_audit = REPO / (
        "reproducibility/ivc_professor_review_20260914/results_raw/"
        "mmot_cached_solver_audit_v1"
    )
    m3ot_diagnostic = REPO / (
        "reproducibility/ivc_professor_review_20260914/results_raw/"
        "m3ot_linker_diagnostic_v2"
    )
    m3ot_direct = ACE_ROOT / "results_raw/m3ot_direct_crop_v1"
    mmot_ace_v = ACE_ROOT / "results_raw/mmot_full50_v1"
    reid = MMOT_WORKSPACE / "assets/reid_r50_6e_mot17-4bf6b63d.pth"

    key_files = {
        "reid_checkpoint": reid,
        "mmot_evaluator_entrypoint": MMOT_WORKSPACE / "scripts/run_mmot_locked_temporal.py",
        "legacy_benchmark_script": REPO / (
            "reproducibility/ivc_temporal_meta_review_20260914/scripts/"
            "run_full50_linker_benchmark.py"
        ),
        "cached_solver_audit_script": REPO / (
            "reproducibility/ivc_professor_review_20260914/scripts/"
            "run_cached_solver_audit.py"
        ),
        "edge_decision_trace": solver_audit / "edge_decision_trace.csv",
        "solver_metrics": solver_audit / "solver_metrics_per_sequence.csv",
        "oracle_result_manifest": oracle_results / "manifest.json",
        "oracle_metrics": oracle_results / "results/linker_comparison_per_sequence.csv",
        "detector_result_manifest": detector_results / "manifest.json",
        "detector_metrics": detector_results / "results/detector_input_temporal_per_sequence.csv",
        "m3ot_development_manifest": M3OT_RUN / "val_development_manifest.json",
        "m3ot_held_out_manifest": M3OT_RUN / "test_final_manifest.json",
        "m3ot_historical_manifest": m3ot_diagnostic / "manifest.json",
        "paper_main": PAPER / "main.tex",
        "paper_bibliography": PAPER / "main.bib",
        "paper_introduction": PAPER / "ivc_sections/01_introduction.tex",
        "paper_related_work": PAPER / "ivc_sections/02_related_work.tex",
        "paper_limitations": PAPER / "ivc_sections/08_limitations.tex",
        "paper_appendix": PAPER / "ivc_sections/09_appendix.tex",
        "paper_ace_v_table": PAPER / "ivc_tables/temporal/ace_v_strong_linker.tex",
        "paper_pdf": PAPER / "main.pdf",
    }

    try:
        import numpy
        import scipy
        import torch

        scientific_environment = {
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "torch": torch.__version__,
            "cuda_available_now": torch.cuda.is_available(),
            "cuda_device_now": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except ImportError as error:
        scientific_environment = {"import_error": str(error)}

    payload = {
        "inventory_version": 1,
        "source": {
            "repository": str(ORIGINAL_REPO),
            "worktree": str(REPO),
            "frozen_base_commit": FROZEN_SOURCE_COMMIT,
            "branch": command_output(["git", "-C", str(REPO), "branch", "--show-current"]),
        },
        "paper_source": {
            "repository": str(PAPER),
            "commit": command_output(["git", "-C", str(PAPER), "rev-parse", "HEAD"]),
            "tracked_files_modified": bool(
                command_output([
                    "git", "-C", str(PAPER), "status", "--porcelain",
                    "--untracked-files=no",
                ])
            ),
        },
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            **scientific_environment,
            "recorded_original_cuda": {
                "torch": "2.9.1+cu128",
                "device": "NVIDIA GeForce RTX 5090",
                "available_during_cache_generation": True,
            },
        },
        "fixed_protocol": {
            "candidate": {
                "same_class": True,
                "strict_forward_time": True,
                "maximum_gap_frames": 30,
                "maximum_endpoint_center_distance_pixels": 55.0,
                "maximum_appearance_cosine_distance": 0.30,
            },
            "controlled_cost": "mean(dxy/55, dapp/0.30, gap/30)",
            "partial_hungarian_pair_null_cost": 1.0,
            "reid_checkpoint_sha256": digest(reid) if reid.is_file() else None,
        },
        "frozen_caches": {
            "mmot_oracle_aabb": tree_record(oracle_cache),
            "mmot_detector_input": tree_record(detector_cache),
            "mmot_oracle_results": tree_record(oracle_results),
            "mmot_detector_results": tree_record(detector_results),
            "mmot_cached_solver_audit": tree_record(solver_audit),
            "m3ot_historical_gt_admission_diagnostic": tree_record(m3ot_diagnostic),
            "m3ot_direct_tracker_crop": tree_record(m3ot_direct),
            "mmot_ace_v_exploratory_retest": tree_record(mmot_ace_v),
        },
        "data_roots": {
            "mmot": {"path": str(MMOT_DATA), "exists": MMOT_DATA.is_dir()},
            "m3ot": {
                "path": str(M3OT_RUN),
                "exists": M3OT_RUN.is_dir(),
                "development_role": "configuration_selection",
                "held_out_role": "exposed_exploratory_retest",
            },
        },
        "key_files": {name: file_record(path) for name, path in key_files.items()},
        "availability": {
            "direct_tracker_box_mmot_descriptors": True,
            "direct_tracker_box_m3ot_descriptors": (
                m3ot_direct / "verification_features.csv"
            ).is_file(),
            "direct_tracker_box_m3ot_action": (
                "generated_from_frozen_tracker_boxes_without_GT_crop_admission"
                if (m3ot_direct / "verification_features.csv").is_file()
                else "generate_from_frozen_tracker_boxes_without_GT_crop_admission"
            ),
            "fresh_independent_confirmation_set": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
