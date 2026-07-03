"""Build a readable AeroGraph prompt/response audit report."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs/reports/live/aerograph_prompt_audit"
DEFAULT_DIRS = [
    ROOT / "outputs/reasoning/uavmarine_s0_viewer160_session_recapture_from_detector_conf001_rule_based",
    ROOT / "outputs/reasoning/uavmarine_s1_viewer160_session_recapture_from_detector_conf001_rule_based",
    ROOT / "outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_rule_based",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_run(path: Path) -> list[dict[str, Any]]:
    summary = read_json(path / "summary.json")
    prompts = read_json(path / "prompts.json")
    responses = {row["object_id"]: row for row in read_json(path / "llm_responses.json")}
    decisions = {row["object_id"]: row for row in read_json(path / "final_decisions.json")}
    rows = []
    for object_id, prompt in prompts.items():
        response = responses.get(object_id, {})
        decision = decisions.get(object_id, {})
        rows.append(
            {
                "run_dir": str(path.relative_to(ROOT)),
                "scenario": summary.get("scenario", ""),
                "provider": summary.get("provider", ""),
                "object_id": object_id,
                "prompt_chars": len(prompt),
                "prompt": prompt,
                "predicted_class": response.get("predicted_class"),
                "llm_confidence": response.get("confidence"),
                "recommended_action": response.get("recommended_action"),
                "final_should_reobserve": decision.get("should_reobserve"),
                "final_decision_source": decision.get("decision_source"),
                "response_raw": response.get("raw", response),
                "final_decision": decision,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "run_dir",
        "scenario",
        "provider",
        "object_id",
        "prompt_chars",
        "predicted_class",
        "llm_confidence",
        "recommended_action",
        "final_should_reobserve",
        "final_decision_source",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_md(path: Path, rows: list[dict[str, Any]], *, max_examples: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_scenario.setdefault(str(row["scenario"]), []).append(row)

    lines = [
        "# AeroGraph Prompt Audit",
        "",
        "This report exposes what the graph-grounded reasoner receives and returns.",
        "It is meant for paper/rebuttal inspection, not as an external LLM benchmark.",
        "",
        "## Summary",
        "",
        "| Scenario | Provider | Prompts | Reobserve decisions |",
        "| --- | --- | ---: | ---: |",
    ]
    for scenario, group in sorted(by_scenario.items()):
        provider = sorted({str(row["provider"]) for row in group})
        reobs = sum(1 for row in group if row.get("final_should_reobserve"))
        lines.append(f"| {scenario} | {', '.join(provider)} | {len(group)} | {reobs} |")

    lines.extend(
        [
            "",
            "## Prompt Contract",
            "",
            "- The prompt asks for valid JSON only.",
            "- The allowed fields are decision, predicted_class, confidence, evidence_clues, missing_evidence, and recommended_action.",
            "- The final action is still checked by the graph/safety adjudicator.",
            "- Rule-based rows are transparent plumbing checks; external-provider rows should be reported separately.",
            "",
            "## Representative Full Prompts",
            "",
        ]
    )
    for index, row in enumerate(rows[:max_examples], start=1):
        lines.extend(
            [
                f"### Example {index}: {row['scenario']} / {row['object_id']}",
                "",
                f"- Provider: `{row['provider']}`",
                f"- Response class/action: `{row.get('predicted_class')}` / `{row.get('recommended_action')}`",
                f"- Final should_reobserve: `{row.get('final_should_reobserve')}`",
                "",
                "Prompt:",
                "",
                "```text",
                str(row["prompt"]),
                "```",
                "",
                "Response raw:",
                "",
                "```json",
                json.dumps(row["response_raw"], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Full Machine-Readable Files",
            "",
            "- `aerograph_prompt_audit_full.json` contains every prompt and response.",
            "- `aerograph_prompt_audit_table.csv` contains a compact run table.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AeroGraph prompt audit report.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-examples", type=int, default=6)
    parser.add_argument("run_dirs", nargs="*", type=Path)
    args = parser.parse_args()

    run_dirs = args.run_dirs or DEFAULT_DIRS
    rows: list[dict[str, Any]] = []
    missing = []
    for run_dir in run_dirs:
        if all((run_dir / name).exists() for name in ("summary.json", "prompts.json", "llm_responses.json", "final_decisions.json")):
            rows.extend(load_run(run_dir))
        else:
            missing.append(str(run_dir))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    full_json = args.out_dir / "aerograph_prompt_audit_full.json"
    csv_path = args.out_dir / "aerograph_prompt_audit_table.csv"
    md_path = args.out_dir / "aerograph_prompt_audit.md"
    full_json.write_text(json.dumps({"rows": rows, "missing": missing}, indent=2, ensure_ascii=False), encoding="utf-8")
    if rows:
        write_csv(csv_path, rows)
        write_md(md_path, rows, max_examples=args.max_examples)
    print(
        json.dumps(
            {
                "status": "aerograph_prompt_audit_complete",
                "rows": len(rows),
                "missing": missing,
                "markdown": str(md_path.relative_to(ROOT)),
                "json": str(full_json.relative_to(ROOT)),
                "csv": str(csv_path.relative_to(ROOT)),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
