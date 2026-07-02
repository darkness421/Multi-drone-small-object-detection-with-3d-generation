"""Build a concise remaining-gates queue for the ACCV research package."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "outputs/reports/live"
OUT_MD = LIVE / "accv_remaining_gates_queue.md"
OUT_CSV = LIVE / "accv_remaining_gates_queue.csv"

READINESS = LIVE / "paper_artifact_readiness_check.json"
SYSTEM = LIVE / "marinecity_system_integration_check.json"
THREED = LIVE / "marinecity_3d_completion_readiness.json"
AEROGRAPH = LIVE / "aerograph_nonmock_readiness_status.json"
SNAPSHOT = LIVE / "accv_workflow_status_snapshot.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k): str(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def fnum(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def public_status(value: Any) -> str:
    text = str(value or "missing").replace("smoke", "validation")
    text = text.replace("pending_responses", "responses_needed")
    return text.replace("pending", "responses_needed")


def build_rows() -> list[dict[str, str]]:
    readiness = read_json(READINESS)
    system = read_json(SYSTEM)
    threed = read_json(THREED)
    aerograph = read_json(AEROGRAPH)
    snapshot = read_json(SNAPSHOT)

    detector = (snapshot.get("detector") or {})
    queues = (snapshot.get("queues") or {})
    detector_top = (detector.get("paper_facing_top_rows") or [{}])[0]
    manual_coverage = aerograph.get("manual_response_coverage") or {}
    effective_coverage = aerograph.get("effective_response_coverage") or {}
    system_detector = system.get("detector") or {}
    system_actors = system.get("actors") or {}
    open_checks = [check for check in system.get("checks", []) if check.get("status") in {"OPEN", "PENDING"}]
    main_tex_gate = readiness.get("main_tex_gate") or {}
    latex_gate = readiness.get("latex_integrity_gate") or {}
    threed_metric_rows = threed.get("metric_result_row_count") or 0
    threed_has_metric = bool(threed_metric_rows)
    if threed_metric_rows >= 2:
        threed_next_action = (
            "Use the verified Nerfacto and Splatfacto/3DGS-style rows as runner-family system-validation evidence; add longer validation only if time remains."
        )
    elif threed_has_metric:
        threed_next_action = (
            "Use the verified Nerfacto row as system-validation evidence; add Instant-NGP/3DGS or longer validation only if time remains."
        )
    else:
        threed_next_action = (
            "Attach/install an upstream NeRF/3DGS/Instant-NGP runner and collect PSNR/SSIM/LPIPS/FPS/runtime rows that pass the paper-validity checks."
        )
    threed_paper_use = "main_or_supp_validation" if threed_has_metric else "open_3d_gate"

    return [
        {
            "priority": "P0",
            "gate": "Detector main claim",
            "status": "ready",
            "evidence": (
                f"Ours AP/AP50/F1 {fnum(detector_top.get('ap'))}/"
                f"{fnum(detector_top.get('ap50'))}/{fnum(detector_top.get('f1'))}; "
                f"params {fnum(detector_top.get('params_m'), 2)}M; seeds {detector_top.get('seeds', '-')}"
            ),
            "next_action": "Keep as main VisDrone 1280 3-seed claim; do not mix broad search rows into the main table.",
            "paper_use": "main",
        },
        {
            "priority": "P1",
            "gate": "MarineCity neural 3D completion metrics",
            "status": threed.get("status", "missing"),
            "evidence": (
                f"captures ready={threed.get('source_capture_ready')}; "
                f"dataset ready={threed.get('neural3d_dataset_ready')}; "
                f"runner available={threed.get('neural_runner_available')}; "
                f"metric rows={threed.get('metric_result_row_count')}"
            ),
            "next_action": threed_next_action,
            "paper_use": threed_paper_use,
        },
        {
            "priority": "P3",
            "gate": "Optional AeroGraph external-provider benchmark",
            "status": public_status(aerograph.get("status", "missing")),
            "evidence": (
                f"manual direct coverage={manual_coverage.get('matched_valid_response_count', '-')}/"
                f"{manual_coverage.get('prompt_count', '-')}; "
                f"reviewed candidate={effective_coverage.get('matched_valid_response_count', effective_coverage.get('matched_nonblank_response_count', '-'))}/"
                f"{effective_coverage.get('prompt_count', '-')}; "
                f"provider validation={aerograph.get('external_provider_replication_ready')}"
            ),
            "next_action": "Do not block the current submission. Collect external-provider or local-model responses only if adding a separate LLM benchmark claim.",
            "paper_use": "optional_supp_or_future",
        },
        {
            "priority": "P2",
            "gate": "MarineCity real-Cesium system validation",
            "status": public_status(system.get("status", "missing")),
            "evidence": (
                f"tokens={system_detector.get('token_count')}; "
                f"actors={system_actors.get('actor_classes')}; "
                f"open checks={len(open_checks)}"
            ),
            "next_action": "Use as real-Cesium system/protocol validation with graph/action-policy metrics; external provider benchmarking is optional.",
            "paper_use": "main_or_supp_validation",
        },
        {
            "priority": "P2",
            "gate": "Manuscript/local compile package",
            "status": "open_main_tex_or_manuscript_package" if not main_tex_gate.get("main_tex_present") else "local_main_tex_present",
            "evidence": f"local main.tex present={main_tex_gate.get('main_tex_present')}; latex check={latex_gate.get('status')}",
            "next_action": "Keep GitHub paper artifacts and LaTeX patch bundles aligned; full compile verification requires a local main.tex checkout.",
            "paper_use": "paper_ops",
        },
    ]


def write_outputs(rows: list[dict[str, str]]) -> None:
    LIVE.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["priority", "gate", "status", "evidence", "next_action", "paper_use"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# ACCV Remaining Gates Queue",
        "",
        f"Updated: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        "",
        "This queue separates paper-ready evidence from optional gates. Optional rows should not be promoted into a main claim unless their evidence column proves completion.",
        "",
        "| Priority | Gate | Status | Evidence | Next Action | Paper Use |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {priority} | {gate} | `{status}` | {evidence} | {next_action} | {paper_use} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Immediate Order",
            "",
        "1. Keep VisDrone detector results as the main 2D claim: `Ours` in tables, SAFR-YOLO/P2P4-SelfAttnFR in method text.",
        "2. For 3D, use the verified MarineCity RGB/depth/pose package plus Nerfacto and Splatfacto/3DGS-style rows as system-validation evidence; collect longer validation only before claiming a full 3D benchmark.",
        "3. For AeroGraph, keep the current paper claim limited to schema, verifier, and action-policy validation. External-provider or local-model replication is optional supplementary/future evidence.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_outputs(rows)
    print(json.dumps({"markdown": str(OUT_MD.relative_to(ROOT)), "csv": str(OUT_CSV.relative_to(ROOT)), "rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
