#!/usr/bin/env python3
"""Build the professor-review evidence pack from immutable ACE-V result CSVs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


ACE_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_COMMIT = "9cd5fb8c319e40cb3f25b469f0bf8dbb8e63bc0b"
BOOTSTRAP_SEED = 20260915
BOOTSTRAP_RESAMPLES = 10000
CONFIGURABLE_M3OT_METHODS = {
    "cost_h_margin_reassign",
    "cost_h_motion_reassign",
    "cost_h_full_postfilter",
    "cost_h_full_reassign",
    "path_g_full_reassign",
}
CONTRASTS = (
    (
        "hungarian_full_verifier",
        "cost_h_full_reassign",
        "cost_h",
        "Hungarian + full verifier/reassignment minus Hungarian",
    ),
    (
        "greedy_full_verifier",
        "path_g_full_reassign",
        "path_g",
        "Path-constrained greedy + same full verifier/reassignment minus greedy",
    ),
    (
        "margin_only",
        "cost_h_margin_reassign",
        "cost_h",
        "Hungarian + margin-only verifier/reassignment minus Hungarian",
    ),
    (
        "motion_only",
        "cost_h_motion_reassign",
        "cost_h",
        "Hungarian + motion-only verifier/reassignment minus Hungarian",
    ),
    (
        "same_cue_cost_only",
        "cost_h_soft_information",
        "cost_h",
        "Hungarian + same-cue soft cost minus Hungarian",
    ),
    (
        "post_filter_only",
        "cost_h_full_postfilter",
        "cost_h",
        "Hungarian + full verifier post-filter minus Hungarian",
    ),
    (
        "reassignment_after_verification",
        "cost_h_full_reassign",
        "cost_h_full_postfilter",
        "Verification followed by reassignment minus post-filter only",
    ),
)
METRICS = ("HOTA", "AssA", "IDF1", "IDSW")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing to write an empty CSV: {path}")
    fields = list(rows[0])
    if any(set(row) != set(fields) for row in rows):
        raise ValueError(f"nonuniform CSV fields: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_core(path: Path):
    spec = importlib.util.spec_from_file_location("ace_v_review_core", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selected_m3ot_rows(path: Path, tau_a: float, tau_m: float) -> list[dict]:
    rows = read_csv(path)
    selected = []
    for row in rows:
        if row["method"] not in CONFIGURABLE_M3OT_METHODS:
            selected.append(row)
            continue
        if float(row["tau_a"]) == tau_a and float(row["tau_m"]) == tau_m:
            selected.append(row)
    return selected


def accepted_count(row: dict) -> int:
    if row.get("accepted_links") not in (None, ""):
        return int(row["accepted_links"])
    return sum(int(row[name]) for name in ("accepted_correct", "accepted_false", "accepted_unknown"))


def pair_rows(
    rows: list[dict],
    dataset: str,
    protocol_field: str,
    selected_tau_a: float,
    selected_tau_m: float,
) -> list[dict]:
    key = lambda row: (
        row[protocol_field], row["sequence"], row["tracker"], row["method"]
    )
    lookup = {key(row): row for row in rows}
    if len(lookup) != len(rows):
        raise ValueError(f"duplicate selected rows in {dataset}")
    output = []
    for protocol in sorted({row[protocol_field] for row in rows}):
        sequences = sorted({row["sequence"] for row in rows if row[protocol_field] == protocol})
        trackers = sorted({row["tracker"] for row in rows if row[protocol_field] == protocol})
        for contrast, treatment, baseline, description in CONTRASTS:
            for sequence in sequences:
                for tracker in trackers:
                    base = lookup.get((protocol, sequence, tracker, baseline))
                    treated = lookup.get((protocol, sequence, tracker, treatment))
                    if base is None or treated is None:
                        raise KeyError(
                            f"missing {dataset}/{protocol}/{sequence}/{tracker}: "
                            f"{baseline} or {treatment}"
                        )
                    row = {
                        "dataset": dataset,
                        "protocol": protocol,
                        "data_role": (
                            "development"
                            if dataset == "M3OT" and protocol == "development"
                            else "exposed_exploratory_retest"
                        ),
                        "sequence": sequence,
                        "tracker": tracker,
                        "contrast": contrast,
                        "description": description,
                        "baseline": baseline,
                        "treatment": treatment,
                        "tau_a": selected_tau_a,
                        "tau_m": selected_tau_m,
                        "gt_used_by_linker_or_verifier": False,
                        "gt_use": (
                            "oracle tracker input plus metrics/post-hoc edge labels; "
                            "not crop admission, candidates, solver, or verifier"
                            if dataset == "M3OT"
                            else "metrics and post-hoc edge labels only"
                        ),
                    }
                    for metric in METRICS:
                        caster = int if metric == "IDSW" else float
                        baseline_value = caster(base[metric])
                        treatment_value = caster(treated[metric])
                        row[f"baseline_{metric}"] = baseline_value
                        row[f"treatment_{metric}"] = treatment_value
                        row[f"delta_{metric}"] = treatment_value - baseline_value
                    for prefix, value in (("baseline", base), ("treatment", treated)):
                        row[f"{prefix}_accepted_links"] = accepted_count(value)
                        for label in ("correct", "false", "unknown"):
                            row[f"{prefix}_accepted_{label}"] = int(value[f"accepted_{label}"])
                    output.append(row)
    return output


def bootstrap_interval(values: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_RESAMPLES, dtype=float)
    for index in range(BOOTSTRAP_RESAMPLES):
        means[index] = float(np.mean(values[rng.integers(0, len(values), len(values))]))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def conditional_error(correct: int, false: int) -> float | str:
    return false / (correct + false) if correct + false else "N/A"


def auditable_fraction(correct: int, false: int, unknown: int) -> float | str:
    total = correct + false + unknown
    return (correct + false) / total if total else "N/A"


def summary_row(values: list[dict], tracker: str) -> dict:
    by_sequence: dict[str, list[dict]] = defaultdict(list)
    for row in values:
        by_sequence[row["sequence"]].append(row)
    expected_trackers = {row["tracker"] for row in values}
    if tracker != "all_trackers_sequence_mean" and expected_trackers != {tracker}:
        raise ValueError("unexpected tracker grouping")
    sequence_deltas = {
        metric: np.asarray([
            np.mean([float(row[f"delta_{metric}"]) for row in rows])
            for _, rows in sorted(by_sequence.items())
        ])
        for metric in ("HOTA", "AssA", "IDF1")
    }
    low, high = bootstrap_interval(sequence_deltas["IDF1"])
    base_counts = {
        label: sum(int(row[f"baseline_accepted_{label}"]) for row in values)
        for label in ("correct", "false", "unknown")
    }
    treatment_counts = {
        label: sum(int(row[f"treatment_accepted_{label}"]) for row in values)
        for label in ("correct", "false", "unknown")
    }
    idf1 = sequence_deltas["IDF1"]
    first = values[0]
    return {
        "dataset": first["dataset"],
        "protocol": first["protocol"],
        "data_role": first["data_role"],
        "tracker": tracker,
        "contrast": first["contrast"],
        "description": first["description"],
        "baseline": first["baseline"],
        "treatment": first["treatment"],
        "sequence_count": len(by_sequence),
        "tracker_count": len(expected_trackers),
        "mean_delta_HOTA_pp": float(np.mean(sequence_deltas["HOTA"])),
        "mean_delta_AssA_pp": float(np.mean(sequence_deltas["AssA"])),
        "mean_delta_IDF1_pp": float(np.mean(idf1)),
        "IDF1_bootstrap_95_low_pp": low,
        "IDF1_bootstrap_95_high_pp": high,
        "improved_sequences": int(np.sum(idf1 > 1e-12)),
        "tied_sequences": int(np.sum(np.abs(idf1) <= 1e-12)),
        "worsened_sequences": int(np.sum(idf1 < -1e-12)),
        "baseline_IDSW_total": sum(int(row["baseline_IDSW"]) for row in values),
        "treatment_IDSW_total": sum(int(row["treatment_IDSW"]) for row in values),
        "delta_IDSW_total": sum(int(row["delta_IDSW"]) for row in values),
        "baseline_accepted_links": sum(base_counts.values()),
        "treatment_accepted_links": sum(treatment_counts.values()),
        "baseline_conditional_link_error": conditional_error(
            base_counts["correct"], base_counts["false"]
        ),
        "treatment_conditional_link_error": conditional_error(
            treatment_counts["correct"], treatment_counts["false"]
        ),
        "baseline_auditable_fraction": auditable_fraction(**base_counts),
        "treatment_auditable_fraction": auditable_fraction(**treatment_counts),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "fresh_confirmation": False,
    }


def summarize(paired: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in paired:
        groups[(row["dataset"], row["protocol"], row["contrast"], row["tracker"])].append(row)
    output = [summary_row(values, key[3]) for key, values in sorted(groups.items())]
    all_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in paired:
        all_groups[(row["dataset"], row["protocol"], row["contrast"])].append(row)
    output.extend(
        summary_row(values, "all_trackers_sequence_mean")
        for _, values in sorted(all_groups.items())
    )
    return sorted(
        output,
        key=lambda row: (
            row["dataset"], row["protocol"], row["contrast"], row["tracker"]
        ),
    )


def equivalence_rows(core, path: Path, dataset: str) -> list[dict]:
    rows = read_csv(path)
    for row in rows:
        row["motion_available"] = row["motion_available"] == "True"
        row["competition_ambiguity"] = float(row["competition_ambiguity"])
        row["motion_residual"] = (
            float(row["motion_residual"]) if row["motion_residual"] else None
        )
    group_fields = (
        ("protocol", "family", "sequence", "class_name", "tracker")
        if dataset == "MMOT"
        else ("split", "sequence", "modality", "tracker")
    )
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in group_fields)].append(row)
    output = []
    for key, features in sorted(groups.items()):
        off = core.filter_edges(features, "V_off", 0.0, 0.0)
        for solver_name, solver in (
            ("controlled_partial_hungarian", core.partial_hungarian),
            ("path_constrained_greedy", core.path_constrained_greedy),
        ):
            base_pairs = [core.pair(edge) for edge in solver(features)]
            off_pairs = [core.pair(edge) for edge in solver(off)]
            metadata = dict(zip(group_fields, key))
            output.append({
                "dataset": dataset,
                "protocol": metadata.get("protocol", metadata.get("split")),
                "family": metadata.get("family", "N/A"),
                "sequence": metadata["sequence"],
                "class_or_modality": metadata.get("class_name", metadata.get("modality")),
                "tracker": metadata["tracker"],
                "solver": solver_name,
                "candidate_edges": len(features),
                "baseline_selected_edges": len(base_pairs),
                "V_off_selected_edges": len(off_pairs),
                "selected_pairs_identical": base_pairs == off_pairs,
            })
    return output


def m3ot_control_summary(path: Path) -> list[dict]:
    rows = read_csv(path)
    if any(row["crop_admission_uses_gt"] != "False" for row in rows):
        raise AssertionError("M3OT direct-crop diagnostic contains GT crop admission")
    output = []
    for split in ("development", "held_out", "all"):
        values = rows if split == "all" else [row for row in rows if row["split"] == split]
        total_tracklets = sum(int(row["tracklets_total"]) for row in values)
        cropped_tracklets = sum(int(row["tracklets_with_direct_crops"]) for row in values)
        output.append({
            "split": split,
            "sequence_tracker_cases": len(values),
            "tracker_observations": sum(int(row["tracker_observations"]) for row in values),
            "admitted_direct_tracker_boxes": sum(
                int(row["admitted_direct_tracker_boxes"]) for row in values
            ),
            "tracklets_total": total_tracklets,
            "tracklets_with_direct_crops": cropped_tracklets,
            "direct_crop_tracklet_coverage": (
                cropped_tracklets / total_tracklets if total_tracklets else "N/A"
            ),
            "crop_admission_uses_gt": False,
            "upstream_tracker_input": "oracle_box",
            "scope_note": (
                "Crop admission and descriptors use tracker boxes only; the upstream "
                "M3OT tracker run still uses oracle-box detections."
            ),
        })
    return output


def status_rows() -> list[dict]:
    common = {
        "status": "완료",
        "implementation_commit": EXPERIMENT_COMMIT,
        "config": "reproducibility/ace_v_pilot_20260915/protocol_freeze.yaml",
        "historical_job_id": "not_persisted",
        "historical_stdout_stderr_log": "not_persisted",
        "currently_running": False,
    }
    mmot_csv = (
        "reproducibility/ace_v_pilot_20260915/results_raw/mmot_full50_v1/"
        "hybrid_results_per_sequence.csv"
    )
    m3ot_csv = (
        "reproducibility/ace_v_pilot_20260915/results_raw/m3ot_direct_crop_v1/"
        "hybrid_results_per_sequence.csv"
    )
    return [
        {
            "item": "Hungarian alone vs Hungarian + evidence verifier",
            **common,
            "methods": "cost_h vs cost_h_full_reassign",
            "code": "scripts/ace_v_core.py; scripts/run_ace_v_mmot.py; scripts/run_ace_v_m3ot.py",
            "result_csv": f"{mmot_csv}; {m3ot_csv}",
            "execution_manifest": "results_raw/mmot_full50_v1/manifest.json; results_raw/m3ot_direct_crop_v1/manifest.json",
            "scope_note": "Same cached candidates and controlled cost; GT is evaluation/post-hoc only.",
        },
        {
            "item": "Geometry+ReID greedy alone vs greedy + identical verifier",
            **common,
            "methods": "path_g vs path_g_full_reassign",
            "code": "scripts/ace_v_core.py; scripts/run_ace_v_mmot.py; scripts/run_ace_v_m3ot.py",
            "result_csv": f"{mmot_csv}; {m3ot_csv}",
            "execution_manifest": "results_raw/mmot_full50_v1/manifest.json; results_raw/m3ot_direct_crop_v1/manifest.json",
            "scope_note": "Path-constrained Geometry+ReID greedy receives the same V_full gate.",
        },
        {
            "item": "Margin-only / motion-only / same-cue cost-only controls",
            **common,
            "methods": "cost_h_margin_reassign; cost_h_motion_reassign; cost_h_soft_information",
            "code": "scripts/ace_v_core.py; scripts/run_ace_v_mmot.py; scripts/run_ace_v_m3ot.py",
            "result_csv": f"{mmot_csv}; {m3ot_csv}",
            "execution_manifest": "results_raw/mmot_full50_v1/manifest.json; results_raw/m3ot_direct_crop_v1/manifest.json",
            "scope_note": "The soft-cost control uses the same margin and motion information.",
        },
        {
            "item": "Post-filter-only vs verification followed by reassignment",
            **common,
            "methods": "cost_h_full_postfilter vs cost_h_full_reassign",
            "code": "scripts/run_ace_v_mmot.py; scripts/run_ace_v_m3ot.py",
            "result_csv": f"{mmot_csv}; {m3ot_csv}",
            "execution_manifest": "results_raw/mmot_full50_v1/manifest.json; results_raw/m3ot_direct_crop_v1/manifest.json",
            "scope_note": "Same selected tau_a=0.10 and tau_m=4.0; only reassignment differs.",
        },
        {
            "item": "M3OT direct tracker-box crop control",
            **common,
            "methods": "direct tracker-box ReID descriptor extraction",
            "code": "scripts/run_ace_v_m3ot.py",
            "result_csv": "results_raw/m3ot_direct_crop_v1/m3ot_direct_crop_diagnostic.csv",
            "execution_manifest": "results_raw/m3ot_direct_crop_v1/manifest.json",
            "scope_note": "Crop admission is GT-free, but the upstream M3OT tracker detections are oracle boxes.",
        },
    ]


def build_component_markdown(output_dir: Path, summary: list[dict]) -> None:
    labels = (
        ("M3OT", "development", "M3OT development"),
        ("M3OT", "held_out", "M3OT exposed held-out"),
        ("MMOT", "oracle_aabb", "MMOT oracle AABB"),
        ("MMOT", "official_detector", "MMOT official detector"),
    )
    contrast_labels = {
        "hungarian_full_verifier": "H+full-V reassign - H",
        "greedy_full_verifier": "G+full-V reassign - G",
        "margin_only": "H+margin-only - H",
        "motion_only": "H+motion-only - H",
        "same_cue_cost_only": "H+same-cue soft cost - H",
        "post_filter_only": "H+post-filter - H",
        "reassignment_after_verification": "reassign - post-filter",
    }
    lookup = {
        (row["dataset"], row["protocol"], row["contrast"]): row
        for row in summary if row["tracker"] == "all_trackers_sequence_mean"
    }
    lines = [
        "# Strong-linker and component comparison",
        "",
        "All cells are equal-sequence mean IDF1 changes in percentage points. MMOT and M3OT held-out are exposed exploratory retests.",
        "",
        "| Contrast | M3OT dev | M3OT held-out | MMOT oracle | MMOT detector |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for contrast, label in contrast_labels.items():
        values = [float(lookup[(dataset, protocol, contrast)]["mean_delta_IDF1_pp"]) for dataset, protocol, _ in labels]
        lines.append(
            f"| {label} | " + " | ".join(f"{value:+.3f}" for value in values) + " |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- The full verifier fails the required replication: both strong-linker contrasts worsen on MMOT.",
        "- Motion-only is the least harmful control on MMOT, but its IDF1 confidence intervals include zero and ID switches increase in the all-tracker totals.",
        "- Reassignment is consistently better than post-filtering on MMOT, yet full reassignment still remains below the corresponding standalone Hungarian baseline.",
        "- M3OT held-out gains occur in one of four sequences and were observed after that split had already been inspected; they are not independent confirmation.",
        "- No treatment is promoted to a manuscript method or selected post hoc from these exposed rows.",
    ])
    (output_dir / "component_comparison_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_latex_table(output_dir: Path, summary: list[dict]) -> None:
    lookup = {
        (row["dataset"], row["protocol"], row["contrast"]): row
        for row in summary if row["tracker"] == "all_trackers_sequence_mean"
    }
    settings = (
        ("M3OT development", "M3OT", "development"),
        ("M3OT held-out", "M3OT", "held_out"),
        ("MMOT oracle AABB", "MMOT", "oracle_aabb"),
        ("MMOT official detector", "MMOT", "official_detector"),
    )
    lines = [
        "\\begin{tabular}{lrr}",
        "\\toprule",
        "Input & H+V $-$ H & G+V $-$ G \\\\",
        "\\midrule",
    ]
    for label, dataset, protocol in settings:
        h_value = float(lookup[(dataset, protocol, "hungarian_full_verifier")]["mean_delta_IDF1_pp"])
        g_value = float(lookup[(dataset, protocol, "greedy_full_verifier")]["mean_delta_IDF1_pp"])
        lines.append(f"{label} & ${h_value:+.3f}$ & ${g_value:+.3f}$ \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    (output_dir / "paper_table_ace_v_strong_linker.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_status_markdown(output_dir: Path, summary: list[dict], equivalence: list[dict]) -> None:
    def result(dataset: str, protocol: str, contrast: str) -> dict:
        return next(
            row for row in summary
            if row["dataset"] == dataset and row["protocol"] == protocol
            and row["contrast"] == contrast
            and row["tracker"] == "all_trackers_sequence_mean"
        )

    primary_rows = [
        ("M3OT development", result("M3OT", "development", "hungarian_full_verifier"), result("M3OT", "development", "greedy_full_verifier")),
        ("M3OT exposed held-out", result("M3OT", "held_out", "hungarian_full_verifier"), result("M3OT", "held_out", "greedy_full_verifier")),
        ("MMOT oracle AABB", result("MMOT", "oracle_aabb", "hungarian_full_verifier"), result("MMOT", "oracle_aabb", "greedy_full_verifier")),
        ("MMOT official detector", result("MMOT", "official_detector", "hungarian_full_verifier"), result("MMOT", "official_detector", "greedy_full_verifier")),
    ]
    lines = [
        "# Professor-review experiment status",
        "",
        "Generated from committed result CSVs without rerunning the experiment or changing the manuscript.",
        "",
        "## Status",
        "",
        "| Requested item | Status | Evidence |",
        "| --- | --- | --- |",
        "| Hungarian alone vs Hungarian + evidence verifier | 완료 | `cost_h` vs `cost_h_full_reassign` |",
        "| Geometry+ReID greedy alone vs greedy + same verifier | 완료 | `path_g` vs `path_g_full_reassign` |",
        "| Margin-only / motion-only / same-cue cost-only | 완료 | Three component methods in per-sequence CSV |",
        "| Post-filter-only vs verification then reassignment | 완료 | `cost_h_full_postfilter` vs `cost_h_full_reassign` |",
        "| M3OT direct tracker-box crop control | 완료 (범위 제한) | Crop admission is GT-free; upstream detections remain oracle boxes |",
        "",
        f"Implementation commit: `{EXPERIMENT_COMMIT}`.",
        "Frozen config: `reproducibility/ace_v_pilot_20260915/protocol_freeze.yaml`.",
        "The historical shell command, scheduler job ID, and stdout/stderr log were not persisted. This is a provenance gap; no job is currently running. The COMPLETE manifests retain input/output hashes, runtime, environment, and selected configuration.",
        "Recorded runtime: MMOT 461.358 s; M3OT 175.341 s.",
        "",
        "## Primary result",
        "",
        "| Input | H+V - H IDF1 | G+V - G IDF1 |",
        "| --- | ---: | ---: |",
    ]
    for name, h_row, g_row in primary_rows:
        lines.append(
            f"| {name} | {float(h_row['mean_delta_IDF1_pp']):+.3f} pp | "
            f"{float(g_row['mean_delta_IDF1_pp']):+.3f} pp |"
        )
    lines.extend([
        "",
        "The verifier does not produce a solver-agnostic improvement: MMOT worsens for both primary contrasts, and M3OT held-out improves only for Hungarian while tying greedy. These are exposed exploratory retests, not fresh confirmation.",
        "",
        "## Base-off check",
        "",
        f"All {len(equivalence)} cached solver instances reproduced exactly with `V_off`: "
        f"{sum(row['selected_pairs_identical'] for row in equivalence)}/{len(equivalence)} identical.",
        "",
        "## Artifact map",
        "",
        "- Sequence-level requested contrasts: `requested_contrasts_per_sequence.csv`",
        "- Aggregate deltas and component comparisons: `requested_contrasts_summary.csv`",
        "- Readable component summary: `component_comparison_summary.md`",
        "- CSV-generated Appendix table: `paper_table_ace_v_strong_linker.tex`",
        "- Machine-readable five-item status table: `experiment_status.csv`",
        "- Verifier-off cached equivalence: `base_off_equivalence.csv`",
        "- M3OT crop-admission scope: `m3ot_preprocessing_control.csv`",
        "- Commands recoverable from manifest parameters: `reproduction_commands.md`",
        "- Review disposition: `professor_review_resolution.md`",
    ])
    (output_dir / "experiment_status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_commands_markdown(output_dir: Path) -> None:
    lines = [
        "# Reproduction commands",
        "",
        "The exact historical shell strings and scheduler IDs were not logged. The commands below are reconstructed from the COMPLETE manifests and current CLI contracts. They write to new directories and must not target the committed result directories.",
        "",
        "## M3OT development selection and exposed held-out retest",
        "",
        "```bash",
        "python reproducibility/ace_v_pilot_20260915/scripts/run_ace_v_m3ot.py \\",
        "  --workspace /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal \\",
        "  --diagnostic-script reproducibility/ivc_professor_review_20260914/scripts/run_m3ot_linker_diagnostic.py \\",
        "  --ace-core reproducibility/ace_v_pilot_20260915/scripts/ace_v_core.py \\",
        "  --development-manifest /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/val_development_manifest.json \\",
        "  --held-out-manifest /mnt/ssd2/meme_comparison/runs/accv2026_rebuttal/results/rebuttal_r3/m3ot_ambiguity_aware/test_final_manifest.json \\",
        "  --checkpoint /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal/assets/reid_r50_6e_mot17-4bf6b63d.pth \\",
        "  --device cpu --threads 8 \\",
        "  --output-dir reproducibility/ace_v_pilot_20260915/results_raw/rerun_m3ot_NEW",
        "```",
        "",
        "## MMOT exposed 50-sequence retest",
        "",
        "```bash",
        "python reproducibility/ace_v_pilot_20260915/scripts/run_ace_v_mmot.py \\",
        "  --benchmark-script reproducibility/ivc_temporal_meta_review_20260914/scripts/run_full50_linker_benchmark.py \\",
        "  --audit-script reproducibility/ivc_professor_review_20260914/scripts/run_cached_solver_audit.py \\",
        "  --ace-core reproducibility/ace_v_pilot_20260915/scripts/ace_v_core.py \\",
        "  --workspace /mnt/ssd2/meme_comparison/workspace/accv2026_rebuttal \\",
        "  --oracle-cache /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e1_direct_full50_v1 \\",
        "  --detector-cache /home/oem/projects/multi-uav-marine-city/outputs/experiments/ivc_temporal_meta_review_20260913/results_raw/e3_temporal_full50_v1 \\",
        "  --family-root legacy12 /mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav/raw/MMOT/extracted/test_meta_review_split/legacy12 \\",
        "  --family-root confirmation38 /mnt/ssd2/meme_comparison/data_cache/accv2026_rebuttal_real_uav/raw/MMOT/extracted/test_meta_review_split/confirmation38 \\",
        "  --selected-config reproducibility/ace_v_pilot_20260915/results_raw/m3ot_direct_crop_v1/selected_config.json \\",
        "  --output-dir reproducibility/ace_v_pilot_20260915/results_raw/rerun_mmot_NEW",
        "```",
        "",
        "## This review pack",
        "",
        "```bash",
        "python reproducibility/ace_v_pilot_20260915/scripts/build_review_response.py",
        "```",
    ]
    (output_dir / "reproduction_commands.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_resolution_markdown(output_dir: Path) -> None:
    lines = [
        "# Professor-review resolution",
        "",
        "| Review requirement | Disposition | Evidence |",
        "| --- | --- | --- |",
        "| H+V minus H on identical inputs | 해결 | Sequence and summary CSVs; result is mixed/negative |",
        "| Greedy+same verifier minus greedy | 해결 | Sequence and summary CSVs; no robust gain |",
        "| Same-information simple controls | 해결 | Margin-only, motion-only, and soft-cost contrasts |",
        "| Post-filter versus reassignment | 해결 | Direct contrast from committed per-sequence rows |",
        "| Verifier disabled reproduces base linker | 해결 | Cached pair-level equivalence for both solvers |",
        "| M3OT crop admission without GT | 부분해결 | Direct tracker-box crops are GT-free, but upstream tracker detections are oracle boxes |",
        "| Development/test separation | 해결 | M3OT development selects tau; held-out and MMOT are explicitly exposed retests |",
        "| Fresh independent confirmation | 미해결 | No unexposed dataset is available |",
        "| Solver-agnostic evidence-verifier advantage | 미해결 | Frozen success rule failed; negative results retained |",
        "| Manuscript performance claim/table | 미반영 | Evidence does not justify a new performance claim or table |",
        "",
        "No experiment row was removed because it was unfavorable. No threshold was selected on MMOT or M3OT held-out.",
    ]
    (output_dir / "professor_review_resolution.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ACE_ROOT / "results_raw/review_response_20260916",
    )
    args = parser.parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    mmot_dir = ACE_ROOT / "results_raw/mmot_full50_v1"
    m3ot_dir = ACE_ROOT / "results_raw/m3ot_direct_crop_v1"
    core_path = ACE_ROOT / "scripts/ace_v_core.py"
    selected = json.loads((m3ot_dir / "selected_config.json").read_text(encoding="utf-8"))
    tau_a, tau_m = float(selected["tau_a"]), float(selected["tau_m"])

    mmot_rows = read_csv(mmot_dir / "hybrid_results_per_sequence.csv")
    m3ot_rows = selected_m3ot_rows(
        m3ot_dir / "hybrid_results_per_sequence.csv", tau_a, tau_m
    )
    paired = pair_rows(mmot_rows, "MMOT", "protocol", tau_a, tau_m)
    paired.extend(pair_rows(m3ot_rows, "M3OT", "split", tau_a, tau_m))
    paired.sort(
        key=lambda row: (
            row["dataset"], row["protocol"], row["contrast"],
            row["sequence"], row["tracker"],
        )
    )
    summary = summarize(paired)

    core = load_core(core_path)
    equivalence = equivalence_rows(
        core, mmot_dir / "verification_features.csv", "MMOT"
    )
    equivalence.extend(
        equivalence_rows(core, m3ot_dir / "verification_features.csv", "M3OT")
    )
    equivalence.sort(
        key=lambda row: (
            row["dataset"], row["protocol"], row["sequence"],
            row["tracker"], row["solver"], row["class_or_modality"],
        )
    )
    if not all(row["selected_pairs_identical"] for row in equivalence):
        raise AssertionError("V_off failed to reproduce at least one base solver instance")

    controls = m3ot_control_summary(m3ot_dir / "m3ot_direct_crop_diagnostic.csv")
    statuses = status_rows()
    write_csv(output_dir / "requested_contrasts_per_sequence.csv", paired)
    write_csv(output_dir / "requested_contrasts_summary.csv", summary)
    write_csv(output_dir / "base_off_equivalence.csv", equivalence)
    write_csv(output_dir / "m3ot_preprocessing_control.csv", controls)
    write_csv(output_dir / "experiment_status.csv", statuses)
    build_status_markdown(output_dir, summary, equivalence)
    build_component_markdown(output_dir, summary)
    build_latex_table(output_dir, summary)
    build_commands_markdown(output_dir)
    build_resolution_markdown(output_dir)

    inputs = [
        ACE_ROOT / "protocol_freeze.yaml",
        core_path,
        mmot_dir / "hybrid_results_per_sequence.csv",
        mmot_dir / "verification_features.csv",
        mmot_dir / "manifest.json",
        m3ot_dir / "hybrid_results_per_sequence.csv",
        m3ot_dir / "verification_features.csv",
        m3ot_dir / "m3ot_direct_crop_diagnostic.csv",
        m3ot_dir / "selected_config.json",
        m3ot_dir / "manifest.json",
    ]
    outputs = sorted(path for path in output_dir.iterdir() if path.name != "manifest.json")
    manifest = {
        "status": "COMPLETE_POSTHOC_AUDIT",
        "experiment_commit": EXPERIMENT_COMMIT,
        "new_experiment_executed": False,
        "source_results_reused": True,
        "historical_stdout_log_available": False,
        "historical_scheduler_job_id_available": False,
        "selected_config": {"tau_a": tau_a, "tau_m": tau_m},
        "input_sha256": {str(path.relative_to(ACE_ROOT)): sha256(path) for path in inputs},
        "output_sha256": {path.name: sha256(path) for path in outputs},
        "row_counts": {
            "requested_contrasts_per_sequence": len(paired),
            "requested_contrasts_summary": len(summary),
            "base_off_equivalence": len(equivalence),
            "m3ot_preprocessing_control": len(controls),
            "experiment_status": len(statuses),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": manifest["status"],
        "paired_rows": len(paired),
        "summary_rows": len(summary),
        "base_off_instances": len(equivalence),
        "base_off_identical": sum(row["selected_pairs_identical"] for row in equivalence),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
