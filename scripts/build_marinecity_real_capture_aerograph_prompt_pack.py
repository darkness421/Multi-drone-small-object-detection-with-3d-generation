"""Build AeroGraph prompt pack from the latest real-capture smoke outputs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_RUNS = [
    ("S0", "s0_locked_roi", "outputs/reasoning/marinecity_real_capture_s0_reasoner_smoke"),
    ("S1", "s1_adjacent_overlap", "outputs/reasoning/marinecity_real_capture_s1_reasoner_smoke"),
    ("S2", "s2_coastline_multiview", "outputs/reasoning/marinecity_real_capture_s2_reasoner_smoke"),
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _class_from_decision(row: dict[str, Any]) -> str:
    value = row.get("predicted_class")
    if value:
        return str(value)
    object_id = str(row.get("object_id", ""))
    for label in ["pedestrian", "person", "truck", "bus", "van", "car"]:
        if label in object_id:
            return label
    return "unknown"


def _manual_template_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            "scenario_id": row.get("scenario_id"),
            "object_id": row.get("object_id"),
            "candidate_class": row.get("candidate_class"),
            "prompt": row.get("prompt"),
            "response_text": "",
        }
        for index, row in enumerate(rows, start=1)
    ]


def _write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# MarineCity Real-Capture AeroGraph Prompt Pack",
        "",
        "This compact pack matches the current 23-token real-Cesium detector smoke run.",
        "Use it for a quick GPT/Factory/local non-mock smoke before the full 49-prompt final gate.",
        "",
    ]
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## Item {index:02d}: {row['scenario_id']} / {row['object_id']} / {row['candidate_class']}",
                "",
                f"- Mock decision source: `{row.get('mock_decision', '')}`",
                f"- Re-observe expected: `{row.get('should_reobserve')}`",
                "",
                "```text",
                str(row.get("prompt", "")),
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def collect_rows(repo_root: Path, runs: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_id, scenario_name, run_dir_text in runs:
        run_dir = repo_root / run_dir_text
        prompts_path = run_dir / "prompts.json"
        decisions_path = run_dir / "final_decisions.json"
        summary_path = run_dir / "summary.json"
        if not prompts_path.exists() or not decisions_path.exists():
            continue
        prompts = _read_json(prompts_path)
        decisions = {str(row["object_id"]): row for row in _read_json(decisions_path)}
        summary = _read_json(summary_path) if summary_path.exists() else {}
        for object_id, prompt in prompts.items():
            decision = decisions.get(str(object_id), {})
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "scenario": scenario_name,
                    "object_id": str(object_id),
                    "candidate_class": _class_from_decision(decision),
                    "mock_decision": decision.get("decision_source", ""),
                    "should_reobserve": bool(decision.get("should_reobserve", False)),
                    "mock_confidence": decision.get("confidence", None),
                    "runner_provider": summary.get("runner_provider", "mock"),
                    "source_run_dir": str(run_dir.relative_to(repo_root)),
                    "prompt": prompt,
                }
            )
    return rows


def build(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    out_dir = repo_root / args.out_dir
    rows = collect_rows(repo_root, DEFAULT_RUNS)
    class_counts = Counter(row["candidate_class"] for row in rows)
    scenario_counts = Counter(row["scenario_id"] for row in rows)

    all_jsonl = out_dir / "aerograph_real_capture_prompts_all.jsonl"
    counted_jsonl = out_dir / f"aerograph_real_capture_prompts_{len(rows)}.jsonl"
    markdown_path = out_dir / "aerograph_real_capture_prompts_all.md"
    template_path = out_dir / "aerograph_real_capture_manual_response_template_all.jsonl"
    manifest_path = out_dir / "manifest.json"

    _write_jsonl(all_jsonl, rows)
    _write_jsonl(counted_jsonl, rows)
    _write_markdown(markdown_path, rows)
    _write_jsonl(template_path, _manual_template_rows(rows))

    manifest = {
        "status": "aerograph_real_capture_prompt_pack_ready",
        "total_prompts": len(rows),
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "class_counts": dict(sorted(class_counts.items())),
        "all_jsonl": str(all_jsonl.relative_to(repo_root)),
        "counted_jsonl": str(counted_jsonl.relative_to(repo_root)),
        "markdown": str(markdown_path.relative_to(repo_root)),
        "manual_response_template_all": str(template_path.relative_to(repo_root)),
        "source": "current 23-token real-Cesium MarineCity detector-to-reasoner smoke outputs",
        "claiming_rule": "Use as compact non-mock smoke only; full AeroGraph paper-table promotion still requires the 49-prompt final provider gate unless the paper explicitly switches to this 23-prompt protocol.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compact real-capture AeroGraph prompt pack.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default="outputs/reports/live/aerograph_real_capture_prompt_pack")
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
