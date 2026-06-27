"""Build a concise next-execution handoff for the remaining ACCV gates."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "outputs/reports/live"
OUT = LIVE / "accv_next_execution_handoff.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def rel(path: Path | str) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    status = read_json(LIVE / "accv_workflow_status_snapshot.json")
    threed = read_json(LIVE / "marinecity_3d_completion_readiness.json")
    aerograph = read_json(LIVE / "aerograph_nonmock_readiness_status.json")
    prompt_integrity = read_json(LIVE / "aerograph_prompt_pack_integrity.json")
    paper = read_json(LIVE / "paper_artifact_readiness_check.json")
    external_caps = read_json(LIVE / "external_gate_capabilities.json")

    detector = status.get("detector", {}) or {}
    detector_top = (detector.get("paper_facing_top_rows") or [{}])[0]
    manual = aerograph.get("manual_response_coverage", {}) or {}
    web_batches = aerograph.get("web_batch_progress", []) or []
    first_batch = web_batches[0] if web_batches else {}
    external_aerograph = (external_caps.get("aerograph_execution", {}) or {})
    external_3d = (external_caps.get("neural_3d_execution", {}) or {})
    metric_rows = threed.get("metric_result_row_count") or 0
    metric_status = (
        "single-runner smoke metric available"
        if metric_rows
        else "metric rows still missing"
    )
    metric_next = (
        "Keep the verified Nerfacto row as paper-safe system-smoke evidence. Add another runner only if time allows before upgrading to a full benchmark claim."
        if metric_rows
        else "Attach an upstream runner such as Nerfstudio, Instant-NGP, or 3DGS and write non-placeholder PSNR/SSIM/LPIPS/FPS/runtime rows."
    )

    lines = [
        "# ACCV Next Execution Handoff",
        "",
        f"Updated: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        "",
        "This file lists only the next actions needed to move the research package closer to paper-ready completion. It intentionally separates paper-ready evidence from blocked external gates.",
        "",
        "## External Capability Snapshot",
        "",
        f"- Current shell capability status: `{external_caps.get('status', 'missing')}`.",
        f"- AeroGraph provider configured: `{external_aerograph.get('ready')}`; modes `{external_aerograph.get('provider_modes', [])}`.",
        f"- Neural-3D runner configured: `{external_3d.get('ready')}`; metric rows `{external_3d.get('metric_result_row_count')}`.",
        f"- Capability report: `outputs/reports/live/external_gate_capabilities.md`.",
        "",
        "## Already Paper-Ready",
        "",
        f"- Detector main claim: `Ours`, AP/AP50/F1 `{detector_top.get('ap')}`/`{detector_top.get('ap50')}`/`{detector_top.get('f1')}`, params `{detector_top.get('params_m')}M`, seeds `{detector_top.get('seeds')}`.",
        "- TinyPerson: corrected original-window/1280 diagnostic is complete, but Ours is below YOLOv9m; keep it as a supplementary limitation only.",
        f"- Paper artifact audit: `{paper.get('status')}`.",
        "",
        "## Gate 1: Neural 3D Completion Metrics",
        "",
        f"- Current status: `{threed.get('status')}`.",
        f"- Source capture ready: `{threed.get('source_capture_ready')}`; dataset ready: `{threed.get('neural3d_dataset_ready')}`; neural runner available: `{threed.get('neural_runner_available')}`.",
        f"- Transforms input: `{threed.get('neural3d_dataset_transforms')}`.",
        f"- Metric state: `{metric_status}`; metric rows `{metric_rows}`; missing optional methods: `{threed.get('missing_expected_methods')}`.",
        "",
        "Next executable options:",
        "",
        "```bash",
        "python scripts/check_marinecity_3d_runner_preflight.py",
        "python scripts/check_marinecity_3d_completion_readiness.py",
        "```",
        "",
        "After an upstream runner finishes, import its verified JSON/CSV metrics with:",
        "",
        "```bash",
        "python scripts/import_marinecity_3d_metrics.py PATH_TO_RUNNER_METRICS.json --overwrite",
        "python scripts/build_marinecity_3d_results_table.py",
        "python scripts/check_marinecity_3d_completion_readiness.py",
        "```",
        "",
        metric_next,
        "",
        "## Gate 2: AeroGraph External Non-Mock Reasoner",
        "",
        f"- Current status: `{aerograph.get('status')}`.",
        f"- Prompt-pack integrity: `{prompt_integrity.get('status')}`, prompts `{prompt_integrity.get('total_prompts')}`.",
        f"- Manual/direct valid responses: `{manual.get('matched_valid_response_count')}/{manual.get('prompt_count')}`.",
        f"- External-provider replication ready: `{aerograph.get('external_provider_replication_ready')}`.",
        "",
        "Fast smoke path:",
        "",
        "```bash",
        "OPENAI_API_KEY=... AEROGRAPH_PROVIDER=openai bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh",
        "# or",
        "AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' AEROGRAPH_PROVIDER=command bash scripts/ubuntu/start_aerograph_real_capture_smoke_queue.sh",
        "# AEROGRAPH_COMMAND can point to any local command that reads stdin and returns AeroGraph JSON.",
        "```",
        "",
        "Final 49-prompt path:",
        "",
        "```bash",
        "OPENAI_API_KEY=... AEROGRAPH_PROVIDER=openai bash scripts/ubuntu/start_aerograph_nonmock_queue.sh",
        "# or",
        "AEROGRAPH_COMMAND='COMMAND_THAT_READS_STDIN_AND_RETURNS_JSON' AEROGRAPH_PROVIDER=command bash scripts/ubuntu/start_aerograph_nonmock_queue.sh",
        "# AEROGRAPH_COMMAND can point to any local command that reads stdin and returns AeroGraph JSON.",
        "```",
        "",
        "Manual web fallback:",
        "",
        f"- Start with batch: `{first_batch.get('path', 'outputs/reports/live/aerograph_prompt_pack/web_batches/aerograph_web_batch_01_001-010.md')}`.",
        "- Save JSONL answers into `outputs/reasoning/aerograph_manual_responses.jsonl`.",
        "- Or save raw ChatGPT/Codex/OpenAI-web answers as `.md`, `.txt`, `.json`, or `.jsonl` and run the one-command importer:",
        "",
        "```bash",
        "python scripts/import_aerograph_external_responses.py \\",
        "  --mode final49 \\",
        "  --input reasoning/aerograph_web_raw_batches/*.md \\",
        "  --provider-label \"ChatGPT/Codex web\"",
        "",
        "python scripts/import_aerograph_external_responses.py \\",
        "  --mode compact23 \\",
        "  --input reasoning/aerograph_real_capture_web_raw_batches/*.md \\",
        "  --provider-label \"ChatGPT/Codex web compact\"",
        "```",
        "",
        "```bash",
        "python scripts/import_aerograph_manual_responses.py \\",
        "  --responses outputs/reasoning/aerograph_manual_responses.jsonl \\",
        "  --provider-label \"ChatGPT/Codex web\" \\",
        "  --out-dir outputs/reasoning/aerograph_prompt_pack_eval_manual_web",
        "python scripts/build_aerograph_reasoner_table.py",
        "python scripts/check_aerograph_nonmock_readiness.py",
        "python scripts/check_paper_artifact_readiness.py",
        "```",
        "",
        "## Safe Rebuild After Any New Result",
        "",
        "```bash",
        "python scripts/build_accv_remaining_gates_queue.py",
        "python scripts/build_accv_status_snapshot.py",
        "python scripts/build_live_training_dashboard.py",
        "python scripts/check_latex_patch_integrity.py",
        "```",
        "",
    ]
    LIVE.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"handoff": rel(OUT)}, indent=2))


if __name__ == "__main__":
    main()
