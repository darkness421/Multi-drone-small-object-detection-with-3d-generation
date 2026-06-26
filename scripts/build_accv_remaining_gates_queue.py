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
TINYPERSON = ROOT / "outputs/experiments/tinyperson_corner_original/live_summary.csv"


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


def tinyperson_note(rows: list[dict[str, str]]) -> tuple[str, str]:
    if not rows:
        return "closed_archive_only", "TinyPerson rows are missing; no further TinyPerson experiments are scheduled."
    pieces = []
    complete = []
    for row in rows:
        raw_status = row.get("status") or "unknown"
        display_status = "complete" if raw_status == "complete" else "archived_stopped"
        pieces.append(
            f"{row.get('method')} seed {row.get('seed')} img{row.get('imgsz')}: "
            f"{display_status} e{row.get('latest_epoch')} best AP {fnum(row.get('best_ap'))}/"
            f"AP50 {fnum(row.get('best_ap50'))}"
        )
        if raw_status == "complete":
            complete.append(row.get("method", ""))
    status = "closed_archive_only"
    return status, "; ".join(pieces)


def build_rows() -> list[dict[str, str]]:
    readiness = read_json(READINESS)
    system = read_json(SYSTEM)
    threed = read_json(THREED)
    aerograph = read_json(AEROGRAPH)
    snapshot = read_json(SNAPSHOT)
    tinyperson_rows = read_csv(TINYPERSON)
    tinyperson_status, tinyperson_evidence = tinyperson_note(tinyperson_rows)
    tinyperson_action = (
        "Stop TinyPerson here. Keep existing rows as internal archive/protocol diagnostics only; do not include TinyPerson in the default main or supplementary paper."
    )

    detector = (snapshot.get("detector") or {})
    queues = (snapshot.get("queues") or {})
    detector_top = (detector.get("paper_facing_top_rows") or [{}])[0]
    manual_coverage = aerograph.get("manual_response_coverage") or {}
    effective_coverage = aerograph.get("effective_response_coverage") or {}
    system_detector = system.get("detector") or {}
    system_actors = system.get("actors") or {}
    pending_checks = [check for check in system.get("checks", []) if check.get("status") == "PENDING"]
    main_tex_gate = readiness.get("main_tex_gate") or {}
    latex_gate = readiness.get("latex_integrity_gate") or {}

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
            "priority": "P3",
            "gate": "TinyPerson archive-only diagnostic",
            "status": tinyperson_status,
            "evidence": tinyperson_evidence,
            "next_action": tinyperson_action,
            "paper_use": "internal_archive",
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
            "next_action": "Attach/install an upstream NeRF/3DGS/Instant-NGP runner and collect PSNR/SSIM/LPIPS/FPS/runtime rows; placeholders are not paper-valid.",
            "paper_use": "pending_3d",
        },
        {
            "priority": "P1",
            "gate": "AeroGraph external non-mock reasoner",
            "status": aerograph.get("status", "missing"),
            "evidence": (
                f"manual direct coverage={manual_coverage.get('matched_valid_response_count', '-')}/"
                f"{manual_coverage.get('prompt_count', '-')}; "
                f"reviewed candidate={effective_coverage.get('matched_valid_response_count', effective_coverage.get('matched_nonblank_response_count', '-'))}/"
                f"{effective_coverage.get('prompt_count', '-')}; "
                f"external replication={aerograph.get('external_provider_replication_ready')}"
            ),
            "next_action": "Keep Codex-assisted reviewed candidate visible; collect OpenAI/ChatGPT/local-provider replication before making a final external-provider reasoner claim.",
            "paper_use": "pending_reasoner",
        },
        {
            "priority": "P2",
            "gate": "MarineCity real-Cesium system smoke",
            "status": system.get("status", "missing"),
            "evidence": (
                f"tokens={system_detector.get('token_count')}; "
                f"actors={system_actors.get('actor_classes')}; "
                f"pending={len(pending_checks)}"
            ),
            "next_action": "Use as system/protocol validation only; upgrade after neural 3D and external reasoner gates pass.",
            "paper_use": "main_smoke_or_supp",
        },
        {
            "priority": "P2",
            "gate": "Overleaf/local compile sync",
            "status": "pending_main_tex_or_overleaf_sync" if not main_tex_gate.get("main_tex_present") else "local_main_tex_present",
            "evidence": f"local main.tex present={main_tex_gate.get('main_tex_present')}; latex check={latex_gate.get('status')}",
            "next_action": "Keep GitHub/Overleaf patch bundles synced; full compile verification requires the Overleaf project or a local main.tex checkout.",
            "paper_use": "paper_ops",
        },
    ]


def write_outputs(rows: list[dict[str, str]]) -> None:
    LIVE.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["priority", "gate", "status", "evidence", "next_action", "paper_use"])
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# ACCV Remaining Gates Queue",
        "",
        f"Updated: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        "",
        "This queue separates paper-ready evidence from pending gates. Do not promote a pending row into a main claim until its evidence column proves completion.",
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
        "1. Close TinyPerson as an internal archive-only diagnostic; do not spend more GPU time or default paper space on it.",
        "2. Keep VisDrone detector results as the main 2D claim: `Ours` in tables, SAFR-YOLO/P2P4-SelfAttnFR in method text.",
        "3. For 3D, use the verified MarineCity RGB/depth/pose package as input and collect real neural metrics before any reconstruction claim.",
        "4. For AeroGraph, keep the reviewed candidate visible and collect external OpenAI/ChatGPT/local-provider replication before final reasoner claims.",
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
