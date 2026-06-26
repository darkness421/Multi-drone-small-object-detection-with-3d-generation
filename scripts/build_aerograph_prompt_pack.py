"""Build a compact prompt pack for non-mock AeroGraph Reasoner evaluation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_RUNS = [
    ("S0", "s0_locked_roi", "outputs/reasoning/uavmarine_s0_viewer160_session_recapture_from_detector_conf001_mock"),
    ("S1", "s1_adjacent_overlap", "outputs/reasoning/uavmarine_s1_viewer160_session_recapture_from_detector_conf001_mock"),
    ("S2", "s2_coastline_multiview", "outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_mock"),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def class_from_decision(row: dict[str, Any]) -> str:
    value = row.get("predicted_class")
    if value:
        return str(value)
    object_id = str(row.get("object_id", ""))
    for label in ["pedestrian", "person", "truck", "bus", "van", "car"]:
        if label in object_id:
            return label
    return "unknown"


def collect_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_id, scenario_name, run_dir_text in DEFAULT_RUNS:
        run_dir = repo_root / run_dir_text
        prompts_path = run_dir / "prompts.json"
        decisions_path = run_dir / "final_decisions.json"
        summary_path = run_dir / "summary.json"
        if not prompts_path.exists() or not decisions_path.exists():
            continue

        prompts = read_json(prompts_path)
        decisions = {str(row["object_id"]): row for row in read_json(decisions_path)}
        summary = read_json(summary_path) if summary_path.exists() else {}
        for object_id, prompt in prompts.items():
            decision = decisions.get(str(object_id), {})
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "scenario": scenario_name,
                    "object_id": str(object_id),
                    "candidate_class": class_from_decision(decision),
                    "mock_decision": decision.get("decision_source", ""),
                    "should_reobserve": bool(decision.get("should_reobserve", False)),
                    "mock_confidence": decision.get("confidence", None),
                    "runner_provider": summary.get("runner_provider", "mock"),
                    "prompt": prompt,
                }
            )
    return rows


def representative_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    target_order = ["bus", "van", "pedestrian", "car", "truck", "person", "unknown"]
    selected: list[dict[str, Any]] = []
    used: set[tuple[str, str, str]] = set()

    for label in target_order:
        for row in rows:
            key = (row["scenario_id"], row["object_id"], row["candidate_class"])
            if key in used or row["candidate_class"] != label:
                continue
            selected.append(row)
            used.add(key)
            break
        if len(selected) >= limit:
            return selected

    for scenario_id in ["S0", "S1", "S2"]:
        for row in rows:
            key = (row["scenario_id"], row["object_id"], row["candidate_class"])
            if key in used or row["scenario_id"] != scenario_id:
                continue
            selected.append(row)
            used.add(key)
            if len(selected) >= limit:
                return selected

    return selected


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# AeroGraph Non-Mock Prompt Pack",
        "",
        "Use these prompts for GPT/Factory/local LLM evaluation. Return only the JSON schema requested inside each prompt.",
        "",
    ]
    for idx, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## Test {idx:02d}: {row['scenario_id']} / {row['object_id']} / {row['candidate_class']}",
                "",
                f"- Mock decision source: `{row.get('mock_decision', '')}`",
                f"- Re-observe expected from graph gate: `{row.get('should_reobserve')}`",
                "",
                "```text",
                row["prompt"],
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def manual_template_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    template_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        template_rows.append(
            {
                "index": index,
                "scenario_id": row.get("scenario_id"),
                "object_id": row.get("object_id"),
                "candidate_class": row.get("candidate_class"),
                "prompt": row.get("prompt"),
                "response_text": "",
            }
        )
    return template_rows


def archive_stale_counted_prompt_packs(out_dir: Path, archive_dir: Path, active_counted_jsonl: Path) -> list[str]:
    """Move obsolete counted prompt packs, e.g. aerograph_prompts_79.jsonl."""

    archived: list[str] = []
    for path in sorted(out_dir.glob("aerograph_prompts_[0-9]*.jsonl")):
        if path.resolve() == active_counted_jsonl.resolve():
            continue
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / path.name
        if target.exists():
            target = archive_dir / f"{path.stem}_legacy{path.suffix}"
        path.rename(target)
        archived.append(str(target))
    return archived


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    out_dir = repo_root / args.out_dir
    archive_dir = repo_root / args.archive_dir
    rows = collect_rows(repo_root)
    sample = representative_sample(rows, args.sample_limit)
    class_counts = Counter(row["candidate_class"] for row in rows)
    scenario_counts = Counter(row["scenario_id"] for row in rows)

    all_jsonl = out_dir / "aerograph_prompts_all.jsonl"
    counted_jsonl = out_dir / f"aerograph_prompts_{len(rows)}.jsonl"
    sample_jsonl = out_dir / f"aerograph_prompts_sample{args.sample_limit}.jsonl"
    sample_md = out_dir / f"aerograph_prompts_sample{args.sample_limit}.md"
    template_all = out_dir / "aerograph_manual_response_template_all.jsonl"
    template_sample = out_dir / f"aerograph_manual_response_template_sample{args.sample_limit}.jsonl"
    manifest_path = out_dir / "manifest.json"

    write_jsonl(all_jsonl, rows)
    write_jsonl(counted_jsonl, rows)
    write_jsonl(sample_jsonl, sample)
    write_markdown(sample_md, sample)
    write_jsonl(template_all, manual_template_rows(rows))
    write_jsonl(template_sample, manual_template_rows(sample))
    archived_legacy_prompt_packs = archive_stale_counted_prompt_packs(out_dir, archive_dir, counted_jsonl)

    manifest = {
        "status": "aerograph_prompt_pack_ready",
        "total_prompts": len(rows),
        "sample_prompts": len(sample),
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "class_counts": dict(sorted(class_counts.items())),
        "all_jsonl": str(all_jsonl.relative_to(repo_root)),
        "counted_jsonl": str(counted_jsonl.relative_to(repo_root)),
        "sample_jsonl": str(sample_jsonl.relative_to(repo_root)),
        "sample_markdown": str(sample_md.relative_to(repo_root)),
        "manual_response_template_all": str(template_all.relative_to(repo_root)),
        "manual_response_template_sample": str(template_sample.relative_to(repo_root)),
        "archived_legacy_prompt_packs": archived_legacy_prompt_packs,
        "note": "These are real-Cesium detector-token prompts. Non-mock GPT/Factory responses are pending provider/API execution.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AeroGraph prompt pack for non-mock LLM evaluation.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default="outputs/reports/live/aerograph_prompt_pack")
    parser.add_argument("--archive-dir", default="outputs/reports/archive/aerograph_prompt_pack")
    parser.add_argument("--sample-limit", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
