"""Audit paper-facing ACCV artifacts before Overleaf integration."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Artifact:
    group: str
    path: str
    placement: str
    required_now: bool
    note: str


ARTIFACTS = [
    Artifact("main_detector", "paper/sections/05_experiments_current_detector_status.tex", "main", True, "Detector result section patch"),
    Artifact("main_detector", "paper/tables/main_detector_comparison_table.tex", "main", True, "Compact final detector table"),
    Artifact("main_detector", "paper/tables/final_ablation_main_table.tex", "main", True, "Compact final ablation table"),
    Artifact("main_detector", "paper/tables/related_work_detector_status_table.tex", "main", True, "Cited related-work detector table"),
    Artifact("main_detector", "paper/figures/results/paper_fig01_main_detector_table.png", "main_optional", True, "Detector table visual"),
    Artifact("main_detector", "paper/figures/results/paper_fig04_ap_ap50_bar_chart.png", "main_or_supp", True, "AP/AP50 chart"),
    Artifact("main_detector", "paper/figures/results/paper_fig05_ap_params_scatter.png", "main_or_supp", True, "AP vs params chart"),
    Artifact("main_system", "paper/sections/06_marinecity_3d_readiness.tex", "main", True, "MarineCity protocol section patch"),
    Artifact("main_system", "paper/tables/marinecity_system_scenario_table.tex", "main", True, "Real-Cesium smoke/protocol table"),
    Artifact("main_system", "paper/tables/marinecity_system_token_results.csv", "main_source", True, "Source CSV for real-Cesium detector-to-reasoner smoke table"),
    Artifact("main_system", "paper/tables/marinecity_real_capture_benchmark_table.tex", "main", True, "Verified real-Cesium capture-source table"),
    Artifact("main_system", "paper/tables/marinecity_crossview_evidence_graph_table.tex", "main", True, "Real-Cesium cross-view evidence graph smoke table"),
    Artifact("main_system", "paper/sections/07_marinecity_qualitative_figure_slots.tex", "main_optional", True, "Safe qualitative figure slots"),
    Artifact("bundle", "paper/sections/main_results_patch_bundle.tex", "main_bundle", True, "Overleaf-ready main results patch bundle"),
    Artifact("bundle", "paper/sections/supplementary_patch_bundle.tex", "supp_bundle", True, "Overleaf-ready supplementary patch bundle"),
    Artifact("supp_detector", "paper/sections/supp_detector_experiment_inventory.tex", "supp", True, "Supplementary detector inventory"),
    Artifact("supp_detector", "paper/tables/final_ablation_supplementary_table.tex", "supp", True, "Full ablation table"),
    Artifact("supp_detector", "paper/tables/tinyperson_640_stress_table.tex", "supp", True, "TinyPerson 640 supplementary stress-test table"),
    Artifact("supp_detector", "paper/tables/tinyperson_eval_imgsz_sweep_table.tex", "supp", True, "TinyPerson eval-only input-size sensitivity table"),
    Artifact("supp_detector", "paper/figures/results/paper_fig10_final_ablation_metric_heatmap.png", "supp", True, "Ablation heatmap"),
    Artifact("supp_detector", "paper/figures/results/paper_fig11_final_detector_feature_activation_heatmap.png", "supp", True, "Detector activation/heatmap sheet"),
    Artifact("supp_detector", "paper/figures/results/paper_fig12_tinyperson_640_stress.png", "supp", True, "TinyPerson 640 supplementary stress-test figure"),
    Artifact("supp_detector", "paper/figures/results/paper_fig13_tinyperson_eval_imgsz_sweep.png", "supp", True, "TinyPerson eval-only input-size sensitivity figure"),
    Artifact("supp_system", "paper/figures/results/marinecity_system/contact_sheet_3_scenarios.png", "supp_or_main_smoke", True, "Three-scenario real-Cesium smoke sheet"),
    Artifact("supp_system", "paper/figures/results/marinecity_system/marinecity_detector_preview_contact_sheet.png", "main_or_supp_smoke", True, "Real-Cesium detector preview contact sheet from SAFR-YOLO smoke run"),
    Artifact("supp_system", "paper/figures/results/marinecity_system/marinecity_real_capture_benchmark_contact_sheet.png", "supp", True, "Real-Cesium 3-scenario x 3-UAV capture contact sheet"),
    Artifact("supp_system", "paper/figures/results/marinecity_system/marinecity_crossview_evidence_graph.png", "supp", True, "Real-Cesium cross-view evidence graph smoke figure"),
    Artifact("supp_system", "paper/figures/results/marinecity_system/marinecity_qualitative_selection_manifest.md", "supp", True, "MarineCity qualitative selection rules"),
    Artifact("supp_system", "paper/figures/results/marinecity_system/marinecity_qualitative_gate.md", "supp", True, "MarineCity full-frame vs crop-only qualitative gate"),
    Artifact("supp_system", "outputs/reports/live/marinecity_real_capture_benchmark.md", "runbook", True, "Real-Cesium capture benchmark manifest summary"),
    Artifact("supp_system", "outputs/reports/live/marinecity_detector_reasoner_smoke.md", "runbook", True, "Real-Cesium detector-to-reasoner smoke report"),
    Artifact("supp_system", "outputs/reports/live/marinecity_crossview_evidence_graph.md", "runbook", True, "Real-Cesium cross-view evidence graph smoke report"),
    Artifact("supp_system", "outputs/reports/live/marinecity_system_integration_check.md", "runbook", True, "Real-Cesium object/UAV/camera/YOLO/3D/LLM integration gate"),
    Artifact("pending_3d", "outputs/reports/live/marinecity_neural3d_dataset_export.md", "runbook", True, "MarineCity real-capture neural-3D input dataset export"),
    Artifact("pending_3d", "outputs/reports/live/marinecity_3d_runner_preflight.md", "runbook", True, "MarineCity local neural-3D runner dependency preflight"),
    Artifact("pending_3d", "outputs/reports/live/marinecity_depth_pointcloud_smoke.md", "runbook", True, "MarineCity depth-fused 3D geometry smoke artifact"),
    Artifact("pending_3d", "paper/figures/results/marinecity_system/marinecity_depth_pointcloud_smoke_topdown.png", "supp", True, "Depth point-cloud smoke preview figure"),
    Artifact("pending_3d", "outputs/reports/live/marinecity_3d_completion_readiness.md", "runbook", True, "MarineCity neural 3D completion readiness gate"),
    Artifact("pending_reasoner", "paper/tables/aerograph_reasoner_results_placeholder.tex", "pending", True, "AeroGraph table slot must stay pending until all prompt-pack non-mock responses are valid-schema complete"),
    Artifact("pending_reasoner", "docs/aerograph_nonmock_collection_plan.md", "runbook", True, "Non-mock reasoner collection gate"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_prompt_pack_integrity.md", "audit", True, "AeroGraph prompt/template/batch consistency check"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_packet.md", "runbook", True, "One-file web LLM handoff for AeroGraph collection"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_prompt_pack/aerograph_web_collection_checklist.csv", "runbook", True, "Per-prompt AeroGraph non-mock collection checklist"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_real_capture_prompt_pack/manifest.json", "runbook", True, "Compact 23-prompt real-capture AeroGraph smoke pack"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_real_capture_prompt_pack/web_batches/README.md", "runbook", True, "Compact real-capture web-provider batch index"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_packet.md", "runbook", True, "Compact real-capture web-provider collection packet"),
    Artifact("pending_reasoner", "outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_web_collection_checklist.csv", "runbook", True, "Compact real-capture web-provider collection checklist"),
    Artifact("pending_reasoner", "outputs/reasoning/aerograph_real_capture_eval_dryrun/manifest.json", "audit", True, "Compact real-capture prompt-pack runner dry-run check"),
    Artifact("pending_reasoner", "scripts/normalize_aerograph_web_responses.py", "runbook_helper", True, "Web LLM raw-output normalizer for AeroGraph manual responses"),
    Artifact("audit", "paper/figures/results/paper_artifact_readiness_manifest.md", "audit", True, "Human-readable artifact manifest"),
    Artifact("audit", "outputs/reports/live/latex_patch_integrity_check.md", "audit", True, "LaTeX input/figure/label integrity check"),
    Artifact("audit", "docs/accv_research_package_readiness_audit_2026-06-25.md", "audit", True, "Claim readiness audit"),
]


PROHIBITED_READY_CLAIMS = [
    (re.compile(r"full\s+3D\s+reconstruction\s+benchmark\s+is\s+complete", re.I), "Claims full 3D reconstruction benchmark is complete"),
    (re.compile(r"non[- ]mock\s+(?:LLM|VLM|AeroGraph).*complete", re.I), "Claims non-mock reasoner is complete"),
    (re.compile(r"autonomous\s+UAV\s+control", re.I), "Claims autonomous UAV control"),
    (re.compile(r"proxy\s+MarineCity\s+stage", re.I), "Stale proxy-stage wording"),
    (re.compile(r"fake\s+city\s+geometry\s+is\s+used", re.I), "Suggests fake city evidence"),
]


TEXT_SCOPE = [
    "paper/draft_notes.md",
    "paper/sections/05_experiments_current_detector_status.tex",
    "paper/sections/06_marinecity_3d_readiness.tex",
    "paper/sections/07_marinecity_qualitative_figure_slots.tex",
    "paper/sections/README.md",
    "paper/figures/README.md",
    "paper/figures/results/paper_artifact_readiness_manifest.md",
    "docs/accv_research_package_readiness_audit_2026-06-25.md",
    "docs/aerograph_nonmock_collection_plan.md",
    "docs/aerograph_reasoner_naming.md",
    "outputs/reports/live/accv_workflow_status_snapshot.md",
    "outputs/reports/live/marinecity_real_capture_benchmark.md",
    "outputs/reports/live/marinecity_system_integration_check.md",
    "outputs/reports/live/marinecity_neural3d_dataset_export.md",
    "outputs/reports/live/marinecity_3d_runner_preflight.md",
    "outputs/reports/live/marinecity_depth_pointcloud_smoke.md",
    "outputs/reports/live/marinecity_3d_completion_readiness.md",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def artifact_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in ARTIFACTS:
        path = REPO_ROOT / item.path
        rows.append(
            {
                "group": item.group,
                "path": item.path,
                "placement": item.placement,
                "required_now": item.required_now,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "status": "ok" if path.exists() or not item.required_now else "missing",
                "note": item.note,
            }
        )
    return rows


def stale_claim_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in TEXT_SCOPE:
        path = REPO_ROOT / item
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern, reason in PROHIBITED_READY_CLAIMS:
                if pattern.search(line):
                    rows.append(
                        {
                            "path": item,
                            "line": str(line_number),
                            "reason": reason,
                            "text": line.strip()[:220],
                        }
                    )
    return rows


def aerograph_gate() -> dict[str, Any]:
    readiness = read_json(REPO_ROOT / "outputs/reports/live/aerograph_nonmock_readiness_status.json")
    table_manifest = read_json(REPO_ROOT / "outputs/reports/live/aerograph_reasoner_table_manifest.json")
    coverage = (
        readiness.get("effective_response_coverage")
        or readiness.get("manual_response_coverage", {})
        or {}
    )
    matched = int(coverage.get("matched_valid_response_count", coverage.get("matched_nonblank_response_count", 0)) or 0)
    total = int(coverage.get("prompt_count", 0) or 0)
    return {
        "status": readiness.get("status", "missing"),
        "matched_nonblank_response_count": int(coverage.get("matched_nonblank_response_count", matched) or 0),
        "matched_valid_response_count": matched,
        "prompt_count": total,
        "coverage_ratio": coverage.get("valid_coverage_ratio", coverage.get("coverage_ratio", 0.0)),
        "paper_table_status": table_manifest.get("status", "missing"),
        "non_mock_outputs_ready": bool(table_manifest.get("non_mock_outputs_ready")),
        "external_provider_replication_ready": bool(readiness.get("external_provider_replication_ready")),
        "reviewed_candidate_valid_count": int(readiness.get("reviewed_candidate_valid_count", 0) or 0),
        "complete": total > 0
        and matched == total
        and bool(table_manifest.get("non_mock_outputs_ready"))
        and bool(readiness.get("external_provider_replication_ready")),
    }


def main_tex_gate() -> dict[str, Any]:
    candidates = sorted(REPO_ROOT.glob("**/main.tex"))
    local_candidates = [path for path in candidates if ".git" not in path.parts and "outputs" not in path.parts]
    return {
        "main_tex_candidates": [rel(path) for path in local_candidates],
        "main_tex_present": bool(local_candidates),
        "note": "No local main.tex means current files are Overleaf-ready patches rather than a full local paper build."
        if not local_candidates
        else "Local main.tex exists; run LaTeX compile/page audit next.",
    }


def latex_integrity_gate() -> dict[str, Any]:
    report = read_json(REPO_ROOT / "outputs/reports/live/latex_patch_integrity_check.json")
    return {
        "status": report.get("status", "missing"),
        "missing_input_count": report.get("missing_input_count"),
        "missing_graphics_count": report.get("missing_graphics_count"),
        "duplicate_label_count": report.get("duplicate_label_count"),
        "unresolved_ref_count": report.get("unresolved_ref_count"),
        "pending_review_count": report.get("pending_review_count"),
    }


def marinecity_qualitative_gate() -> dict[str, Any]:
    report = read_json(REPO_ROOT / "outputs/reports/live/marinecity_qualitative_gate.json")
    checks = report.get("checks", {}) or {}
    full = report.get("best_full_capture", {}) or {}
    crop = report.get("best_crop_candidate", {}) or {}
    return {
        "status": report.get("status", "missing"),
        "real_cesium_ok": checks.get("real_cesium_ok"),
        "system_smoke_ok": checks.get("system_smoke_ok"),
        "crop_supplementary_ready": checks.get("crop_supplementary_ready"),
        "full_frame_main_ready": checks.get("full_frame_main_ready"),
        "best_full_black_ratio": full.get("best_black_ratio"),
        "mean_top3_black_ratio": full.get("mean_top3_black_ratio"),
        "best_crop_black_ratio": crop.get("black_ratio"),
        "claiming_rule": report.get("claiming_rule", ""),
    }


def marinecity_system_integration_gate() -> dict[str, Any]:
    report = read_json(REPO_ROOT / "outputs/reports/live/marinecity_system_integration_check.json")
    checks = report.get("checks", []) or []
    return {
        "status": report.get("status", "missing"),
        "fail_count": sum(1 for row in checks if row.get("status") == "FAIL"),
        "warn_count": sum(1 for row in checks if row.get("status") == "WARN"),
        "pending_count": sum(1 for row in checks if row.get("status") == "PENDING"),
        "detector_token_count": (report.get("detector", {}) or {}).get("token_count"),
        "detector_classes": (report.get("detector", {}) or {}).get("tokens_by_class"),
        "actor_classes": (report.get("actors", {}) or {}).get("actor_classes"),
        "three_d_status": (report.get("three_d_completion", {}) or {}).get("status"),
        "llm_external_ready": (report.get("llm_reasoner", {}) or {}).get("external_provider_replication_ready"),
        "tinyperson_status": (report.get("tinyperson_640", {}) or {}).get("status"),
    }


def marinecity_3d_completion_gate() -> dict[str, Any]:
    report = read_json(REPO_ROOT / "outputs/reports/live/marinecity_3d_completion_readiness.json")
    return {
        "status": report.get("status", "missing"),
        "source_capture_ready": report.get("source_capture_ready"),
        "neural3d_dataset_ready": report.get("neural3d_dataset_ready"),
        "depth_pointcloud_smoke_ready": report.get("depth_pointcloud_smoke_ready"),
        "depth_pointcloud_point_count": report.get("depth_pointcloud_point_count"),
        "neural_runner_available": report.get("neural_runner_available"),
        "metric_result_row_count": report.get("metric_result_row_count"),
        "methods_ready": report.get("methods_ready"),
        "missing_expected_methods": report.get("missing_expected_methods"),
        "claiming_rule": report.get("claiming_rule", ""),
    }


def build_report() -> dict[str, Any]:
    artifacts = artifact_rows()
    stale = stale_claim_rows()
    missing_required = [row for row in artifacts if row["required_now"] and not row["exists"]]
    aerograph = aerograph_gate()
    main_tex = main_tex_gate()
    latex_integrity = latex_integrity_gate()
    marinecity_qual = marinecity_qualitative_gate()
    marinecity_system = marinecity_system_integration_gate()
    marinecity_3d = marinecity_3d_completion_gate()
    status = "paper_artifact_audit_ok_with_pending_gates"
    latex_bad = latex_integrity.get("status") not in {"latex_patch_integrity_ok"}
    if missing_required or stale or latex_bad:
        status = "paper_artifact_audit_needs_attention"
    prompt_count = int(aerograph.get("prompt_count", 0) or 0)
    aerograph_claim = (
        "ready_external_provider_prompt_run"
        if aerograph.get("complete")
        else "candidate_ready_external_provider_pending"
        if aerograph.get("reviewed_candidate_valid_count") == prompt_count and prompt_count
        else f"pending_nonmock_{prompt_count}_prompt_run"
        if prompt_count
        else "pending_nonmock_prompt_run"
    )
    return {
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "status": status,
        "artifact_count": len(artifacts),
        "missing_required_count": len(missing_required),
        "stale_claim_count": len(stale),
        "artifacts": artifacts,
        "missing_required": missing_required,
        "stale_claims": stale,
        "aerograph_gate": aerograph,
        "marinecity_qualitative_gate": marinecity_qual,
        "marinecity_system_integration_gate": marinecity_system,
        "marinecity_3d_completion_gate": marinecity_3d,
        "main_tex_gate": main_tex,
        "latex_integrity_gate": latex_integrity,
        "claiming_summary": {
            "detector": "ready",
            "marinecity_system": "ready_as_real_cesium_smoke_protocol_only",
            "marinecity_qualitative": "ready_for_main"
            if marinecity_qual.get("full_frame_main_ready")
            else "pending_clean_full_frame_recapture",
            "aerograph": aerograph_claim,
            "final_3d_completion": "ready"
            if marinecity_3d.get("status") == "marinecity_3d_completion_ready"
            else "pending_neural_3d_completion_metrics",
            "local_compile": "pending_main_tex_or_overleaf_sync",
        },
    }


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return lines


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    aerograph = report["aerograph_gate"]
    main_tex = report["main_tex_gate"]
    marinecity_qual = report["marinecity_qualitative_gate"]
    marinecity_system = report["marinecity_system_integration_gate"]
    marinecity_3d = report["marinecity_3d_completion_gate"]
    lines = [
        "# Paper Artifact Readiness Check",
        "",
        f"Updated: `{report['updated_at_kst']}`",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Artifacts checked: `{report['artifact_count']}`",
        f"- Missing required artifacts: `{report['missing_required_count']}`",
        f"- Stale/unsafe claim matches: `{report['stale_claim_count']}`",
        f"- AeroGraph effective valid response coverage: `{aerograph['matched_valid_response_count']}/{aerograph['prompt_count']}`",
        f"- AeroGraph reviewed-candidate coverage: `{aerograph['reviewed_candidate_valid_count']}/{aerograph['prompt_count']}`",
        f"- AeroGraph external-provider replication ready: `{aerograph['external_provider_replication_ready']}`",
        f"- AeroGraph table status: `{aerograph['paper_table_status']}`",
        f"- MarineCity qualitative gate: `{marinecity_qual['status']}`",
        f"- MarineCity integration gate: `{marinecity_system['status']}`; fails `{marinecity_system['fail_count']}`, warnings `{marinecity_system['warn_count']}`, pending `{marinecity_system['pending_count']}`",
        f"- MarineCity 3D completion gate: `{marinecity_3d['status']}`; metric rows `{marinecity_3d['metric_result_row_count']}`",
        f"- MarineCity main full-frame ready: `{marinecity_qual['full_frame_main_ready']}`",
        f"- Local main.tex present: `{main_tex['main_tex_present']}`",
        f"- LaTeX patch integrity: `{report['latex_integrity_gate']['status']}`",
        f"- Main.tex note: {main_tex['note']}",
        "",
        "## Claiming Summary",
        "",
    ]
    for key, value in report["claiming_summary"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## MarineCity Integration Gate",
            "",
            f"- Status: `{marinecity_system['status']}`",
            f"- Fail/warn/pending count: `{marinecity_system['fail_count']}` / `{marinecity_system['warn_count']}` / `{marinecity_system['pending_count']}`",
            f"- Detector token count: `{marinecity_system['detector_token_count']}`",
            f"- Detector classes: `{marinecity_system['detector_classes']}`",
            f"- Actor classes: `{marinecity_system['actor_classes']}`",
            f"- 3D status: `{marinecity_system['three_d_status']}`",
            f"- LLM external ready: `{marinecity_system['llm_external_ready']}`",
            f"- TinyPerson status: `{marinecity_system['tinyperson_status']}`",
            "",
            "## MarineCity 3D Completion Gate",
            "",
            f"- Status: `{marinecity_3d['status']}`",
            f"- Source capture ready: `{marinecity_3d['source_capture_ready']}`",
            f"- Neural-3D input dataset ready: `{marinecity_3d['neural3d_dataset_ready']}`",
            f"- Neural runner available: `{marinecity_3d['neural_runner_available']}`",
            f"- Depth point-cloud smoke ready: `{marinecity_3d['depth_pointcloud_smoke_ready']}`; points `{marinecity_3d['depth_pointcloud_point_count']}`",
            f"- Metric result rows: `{marinecity_3d['metric_result_row_count']}`",
            f"- Methods ready: `{marinecity_3d['methods_ready']}`",
            f"- Missing expected methods: `{marinecity_3d['missing_expected_methods']}`",
            f"- Claiming rule: {marinecity_3d['claiming_rule']}",
            "",
            "## MarineCity Qualitative Gate",
            "",
            f"- Status: `{marinecity_qual['status']}`",
            f"- Real Cesium OK: `{marinecity_qual['real_cesium_ok']}`",
            f"- System smoke OK: `{marinecity_qual['system_smoke_ok']}`",
            f"- Crop supplementary ready: `{marinecity_qual['crop_supplementary_ready']}`",
            f"- Full-frame main ready: `{marinecity_qual['full_frame_main_ready']}`",
            f"- Best full-frame void ratio: `{marinecity_qual['best_full_black_ratio']}`",
            f"- Mean top-3 full-frame void ratio: `{marinecity_qual['mean_top3_black_ratio']}`",
            f"- Best crop void ratio: `{marinecity_qual['best_crop_black_ratio']}`",
            f"- Claiming rule: {marinecity_qual['claiming_rule']}",
        ]
    )

    if report["missing_required"]:
        lines.extend(["", "## Missing Required Artifacts", ""])
        lines.extend(markdown_table(report["missing_required"], ["group", "path", "placement", "note"]))

    if report["stale_claims"]:
        lines.extend(["", "## Stale Or Unsafe Claim Matches", ""])
        lines.extend(markdown_table(report["stale_claims"], ["path", "line", "reason", "text"]))

    lines.extend(["", "## Artifact Inventory", ""])
    lines.extend(markdown_table(report["artifacts"], ["group", "path", "placement", "exists", "status", "note"]))
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", default="outputs/reports/live/paper_artifact_readiness_check.json")
    parser.add_argument("--out-md", default="outputs/reports/live/paper_artifact_readiness_check.md")
    args = parser.parse_args()
    report = build_report()
    out_json = REPO_ROOT / args.out_json
    out_md = REPO_ROOT / args.out_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, report)
    print(json.dumps({"json": rel(out_json), "markdown": rel(out_md), "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
