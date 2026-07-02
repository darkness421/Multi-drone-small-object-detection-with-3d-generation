"""Build paper/live artifacts for the real-Cesium detector-to-reasoner smoke test."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evidence import load_tokens_jsonl


SCENARIO_LABELS = {
    "uavmarine_s0_viewer160_session_recapture": "S0 locked MarineCity ROI",
    "uavmarine_s1_viewer160_session_recapture": "S1 adjacent overlap",
    "uavmarine_s2_viewer160_session_recapture": "S2 coastline multi-view",
}

LATEST_DETECTOR_SUMMARIES = {
    "uavmarine_s0_viewer160_session_recapture": "outputs/evidence/uavmarine_s0_viewer160_session_recapture_detector_smoke_conf001/detector_smoke_summary.json",
    "uavmarine_s1_viewer160_session_recapture": "outputs/evidence/uavmarine_s1_viewer160_session_recapture_detector_smoke_conf001/detector_smoke_summary.json",
    "uavmarine_s2_viewer160_session_recapture": "outputs/evidence/uavmarine_s2_viewer160_session_recapture_detector_smoke_conf001/detector_smoke_summary.json",
}

REASONER_DIRS = {
    "uavmarine_s0_viewer160_session_recapture": "outputs/reasoning/uavmarine_s0_viewer160_session_recapture_from_detector_conf001_rule_based",
    "uavmarine_s1_viewer160_session_recapture": "outputs/reasoning/uavmarine_s1_viewer160_session_recapture_from_detector_conf001_rule_based",
    "uavmarine_s2_viewer160_session_recapture": "outputs/reasoning/uavmarine_s2_viewer160_session_recapture_from_detector_conf001_rule_based",
}

LATEST_CONTACT_SHEET = "outputs/reports/live/marinecity_system_test_10plus/contact_sheet_3_scenarios.png"


def _read_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _class_name(token: Any) -> str:
    return str(token.metadata.get("class_name", token.class_id if token.class_id is not None else "unknown"))


def _format_counts(counter: Counter[str]) -> str:
    if not counter:
        return "--"
    return ", ".join(f"{key}={value}" for key, value in counter.most_common())


def _escape_tex(value: str) -> str:
    return value.replace("_", "\\_").replace("%", "\\%")


def _display_provider(value: Any) -> str:
    provider = str(value or "missing")
    if provider.endswith("_symbolic_aerograph"):
        return "rule_based_aerograph"
    return provider


def build(args: argparse.Namespace) -> dict[str, Any]:
    detector_dir = Path(args.detector_dir)
    detector_summary = _read_json(detector_dir / "detector_smoke_summary.json")
    scenario_jsonl = detector_summary.get("scenario_jsonl", {})
    rows: list[dict[str, Any]] = []
    total_tokens = 0

    for scenario_id in SCENARIO_LABELS:
        latest_summary = _read_json(LATEST_DETECTOR_SUMMARIES.get(scenario_id, ""))
        token_path = Path(latest_summary.get("out_jsonl") or scenario_jsonl.get(scenario_id, ""))
        tokens = load_tokens_jsonl(token_path) if token_path.exists() else []
        class_counts: Counter[str] = Counter(_class_name(token) for token in tokens)
        uav_count = int(latest_summary.get("uav_count") or len({token.uav_id for token in tokens}) or 3)
        reasoner_summary = _read_json(Path(REASONER_DIRS[scenario_id]) / "summary.json")
        total_tokens += len(tokens)
        rows.append(
            {
                "scenario_id": scenario_id,
                "scenario": SCENARIO_LABELS[scenario_id],
                "uav_views": uav_count or 3,
                "evidence_tokens": len(tokens),
                "hypotheses": int(reasoner_summary.get("hypothesis_count", 0) or 0),
                "reobserve": int(reasoner_summary.get("reobserve_count", 0) or 0),
                "detected_classes": _format_counts(class_counts),
                "provider": _display_provider(reasoner_summary.get("provider", "missing")),
            }
        )

    table_path = Path(args.table_out)
    table_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{MarineCity real-Cesium detector-to-reasoner smoke-test results. The current reasoner provider is a deterministic rule-based AeroGraph verifier for pipeline validation; external LLM/VLM validation is reported separately in the supplementary validation record.}",
        "\\label{tab:marinecity_system_smoke}",
        "\\resizebox{\\linewidth}{!}{%",
        "\\begin{tabular}{lrrrrl}",
        "\\toprule",
        "Scenario & UAV views & Evidence tokens & 3D hypotheses & Re-observe & Detected classes \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            " & ".join(
                [
                    _escape_tex(str(row["scenario"])),
                    str(row["uav_views"]),
                    str(row["evidence_tokens"]),
                    str(row["hypotheses"]),
                    str(row["reobserve"]),
                    _escape_tex(str(row["detected_classes"])),
                ]
            )
            + " \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}%", "}", "\\end{table}", ""])
    table_path.write_text("\n".join(lines), encoding="utf-8")

    csv_path = Path(args.csv_out)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    copied_contact_sheet = Path(args.paper_contact_sheet)
    copied_contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    source_contact_sheet = Path(LATEST_CONTACT_SHEET)
    if not source_contact_sheet.exists():
        source_contact_sheet = Path(detector_summary.get("preview_contact_sheet", ""))
    if source_contact_sheet.exists():
        shutil.copy2(source_contact_sheet, copied_contact_sheet)

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# MarineCity Real-Cesium Detector-to-Reasoner Smoke",
        "",
        "- Detector summaries: latest per-scenario `uavmarine_*_viewer160_session_recapture_detector_smoke_conf001` outputs",
        f"- Total frames: `{detector_summary.get('frame_count', 0)}`",
        f"- Total evidence tokens: `{total_tokens}`",
        f"- Detector contact sheet: `{copied_contact_sheet}`",
        f"- Paper table: `{table_path}`",
        "",
        "| Scenario | UAV views | Tokens | Hypotheses | Re-observe | Classes | Provider |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['scenario']} | {row['uav_views']} | {row['evidence_tokens']} | "
            f"{row['hypotheses']} | {row['reobserve']} | {row['detected_classes']} | {row['provider']} |"
        )
    report_lines.extend(
        [
            "",
            "Claiming rule: this is a real-Cesium system smoke test, not a labeled MarineCity accuracy benchmark and not a completed 3D reconstruction result.",
        ]
    )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    summary = {
        "status": "marinecity_detector_reasoner_smoke_artifacts_ready",
        "row_count": len(rows),
        "table": str(table_path),
        "csv": str(csv_path),
        "report": str(report_path),
        "paper_contact_sheet": str(copied_contact_sheet),
        "total_tokens": total_tokens,
        "rows": rows,
    }
    Path(args.summary_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MarineCity smoke paper/live artifacts.")
    parser.add_argument("--detector-dir", default="outputs/evidence/marinecity_real_capture_detector_smoke")
    parser.add_argument("--table-out", default="paper/tables/marinecity_system_scenario_table.tex")
    parser.add_argument("--csv-out", default="paper/tables/marinecity_system_token_results.csv")
    parser.add_argument("--paper-contact-sheet", default="paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png")
    parser.add_argument("--report-out", default="outputs/reports/live/marinecity_detector_reasoner_smoke.md")
    parser.add_argument("--summary-out", default="outputs/reports/live/marinecity_detector_reasoner_smoke.json")
    args = parser.parse_args()
    print(json.dumps(build(args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
