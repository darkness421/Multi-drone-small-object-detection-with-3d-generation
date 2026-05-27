"""Decide whether detector experiments are ready for the next project stage."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


DEFAULT_CANDIDATE_REGEX = r"(?i)(proposed|com3d|ace|wavelet|deformable|tiling|ours)"


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    parsed = as_float(value)
    return int(parsed) if parsed is not None else None


def read_rows(path: str | Path) -> list[dict[str, str]]:
    path = resolve_path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_name(row: dict[str, str]) -> str:
    return " ".join([row.get("method", ""), row.get("model", "")]).strip()


def is_candidate(row: dict[str, str], pattern: re.Pattern[str]) -> bool:
    return bool(pattern.search(row_name(row)))


def best_row(rows: list[dict[str, str]], metric: str) -> dict[str, str] | None:
    scored = [(value, row) for row in rows if (value := as_float(row.get(metric))) is not None]
    if not scored:
        return None
    return max(scored, key=lambda item: item[0])[1]


def is_lightweight(row: dict[str, str], max_params: float) -> bool:
    params = as_float(row.get("Params_mean"))
    if params is not None:
        return params <= max_params
    return (row.get("param_size_group") or row.get("size_group") or row.get("model_scale")) in {"nano", "small"}


def compact_row(row: dict[str, str] | None, metric: str, secondary_metric: str) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "method": row.get("method", ""),
        "model": row.get("model", ""),
        "detector_family": row.get("detector_family", ""),
        "model_version": row.get("model_version", ""),
        "model_scale": row.get("model_scale", ""),
        "param_size_group": row.get("param_size_group", ""),
        "seed_count": as_int(row.get("seed_count")),
        "analysis_level": row.get("analysis_level", ""),
        metric: as_float(row.get(metric)),
        secondary_metric: as_float(row.get(secondary_metric)),
        "Params_mean": as_float(row.get("Params_mean")),
        "GFLOPs_mean": as_float(row.get("GFLOPs_mean")),
    }


def metric_value(row: dict[str, str] | None, metric: str) -> float | None:
    if row is None:
        return None
    return as_float(row.get(metric))


def candidate_gap(
    candidate: dict[str, str] | None,
    baseline: dict[str, str] | None,
    metric: str,
    secondary_metric: str,
) -> dict[str, Any] | None:
    if candidate is None or baseline is None:
        return None
    candidate_metric = metric_value(candidate, metric)
    baseline_metric = metric_value(baseline, metric)
    candidate_secondary = metric_value(candidate, secondary_metric)
    baseline_secondary = metric_value(baseline, secondary_metric)
    return {
        "baseline_method": baseline.get("method", "") or baseline.get("model", ""),
        "candidate_method": candidate.get("method", "") or candidate.get("model", ""),
        f"{metric}_delta": None if candidate_metric is None or baseline_metric is None else candidate_metric - baseline_metric,
        f"{secondary_metric}_delta": None
        if candidate_secondary is None or baseline_secondary is None
        else candidate_secondary - baseline_secondary,
    }


def decide_stage(
    rows: list[dict[str, str]],
    candidate_regex: str,
    metric: str,
    secondary_metric: str,
    lightweight_max_params: float,
    min_delta: float,
    require_main: bool,
) -> dict[str, Any]:
    pattern = re.compile(candidate_regex)
    completed = [row for row in rows if row.get("analysis_level") and as_float(row.get(metric)) is not None]
    baseline_rows = [row for row in completed if not is_candidate(row, pattern)]
    candidate_rows = [row for row in completed if is_candidate(row, pattern)]

    if require_main:
        baseline_rows = [row for row in baseline_rows if row.get("analysis_level") == "main"]
        candidate_rows = [row for row in candidate_rows if row.get("analysis_level") == "main"]

    best_baseline = best_row(baseline_rows, metric)
    lightweight_rows = [row for row in baseline_rows if is_lightweight(row, lightweight_max_params)]
    best_lightweight = best_row(lightweight_rows, metric)
    best_candidate = best_row(candidate_rows, metric)

    baseline_thresholds = [value for value in [metric_value(best_baseline, metric), metric_value(best_lightweight, metric)] if value is not None]
    candidate_metric = metric_value(best_candidate, metric)
    has_candidate_win = bool(baseline_thresholds) and candidate_metric is not None and all(candidate_metric >= value + min_delta for value in baseline_thresholds)

    if not baseline_rows:
        next_stage = "run_baseline_sweep"
        rationale = "No completed baseline summary rows were found."
    elif not candidate_rows:
        next_stage = "finish_baselines_then_build_proposed"
        rationale = "Baseline/comparison models are being established; proposed detector rows are not present yet."
    elif has_candidate_win:
        next_stage = "proceed_to_3d_benchmark"
        rationale = "The best proposed detector meets or exceeds the best overall and best lightweight baselines."
    else:
        next_stage = "iterate_proposed_detector"
        rationale = "The proposed detector does not yet beat the selected baseline thresholds."

    return {
        "metric": metric,
        "secondary_metric": secondary_metric,
        "candidate_regex": candidate_regex,
        "lightweight_max_params": lightweight_max_params,
        "min_delta": min_delta,
        "require_main": require_main,
        "baseline_count": len(baseline_rows),
        "candidate_count": len(candidate_rows),
        "best_overall_baseline": compact_row(best_baseline, metric, secondary_metric),
        "best_lightweight_baseline": compact_row(best_lightweight, metric, secondary_metric),
        "best_proposed_candidate": compact_row(best_candidate, metric, secondary_metric),
        "candidate_vs_best_overall": candidate_gap(best_candidate, best_baseline, metric, secondary_metric),
        "candidate_vs_best_lightweight": candidate_gap(best_candidate, best_lightweight, metric, secondary_metric),
        "recommended_next_stage": next_stage,
        "rationale": rationale,
    }


def format_model_cells(row: dict[str, Any] | None, metric: str, secondary_metric: str) -> str:
    if row is None:
        return "n/a | n/a | n/a | n/a | n/a | n/a | n/a"
    return (
        f"{row.get('method') or 'n/a'} | {row.get('detector_family') or 'n/a'} | "
        f"{row.get('model_version') or 'n/a'} | {row.get('param_size_group') or row.get('model_scale') or 'n/a'} | "
        f"{row.get('seed_count') or 'n/a'} | {row.get(metric) if row.get(metric) is not None else 'n/a'} | "
        f"{row.get(secondary_metric) if row.get(secondary_metric) is not None else 'n/a'}"
    )


def write_markdown(path: Path, decision: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metric = str(decision["metric"])
    secondary_metric = str(decision["secondary_metric"])
    lines = [
        "# Detector Stage Gate",
        "",
        f"Recommended next stage: `{decision['recommended_next_stage']}`",
        "",
        decision["rationale"],
        "",
        "## Selection",
        "",
        f"- Primary metric: `{metric}`",
        f"- Secondary metric: `{secondary_metric}`",
        f"- Dataset filter: `{decision.get('dataset') or 'all'}`",
        f"- Baseline rows: `{decision['baseline_count']}`",
        f"- Proposed/candidate rows: `{decision['candidate_count']}`",
        f"- Lightweight threshold: `{decision['lightweight_max_params']}` params",
        f"- Minimum required delta: `{decision['min_delta']}`",
        "",
        "| Role | Method | Family | Version | Size | Seeds | Primary | Secondary |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| Best overall baseline | {format_model_cells(decision['best_overall_baseline'], metric, secondary_metric)} |",
        f"| Best lightweight baseline | {format_model_cells(decision['best_lightweight_baseline'], metric, secondary_metric)} |",
        f"| Best proposed candidate | {format_model_cells(decision['best_proposed_candidate'], metric, secondary_metric)} |",
        "",
        "## Gate Gaps",
        "",
        format_gap_table(decision, metric, secondary_metric),
        "",
        "## Interpretation",
        "",
        "- If the recommended stage is `finish_baselines_then_build_proposed`, complete all baseline and comparison sweeps before changing the proposed detector.",
        "- If the recommended stage is `iterate_proposed_detector`, continue ablations on wavelet stem, partial deformable neck, and tiling inference.",
        "- If the recommended stage is `proceed_to_3d_benchmark`, freeze the detector choice and start Marine City multi-angle benchmark and 3D generation experiments.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def format_gap(value: Any) -> str:
    parsed = as_float(value)
    if parsed is None:
        return "n/a"
    return f"{parsed:+.4f}"


def format_gap_table(decision: dict[str, Any], metric: str, secondary_metric: str) -> str:
    rows = []
    for label, key in [
        ("Best overall baseline", "candidate_vs_best_overall"),
        ("Best lightweight baseline", "candidate_vs_best_lightweight"),
    ]:
        gap = decision.get(key)
        if not gap:
            continue
        rows.append(
            "| "
            + " | ".join(
                [
                    label,
                    str(gap.get("baseline_method") or "n/a"),
                    str(gap.get("candidate_method") or "n/a"),
                    format_gap(gap.get(f"{metric}_delta")),
                    format_gap(gap.get(f"{secondary_metric}_delta")),
                ]
            )
            + " |"
        )
    if not rows:
        return "_No proposed candidate gap is available yet._"
    return "\n".join(
        [
            "| Threshold | Baseline | Candidate | Primary Delta | Secondary Delta |",
            "| --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def write_json(path: Path, decision: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether detector experiments are ready for the next stage.")
    parser.add_argument("--summary-csv", default="outputs/experiments/server_baseline_summary.csv")
    parser.add_argument("--dataset", default=None, help="Optional dataset filter for the stage gate.")
    parser.add_argument("--candidate-regex", default=DEFAULT_CANDIDATE_REGEX)
    parser.add_argument("--metric", default="best_AP_mean")
    parser.add_argument("--secondary-metric", default="best_AP50_mean")
    parser.add_argument("--lightweight-max-params", type=float, default=15_000_000)
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--require-main", action="store_true")
    parser.add_argument("--out-json", default="outputs/experiments/detector_stage_gate.json")
    parser.add_argument("--out-md", default="outputs/experiments/detector_stage_gate.md")
    args = parser.parse_args()

    rows = read_rows(args.summary_csv)
    if args.dataset:
        rows = [row for row in rows if row.get("dataset") == args.dataset]
    decision = decide_stage(
        rows,
        args.candidate_regex,
        args.metric,
        args.secondary_metric,
        args.lightweight_max_params,
        args.min_delta,
        args.require_main,
    )
    decision["dataset"] = args.dataset or "all"
    write_json(resolve_path(args.out_json), decision)
    write_markdown(resolve_path(args.out_md), decision)
    print(f"Recommended next stage: {decision['recommended_next_stage']}")
    print(decision["rationale"])
    print(f"Wrote {resolve_path(args.out_json)}")
    print(f"Wrote {resolve_path(args.out_md)}")


if __name__ == "__main__":
    main()
