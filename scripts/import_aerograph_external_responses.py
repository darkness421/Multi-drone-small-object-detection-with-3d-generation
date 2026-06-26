"""One-command import for external AeroGraph web/provider responses.

Use this after collecting ChatGPT/Codex/OpenAI-web/local-LLM answers in raw
Markdown, text, JSON, or JSONL files. The script normalizes raw responses,
imports them against either the compact 23-prompt real-capture pack or the full
49-prompt final pack, and rebuilds the paper/readiness artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


MODES = {
    "final49": {
        "prompt_pack": "outputs/reports/live/aerograph_prompt_pack/aerograph_prompts_all.jsonl",
        "normalized": "outputs/reasoning/aerograph_manual_responses.normalized.jsonl",
        "manual": "outputs/reasoning/aerograph_manual_responses.jsonl",
        "out_dir": "outputs/reasoning/aerograph_prompt_pack_eval_manual_web",
        "provider_default": "ChatGPT/Codex web final49",
        "normalization_report_json": "outputs/reports/live/aerograph_web_response_normalization_report.json",
        "normalization_report_md": "outputs/reports/live/aerograph_web_response_normalization_report.md",
    },
    "compact23": {
        "prompt_pack": "outputs/reports/live/aerograph_real_capture_prompt_pack/aerograph_real_capture_prompts_all.jsonl",
        "normalized": "outputs/reasoning/aerograph_real_capture_manual_responses.normalized.jsonl",
        "manual": "outputs/reasoning/aerograph_real_capture_manual_responses.jsonl",
        "out_dir": "outputs/reasoning/aerograph_real_capture_eval_manual_web",
        "provider_default": "ChatGPT/Codex web compact23",
        "normalization_report_json": "outputs/reports/live/aerograph_real_capture_web_response_normalization_report.json",
        "normalization_report_md": "outputs/reports/live/aerograph_real_capture_web_response_normalization_report.md",
    },
}


def run_cmd(cmd: list[str], *, allow_failure: bool = False) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    result = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }
    if proc.returncode != 0 and not allow_failure:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(proc.returncode)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(MODES), default="final49")
    parser.add_argument("--input", nargs="+", required=True, help="Raw web response files, directories, or globs.")
    parser.add_argument("--provider-label", default="", help="Provider label to write into the imported manifest.")
    parser.add_argument("--allow-partial", action="store_true", help="Allow import before all prompts have responses.")
    parser.add_argument("--require-valid", action="store_true", help="Fail normalization if any raw row fails response schema.")
    parser.add_argument("--skip-table", action="store_true", help="Skip final paper table rebuild.")
    args = parser.parse_args()

    cfg = MODES[args.mode]
    provider = args.provider_label or cfg["provider_default"]
    normalize_cmd = [
        sys.executable,
        "scripts/normalize_aerograph_web_responses.py",
        "--input",
        *args.input,
        "--out",
        cfg["normalized"],
        "--append-to",
        cfg["manual"],
        "--report-json",
        cfg["normalization_report_json"],
        "--report-md",
        cfg["normalization_report_md"],
    ]
    if args.require_valid:
        normalize_cmd.append("--require-valid")

    import_cmd = [
        sys.executable,
        "scripts/import_aerograph_manual_responses.py",
        "--prompt-pack",
        cfg["prompt_pack"],
        "--responses",
        cfg["manual"],
        "--provider-label",
        provider,
        "--out-dir",
        cfg["out_dir"],
    ]
    if args.allow_partial:
        import_cmd.append("--allow-partial")

    commands = [run_cmd(normalize_cmd), run_cmd(import_cmd, allow_failure=args.allow_partial)]
    if args.mode == "final49" and not args.skip_table:
        commands.append(run_cmd([sys.executable, "scripts/build_aerograph_reasoner_table.py"]))
    commands.append(run_cmd([sys.executable, "scripts/check_aerograph_nonmock_readiness.py"]))
    commands.append(run_cmd([sys.executable, "scripts/check_paper_artifact_readiness.py"]))
    commands.append(run_cmd([sys.executable, "scripts/build_accv_status_snapshot.py"]))
    commands.append(run_cmd([sys.executable, "scripts/build_accv_remaining_gates_queue.py"]))

    manifest_path = ROOT / cfg["out_dir"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    report = {
        "status": "aerograph_external_response_import_finished",
        "mode": args.mode,
        "provider_label": provider,
        "prompt_pack": cfg["prompt_pack"],
        "manual_responses": cfg["manual"],
        "out_dir": cfg["out_dir"],
        "manifest_status": manifest.get("status"),
        "non_mock_outputs_ready": manifest.get("non_mock_outputs_ready"),
        "valid_non_mock_output_count": manifest.get("valid_non_mock_output_count"),
        "missing_response_count": manifest.get("missing_response_count"),
        "commands": commands,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
